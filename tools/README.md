# 🛠️ Tools

This folder contains helper scripts for managing your work notes.

---

## linux-setup.sh

A one-shot setup and launch script for the web app on any Linux machine.

```bash
# Run from the repository root:
bash tools/linux-setup.sh              # default port 5000
bash tools/linux-setup.sh --port 8080  # use a different port
```

What it does:
1. Checks for Python 3.10+ and git
2. Creates a Python virtual environment at `.venv/`
3. Installs all dependencies from `tools/requirements-web.txt`
4. Scaffolds `tools/.env` from `tools/.env.example` (if not already present)
5. Checks that the chosen port is not already in use — errors with a helpful message if it is
6. Starts the web app at `http://localhost:<PORT>`

Options:

| Flag | Purpose |
|---|---|
| `--port PORT`, `-p PORT` | Port to run on (default: `5000`) |
| `--help`, `-h` | Show usage |

Optional environment variables:

| Variable | Purpose |
|---|---|
| `APP_USERNAME` | HTTP Basic Auth username (strongly recommended for shared machines) |
| `APP_PASSWORD` | HTTP Basic Auth password |
| `PORT` | Alternative to `--port`; `--port` flag takes precedence |

```bash
# Example — launch with password protection on port 8080:
APP_USERNAME=registrar APP_PASSWORD=secret bash tools/linux-setup.sh --port 8080
```

See the **🐧 Run the Web App Locally on Linux** section of [SETUP.md](../SETUP.md) for the full walkthrough, including how to use ngrok to create a public link.

---

## auto-sync.sh

A background watcher that commits and pushes every change automatically.  Designed for a Linux machine (e.g. Jetson Orin Nano) where the repo lives inside a Google Drive folder mounted via rclone.  See the **🐧 Linux / Jetson Orin Nano Setup (Automatic Sync)** section of [SETUP.md](../SETUP.md) for full instructions.

---

## notes_helper.py

A command-line tool to **analyze**, **sort**, **organize**, **search**, and **import** your notes.

**Requirements:** Python 3.10+ (no extra packages needed — uses the standard library only)

> **Note:** Python 3.10+ is required because the source uses the `X | Y` union-type syntax
> (e.g. `str | None`) introduced in that version.

**Module layout** — the tool is split across several files to keep each one readable:

| File | Contents |
|------|----------|
| `notes_helper.py` | Entry point — argument parser and `main()` |
| `_helpers.py` | Core utilities: file discovery, metadata extraction |
| `_commands.py` | Subcommands: `analyze`, `sort`, `organize`, `search` |
| `_importer.py` | Subcommands: `import`, `process-inbox`; folder-detection logic |
| `_agent.py` | Interactive agent mode |

### Usage

Run all commands from the **repository root**:

```bash
python3 tools/notes_helper.py <COMMAND> [OPTIONS]
```

---

### Commands

#### `analyze` — Inspect notes in detail

Displays word count, headings, open/completed action items, and dates for one file or all notes.

```bash
# Analyze all notes
python3 tools/notes_helper.py analyze

# Analyze a single file
python3 tools/notes_helper.py analyze daily-logs/2026-03/2026-03-13.md
```

**Sample output:**

```
============================================================
  📄 daily-logs/2026-03/2026-03-13.md
============================================================
  Title    : 2026 03 13
  Folder   : daily-logs
  Words    : 326
  Modified : 2026-03-13 11:54
  Headings :
        ### Today's Focus
        ### Completed
        ### In Progress
        ### Blockers / Questions
        ### Notes
  Open action items (4):
    - [ ] Fill in Spring 2026 timeline dates
    …
  Dates found  : 2026-03-13
```

---

#### `sort` — List notes sorted by a criterion

```bash
# Sort all notes alphabetically by path (default)
python3 tools/notes_helper.py sort

# Sort by most recently modified
python3 tools/notes_helper.py sort --by date

# Sort by word count (largest first)
python3 tools/notes_helper.py sort --by size

# Limit to one top-level folder
python3 tools/notes_helper.py sort --by size --folder graduation

# Sort assets (images, documents, spreadsheets) by file size
python3 tools/notes_helper.py sort --by size --folder assets

# Sort assets by most recently modified
python3 tools/notes_helper.py sort --by date --folder assets
```

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--by` | `name`, `date`, `size` | `name` | Sort criterion |
| `--folder` | folder name | all | Limit to one top-level folder; use `assets` to list asset files |

> **Note:** When `--folder assets` is used, the `size` column shows file size (KB/MB) instead of word count, and all file types (PDFs, images, spreadsheets) are listed — not just Markdown files.

---

#### `organize` — Generate a master index

Produces a Markdown index of all notes grouped by folder, including a word-count summary table, a consolidated list of all open action items, an **Assets inventory** table, and — when files are waiting — an **Inbox** section listing what still needs to be imported.

```bash
# Print the index to the terminal
python3 tools/notes_helper.py organize

# Write the index to a file (refreshes it each time)
python3 tools/notes_helper.py organize --output tools/index.md

