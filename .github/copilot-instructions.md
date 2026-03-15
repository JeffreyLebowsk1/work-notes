# Copilot Instructions — Work Notes (Registrar's Office)

This repository is a personal knowledge base **and web application** for a Student Records Registrar's Office employee at Central Carolina Community College. It stores work procedures, policies, meeting notes, daily logs, and coordination materials — and serves them through a Flask-based web GUI hosted on a Jetson Orin Nano.

---

## Core Principles

**Organization, deduplication, and accuracy are the top priorities for every change in this repo.**

1. **Organization** — Every file belongs in the correct section directory. Follow the established folder hierarchy. Use the naming conventions already in place (e.g., `YYYY-MM-DD-topic.md` for meeting notes, `YYYY-MM-DD.md` for daily logs). Never create a new top-level directory without a clear reason.

2. **Deduplication** — Before adding new content, check whether it already exists somewhere in the repository. Consolidate overlapping information rather than duplicating it. If content exists in multiple places, merge it into the most appropriate location and remove the redundant copies.

3. **Accuracy** — Only include factual, verified information. Dates, policy names, process steps, and institutional references must be correct. Correct inaccurate or outdated content rather than leaving it alongside the updated version.

---

## Repository Structure

```
work-notes/
├── .github/
│   ├── copilot-instructions.md   ← This file
│   └── workflows/
│       └── notes-helper.yml      ← GitHub Actions workflow
├── README.md                     ← Main navigation hub
├── SETUP.md                      ← Git + Google Drive setup guide
├── _links.md                     ← Centralized index of important links
├── academic-calendar.md          ← Auto-synced from calendar.cccc.edu
├── contacts.md                   ← Staff contacts directory
├── email-templates.md            ← Common registrar email templates
├── admissions/                   ← Admissions notes and requirements
├── assets/                       ← Shared images, spreadsheets, and documents
├── continuing-education/         ← CE scholarship processes and workforce programs
├── daily-logs/                   ← Day-to-day logs, organized by month (YYYY-MM/)
├── financial-aid/                ← Financial aid reference
├── graduation/                   ← Graduation Coordinator hub
│   ├── ceremonies/
│   ├── checklists/
│   ├── communications/
│   ├── student-tracking/
│   └── timelines/
├── inbox/                        ← Drop zone for files to be auto-sorted
├── meetings/                     ← Meeting notes by date
├── personal-data/                ← FERPA and data handling guidelines
├── residency-tuition/            ← Residency determinations and tuition classifications
├── tests/                        ← pytest test suite for tools/
├── tools/                        ← Flask web app, CLI utility, and supporting modules
│   ├── app.py                    ← Flask web application (main)
│   ├── notes_helper.py           ← CLI entry point
│   ├── config.py                 ← Environment-based configuration
│   ├── ai_providers.py           ← Gemini / Perplexity AI integration
│   ├── _helpers.py               ← Shared utilities (file discovery, metadata)
│   ├── _commands.py              ← CLI subcommands (analyze, sort, organize, search)
│   ├── _importer.py              ← File import and inbox processing
│   ├── _agent.py                 ← Interactive agent mode
│   ├── _advisor.py               ← Student advisor lookup (parses Excel)
│   ├── _calendar_sync.py         ← Scrapes calendar.cccc.edu → academic-calendar.md
│   ├── _directory_sync.py        ← Scrapes cccc.edu staff/dept directories
│   ├── _qr_generator.py          ← QR code generation via qoder API
│   ├── _pii_scanner.py           ← Pre-commit PII detection
│   ├── templates/                ← Jinja2 HTML templates
│   ├── static/                   ← CSS, JS, icons, manifest
│   └── .env                      ← Local secrets (not committed)
├── transcripts/                  ← Transcript processing procedures and templates
└── updates/                      ← Running log of policy, technology, and workflow changes
```

---

## Development Environment

The user edits this repo on **Windows** in VS Code, with the code stored at `H:\work-notes`. The production server is a **Jetson Orin Nano** on the local network, accessed via SSH.

- **SSH alias**: `madmatter-lan` → `madmatter@192.168.1.146`
- **Jetson repo path**: `/home/madmatter/work-notes`
- **The Windows and Jetson repos are the same Git repo** — changes flow through `git push` / `git pull`.
- **Do NOT run `python tools/app.py` on Windows** — the Flask app runs on the Jetson only.
- **Do NOT create scratch/temp files in the repo root** — they risk being committed. Use terminal pipes or system temp directories.

---

## Deployment Workflow

After making code changes, the deploy cycle is:

```powershell
# 1. Commit and push (from Windows)
git add -A; git commit -m "description"; git push

# 2. Pull on Jetson (single SSH command)
ssh madmatter-lan "cd /home/madmatter/work-notes && git pull"

# 3. Restart the service (single SSH command)
ssh madmatter-lan "systemctl --user restart work-notes-web"

# 4. Verify (single SSH command)
ssh madmatter-lan "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:4200/"
```

### Critical deployment rules

- **ALWAYS use `systemctl --user restart work-notes-web`** to restart the app. Never use raw `pkill`/`gunicorn` commands.
- **Never chain multiple commands in a single SSH string from PowerShell** — `ssh host "cmd1 && cmd2"` is unreliable. Use separate `ssh` calls, one command each.
- **Other managed services**: `work-notes-web` (Flask/gunicorn on :4200), `qrcoder` (QR API on :8080), `ngrok` (tunnel manager). All are user-level systemd services.
- **Public URLs**: `https://cccc.ngrok.app` (web app), `https://qoder.ngrok.app` (QR API)

