"""
_directory_sync.py — Sync faculty/staff and department directories from cccc.edu.

Scrapes the public CCCC Faculty & Staff Directory and Department & Office
Directory, then writes markdown reference files.

Usage via CLI:
    python tools/notes_helper.py sync-directory
    python tools/notes_helper.py sync-directory --dry-run
    python tools/notes_helper.py sync-directory --with-detail
"""

from __future__ import annotations

import html as html_mod
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FACULTY_URL = "https://www.cccc.edu/about/faculty-staff-directory"
DEPT_URL = "https://www.cccc.edu/about/department-office-directory"
BASE_URL = "https://www.cccc.edu"

REPO_ROOT = Path(__file__).resolve().parent.parent
FACULTY_MD = REPO_ROOT / "documentation" / "faculty-staff-directory.md"
DEPT_MD = REPO_ROOT / "documentation" / "department-office-directory.md"

# Regex patterns for listing page
_ITEM_RE = re.compile(
    r'<article\s+class="faculty-staff__item">\s*'
    r'<div\s+class="faculty-staff__image">\s*'
    r'(?:<img\s+src="([^"]*)"[^>]*>)?\s*'
    r'</div>\s*'
    r'<div\s+class="faculty-staff__content">.*?'
    r'<h4\s+class="faculty-staff__name">\s*'
    r'<a\s+href="([^"]*)">\s*(.*?)\s*</a>\s*'
    r'</h4>\s*'
    r'<div\s+class="faculty-staff__role">\s*(.*?)\s*</div>\s*'
    r'<div\s+class="faculty-staff__department">(.*?)</div>',
    re.DOTALL,
)

# Detail page patterns
_EMAIL_RE = re.compile(r'mailto:([\w.+-]+@cccc\.edu)')
_PHONE_RE = re.compile(r'\((\d{3})\)\s*(\d{3})[\s-]?(\d{4})')
_CAMPUS_RE = re.compile(
    r'<a[^>]*class="inline-text-link"[^>]*>(.*?)</a>',
)
_BUILDING_RE = re.compile(
    r'<p>(\d+\s+\w.*?)</p>',  # e.g. "6 Lett Hall"
)

# Department directory patterns
_DEPT_LINK_RE = re.compile(
    r'<span\s+class="field-content">\s*<a\s+href="([^"]*)">(.*?)</a>\s*</span>'
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class StaffEntry:
    """One faculty/staff member."""
    __slots__ = (
        "name", "role", "department", "photo_url",
        "detail_path", "email", "phone", "campus", "building",
    )

    def __init__(
        self,
        name: str,
        role: str,
        department: str,
        photo_url: str = "",
        detail_path: str = "",
    ):
        self.name = name
        self.role = role
        self.department = department
        self.photo_url = photo_url
        self.detail_path = detail_path
        self.email = ""
        self.phone = ""
        self.campus = ""
        self.building = ""


# ---------------------------------------------------------------------------
# Scraper — listing pages
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Decode HTML entities and normalize whitespace."""
    text = html_mod.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _get_session() -> "requests.Session":
    """Create a requests session with retry and keep-alive."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "CCCC-WorkNotes/1.0 (staff reference sync)",
    })
    return s


def _fetch(session: "requests.Session", url: str, retries: int = 2) -> str:
    """GET with retry on timeout."""
    for attempt in range(retries + 1):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            if attempt == retries:
                raise
            print(f"    ⏳ Retry {attempt + 1} for {url}")
            time.sleep(2)
    return ""  # unreachable


def fetch_listing_page(session: "requests.Session", page: int = 0) -> list[StaffEntry]:
    """Fetch one page of the faculty/staff listing (20 per page)."""
    if requests is None:
        raise RuntimeError("pip install requests")

    url = f"{FACULTY_URL}?page={page}"
    html = _fetch(session, url)

    entries: list[StaffEntry] = []
    for m in _ITEM_RE.finditer(html):
        photo_src, detail_href, name_raw, role_raw, dept_raw = m.groups()
        entry = StaffEntry(
            name=_clean(name_raw),
            role=_clean(role_raw),
            department=_clean(dept_raw),
            photo_url=(BASE_URL + photo_src) if photo_src else "",
            detail_path=detail_href or "",
        )
        entries.append(entry)
    return entries


