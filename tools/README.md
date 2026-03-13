# 🛠️ Tools

This folder contains helper scripts for managing your work notes.

---

## notes_helper.py

A command-line tool to **analyze**, **sort**, **organize**, **search**, and **import** your notes.

**Requirements:** Python 3.8+ (no extra packages needed — uses the standard library only)

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
```

**Options:**

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--by` | `name`, `date`, `size` | `name` | Sort criterion |
| `--folder` | folder name | all | Limit to one top-level folder |

---

#### `organize` — Generate a master index

Produces a Markdown index of all notes grouped by folder, including a word-count summary table and a consolidated list of all open action items.

```bash
# Print the index to the terminal
python3 tools/notes_helper.py organize

# Write the index to a file (refreshes it each time)
python3 tools/notes_helper.py organize --output tools/index.md
```

> **Tip:** Re-run with `--output tools/index.md` whenever you add new notes to keep the index current.

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

### Quick Reference

| Goal | Command |
|------|---------|
| What's in this note? | `python3 tools/notes_helper.py analyze <file>` |
| What have I written recently? | `python3 tools/notes_helper.py sort --by date` |
| Which notes are the most detailed? | `python3 tools/notes_helper.py sort --by size` |
| Get a full overview of all notes | `python3 tools/notes_helper.py organize` |
| Find everything about a topic | `python3 tools/notes_helper.py search <keyword>` |
| Refresh the master index file | `python3 tools/notes_helper.py organize --output tools/index.md` |
| Bring in an external note file | `python3 tools/notes_helper.py import <file>` |
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
| **Command** | `analyze`, `sort`, `organize`, `search`, or `import` |
| **File** | *(analyze)* Path to a single note, or blank for all notes; *(import)* path to the file to import |
| **Keyword** | *(search only)* Keyword or phrase to search for |
| **Folder** | *(sort / search)* Limit to a top-level folder, e.g. `graduation` |
| **Sort by** | *(sort only)* `name`, `date`, or `size` |
| **Context** | *(search only)* Lines of context around matches (default: 2) |
| **Output** | *(organize only)* File to write the index to, e.g. `tools/index.md` |
| **Import dest** | *(import only)* Destination folder or path (leave blank to auto-detect) |
| **Import dry-run** | *(import only)* `true` to preview without copying |
| **Import organize** | *(import only)* `true` to refresh the index after import |

6. Click **Run workflow** — the output appears in the workflow run log.

> **Tip:** When you run `import`, the workflow automatically commits the new file (and the refreshed index if **Import organize** is `true`) back to the repository.

---

## Interactive Agent Mode

If you have access to a terminal but prefer not to memorise command syntax, use the **agent** subcommand:

```bash
python3 tools/notes_helper.py agent
```

You will see a prompt where you can type requests in plain language:

```
notes> import /path/to/note.md
notes> import /path/to/note.md to meetings
notes> import /path/to/note.md dry-run
notes> analyze daily-logs/2026-03/2026-03-13.md
notes> sort by date
notes> sort by size in graduation
notes> organize to tools/index.md
notes> search FERPA
notes> search deadline in graduation
notes> help
notes> quit
```

The agent interprets your request, runs the right command, and prints the result — no flags needed.