# Process any pending inbox/ files first, then generate the index
python3 tools/notes_helper.py organize --check-inbox --output tools/index.md
```

**Options:**

| Option | Description |
|--------|-------------|
| `--output FILE` | Write the index to this file (relative to repo root). Prints to stdout if omitted. |
| `--check-inbox` | Process any pending `inbox/` files before generating the index — equivalent to running `process-inbox` followed by `organize`. |

> **Inbox awareness:** Even without `--check-inbox`, the generated index always includes a
> **📬 Inbox — Pending Files** section when there are unprocessed files in `inbox/`, so you
> never lose track of what's waiting.

> **Tip:** Re-run with `--output tools/index.md` whenever you add new notes or assets to keep the index current.

---

#### `search` — Full-text keyword search

Searches all notes for a keyword or phrase and prints matching lines with surrounding context.

```bash
# Search everywhere
python3 tools/notes_helper.py search "action item"

# Search with more context lines
python3 tools/notes_helper.py search FERPA --context 3

# Limit search to one folder
python3 tools/notes_helper.py search deadline --folder graduation
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--context N` | `2` | Lines of context around each match |
| `--folder FOLDER` | all | Limit search to one top-level folder |

---

#### `import` — Import and organize a note file

Reads a Markdown (or plain-text) file from anywhere on your machine, **automatically detects** the right destination folder based on its content, renames it to match repository conventions, and copies it into place.

```bash
# Auto-detect destination and import
python3 tools/notes_helper.py import /path/to/my-note.md

# Preview what would happen — no files are changed
python3 tools/notes_helper.py import /path/to/my-note.md --dry-run

# Override the auto-detected destination (folder or full path)
python3 tools/notes_helper.py import /path/to/my-note.md --dest meetings
python3 tools/notes_helper.py import /path/to/my-note.md --dest meetings/2026-03-13-topic.md

# Import and immediately refresh the master index
python3 tools/notes_helper.py import /path/to/my-note.md --organize

# Overwrite the destination if it already exists
python3 tools/notes_helper.py import /path/to/my-note.md --force
```

**How destination detection works:**

The tool scores each possible folder against a keyword list derived from the file's name and content:

| Detected folder | Example keywords |
|-----------------|-----------------|
| `graduation` | graduation, ceremony, commencement, diploma, regalia |
| `meetings` | meeting, agenda, minutes, attendees, action items |
| `daily-logs` | today, daily log, today's focus, completed today |
| `transcripts` | transcript, credit transfer, evaluation request |
| `residency-tuition` | residency, tuition, in-state, domicile |
| `admissions` | admissions, application, enrollment, applicant |
| `continuing-education` | continuing education, workforce, scholarship, CE |
| `personal-data` | FERPA, privacy, PII, data handling |
| `updates` | policy update, workflow update, announcement |

Filenames are also normalised automatically:
- Date-stamped files going into **daily-logs** become `YYYY-MM-DD.md` and are placed in the correct `daily-logs/YYYY-MM/` sub-folder.
- Meeting notes become `YYYY-MM-DD-topic.md` inside `meetings/`.
- All other files are renamed to lowercase kebab-case.

**Sample output:**

```
============================================================
  📥 Import Analysis
============================================================
  Source     : /tmp/my-meeting-notes.md
  Detected   : meetings  (confidence: 75%)
  Destination: meetings/2026-03-13-my-meeting-notes.md
  Title      : My Meeting Notes
  Words      : 142
  Open items : 3
  Dates found: 2026-03-13

  ✅ Imported to: meetings/2026-03-13-my-meeting-notes.md
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dest DIR_OR_FILE` | Override destination (folder name or full path, relative to repo root) |
| `--dry-run` | Show analysis and planned destination without copying any files |
| `--force` | Overwrite the destination file if it already exists |
| `--organize` | Refresh `tools/index.md` after a successful import |

---

#### `process-inbox` — Bulk-import everything in the inbox folder

Reads every `.md` and `.txt` file placed in the `inbox/` folder, auto-detects the right destination for each one, imports it, and removes it from the inbox.  This is the same logic as `import` but applied to all inbox files at once.

```bash
# Preview what would happen — no files are moved
python3 tools/notes_helper.py process-inbox --dry-run

# Import all inbox files and refresh the master index
python3 tools/notes_helper.py process-inbox --organize

# Overwrite destinations that already exist
python3 tools/notes_helper.py process-inbox --force --organize
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would happen without copying or deleting any files |
| `--force` | Overwrite destination files that already exist |
| `--organize` | Refresh `tools/index.md` after all files are processed |

> **Tip:** You don't need to run this manually. Just upload files to `inbox/` on GitHub and the **Inbox Processor** workflow runs automatically.

---

### Quick Reference