def fetch_all_staff() -> list[StaffEntry]:
    """Fetch all faculty/staff from all listing pages."""
    session = _get_session()
    all_staff: list[StaffEntry] = []
    page = 0
    while True:
        entries = fetch_listing_page(session, page)
        if not entries:
            break
        all_staff.extend(entries)
        print(f"  Page {page}: {len(entries)} staff")
        page += 1
        time.sleep(0.5)
    return all_staff


# ---------------------------------------------------------------------------
# Scraper — detail pages (optional, slower)
# ---------------------------------------------------------------------------

def fetch_detail(session: "requests.Session", entry: StaffEntry) -> None:
    """Fetch the detail page for one staff member and populate contact info."""
    if requests is None or not entry.detail_path:
        return

    url = BASE_URL + entry.detail_path
    try:
        html = _fetch(session, url)
    except Exception:
        return

    # Email
    em = _EMAIL_RE.search(html)
    if em:
        entry.email = em.group(1)

    # Phone
    ph = _PHONE_RE.search(html)
    if ph:
        entry.phone = f"({ph.group(1)}) {ph.group(2)}-{ph.group(3)}"

    # Campus
    # Look inside <address class="faculty-bio__address">
    addr_match = re.search(
        r'<address\s+class="faculty-bio__address">(.*?)</address>',
        html, re.DOTALL,
    )
    if addr_match:
        addr_html = addr_match.group(1)
        ca = _CAMPUS_RE.search(addr_html)
        if ca:
            entry.campus = _clean(ca.group(1))
        # Building / room — look for lines like "6 Lett Hall"
        # These are in <p> tags after the address
        paragraphs = re.findall(r'<p>(.*?)</p>', addr_html, re.DOTALL)
        for p in paragraphs:
            clean_p = _clean(p)
            # Skip address lines (contain street, state, zip)
            if re.search(r'\d{5}', clean_p):
                continue
            # Skip phone numbers
            if re.search(r'\(\d{3}\)', clean_p):
                continue
            # Skip campus link text (already captured)
            if entry.campus and entry.campus in clean_p:
                continue
            if clean_p and not entry.building:
                entry.building = clean_p


# ---------------------------------------------------------------------------
# Scraper — department directory
# ---------------------------------------------------------------------------

def fetch_all_departments() -> list[tuple[str, str]]:
    """Fetch department names and their filtered faculty URLs.

    Returns list of (department_name, faculty_filter_url).
    """
    if requests is None:
        raise RuntimeError("pip install requests")

    session = _get_session()
    departments: list[tuple[str, str]] = []
    page = 0
    while True:
        url = f"{DEPT_URL}?page={page}"
        html = _fetch(session, url)

        found = _DEPT_LINK_RE.findall(html)
        if not found:
            break
        for href, name in found:
            clean_href = html_mod.unescape(href)
            departments.append((_clean(name), BASE_URL + clean_href))
        print(f"  Dept page {page}: {len(found)} departments")
        page += 1
        time.sleep(0.5)

    return departments


# ---------------------------------------------------------------------------
# Markdown generation — Faculty/Staff Directory
# ---------------------------------------------------------------------------

