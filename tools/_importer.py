"""
_importer.py — Import helpers and subcommands: import, process-inbox.

Handles keyword-based folder detection, filename normalisation, and
file copying into the correct repository location.
"""

import argparse
import csv
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from _commands import cmd_organize
from _helpers import (
    REPO_ROOT,
    _IMAGE_EXTS,
    _PDF_EXTS,
    _SHEET_EXTS,
    _TEXT_EXTS,
    _binary_inbox_dest,
    _parse_note,
    _read_pdf_text,
    _relative,
    pending_inbox_files,
)


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


def _pdf_dest_dir(folder: str) -> Path:
    """Return the assets destination directory for a PDF given its detected folder.

    PDFs are binary files and are stored in assets/, not in the text-note
    directories.  Graduation PDFs go into graduation/assets/ (the section's
    own assets folder); everything else lands in assets/documents/.
    """
    if folder == "graduation":
        return REPO_ROOT / "graduation" / "assets"
    return REPO_ROOT / "assets" / "documents"


# ---------------------------------------------------------------------------
# Import log
# ---------------------------------------------------------------------------

#: Append-only CSV log of every file processed by `import` or `process-inbox`.
IMPORT_LOG_PATH: Path = REPO_ROOT / "tools" / "import-log.csv"

_LOG_HEADER = (
    "timestamp", "source_name", "extension", "size_bytes",
    "content_chars", "detected_folder", "confidence", "destination", "status",
)


def _write_import_log(
    source: Path,
    content: str,
    detected_folder: str,
    confidence: float,
    dest_path: Path | None,
    status: str,
) -> None:
    """Append one row to ``tools/import-log.csv``.

    Creates the file with a header row on first use.  ``dest_path`` may be
    ``None`` for error cases where no destination was determined; the
    ``destination`` column is left empty in that case.
    """
    write_header = (
        not IMPORT_LOG_PATH.exists() or IMPORT_LOG_PATH.stat().st_size == 0
    )
    try:
        dest_display = _relative(dest_path) if dest_path is not None else ""
    except ValueError:
        dest_display = str(dest_path) if dest_path is not None else ""

    with IMPORT_LOG_PATH.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if write_header:
            writer.writerow(_LOG_HEADER)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            source.name,
            source.suffix.lower(),
            source.stat().st_size,
            len(content),
            detected_folder,
            f"{confidence:.2f}",
            dest_display,
            status,
        ])


def cmd_import(args: argparse.Namespace) -> None:
    """
    Import a file into the repository:
    analyze its content, determine the best destination folder,
    rename to match naming conventions, and copy it into place.
    Supports .md, .txt, .pdf, images, and spreadsheets.
    """
    source = Path(args.file)
    if not source.is_absolute():
        source = Path.cwd() / source
    if not source.exists():
        sys.exit(f"File not found: {args.file}")

    ext = source.suffix.lower()
    is_text = ext in _TEXT_EXTS
    is_pdf = ext in _PDF_EXTS
    # Any non-text, non-PDF file is treated as a binary asset
    is_binary = not is_text and not is_pdf

    if is_pdf:
        content = _read_pdf_text(source)
    elif is_text:
        try:
            content = source.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            sys.exit(f"Cannot read file: {exc}")
    else:
        content = ""  # binary files — folder detection uses filename only

    # Detect destination
    detected_folder, confidence = _detect_folder(source.name, content)
    suggested_filename = _suggest_filename(source, detected_folder, content)

    if is_pdf:
        dest_dir = _pdf_dest_dir(detected_folder)
    elif is_binary:
        dest_dir = _binary_inbox_dest(source)
    else:
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
    print(f"  Type       : {ext or '(none)'}")
    print(f"  Detected   : {detected_folder}  (confidence: {confidence:.0%})")
    try:
        dest_display = _relative(dest_path)
    except ValueError:
        dest_display = str(dest_path)
    print(f"  Destination: {dest_display}")

    if is_text:
        meta = _parse_note(source)
        print(f"  Title      : {meta['title']}")
        print(f"  Words      : {meta['words']}")
        if meta["open_items"]:
            print(f"  Open items : {len(meta['open_items'])}")
        if meta["dates_in_text"]:
            print(f"  Dates found: {', '.join(meta['dates_in_text'])}")
    elif is_pdf:
        word_count = len(re.findall(r"\b\w+\b", content))
        print(f"  Words (PDF): {word_count}")
    else:
        size = source.stat().st_size
        if size >= 1_048_576:
            size_display = f"{size / 1_048_576:.1f} MB"
        elif size >= 1024:
            size_display = f"{size / 1024:.1f} KB"
        else:
            size_display = f"{size} B"
        print(f"  Size       : {size_display}")
    print()

    if args.dry_run:
        print("  DRY RUN — no changes made.")
        print(f"  Would copy to: {dest_display}")
        print()
        _write_import_log(source, content, detected_folder, confidence, dest_path, "dry-run")
        return

    if dest_path.exists() and not args.force:
        _write_import_log(source, content, detected_folder, confidence, dest_path, "skipped")
        sys.exit(
            f"Destination already exists: {dest_display}\n"
            "Use --force to overwrite."
        )

    dest_dir.mkdir(parents=True, exist_ok=True)
    if is_text:
        dest_path.write_text(content, encoding="utf-8")
    else:
        shutil.copy2(source, dest_path)
    _write_import_log(source, content, detected_folder, confidence, dest_path, "imported")
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
        ext = source.suffix.lower()
        is_text = ext in _TEXT_EXTS
        is_pdf = ext in _PDF_EXTS
        is_binary = not is_text and not is_pdf

        if is_pdf:
            content = _read_pdf_text(source)
        elif is_text:
            try:
                content = source.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"     ❌ Cannot read: {exc}\n")
                _write_import_log(source, "", "(unknown)", 0.0, None, "error")
                skipped.append(source.name)
                continue
        else:
            content = ""  # binary asset — folder detection from filename only

        detected_folder, confidence = _detect_folder(source.name, content)
        suggested_filename = _suggest_filename(source, detected_folder, content)
        if is_pdf:
            dest_dir = _pdf_dest_dir(detected_folder)
        elif is_binary:
            dest_dir = _binary_inbox_dest(source)
        else:
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
            _write_import_log(source, content, detected_folder, confidence, dest_path, "dry-run")
            imported.append(source.name)
            continue

        if dest_path.exists() and not args.force:
            print("     ⚠️  Destination already exists — skipped (use --force to overwrite)\n")
            _write_import_log(source, content, detected_folder, confidence, dest_path, "skipped")
            skipped.append(source.name)
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        if is_text:
            dest_path.write_text(content, encoding="utf-8")
        else:
            shutil.copy2(source, dest_path)
        source.unlink()
        _write_import_log(source, content, detected_folder, confidence, dest_path, "imported")
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