| Goal | Command |
|------|---------|
| What's in this note? | `python3 tools/notes_helper.py analyze <file>` |
| What have I written recently? | `python3 tools/notes_helper.py sort --by date` |
| Which notes are the most detailed? | `python3 tools/notes_helper.py sort --by size` |
| List all assets by file size | `python3 tools/notes_helper.py sort --by size --folder assets` |
| List all assets by date | `python3 tools/notes_helper.py sort --by date --folder assets` |
| Get a full overview of all notes and assets | `python3 tools/notes_helper.py organize` |
| Find everything about a topic | `python3 tools/notes_helper.py search <keyword>` |
| Refresh the master index file | `python3 tools/notes_helper.py organize --output tools/index.md` |
| Process inbox then refresh the index | `python3 tools/notes_helper.py organize --check-inbox --output tools/index.md` |
| Bring in an external note file | `python3 tools/notes_helper.py import <file>` |
| Process all files in inbox/ | `python3 tools/notes_helper.py process-inbox --organize` |
| Use the tool without remembering commands | `python3 tools/notes_helper.py agent` |

---

## Running via GitHub Actions (no local commands required)

If you can't run commands on your PC, you can trigger the helper tool directly from the **GitHub web interface** using the **Notes Helper** workflow.

### How to use it

1. Go to your repository on [github.com](https://github.com).
2. Click the **Actions** tab.
3. In the left sidebar, click **Notes Helper**.
4. Click **Run workflow** (top-right of the run list).
5. Fill in the inputs:

| Input | Description |
|-------|-------------|
| **Command** | `analyze`, `sort`, `organize`, `search`, `import`, or `process-inbox` |
| **File** | *(analyze)* Path to a single note, or blank for all notes; *(import)* path to the file to import |
| **Keyword** | *(search only)* Keyword or phrase to search for |
| **Folder** | *(sort / search)* Limit to a top-level folder, e.g. `graduation` or `assets` |
| **Sort by** | *(sort only)* `name`, `date`, or `size` |
| **Context** | *(search only)* Lines of context around matches (default: 2) |
| **Output** | *(organize only)* File to write the index to, e.g. `tools/index.md` |
| **Import dest** | *(import only)* Destination folder or path (leave blank to auto-detect) |
| **Import dry-run** | *(import / process-inbox)* `true` to preview without copying |
| **Import organize** | *(import / process-inbox)* `true` to refresh the index after import |

6. Click **Run workflow** — the output appears in the workflow run log.

> **Tip:** When you run `import` or `process-inbox`, the workflow automatically commits the new files (and the refreshed index if **Import organize** is `true`) back to the repository.

### Inbox auto-processing

Uploading files to `inbox/` via the GitHub web interface triggers the **Inbox Processor** workflow automatically — no manual steps needed.  See [`inbox/README.md`](../inbox/README.md) for full details.

---

## Interactive Agent Mode

If you have access to a terminal but prefer not to memorise command syntax, use the **agent** subcommand:

```bash
python3 tools/notes_helper.py agent
```

You will see a prompt where you can type requests in plain language:

```
notes> process inbox
notes> process inbox dry-run
notes> process inbox organize
notes> import /path/to/note.md
notes> import /path/to/note.md to meetings
notes> import /path/to/note.md dry-run
notes> analyze daily-logs/2026-03/2026-03-13.md
notes> sort by date
notes> sort by size in graduation
notes> sort assets by size
notes> organize to tools/index.md
notes> search FERPA
notes> search deadline in graduation
notes> help
notes> quit
```

The agent interprets your request, runs the right command, and prints the result — no flags needed.

---

## Web GUI (`app.py`)

A **Flask web application** that lets you browse, read, search, and ask AI questions about your work notes — all in a clean browser UI using the same visual design as the `linuxnlearn` project.

### Features

| Feature | Description |
|---------|-------------|
| **Home** | Grid of all sections with live note counts |
| **Section view** | Scrollable list of every note in a section, with word count and open action item badges |
| **Note view** | Full markdown rendering, open action items highlighted at the top, prev/next navigation |
| **Search** | Full-text keyword search across all notes with highlighted snippets |
| **AI Assistant** | Chat interface powered by Perplexity or Google Gemini — context-aware per section |

### Setup

**1. Install dependencies**

```bash
pip install -r tools/requirements-web.txt
```

**2. Configure your AI key** *(optional — browsing and search work without it)*

```bash
cp tools/.env.example tools/.env
# Edit tools/.env and add your PERPLEXITY_API_KEY
```

Get a free Perplexity API key at <https://www.perplexity.ai/settings/api>.

**3. Run the app**

```bash
# From the repo root:
python3 tools/app.py
```

Then open **http://localhost:5000** in your browser.

### New files added

| File | Purpose |
|------|---------|
| `tools/app.py` | Flask application — routes for browse, note view, search, and AI |
| `tools/config.py` | Flask + AI provider settings (reads from `tools/.env`) |
| `tools/ai_providers.py` | Perplexity / Gemini abstraction layer |
| `tools/templates/` | Jinja2 HTML templates (base, index, section, note, search, assistant, 404) |
| `tools/static/css/style.css` | Adapted `linuxnlearn` stylesheet |
| `tools/static/js/main.js` | Shared JS placeholder |
| `tools/requirements-web.txt` | Python dependencies for the web app |
| `tools/.env.example` | API key template — copy to `tools/.env` and fill in |

> **Note:** `tools/.env` is in `.gitignore` — your API keys will never be committed.

