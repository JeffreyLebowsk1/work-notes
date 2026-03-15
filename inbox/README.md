# 📥 Inbox

Drop files here and let the Notes Helper sort them for you automatically.

## How it works

1. **Upload** any supported file into this folder via the GitHub web interface ("Add file → Upload files") or by committing it from your machine.
2. **The helper does the rest** — as soon as the files land in `inbox/`, the **Inbox Processor** GitHub Actions workflow runs automatically, imports each file into the correct section of the repository, and removes it from this folder.

> **Tip:** You can also trigger processing manually at any time from the **Actions** tab → **Inbox Processor** → **Run workflow**.

## Supported file types

| Type | Extensions | Destination |
|---|---|---|
| **Text notes** | `.md`, `.txt` | Section folder (e.g. `meetings/`, `daily-logs/`) |
| **PDFs** | `.pdf` | `assets/documents/` (or `graduation/assets/` for graduation PDFs) |
| **Images / scans** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`, `.ico`, `.tiff`, `.tif`, `.bmp` | `assets/images/` |
| **Spreadsheets** | `.xlsx`, `.xls`, `.csv`, `.ods`, `.numbers` | `assets/spreadsheets/` |

Hidden files (starting with `.`) and `README.md` are always skipped.

### PDF handling

- **Digital PDFs** (text layer present) — text is extracted directly with pypdf.
- **Scanned PDFs** (image-only pages) — each image-only page is automatically OCR'd via Tesseract if `pytesseract`, `pdf2image`, and the `tesseract-ocr`/`poppler-utils` system packages are installed. Without those, scanned pages are silently skipped but the PDF is still copied to assets.

## What happens to each file

The helper reads each file's name and content (where possible), then:

- **Auto-detects** the best destination folder (e.g. `meetings/`, `daily-logs/`, `graduation/`)
- **Renames** the file to match repository conventions (e.g. `2026-03-13-topic.md`)
- **Moves** the file into the right place
- **Logs metadata** to `tools/import-log.csv` — every import is recorded with its timestamp, file type, size, detected folder, confidence score, destination, and status
- **Refreshes** `tools/index.md` after all files are processed (when `--organize` is passed)

If the helper can't confidently match a file, it places it in the repository root and you can move it manually.

## Import log

Every file processed — whether imported, skipped, or dry-run — is recorded in `tools/import-log.csv` with the following columns:

| Column | Description |
|---|---|
| `timestamp` | When the file was processed (`YYYY-MM-DDTHH:MM:SS`) |
| `source_name` | Original filename |
| `extension` | File extension (e.g. `.pdf`, `.png`) |
| `size_bytes` | File size in bytes |
| `content_chars` | Characters of text extracted (0 for binary files) |
| `detected_folder` | Auto-detected destination section |
| `confidence` | Folder detection confidence (0.00–1.00) |
| `destination` | Final path where the file was placed |
| `status` | `imported`, `skipped`, `error`, or `dry-run` |

## Running it yourself (command line)

```bash
# Preview what would happen — no changes made (still logged as dry-run)
python3 tools/notes_helper.py process-inbox --dry-run

# Process everything and refresh the master index
python3 tools/notes_helper.py process-inbox --organize

# Overwrite destination files that already exist
python3 tools/notes_helper.py process-inbox --force --organize
```

