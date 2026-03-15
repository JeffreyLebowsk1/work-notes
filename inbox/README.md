# 📥 Inbox

Drop files here and let the Notes Helper sort them for you automatically.

## How it works

1. **Upload** one or more `.md`, `.txt`, or `.pdf` files into this folder via the GitHub web interface ("Add file → Upload files") or by committing them from your machine.
2. **The helper does the rest** — as soon as the files land in `inbox/`, the **Inbox Processor** GitHub Actions workflow runs automatically, imports each file into the correct section of the repository, and removes it from this folder.

> **Tip:** You can also trigger processing manually at any time from the **Actions** tab → **Inbox Processor** → **Run workflow**.

## What happens to each file

The helper reads each file's name and content, then:

- **Auto-detects** the best destination folder (e.g. `meetings/`, `daily-logs/`, `graduation/`)
- **Renames** the file to match repository conventions (e.g. `2026-03-13-topic.md`)
- **Moves** the file into the right place
- **Refreshes** `tools/index.md` after all files are processed

If the helper can't confidently match a file, it places it in the repository root and you can move it manually.

## Running it yourself (command line)

```bash
# Preview what would happen — no changes made
python3 tools/notes_helper.py process-inbox --dry-run

# Process everything and refresh the master index
python3 tools/notes_helper.py process-inbox --organize

# Overwrite destination files that already exist
python3 tools/notes_helper.py process-inbox --force --organize
```

## Notes

- `README.md` (this file) is always skipped.
- Hidden files (starting with `.`) are always skipped.
- `.md` and `.txt` files are imported as notes into the correct section folder.
- `.pdf` files have their text extracted (via pypdf) for folder detection, then the PDF is copied to `assets/documents/` (or the section's assets folder).  Other file types should be placed directly in `assets/`.