---

## Flask Web Application (`tools/app.py`)

The web app renders all markdown notes as styled HTML pages and provides several interactive features:

### Routes

| Route | Template | Purpose |
|-------|----------|---------|
| `/` | `index.html` | Home page — section cards grid |
| `/section/<key>` | `section.html` | List notes in a section |
| `/note/<path>` | `note.html` | Render a single markdown note |
| `/note/new` | `note_new.html` | Create a new note (form) |
| `/search` | `search.html` | Full-text keyword search |
| `/calendar` | `calendar.html` | Interactive grid/list calendar |
| `/contacts` | `note.html` | Staff contacts directory |
| `/advisor` | `advisor.html` | Student advisor lookup |
| `/email-templates` | `email-templates.html` | Registrar email templates |
| `/assets` | `assets.html` | File browser + upload |
| `/assistant` | `assistant.html` | AI chat assistant |
| `/api/ask` | JSON | AI assistant API endpoint |
| `/api/programs` | JSON | Program code autocomplete |
| `/api/advisor` | JSON | Advisor lookup API |

### Key implementation details

- **Markdown rendering**: `_render_markdown()` converts `.md` files to HTML using the `markdown` library with `tables`, `fenced_code`, and `toc` extensions. Mermaid fenced code blocks are converted to `<pre class="mermaid">` for client-side rendering.
- **Mermaid.js v11** is loaded via CDN in `base.html` — any markdown file can include mermaid diagrams in fenced code blocks.
- **Calendar**: `_parse_calendar_events()` parses `academic-calendar.md` into structured event dicts. The template provides grid view (monthly navigation, color-coded event labels) and list view (rendered markdown).
- **Static assets**: CSS in `tools/static/css/style.css`, JS in `tools/static/js/main.js`. Cache-busted via `static_asset_url()`.
- **Config**: `tools/config.py` loads from `tools/.env` — see `tools/.env.example` for all settings.
- **Auth**: Optional HTTP Basic Auth when `APP_USERNAME` and `APP_PASSWORD` are set.

### When modifying the web app

- Edit templates in `tools/templates/`, CSS in `tools/static/css/style.css`, JS in `tools/static/js/main.js`.
- New routes should follow the pattern in existing routes (breadcrumb, page-header, section-content structure).
- All templates extend `base.html` which provides the navbar, footer, dark mode toggle, and bottom navigation.
- After changes, deploy using the workflow above (commit → push → pull → systemctl restart).

---

## CLI Tool (`tools/notes_helper.py`)

Run from the repo root: `python3 tools/notes_helper.py <command>`

| Command | Purpose |
|---------|---------|
| `analyze [FILE]` | Word count, headings, action items, dates |
| `sort [--by date\|size\|name] [--folder DIR]` | List notes sorted |
| `organize [--output FILE]` | Generate master index (`tools/index.md`) |
| `search KEYWORD [--folder DIR]` | Full-text search across notes |
| `import FILE [--dest DIR]` | Import a file into the correct section |
| `process-inbox [--organize]` | Auto-sort files from `inbox/` |
| `agent` | Interactive natural-language mode |
| `sync-calendar [--year YEAR]` | Scrape calendar.cccc.edu → `academic-calendar.md` |
| `sync-directory [--with-detail]` | Scrape faculty/staff and department directories |

---

## Testing

Tests live in `tests/` and use **pytest**. Run from repo root:

```bash
python -m pytest tests/ -v
```

Test files cover: `app.py` helpers, CLI commands, helpers, importer logic, and parser registration. Tests use `tmp_path` fixtures and monkeypatching — they never touch the real repo.

---

## File & Content Conventions

- **Markdown only** for all notes (`.md`). Use headers (`##`, `###`) to organize content within files.
- **Dates** always use ISO format: `YYYY-MM-DD`.
- **Daily logs** go in `daily-logs/YYYY-MM/YYYY-MM-DD.md`.
- **Meeting notes** go in `meetings/YYYY-MM-DD-topic.md`. Use `meetings/template.md` as the starting template.
- **Updates** (policy, tech, workflow, graduation) go in the appropriate file inside `updates/`.
- **Links and external resources** go in `_links.md`, not scattered across individual notes.
- Keep each file focused on one topic. Split large files rather than letting a single file grow unwieldy.
- Section `README.md` files serve as the index/overview for their directory — keep them current when files are added or removed.

---

## What to Avoid

- Do not duplicate content that already exists in another file — link to it instead.
- Do not leave placeholder text, stubs, or "TODO" sections in committed files unless they are explicitly part of a checklist workflow.
- Do not add personal identifiable information (PII) or student records data directly to this repository. Refer to `personal-data/` guidelines for FERPA compliance. Use `tools/_pii_scanner.py` to check before committing.
- Do not rename or restructure directories without updating `README.md`, `SETUP.md`, and the `tools/index.md` to match.
- Do not modify `tools/index.md` by hand — it is auto-generated by `tools/notes_helper.py organize`.
- Do not create scratch or temporary files in the repo root — they risk being committed.
- Do not run the Flask app locally on Windows — it is designed for the Jetson environment.

---

## When Adding or Editing Notes

1. **Check for existing content first** — search the relevant section directory before creating a new file.
2. **Use the correct directory** — match the content to the section described above.
3. **Follow the existing style** — match heading levels, emoji usage, and table formatting already present in that section.
4. **Update the section README** if you add a meaningful new file.
5. **Add links to `_links.md`** if the content references an important external resource.
6. **Regenerate `tools/index.md`** (via `python tools/notes_helper.py organize`) if the overall file structure changes significantly.
