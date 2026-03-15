"""
_helpers.py — Core utilities shared across notes_helper modules.

Provides repo-wide file discovery, metadata extraction, and
path-normalisation helpers used by all subcommands.
"""

import re
from datetime import datetime
from pathlib import Path


def _ocr_page(path: Path, page_number: int) -> str:
    """OCR a single PDF page using pdf2image + pytesseract.

    *page_number* is 1-indexed (first page = 1), matching the convention
    used by pdf2image's ``first_page``/``last_page`` parameters.

    Returns an empty string if pdf2image or pytesseract are not installed,
    if Tesseract is not available on the system PATH, or on any other error.
    Callers should treat a non-empty return value as best-effort OCR output.
    """
    try:
        from pdf2image import convert_from_path  # type: ignore[import]
        import pytesseract  # type: ignore[import]
    except ImportError:
        return ""

    try:
        images = convert_from_path(
            str(path), first_page=page_number, last_page=page_number
        )
        if not images:
            return ""
        return pytesseract.image_to_string(images[0])
    except Exception:  # noqa: BLE001 — Tesseract/poppler errors are environment-dependent
        return ""


def _read_pdf_text(path: Path) -> str:
    """Extract plain text from a PDF file.

    Uses pypdf for fast native text extraction.  For pages that yield no
    text (image-based / scanned pages), automatically falls back to OCR via
    ``pdf2image`` + ``pytesseract`` if those libraries are available and
    Tesseract is installed on the system.  This means the function handles
    both digital-native PDFs and scanned documents transparently.

    Returns an empty string if pypdf is not installed or the file cannot
    be parsed (e.g. encrypted or corrupt PDF).  OCR failures on individual
    pages are silently ignored; the rest of the document is still returned.
    """
    try:
        from pypdf import PdfReader  # type: ignore[import]
    except ImportError:
        return ""

    try:
        reader = PdfReader(str(path))
        parts: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
            else:
                # Page has no text layer — try OCR as a fallback
                ocr_text = _ocr_page(path, i)
                if ocr_text.strip():
                    parts.append(ocr_text)
        return "\n".join(parts)
    except (OSError, ValueError, UnicodeDecodeError):
        return ""
    except Exception:  # noqa: BLE001 — pypdf raises various undocumented errors on corrupt/encrypted PDFs
        return ""

REPO_ROOT = Path(__file__).resolve().parent.parent
IGNORED_DIRS = {".git", ".github", "tools", "assets", "inbox"}


def _all_notes(root: Path = REPO_ROOT) -> list[Path]:
    """Return all Markdown files in the repository, sorted by path."""
    notes = []
    for path in root.rglob("*.md"):
        if not any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
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


def pending_inbox_files() -> list[Path]:
    """Return all processable (.md / .txt / .pdf) files currently sitting in inbox/."""
    inbox_dir = REPO_ROOT / "inbox"
    if not inbox_dir.exists():
        return []
    return sorted(
        p for p in inbox_dir.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and p.name.lower() != "readme.md"
        and p.suffix.lower() in (".md", ".txt", ".pdf")
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
        (len(m.group(1)), line[len(m.group(1)):].strip())
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
