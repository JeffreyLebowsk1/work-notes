"""
_calendar_sync.py — Sync academic-calendar.md from calendar.cccc.edu.

Scrapes the public CCCC college calendar, filters for academic/registrar
events, and writes (or updates) academic-calendar.md in the repo root.

Usage via CLI:
    python tools/notes_helper.py sync-calendar
    python tools/notes_helper.py sync-calendar --year 2026
    python tools/notes_helper.py sync-calendar --dry-run
"""

from __future__ import annotations

import html as html_mod
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CALENDAR_URL = "https://calendar.cccc.edu/month/{year}/{month:02d}/15/"

REPO_ROOT = Path(__file__).resolve().parent.parent
CALENDAR_MD = REPO_ROOT / "academic-calendar.md"

# Regex patterns for parsing the HTML
_DAY_RE = re.compile(r'href="/day/(\d{4})/(\d{1,2})/(\d{1,2})/"')
_EVENT_LI_RE = re.compile(
    r'<li\s+class="mon_event_(?:allday|timed)">\s*'
    r'<a[^>]*>\s*(.*?)\s*</a>',
    re.DOTALL,
)
_TIME_SPAN_RE = re.compile(
    r'<span\s+class="short_start_time">\s*\d{1,2}(?::\d{2})?(?:am|pm)\s*</span>\s*',
    re.IGNORECASE,
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

# Keywords that indicate an academic / registrar event (case-insensitive)
_ACADEMIC_KEYWORDS = [
    r"class(?:es)?\s+begin",
    r"term\b.*\bbegin",
    r"semester\b.*\bbegin",
    r"last\s+day\s+to\s+add",
    r"last\s+day\s+to\s+drop",
    r"last\s+day\s+of\s+class",
    r"\bdrop\b.*\brefund",
    r"\bcensus\b",
    r"\bmidterm\b",
    r"withdraw",
    r"\bgrades?\s+due\b",
    r"graduation\b",
    r"commencement",
    r"\bbreak\b",
    r"\bholiday\b",
    r"college\s+closed",
    r"session\b.*\bbegin",
    r"session\b.*\bend",
    r"registration\b",
    r"enrollment",
    r"deregistration",
    r"wellness\s+day",
    r"student\s+break",
    r"\bterm\b.*\bend",
    r"spring\b.*\bend",
    r"summer\b.*\bend",
    r"fall\b.*\bend",
    r"grad(?:uation)?\s+app",
    r"diploma",
    r"\bfinals?\b",
    r"tuition\s+due",
    r"payment\s+due",
    r"orientation",
]
_ACADEMIC_RE = re.compile("|".join(_ACADEMIC_KEYWORDS), re.IGNORECASE)

# Patterns to exclude even if keywords match
_EXCLUDE_RE = re.compile(
    r"basketball|foundation|blood\s+drive|art\s+of\s+conversation"
    r"|chips\s+&\s+tips|thrive|book\s+club|fundraiser|gala"
    r"|cougar\s+classic",
    re.IGNORECASE,
)

# Term boundaries — month ranges (inclusive)
_TERM_MONTHS: dict[str, tuple[int, int]] = {
    "spring": (1, 5),
    "summer": (5, 8),
    "fall": (8, 12),
}

# ---------------------------------------------------------------------------
# Event ranking  (1 = critical … 4 = noise)
# ---------------------------------------------------------------------------
# Matched top-to-bottom; first match wins.

_RANK_RULES: list[tuple[int, re.Pattern[str]]] = [
    # --- Tier 4  (noise) — check first so it can override lower tiers ---
    (4, re.compile(
        r"notif(?:y|ication)\b.*\bmidterm"
        r"|trio\b|c-step|upward\s+bound"
        r"|cosmetic\s+arts"
        r"|CEC\s+graduation"
        r"|graduation\s+practice",
        re.I,
    )),
    # --- Tier 1  (critical) ---
    (1, re.compile(
        r"term.*classes\s+begin|term\s+begins|term\s+ends"
        r"|spring\s+graduation|summer\s+graduation|fall\s+graduation"
        r"|commencement"
        r"|grades?\s+due\s+to\s+registrar"
        r"|holiday|college\s+closed"
        r"|student\s+break|wellness\s+day",
        re.I,
    )),
    # --- Tier 2a — compound session endings (e.g. "10-wk & Late Session Ends") ---
    (2, re.compile(r"\d+[\s-]?w.*&.*session\s+ends", re.I)),
    # --- Tier 3  (detail) — check BEFORE tier 2 to catch sub-sessions ---
    (3, re.compile(
        r"12[\s-]?w(?:ee)?k"               # any 12-week event
        r"|late\s+session"                  # any late session event
        r"|75%\s+refund"                    # 75% refund (granular)
        r"|DE\s+census"                     # DE-specific census
        r"|2nd\s+8[\s-]?w.*(?:drop|refund|census)"  # 2nd 8-wk details
        r"|orientation"
        r"|enrollment|re-enrollment"
        r"|registration\s+paused"
        r"|deregistration"
        r"|grades?\s+due",                  # non-registrar grades-due
        re.I,
    )),
    # --- Tier 2  (important) ---
    (2, re.compile(
        r"last\s+day\s+to\s+add"
        r"|last\s+day\s+to\s+drop"
        r"|last\s+day.*withdraw"
        r"|census"
        r"|midterm"
        r"|session\s+(?:begins|ends)"
        r"|registration.*(?:begins|ends|opens)"
        r"|graduation\s+app"
        r"|finals",
        re.I,
    )),
]


def rank_event(title: str) -> int:
    """Return the tier (1-4) for an event. Unmatched academic events → 3."""
    for tier, pattern in _RANK_RULES:
        if pattern.search(title):
            return tier
    return 3  # default for anything that passed _is_academic


# ---------------------------------------------------------------------------
# HTML parsing helpers
# ---------------------------------------------------------------------------

def _clean_event_title(raw: str) -> str:
    """Strip HTML tags, time spans, and excess whitespace from an event title."""
    text = _TIME_SPAN_RE.sub("", raw)
    text = _HTML_TAG_RE.sub("", text)
    text = html_mod.unescape(text)       # &amp; → &, etc.
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def _is_academic(title: str) -> bool:
    """Return True if the event title looks like an academic/registrar event."""
    if _EXCLUDE_RE.search(title):
        return False
    return bool(_ACADEMIC_RE.search(title))


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

def fetch_month(year: int, month: int) -> list[tuple[date, str]]:
    """Fetch one month page and return a list of (date, event_title) tuples."""
    if requests is None:
        raise RuntimeError("The 'requests' package is required. pip install requests")

    url = CALENDAR_URL.format(year=year, month=month)
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    html = resp.text

    # Build position-ordered list of day markers
    days: list[tuple[int, date]] = []
    for m in _DAY_RE.finditer(html):
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            days.append((m.start(), date(y, mo, d)))
        except ValueError:
            continue  # skip invalid dates (e.g. overflow cells)

    # Build position-ordered list of event titles
    events: list[tuple[int, str]] = []
    for m in _EVENT_LI_RE.finditer(html):
        title = _clean_event_title(m.group(1))
        if title:
            events.append((m.start(), title))

    # Associate each event with the nearest preceding day marker
    results: list[tuple[date, str]] = []
    for epos, title in events:
        # Find the day whose position is closest before the event
        best_day = None
        for dpos, d in days:
            if dpos <= epos:
                best_day = d
            else:
                break
        if best_day is not None:
            results.append((best_day, title))

    # Deduplicate (events appear twice in HTML: grid + modal popup)
    seen: set[tuple[date, str]] = set()
    unique: list[tuple[date, str]] = []
    for item in results:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return unique


def fetch_term_events(
    year: int,
    month_start: int = 1,
    month_end: int = 12,
    max_tier: int = 2,
) -> list[tuple[date, str, int]]:
    """Fetch events for a range of months, filter, rank, and return.

    Returns list of (date, title, tier) sorted by date.
    Only events with tier <= *max_tier* are included.
    """
    all_events: list[tuple[date, str]] = []
    for month in range(month_start, month_end + 1):
        try:
            raw = fetch_month(year, month)
        except Exception as exc:
            print(f"  ⚠  Could not fetch {year}-{month:02d}: {exc}")
            continue
        academic = [(d, t) for d, t in raw if _is_academic(t)]
        print(f"  {year}-{month:02d}: {len(raw)} total, {len(academic)} academic")
        all_events.extend(academic)

    # Filter to target year only (boundary months show neighboring-year days)
    all_events = [(d, t) for d, t in all_events if d.year == year]

    # Deduplicate across months (overlapping days at month boundaries)
    seen: set[tuple[date, str]] = set()
    unique: list[tuple[date, str]] = []
    for item in all_events:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    # Collapse near-duplicate titles on the same date (e.g. "Holiday College
    # Closed" vs "Holiday - College Closed") by normalizing punctuation.
    def _norm(t: str) -> str:
        return re.sub(r"[\s\-–—]+", " ", t).strip().lower()

    deduped: list[tuple[date, str]] = []
    seen_norm: set[tuple[date, str]] = set()
    for d, t in unique:
        key = (d, _norm(t))
        if key not in seen_norm:
            seen_norm.add(key)
            deduped.append((d, t))

    # Rank and filter
    ranked: list[tuple[date, str, int]] = []
    for d, t in deduped:
        tier = rank_event(t)
        if tier <= max_tier:
            ranked.append((d, t, tier))

    ranked.sort(key=lambda x: x[0])
    return ranked


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _classify_term(d: date, title: str = "") -> str:
    """Classify a date into spring, summer, or fall.

    Uses explicit term keywords in the title first, then falls back
    to date-based heuristics (May 15 is the spring/summer boundary).
    """
    t = title.lower()
    if "summer" in t:
        return "summer"
    if "fall" in t:
        return "fall"
    if "spring" in t:
        return "spring"
    # Date-based fallback
    if d.month <= 4 or (d.month == 5 and d.day <= 14):
        return "spring"
    if d.month <= 7 or (d.month == 8 and d.day <= 14):
        return "summer"
    return "fall"


def _format_date(d: date) -> str:
    """Format a date as 'Mon DD' (e.g. 'Jan 12')."""
    return d.strftime("%b %-d") if hasattr(d, "strftime") else str(d)


def _format_date_win(d: date) -> str:
    """Format a date as 'Mon DD', works on Windows (no %-d)."""
    return f"{d.strftime('%b')} {d.day}"


def _build_term_table(events: list[tuple[date, str, int]], term: str, year: int) -> str:
    """Build a markdown table for one term."""
    label = term.capitalize()
    lines = [
        f"## 🗓️ {label} {year}",
        "",
        "| Event | Date | Notes |",
        "|---|---|---|",
    ]
    if not events:
        lines.append("| *No events found yet* | | Check [calendar.cccc.edu](https://calendar.cccc.edu/) |")
    else:
        for d, title, _tier in events:
            date_str = _format_date_win(d)
            lines.append(f"| {title} | {date_str} | |")

    lines.append("")
    return "\n".join(lines)


def generate_calendar_md(events: list[tuple[date, str, int]], year: int) -> str:
    """Generate the full academic-calendar.md content."""
    # Split events by term
    by_term: dict[str, list[tuple[date, str, int]]] = defaultdict(list)
    for d, title, tier in events:
        term = _classify_term(d, title)
        by_term[term].append((d, title, tier))

    # Read the existing file to preserve the Holiday Calendar section
    holiday_section = ""
    registrar_section = ""
    if CALENDAR_MD.exists():
        existing = CALENDAR_MD.read_text(encoding="utf-8")
        # Extract holiday section (everything from "## 🏖️" to end)
        holiday_match = re.search(
            r"(## 🏖️ CCCC Holiday Calendar.*)",
            existing,
            re.DOTALL,
        )
        if holiday_match:
            holiday_section = holiday_match.group(1).rstrip()

        # Extract registrar section
        registrar_match = re.search(
            r"(## 📌 Registrar Office Key Dates.*?)(?=\n---|\n## 🏖️)",
            existing,
            re.DOTALL,
        )
        if registrar_match:
            registrar_section = registrar_match.group(1).rstrip()

    # Build output
    parts = [
        "# 📅 Academic Calendar",
        "",
        "Key dates and deadlines for the current and upcoming academic year.",
        "",
        "> 🔗 Official CCCC Calendar: [calendar.cccc.edu](https://calendar.cccc.edu/)",
        "",
        "---",
        "",
    ]

    for term in ("spring", "summer", "fall"):
        parts.append(_build_term_table(by_term.get(term, []), term, year))
        parts.append("")

    parts.append("---")
    parts.append("")

    if registrar_section:
        parts.append(registrar_section)
        parts.append("")
        parts.append("---")
        parts.append("")

    if holiday_section:
        parts.append(holiday_section)
    else:
        parts.append("## 🏖️ CCCC Holiday Calendar 2025–2026")
        parts.append("")
        parts.append("*See `assets/documents/Holiday_Calendar_Approved_2025-2026_1.pdf`*")

    parts.append("")
    parts.append("---")
    today = datetime.now().strftime("%Y-%m-%d")
    parts.append(f"*Last synced from calendar.cccc.edu: {today}*")
    parts.append("")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def cmd_sync_calendar(args) -> None:
    """Sync academic-calendar.md from calendar.cccc.edu."""
    year = args.year
    dry_run = args.dry_run

    # --detail → tiers 1-3, --all → tiers 1-4, default → tiers 1-2
    if getattr(args, "all", False):
        max_tier = 4
    elif getattr(args, "detail", False):
        max_tier = 3
    else:
        max_tier = 2

    tier_label = {2: "critical + important", 3: "+ detail", 4: "all events"}
    print(
        f"🔄 Syncing academic calendar for {year} from calendar.cccc.edu "
        f"(showing {tier_label.get(max_tier, 'tier≤' + str(max_tier))}) ..."
    )
    events = fetch_term_events(year, max_tier=max_tier)

    if not events:
        print("  No academic events found.")
        return

    print(f"\n📋 {len(events)} events after ranking (tier ≤ {max_tier})")
    md = generate_calendar_md(events, year)

    if dry_run:
        print("\n--- DRY RUN — would write to academic-calendar.md ---")
        print(md)
        return

    CALENDAR_MD.write_text(md, encoding="utf-8")
    print(f"\n✅ Wrote {CALENDAR_MD.relative_to(REPO_ROOT)}")
