# 📚 Registrar's Office Notes

> Personal work notes, references, and resources for the Student Records Registrar's Office.

## 🗂️ Sections

| Section | Description |
|---|---|
| [📄 Transcripts](./transcripts/) | Transcript processing, procedures, and templates |
| [🏠 Residency & Tuition](./residency-tuition/) | Residency determinations, tuition classifications, data |
| [🎓 Admissions](./admissions/) | Admissions notes, requirements, and coordination |
| [🔒 Personal Data](./personal-data/) | FERPA, data handling guidelines, privacy procedures |
| [🎓 Graduation](./graduation/) | **Graduation Coordinator** — ceremonies, checklists, timelines, and more |
| [💰 Financial Aid](./financial-aid/) | Financial Aid policies, SAP, FAFSA, OBBBA updates, Foundation scholarships |
| [📅 Meetings](./meetings/) | Meeting notes by date |
| [📓 Daily Logs](./daily-logs/) | Day-to-day logs and notes |
| [📁 Assets](./assets/) | Shared images, spreadsheets, and files |
| [📣 Updates & Changes](./updates/) | Policy, technology, workflow, and graduation updates log |
| [📖 Documentation](./documentation/) | Reference guides, glossary, FAQs, and setup documentation |

## 📋 Reference Files

| File | Description |
|---|---|
| [📅 Academic Calendar](./academic-calendar.md) | Key semester dates and Registrar office deadlines |
| [👥 Contacts](./contacts.md) | Internal staff, campus offices, and vendor contacts |
| [❓ FAQ](./documentation/faq.md) | Common student & staff questions with standard answers |
| [🔁 Recurring Tasks](./documentation/recurring-tasks.md) | Daily, weekly, semester, and annual task checklists |
| [🗂️ Glossary](./documentation/glossary.md) | Terms, acronyms, and status codes |
| [📝 Email Templates](./email-templates.md) | Ready-to-use email templates for all areas |
| [🚨 Exceptions & Edge Cases](./documentation/exceptions-and-edge-cases.md) | Log of unusual situations and how they were resolved |
| [📊 Reports](./documentation/reports.md) | Notes on regularly run reports |
| [🔗 Links & Resources](./_links.md) | Central index of important links |
| [⚙️ Setup Guide](./SETUP.md) | Google Drive + GitHub setup and workflow guide |
| [📜 Changelog](./CHANGELOG.md) | History of changes to this repository |

## ⚡ Quick Actions

| Action | What it does | Button |
|---|---|---|
| Notes Helper | analyze, sort, organize, search, import, or process-inbox | [![Notes Helper](https://github.com/JeffreyLebowsk1/work-notes/actions/workflows/notes-helper.yml/badge.svg)](https://github.com/JeffreyLebowsk1/work-notes/actions/workflows/notes-helper.yml) |
| Inbox Processor | import every file waiting in `inbox/` | [![Inbox Processor](https://github.com/JeffreyLebowsk1/work-notes/actions/workflows/inbox-processor.yml/badge.svg)](https://github.com/JeffreyLebowsk1/work-notes/actions/workflows/inbox-processor.yml) |

---

## 🔄 How It Works

The repository is a **living knowledge base** for the Registrar's Office. Here's how all the pieces fit together:

1. **Notes** — All content is stored as Markdown (`.md`) files organized into topic folders (`graduation/`, `meetings/`, `transcripts/`, etc.). Edit them directly in any text editor, VS Code, or the GitHub web interface.

2. **Day-to-day editing** — After editing, commit and push with `git push`.

3. **Inbox** — Drop a `.md` or `.txt` file into [`inbox/`](./inbox/) on GitHub and the **Inbox Processor** workflow automatically detects the correct destination folder, renames the file to match repository conventions, and moves it into place.

4. **CLI Tools** — [`tools/notes_helper.py`](./tools/README.md) is a command-line tool for analyzing notes, sorting by date or size, generating a master index (`tools/index.md`), searching by keyword, and importing external files.

5. **Web App** — Run `python3 tools/app.py` to launch a browser UI (at `http://localhost:4200`) for browsing sections, reading rendered Markdown notes, running full-text searches, and chatting with the AI Assistant.

6. **AI Assistant** — The web app includes a chat interface powered by Perplexity or Google Gemini. It's pre-configured with Registrar's Office context (FERPA, graduation, transcripts, etc.) and can answer procedural questions on demand.

7. **GitHub Actions** — Two workflows let you run tools directly from the GitHub website without a terminal:
   - **[Notes Helper](https://github.com/JeffreyLebowsk1/work-notes/actions/workflows/notes-helper.yml)** — Manually triggered; runs any `notes_helper.py` command (analyze, sort, organize, search, import, process-inbox).
   - **[Inbox Processor](https://github.com/JeffreyLebowsk1/work-notes/actions/workflows/inbox-processor.yml)** — Automatically triggered when files are pushed to `inbox/`; processes and sorts them.

See [SETUP.md](./SETUP.md) for initial setup instructions and [tools/README.md](./tools/README.md) for full CLI and web app documentation.

---

## 📌 Quick Links
- [Today's Log](./daily-logs/)
- [Graduation Checklists](./graduation/checklists/)
- [Upcoming Ceremonies](./graduation/ceremonies/)
- [Latest Updates](./updates/)
- [Recurring Tasks](./documentation/recurring-tasks.md)
- [All Links & Resources](./_links.md)

---
*Last updated: 2026-03-14*
