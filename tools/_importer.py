"""
_importer.py — Import helpers and subcommands: import, process-inbox.

Handles keyword-based folder detection, filename normalisation, and
file copying into the correct repository location.
"""

import argparse
import re
import sys
from pathlib import Path

from _commands import cmd_organize
from _helpers import REPO_ROOT, _parse_note, _relative, pending_inbox_files


# ---------------------------------------------------------------------------
# Folder-detection keyword map
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
    print("  📥 Import Analysis")
    print("=" * 60)
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
        print("  DRY RUN — no changes made.")
        print(f"  Would copy to: {dest_display}")
        print()
        return

    if dest_path.exists() and not args.force:
        sys.exit(
            f"Destination already exists: {dest_display}\n"
            "Use --force to overwrite."
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(content, encoding="utf-8")
    print(f"  ✅ Imported to: {dest_display}")
    print()

    if args.organize:
        idx_path = REPO_ROOT / "tools" / "index.md"
        print("  🔄 Refreshing master index…")
        org_args = argparse.Namespace(output=str(idx_path.relative_to(REPO_ROOT)), check_inbox=False)
        cmd_organize(org_args)


def cmd_process_inbox(args: argparse.Namespace) -> None:
    """
    Process all files in the inbox/ folder: auto-detect the destination
    for each file, import it using the same logic as 'import', then remove
    the original from inbox.  Skips README.md and hidden files.
    """
    inbox_dir = REPO_ROOT / "inbox"
    if not inbox_dir.exists():
        sys.exit("inbox/ folder not found. Create it at the repository root first.")

    candidates = pending_inbox_files()

    if not candidates:
        print("\n📭 No files found in inbox/ to process.\n")
        return

    print(f"\n{'='*60}")
    print(f"  📬 Processing inbox/ ({len(candidates)} file(s))")
    print("=" * 60 + "\n")

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
            print("     ⚠️  Destination already exists — skipped (use --force to overwrite)\n")
            skipped.append(source.name)
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(content, encoding="utf-8")
        source.unlink()
        print(f"     ✅ Imported → {dest_display}\n")
        imported.append(source.name)

    print("=" * 60)
    verb = "previewed" if args.dry_run else "imported"
    print(f"  Done: {len(imported)} {verb}, {len(skipped)} skipped")
    print("=" * 60 + "\n")

    if not args.dry_run and args.organize and imported:
        idx_path = REPO_ROOT / "tools" / "index.md"
        print("  🔄 Refreshing master index…")
        org_args = argparse.Namespace(output=str(idx_path.relative_to(REPO_ROOT)), check_inbox=False)
        cmd_organize(org_args)
