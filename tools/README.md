# 🛠️ Tools

This folder contains helper scripts for managing your work notes.

---

## notes_helper.py

A command-line tool to **analyze**, **sort**, **organize**, and **search** your notes.

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

### Quick Reference

| Goal | Command |
|------|---------|
| What's in this note? | `python3 tools/notes_helper.py analyze <file>` |
| What have I written recently? | `python3 tools/notes_helper.py sort --by date` |
| Which notes are the most detailed? | `python3 tools/notes_helper.py sort --by size` |
| Get a full overview of all notes | `python3 tools/notes_helper.py organize` |
| Find everything about a topic | `python3 tools/notes_helper.py search <keyword>` |
| Refresh the master index file | `python3 tools/notes_helper.py organize --output tools/index.md` |