def generate_faculty_md(
    staff: list[StaffEntry],
    with_detail: bool = False,
) -> str:
    """Generate faculty-staff-directory.md content."""
    # Group by department
    by_dept: dict[str, list[StaffEntry]] = defaultdict(list)
    for s in staff:
        by_dept[s.department or "Other"].append(s)

    # Sort departments alphabetically
    sorted_depts = sorted(by_dept.keys())

    parts = [
        "# 👥 Faculty & Staff Directory",
        "",
        "Auto-synced from [cccc.edu/about/faculty-staff-directory]"
        "(https://www.cccc.edu/about/faculty-staff-directory).",
        "",
        f"> {len(staff)} faculty & staff across {len(sorted_depts)} departments.",
        "",
        "---",
        "",
    ]

    # Table of contents
    parts.append("## Contents")
    parts.append("")
    for dept in sorted_depts:
        anchor = re.sub(r"[^a-z0-9]+", "-", dept.lower()).strip("-")
        parts.append(f"- [{dept}](#{anchor}) ({len(by_dept[dept])})")
    parts.append("")
    parts.append("---")
    parts.append("")

    # Each department section
    for dept in sorted_depts:
        members = sorted(by_dept[dept], key=lambda s: s.name)
        parts.append(f"### {dept}")
        parts.append("")

        if with_detail:
            parts.append("| | Name | Role | Email | Phone | Campus |")
            parts.append("|---|---|---|---|---|---|")
            for s in members:
                photo = f'<img src="{s.photo_url}" width="40" height="40">' if s.photo_url else ""
                email = s.email or ""
                phone = s.phone or ""
                campus = s.campus or ""
                if s.building:
                    campus = f"{campus} — {s.building}" if campus else s.building
                profile = f"[{s.name}]({BASE_URL}{s.detail_path})" if s.detail_path else s.name
                parts.append(f"| {photo} | {profile} | {s.role} | {email} | {phone} | {campus} |")
        else:
            parts.append("| | Name | Role |")
            parts.append("|---|---|---|")
            for s in members:
                photo = f'<img src="{s.photo_url}" width="40" height="40">' if s.photo_url else ""
                profile = f"[{s.name}]({BASE_URL}{s.detail_path})" if s.detail_path else s.name
                parts.append(f"| {photo} | {profile} | {s.role} |")

        parts.append("")

    parts.append("---")
    today = datetime.now().strftime("%Y-%m-%d")
    parts.append(f"*Last synced from cccc.edu: {today}*")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Markdown generation — Department/Office Directory
# ---------------------------------------------------------------------------

def generate_dept_md(departments: list[tuple[str, str]]) -> str:
    """Generate department-office-directory.md content."""
    parts = [
        "# 🏢 Department & Office Directory",
        "",
        "Auto-synced from [cccc.edu/about/department-office-directory]"
        "(https://www.cccc.edu/about/department-office-directory).",
        "",
        f"> {len(departments)} departments and offices.",
        "",
        "---",
        "",
        "| # | Department / Office | Faculty Listing |",
        "|---|---|---|",
    ]

    for i, (name, url) in enumerate(departments, 1):
        parts.append(f"| {i} | {name} | [View staff]({url}) |")

    parts.append("")
    parts.append("---")
    today = datetime.now().strftime("%Y-%m-%d")
    parts.append(f"*Last synced from cccc.edu: {today}*")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def cmd_sync_directory(args) -> None:
    """Sync faculty/staff and department directories from cccc.edu."""
    dry_run = args.dry_run
    with_detail = getattr(args, "with_detail", False)

    print("🔄 Syncing directories from cccc.edu ...")

    # Faculty/Staff
    print("\n📋 Faculty & Staff Directory:")
    staff = fetch_all_staff()
    print(f"  Total: {len(staff)} staff members")

    if with_detail:
        print("\n📇 Fetching contact details (this may take a few minutes) ...")
        detail_session = _get_session()
        for i, s in enumerate(staff):
            fetch_detail(detail_session, s)
            if (i + 1) % 50 == 0:
                print(f"  ... {i + 1}/{len(staff)}")
            time.sleep(0.3)
        print(f"  Done — {sum(1 for s in staff if s.email)} with email")

    faculty_md = generate_faculty_md(staff, with_detail=with_detail)

    # Department/Office
    print("\n🏢 Department & Office Directory:")
    departments = fetch_all_departments()
    print(f"  Total: {len(departments)} departments")

    dept_md = generate_dept_md(departments)

    # Output
    if dry_run:
        print(f"\n--- DRY RUN — faculty-staff-directory.md ({len(staff)} staff) ---")
        # Show first 3000 chars
        print(faculty_md[:3000])
        if len(faculty_md) > 3000:
            print(f"\n  ... ({len(faculty_md)} chars total, truncated)")
        print(f"\n--- DRY RUN — department-office-directory.md ({len(departments)} depts) ---")
        print(dept_md[:2000])
    else:
        FACULTY_MD.write_text(faculty_md, encoding="utf-8")
        print(f"\n✅ Wrote {FACULTY_MD.name} ({len(staff)} staff)")

        DEPT_MD.write_text(dept_md, encoding="utf-8")
        print(f"✅ Wrote {DEPT_MD.name} ({len(departments)} departments)")
