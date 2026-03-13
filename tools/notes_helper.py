#!/usr/bin/env python3
"""
notes_helper.py — Analyze, sort, and organize your work notes.

Usage:
    python3 tools/notes_helper.py analyze [FILE]
    python3 tools/notes_helper.py sort [--by date|size|name] [--folder FOLDER]
    python3 tools/notes_helper.py organize [--output FILE]
    python3 tools/notes_helper.py search KEYWORD [--folder FOLDER]
    python3 tools/notes_helper.py import FILE [--dest DIR] [--dry-run] [--force] [--organize]
    python3 tools/notes_helper.py agent
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
IGNORED_DIRS = {".git", "tools", "assets", "inbox"}


def _all_notes(root: Path = REPO_ROOT) -> list[Path]:
    """Return all Markdown files in the repository, sorted by path."""
    notes = []
    for path in root.rglob("*.md"):
        if not any(part in IGNORED_DIRS for part in path.parts):
            notes.append(path)
    return sorted(notes)


def _all_assets() -> list[Path]:
    """Return all non-hidden, non-placeholder files in assets/, sorted by path."""
    assets_dir = REPO_ROOT / "assets"
    if not assets_dir.exists():
        return []
    return sorted(
        p for p in assets_dir.rglob("*")
        if p.is_file()
        and not p.name.startswith(".")
        and p.name != ".gitkeep"
    )


def _asset_meta(path: Path) -> dict:
    """Extract metadata from any asset file (Markdown or binary)."""
    stat = path.stat()
    size_bytes = stat.st_size
    modified = datetime.fromtimestamp(stat.st_mtime)

    ext = path.suffix.lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"):
        kind = "image"
    elif ext == ".pdf":
        kind = "document"
    elif ext in (".xlsx", ".xls", ".csv", ".ods", ".numbers"):
        kind = "spreadsheet"
    elif ext in (".md", ".txt"):
        kind = "text"
    else:
        kind = ext.lstrip(".") or "file"

    if size_bytes >= 1_048_576:
        size_display = f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes >= 1024:
        size_display = f"{size_bytes / 1024:.1f} KB"
    else:
        size_display = f"{size_bytes} B"

    try:
        rel_to_assets = path.relative_to(REPO_ROOT / "assets")
        subfolder = rel_to_assets.parts[0] if len(rel_to_assets.parts) > 1 else "(root)"
    except ValueError:
        subfolder = "(external)"

    return {
        "path": path,
        "relative": _relative(path),
        "name": path.name,
        "kind": kind,
        "size_bytes": size_bytes,
        "size_display": size_display,
        "modified": modified,
        "subfolder": subfolder,
    }


def _relative(path: Path) -> str:
    """Return path relative to the repo root, or the absolute path if outside the repo."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _parse_note(path: Path) -> dict:
    """Extract metadata from a single Markdown file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Title: first H1 heading or filename stem
    title = path.stem.replace("-", " ").replace("_", " ").title()
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip().lstrip("🎓📄🏠🔒📅📓📁📣").strip()
            break

    # All headings
    headings = [
        (len(m.group(1)), line.lstrip("# ").strip())
        for line in lines
        if (m := re.match(r"^(#{1,6})\s", line))
    ]

    # Word count (non-empty lines, strip markdown syntax)
    words = len(re.findall(r"\b\w+\b", re.sub(r"[#*`_>\[\]()!|]", " ", text)))

    # Action items — Markdown task list items  (- [ ] and - [x])
    open_items = [
        line.strip()
        for line in lines
        if re.match(r"^\s*-\s+\[ \]", line)
    ]
    done_items = [
        line.strip()
        for line in lines
        if re.match(r"^\s*-\s+\[x\]", line, re.IGNORECASE)
    ]

    # Dates mentioned in the file (YYYY-MM-DD)
    dates_in_text = sorted(set(re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)))

    # File dates
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime)

    try:
        folder = (
            path.parent.relative_to(REPO_ROOT).parts[0]
            if path.parent != REPO_ROOT
            else "(root)"
        )
    except ValueError:
        folder = "(external)"

    return {
        "path": path,
        "relative": _relative(path),
        "title": title,
        "headings": headings,
        "words": words,
        "open_items": open_items,
        "done_items": done_items,
        "dates_in_text": dates_in_text,
        "modified": modified,
        "folder": folder,
    }


# ---------------------------------------------------------------------------
# Import helpers
# ---------------------------------------------------------------------------

FOLDER_KEYWORDS: dict[str, list[str]] = {
    "graduation": [
        "graduation", "ceremony", "commencement", "graduate", "diploma",
        "cap and gown", "honor", "honours", "regalia",
    ],
    "meetings": [
        "meeting", "agenda", "minutes", "attendees", "action items",
        "discussion", "follow-up", "follow up",
    ],
    "daily-logs": [
        "today", "daily log", "day log", "log for", "daily notes",
        "today's focus", "completed today", "working on",
    ],
    "transcripts": [
        "transcript", "official records", "unofficial transcript",
        "grade", "credit transfer", "evaluation request",
    ],
    "residency-tuition": [
        "residency", "tuition", "in-state", "out-of-state",
        "domicile", "tuition classification", "residency determination",
    ],
    "admissions": [
        "admissions", "application", "enrollment", "applicant",
        "admission requirements", "new student", "transfer student",
    ],
    "continuing-education": [
        "continuing education", "workforce", "scholarship", "ce ",
        "workforce access", "wap", "non-credit",
    ],
    "personal-data": [
        "ferpa", "privacy", "pii", "personally identifiable",
        "data handling", "student data", "records request",
    ],
    "updates": [
        "policy update", "workflow update", "technology update",
        "system change", "procedure change", "announcement",
    ],
}


def _detect_folder(filename: str, content: str) -> tuple[str, float]:
    """Return the most likely top-level folder and a confidence score (0–1)."""
    text_lower = (filename + " " + content).lower()
    scores: dict[str, int] = {}
    for folder, keywords in FOLDER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score:
            scores[folder] = score

    if not scores:
        return "(root)", 0.0

    best_folder = max(scores, key=lambda f: scores[f])
    total = sum(scores.values())
    confidence = scores[best_folder] / total if total else 0.0
    return best_folder, confidence


def _suggest_filename(source_path: Path, folder: str, content: str) -> str:
    """
    Suggest a destination filename following repository naming conventions:
      - daily-logs → YYYY-MM-DD.md
      - meetings   → YYYY-MM-DD-topic.md
      - others     → lowercase-kebab original name
    """
    stem = source_path.stem
    suffix = source_path.suffix or ".md"

    # Try to extract a date from the filename first, then from the content
    date_str: str | None = None
    date_m = re.search(r"\d{4}-\d{2}-\d{2}", stem)
    if date_m:
        date_str = date_m.group(0)
    else:
        dates_in_content = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", content)
        if dates_in_content:
            date_str = dates_in_content[0]

    if folder == "daily-logs":
        if date_str:
            return f"{date_str}{suffix}"
        return re.sub(r"[^a-zA-Z0-9.]+", "-", stem).strip("-").lower() + suffix

    if folder == "meetings":
        if date_str:
            topic = re.sub(r"\d{4}-\d{2}-\d{2}[-_]?", "", stem).strip("-_ ") or "meeting"
            topic = re.sub(r"[^a-zA-Z0-9]+", "-", topic).strip("-").lower() or "meeting"
            return f"{date_str}-{topic}{suffix}"
        return re.sub(r"[^a-zA-Z0-9.]+", "-", stem).strip("-").lower() + suffix

    # Default: normalize to lowercase kebab
    return re.sub(r"[^a-zA-Z0-9.]+", "-", stem).strip("-").lower() + suffix


def _suggest_dest_dir(folder: str, filename: str) -> Path:
    """
    Return the full destination directory for a file given its target folder.
      - daily-logs → daily-logs/YYYY-MM/
      - meetings   → meetings/
      - others     → <folder>/
    """
    if folder == "daily-logs":
        date_m = re.search(r"\d{4}-\d{2}", filename)
        if date_m:
            ym = date_m.group(0)  # YYYY-MM
            return REPO_ROOT / "daily-logs" / ym
        return REPO_ROOT / "daily-logs"

    if folder in ("(root)", ""):
        return REPO_ROOT

    return REPO_ROOT / folder


# ---------------------------------------------------------------------------
# Subcommand: import
# ---------------------------------------------------------------------------


def cmd_import(args: argparse.Namespace) -> None:
    """
    Import a Markdown file into the repository:
    analyze its content, determine the best destination folder,
    rename to match naming conventions, and copy it into place.
    """
    source = Path(args.file)
    if not source.is_absolute():
        source = Path.cwd() / source
    if not source.exists():
        sys.exit(f"File not found: {args.file}")

    try:
        content = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        sys.exit(f"Cannot read file: {exc}")

    # Detect destination
    detected_folder, confidence = _detect_folder(source.name, content)
    suggested_filename = _suggest_filename(source, detected_folder, content)
    dest_dir = _suggest_dest_dir(detected_folder, suggested_filename)
    dest_path = dest_dir / suggested_filename

    # Allow the user to override the destination
    if args.dest:
        override = Path(args.dest)
        if not override.is_absolute():
            override = REPO_ROOT / override
        if override.suffix:
            # Treat as a full file path
            dest_dir = override.parent
            dest_path = override
        else:
            # Treat as a directory
            dest_dir = override
            dest_path = override / suggested_filename

    # Print analysis
    print(f"\n{'='*60}")
    print(f"  📥 Import Analysis")
    print(f"{'='*60}")
    print(f"  Source     : {source}")
    print(f"  Detected   : {detected_folder}  (confidence: {confidence:.0%})")
    try:
        dest_display = _relative(dest_path)
    except ValueError:
        dest_display = str(dest_path)
    print(f"  Destination: {dest_display}")

    meta = _parse_note(source)
    print(f"  Title      : {meta['title']}")
    print(f"  Words      : {meta['words']}")
    if meta["open_items"]:
        print(f"  Open items : {len(meta['open_items'])}")
    if meta["dates_in_text"]:
        print(f"  Dates found: {', '.join(meta['dates_in_text'])}")
    print()

    if args.dry_run:
        print(f"  DRY RUN — no changes made.")
        print(f"  Would copy to: {dest_display}")
        print()
        return

    if dest_path.exists() and not args.force:
        sys.exit(
            f"Destination already exists: {dest_display}\n"
            f"Use --force to overwrite."
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content, encoding="utf-8")
    print(f"  ✅ Imported to: {dest_display}")
    print()

    if args.organize:
        idx_path = REPO_ROOT / "tools" / "index.md"
        print("  🔄 Refreshing master index…")
        org_args = argparse.Namespace(output=str(idx_path.relative_to(REPO_ROOT)))
        cmd_organize(org_args)


# ---------------------------------------------------------------------------
# Subcommand: process-inbox
# ---------------------------------------------------------------------------


def cmd_process_inbox(args: argparse.Namespace) -> None:
    """
    Process all files in the inbox/ folder: auto-detect the destination
    for each file, import it using the same logic as 'import', then remove
    the original from inbox.  Skips README.md and hidden files.
    """
    inbox_dir = REPO_ROOT / "inbox"
    if not inbox_dir.exists():
        sys.exit("inbox/ folder not found. Create it at the repository root first.")

    candidates = sorted(
        p for p in inbox_dir.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and p.name.lower() != "readme.md"
        and p.suffix.lower() in (".md", ".txt")
    )

    if not candidates:
        print("\n📭 No files found in inbox/ to process.\n")
        return

    print(f"\n{'='*60}")
    print(f"  📬 Processing inbox/ ({len(candidates)} file(s))")
    print(f"{'='*60}\n")

    imported: list[str] = []
    skipped: list[str] = []

    for source in candidates:
        print(f"  ── {source.name}")
        try:
            content = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"     ❌ Cannot read: {exc}\n")
            skipped.append(source.name)
            continue

        detected_folder, confidence = _detect_folder(source.name, content)
        suggested_filename = _suggest_filename(source, detected_folder, content)
        dest_dir = _suggest_dest_dir(detected_folder, suggested_filename)
        dest_path = dest_dir / suggested_filename

        try:
            dest_display = _relative(dest_path)
        except ValueError:
            dest_display = str(dest_path)

        print(f"     Detected   : {detected_folder}  (confidence: {confidence:.0%})")
        print(f"     Destination: {dest_display}")

        if args.dry_run:
            print(f"     DRY RUN — would copy to: {dest_display}\n")
            imported.append(source.name)
            continue

        if dest_path.exists() and not args.force:
            print(f"     ⚠️  Destination already exists — skipped (use --force to overwrite)\n")
            skipped.append(source.name)
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(content, encoding="utf-8")
        source.unlink()
        print(f"     ✅ Imported → {dest_display}\n")
        imported.append(source.name)

    print(f"{'='*60}")
    verb = "previewed" if args.dry_run else "imported"
    print(f"  Done: {len(imported)} {verb}, {len(skipped)} skipped")
    print(f"{'='*60}\n")

    if not args.dry_run and args.organize and imported:
        idx_path = REPO_ROOT / "tools" / "index.md"
        print("  🔄 Refreshing master index…")
        org_args = argparse.Namespace(output=str(idx_path.relative_to(REPO_ROOT)))
        cmd_organize(org_args)


# ---------------------------------------------------------------------------
# Subcommand: analyze
# ---------------------------------------------------------------------------


def cmd_analyze(args: argparse.Namespace) -> None:
    """Print a detailed analysis of one note or all notes."""
    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = REPO_ROOT / target
        if not target.exists():
            sys.exit(f"File not found: {args.file}")
        notes = [target]
    else:
        notes = _all_notes()

    for path in notes:
        meta = _parse_note(path)
        print(f"\n{'='*60}")
        print(f"  📄 {meta['relative']}")
        print(f"{'='*60}")
        print(f"  Title    : {meta['title']}")
        print(f"  Folder   : {meta['folder']}")
        print(f"  Words    : {meta['words']}")
        print(f"  Modified : {meta['modified'].strftime('%Y-%m-%d %H:%M')}")
        if meta["headings"]:
            print(f"  Headings :")
            for level, heading in meta["headings"]:
                print(f"    {'  ' * (level - 1)}{'#' * level} {heading}")
        if meta["open_items"]:
            print(f"  Open action items ({len(meta['open_items'])}):")
            for item in meta["open_items"][:5]:
                print(f"    {item}")
            if len(meta["open_items"]) > 5:
                print(f"    … and {len(meta['open_items']) - 5} more")
        if meta["done_items"]:
            print(
                f"  Completed items : {len(meta['done_items'])}"
            )
        if meta["dates_in_text"]:
            print(f"  Dates found  : {', '.join(meta['dates_in_text'])}")
    print()


# ---------------------------------------------------------------------------
# Subcommand: sort
# ---------------------------------------------------------------------------


def cmd_sort(args: argparse.Namespace) -> None:
    """List notes sorted by the chosen criterion."""

    # Assets are handled separately: all file types, file-size instead of words
    if args.folder == "assets":
        assets_meta = [_asset_meta(p) for p in _all_assets()]
        if not assets_meta:
            print("\nNo files found in assets/.\n")
            return

        by = args.by
        if by == "date":
            assets_meta.sort(key=lambda m: m["modified"], reverse=True)
            col_header = "Modified"
            col_fn = lambda m: m["modified"].strftime("%Y-%m-%d %H:%M")
        elif by == "size":
            assets_meta.sort(key=lambda m: m["size_bytes"], reverse=True)
            col_header = "Size"
            col_fn = lambda m: m["size_display"]
        else:  # name
            assets_meta.sort(key=lambda m: m["relative"])
            col_header = "Type"
            col_fn = lambda m: m["kind"]

        col_w = max(len(col_fn(m)) for m in assets_meta) if assets_meta else 10
        path_w = max(len(m["relative"]) for m in assets_meta) if assets_meta else 20

        header = f"{'Path':<{path_w}}  {col_header}"
        print(f"\n{header}")
        print("-" * (len(header) + 4))
        for m in assets_meta:
            print(f"{m['relative']:<{path_w}}  {col_fn(m)}")
        print(f"\n{len(assets_meta)} asset(s) found.\n")
        return

    notes_meta = [_parse_note(p) for p in _all_notes()]

    if args.folder:
        notes_meta = [m for m in notes_meta if m["folder"] == args.folder]
        if not notes_meta:
            sys.exit(
                f"No notes found in folder '{args.folder}'. "
                f"Available folders: {sorted({m['folder'] for m in [_parse_note(p) for p in _all_notes()]})}"
            )

    by = args.by
    if by == "date":
        notes_meta.sort(key=lambda m: m["modified"], reverse=True)
        col_header = "Modified"
        col_fn = lambda m: m["modified"].strftime("%Y-%m-%d %H:%M")
    elif by == "size":
        notes_meta.sort(key=lambda m: m["words"], reverse=True)
        col_header = "Words"
        col_fn = lambda m: str(m["words"])
    else:  # name
        notes_meta.sort(key=lambda m: m["relative"])
        col_header = "Folder"
        col_fn = lambda m: m["folder"]

    col_w = max(len(col_fn(m)) for m in notes_meta) if notes_meta else 10
    path_w = max(len(m["relative"]) for m in notes_meta) if notes_meta else 20

    header = f"{'Path':<{path_w}}  {col_header}"
    print(f"\n{header}")
    print("-" * (len(header) + 4))
    for m in notes_meta:
        print(f"{m['relative']:<{path_w}}  {col_fn(m)}")
    print(f"\n{len(notes_meta)} note(s) found.\n")


# ---------------------------------------------------------------------------
# Subcommand: organize
# ---------------------------------------------------------------------------


def cmd_organize(args: argparse.Namespace) -> None:
    """Generate (or refresh) a master index of all notes."""
    notes_meta = [_parse_note(p) for p in _all_notes()]

    # Group by top-level folder
    folders: dict[str, list[dict]] = {}
    for m in notes_meta:
        folders.setdefault(m["folder"], []).append(m)

    lines = [
        "# 📋 Master Notes Index",
        "",
        "> Auto-generated by `tools/notes_helper.py organize`  ",
        f"> Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Summary table
    lines += [
        "## Summary",
        "",
        f"| Folder | Notes | Total Words |",
        f"|--------|-------|-------------|",
    ]
    for folder in sorted(folders):
        folder_notes = folders[folder]
        total_words = sum(m["words"] for m in folder_notes)
        lines.append(
            f"| {folder} | {len(folder_notes)} | {total_words:,} |"
        )
    lines += [""]

    # Per-folder detail
    lines.append("## Notes by Folder")
    lines.append("")
    for folder in sorted(folders):
        lines.append(f"### {folder}")
        lines.append("")
        folder_notes = sorted(folders[folder], key=lambda m: m["relative"])
        for m in folder_notes:
            rel = m["relative"]
            # Build a relative link from the index file location
            link = f"../{rel}" if args.output else rel
            open_count = len(m["open_items"])
            badge = f" ✅ {len(m['done_items'])} done" if m["done_items"] else ""
            badge += f" 🔲 {open_count} open" if open_count else ""
            lines.append(
                f"- [{m['title']}]({link}) — {m['words']} words{badge}"
            )
        lines.append("")

    # Open action items summary
    all_open = [
        (m["relative"], item)
        for m in notes_meta
        for item in m["open_items"]
    ]
    if all_open:
        lines += [
            "## Open Action Items",
            "",
        ]
        current_file = None
        for rel, item in sorted(all_open, key=lambda x: x[0]):
            if rel != current_file:
                lines.append(f"**{rel}**")
                current_file = rel
            lines.append(f"  {item}")
        lines.append("")

    # Assets inventory
    all_assets = [_asset_meta(p) for p in _all_assets()]
    if all_assets:
        lines += [
            "## Assets",
            "",
        ]
        by_subfolder: dict[str, list[dict]] = {}
        for a in all_assets:
            by_subfolder.setdefault(a["subfolder"], []).append(a)
        for subfolder in sorted(by_subfolder):
            lines.append(f"### assets/{subfolder}" if subfolder != "(root)" else "### assets")
            lines.append("")
            lines.append(f"| File | Type | Size | Modified |")
            lines.append(f"|------|------|------|----------|")
            for a in sorted(by_subfolder[subfolder], key=lambda x: x["name"]):
                rel = a["relative"]
                link = f"../{rel}" if args.output else rel
                lines.append(
                    f"| [{a['name']}]({link}) | {a['kind']} | {a['size_display']} | {a['modified'].strftime('%Y-%m-%d')} |"
                )
            lines.append("")

    content = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Master index written to: {_relative(out_path)}")
    else:
        print(content)


# ---------------------------------------------------------------------------
# Subcommand: search
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> None:
    """Search all notes for a keyword and print matching lines with context."""
    keyword = args.keyword
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    context = args.context

    notes = _all_notes()
    if args.folder:
        notes = [p for p in notes if p.parts[len(REPO_ROOT.parts)] == args.folder]

    total_matches = 0
    for path in notes:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        matches = [
            (i + 1, line)
            for i, line in enumerate(lines)
            if pattern.search(line)
        ]
        if not matches:
            continue

        print(f"\n{'─'*60}")
        print(f"  📄 {_relative(path)}  ({len(matches)} match(es))")
        print(f"{'─'*60}")
        shown_lines: set[int] = set()
        for lineno, _ in matches:
            start = max(0, lineno - 1 - context)
            end = min(len(lines), lineno + context)
            for i in range(start, end):
                if i not in shown_lines:
                    marker = ">>>" if (i + 1) == lineno else "   "
                    snippet = lines[i]
                    # Highlight the keyword
                    snippet = pattern.sub(
                        lambda m: f"\033[1;33m{m.group()}\033[0m", snippet
                    )
                    print(f"  {marker} {i+1:4d} | {snippet}")
                    shown_lines.add(i)
        total_matches += len(matches)

    if total_matches == 0:
        print(f'\nNo matches found for "{keyword}".\n')
    else:
        print(f'\n{total_matches} match(es) for "{keyword}" across {len(notes)} file(s).\n')


# ---------------------------------------------------------------------------
# Subcommand: agent (interactive mode)
# ---------------------------------------------------------------------------

_AGENT_HELP = """\
Notes Helper Agent — type a request in plain language and I'll do it for you.

Examples:
  process inbox
  process inbox dry-run
  process inbox organize
  import /path/to/note.md
  import /path/to/note.md to meetings
  import /path/to/note.md --dry-run
  analyze all notes
  analyze daily-logs/2026-03/2026-03-13.md
  sort by date
  sort by size in graduation
  sort assets by date
  sort assets by size
  organize
  organize to tools/index.md
  search FERPA
  search deadline in graduation
  help
  quit
"""

_INTENT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bprocess.?inbox\b|\binbox\b", re.I), "process-inbox"),
    (re.compile(r"\bimport\b|\bupload\b|\bingest\b|\badd\s+file\b", re.I), "import"),
    (re.compile(r"\banalyze\b", re.I), "analyze"),
    (re.compile(r"\bsort\b|\blist\b|\border\b", re.I), "sort"),
    (re.compile(r"\borganize\b|\bindex\b|\bmaster\b", re.I), "organize"),
    (re.compile(r"\bsearch\b|\bfind\b|\blook\b|\bgrep\b", re.I), "search"),
]


def _parse_agent_input(text: str) -> argparse.Namespace | None:
    """Turn a natural-language request into an argparse Namespace, or None if unrecognised."""
    text = text.strip()
    if not text:
        return None

    # Detect intent
    intent = None
    for pattern, name in _INTENT_PATTERNS:
        if pattern.search(text):
            intent = name
            break

    if intent is None:
        return None

    ns = argparse.Namespace()

    if intent == "process-inbox":
        ns.func = cmd_process_inbox
        ns.dry_run = bool(re.search(r"\bdry.?run\b", text, re.I))
        ns.force = bool(re.search(r"\bforce\b|\boverwrite\b", text, re.I))
        ns.organize = bool(re.search(r"\borganize\b|\bindex\b", text, re.I))
        return ns

    if intent == "import":
        # "import <file>" or "upload <file>"
        m = re.search(r"\b(?:import|upload|ingest|add\s+file)\b\s+(\S+)", text, re.I)
        file_arg = m.group(1).strip() if m else None
        if not file_arg:
            print("Please specify a file path, e.g.: import /path/to/note.md")
            return None
        dest_m = re.search(r"\b(?:to|into|dest(?:ination)?)\s+(\S+)", text, re.I)
        ns.func = cmd_import
        ns.file = file_arg
        ns.dest = dest_m.group(1) if dest_m else None
        ns.dry_run = bool(re.search(r"\bdry.?run\b", text, re.I))
        ns.force = bool(re.search(r"\bforce\b|\boverwrite\b", text, re.I))
        ns.organize = bool(re.search(r"\borganize\b|\bindex\b", text, re.I))
        return ns

    if intent == "analyze":
        # "analyze <file>" or "analyze all"
        m = re.search(r"\banalyze\b\s+(.+)", text, re.I)
        file_arg = m.group(1).strip() if m else None
        if file_arg and file_arg.lower() in ("all", "all notes", "everything"):
            file_arg = None
        ns.func = cmd_analyze
        ns.file = file_arg
        return ns

    if intent == "sort":
        by = "name"
        for word in ("date", "size", "name"):
            if re.search(rf"\b{word}\b", text, re.I):
                by = word
                break
        folder_m = re.search(r"\bin\s+(\S+)", text, re.I)
        if folder_m:
            folder = folder_m.group(1)
        elif re.search(r"\bassets\b", text, re.I):
            folder = "assets"
        else:
            folder = None
        ns.func = cmd_sort
        ns.by = by
        ns.folder = folder
        return ns

    if intent == "organize":
        output_m = re.search(r"\b(?:to|into|output|file)\s+(\S+)", text, re.I)
        ns.func = cmd_organize
        ns.output = output_m.group(1) if output_m else None
        return ns

    if intent == "search":
        # Extract keyword: everything after the verb, strip trailing folder hint
        kw_m = re.search(r"\b(?:search|find|look\s+for|grep)\b\s+(.+)", text, re.I)
        if not kw_m:
            return None
        keyword_part = kw_m.group(1).strip()
        folder = None
        folder_m = re.search(r"\s+in\s+(\S+)\s*$", keyword_part, re.I)
        if folder_m:
            folder = folder_m.group(1)
            keyword_part = keyword_part[: folder_m.start()].strip()
        # Strip surrounding quotes if present
        keyword_part = keyword_part.strip('"\'')
        if not keyword_part:
            return None
        ns.func = cmd_search
        ns.keyword = keyword_part
        ns.folder = folder
        ns.context = 2
        return ns

    return None


def cmd_agent(_args: argparse.Namespace) -> None:
    """Start an interactive agent session."""
    print(_AGENT_HELP)
    while True:
        try:
            raw = input("notes> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        lower = raw.lower()
        if lower in ("quit", "exit", "bye", "q"):
            print("Goodbye!")
            break
        if lower in ("help", "?", "h"):
            print(_AGENT_HELP)
            continue

        ns = _parse_agent_input(raw)
        if ns is None:
            print(
                "Sorry, I didn't understand that. Try 'help' for examples, "
                "or use one of: analyze, sort, organize, search."
            )
            continue

        try:
            ns.func(ns)
        except SystemExit as exc:
            # cmd_* may call sys.exit() on errors — show the message gracefully
            if exc.code:
                print(f"Error: {exc.code}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notes_helper.py",
        description="Work Notes Helper — analyze, sort, and organize your notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/notes_helper.py analyze
  python3 tools/notes_helper.py analyze daily-logs/2026-03/2026-03-13.md
  python3 tools/notes_helper.py sort --by date
  python3 tools/notes_helper.py sort --by size --folder graduation
  python3 tools/notes_helper.py sort --by size --folder assets
  python3 tools/notes_helper.py organize
  python3 tools/notes_helper.py organize --output tools/index.md
  python3 tools/notes_helper.py search "action item"
  python3 tools/notes_helper.py search FERPA --context 3
  python3 tools/notes_helper.py import /path/to/note.md
  python3 tools/notes_helper.py import /path/to/note.md --dest meetings --organize
  python3 tools/notes_helper.py import /path/to/note.md --dry-run
  python3 tools/notes_helper.py process-inbox --organize
  python3 tools/notes_helper.py process-inbox --dry-run
  python3 tools/notes_helper.py agent
        """,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # analyze
    p_analyze = sub.add_parser(
        "analyze", help="Analyze note(s): word count, headings, action items, dates"
    )
    p_analyze.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="Path to a single note (relative to repo root). Analyzes all notes if omitted.",
    )
    p_analyze.set_defaults(func=cmd_analyze)

    # sort
    p_sort = sub.add_parser(
        "sort", help="List notes sorted by date, size, or name"
    )
    p_sort.add_argument(
        "--by",
        choices=["date", "size", "name"],
        default="name",
        help="Sort criterion (default: name)",
    )
    p_sort.add_argument(
        "--folder",
        metavar="FOLDER",
        help="Limit to a top-level folder (e.g. graduation, meetings)",
    )
    p_sort.set_defaults(func=cmd_sort)

    # organize
    p_org = sub.add_parser(
        "organize", help="Generate a master index of all notes"
    )
    p_org.add_argument(
        "--output",
        metavar="FILE",
        help="Write the index to this file (relative to repo root). Prints to stdout if omitted.",
    )
    p_org.set_defaults(func=cmd_organize)

    # search
    p_search = sub.add_parser(
        "search", help="Search notes for a keyword"
    )
    p_search.add_argument("keyword", help="Keyword or phrase to search for")
    p_search.add_argument(
        "--context",
        type=int,
        default=2,
        metavar="N",
        help="Number of context lines around each match (default: 2)",
    )
    p_search.add_argument(
        "--folder",
        metavar="FOLDER",
        help="Limit search to a top-level folder",
    )
    p_search.set_defaults(func=cmd_search)

    # import
    p_import = sub.add_parser(
        "import",
        help="Import a note file: auto-detect its destination, rename, and copy it into the repo",
    )
    p_import.add_argument(
        "file",
        metavar="FILE",
        help="Path to the file to import (absolute or relative to current directory)",
    )
    p_import.add_argument(
        "--dest",
        metavar="DIR",
        help=(
            "Override the auto-detected destination. "
            "Can be a directory (e.g. meetings) or a full file path. "
            "Relative paths are resolved from the repo root."
        ),
    )
    p_import.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without copying any files",
    )
    p_import.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination file if it already exists",
    )
    p_import.add_argument(
        "--organize",
        action="store_true",
        help="Refresh tools/index.md after a successful import",
    )
    p_import.set_defaults(func=cmd_import)

    # process-inbox
    p_inbox = sub.add_parser(
        "process-inbox",
        help="Import all files from the inbox/ folder, then remove them from inbox",
    )
    p_inbox.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without copying or deleting any files",
    )
    p_inbox.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination files that already exist",
    )
    p_inbox.add_argument(
        "--organize",
        action="store_true",
        help="Refresh tools/index.md after all files are processed",
    )
    p_inbox.set_defaults(func=cmd_process_inbox)

    # agent
    p_agent = sub.add_parser(
        "agent",
        help="Interactive agent mode — type requests in plain language",
    )
    p_agent.set_defaults(func=cmd_agent)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
