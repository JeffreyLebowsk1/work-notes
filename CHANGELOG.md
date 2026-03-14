# 📜 Changelog

A log of significant changes to this repository — new sections, reorganizations, and major updates.

> Add newest entries at the top.

---

## 2026-03-14 — Email Templates, Mermaid Diagrams, QR Codes & UI Polish

### Added
- **Email Templates Page** — New `/email-templates` route displaying all email templates from multiple files
  - Templates aggregated from: email-templates.md, graduation/communications/*.md, transcripts/templates/*.md, admissions/homeschool-transcripts.md, continuing-education/personal-enrichment.md
  - Each template includes "Send" button (mailto: link) to open default email client with pre-filled subject and body
  - Supports both `Subject:` and `**Subject:**` markdown formats
- **QR Code Infrastructure** — Created tools/_qr_generator.py module with CLI integration for batch QR generation
  - tools/qr_config.json — centralized list of 14 important links (CFNC, FAFSA, Parchment, NSC, DiplomaSender, CCCC portals, etc.)
  - assets/images/qr-codes/README.md — QR code inventory with credit to qoder API
  - Total: 14 QR code PNG files generated (7 new + 7 existing)
- **Visual Flowcharts & Timelines** — Added Mermaid diagrams to 13 procedural files:
  - Admissions: health-sciences-changes.md (admissions decision tree), foreign-students-and-registration.md
  - Continuing Education: abe-registration.md, esl-program.md
  - Graduation: ceremony-day.md (timeline), post-ceremony.md (timeline)
  - Financial Aid: foundation-scholarships.md (eligibility flowchart)
  - Residency: policies.md (residency determination flowchart)
  - Transcripts, CCP procedures, CE scholarships, data requests, master checklist (all from previous session)
- **Template Navigation Link** — Added "📧 Email" link to main navbar

### Fixed
- **Residency Policy Links** — Replaced 4 placeholder `<!-- link -->` comments with actual links:
  - State Residency Statutes → ncresidency.org
  - Institutional Residency Policy → rds.md
  - Tuition Rate Schedule → contacts.md
  - Residency Appeal Form → ncresidency.org
- **Chat Container Width** — Reduced desktop chat area from 500px to 350px min-height; added 950px max-width constraint
- **Reference Links** — Applied 20 unlinked URL fixes across 8 files (CFNC, DiplomaSender, Parchment, NSC, Herff Jones, NCSEAA, NCCCS, NCICU, SACSCOC, Nelnet)

### Improved
- **Email Template Parser** — Now scans 8 different template locations with support for multiple markdown subject formats
- **URL Encoding** — Proper URI encoding for mailto: links; templates auto-truncated at 1800 chars to respect URL length limits

### Technical
- Commits: ba5d73a (Mermaid), b80a87e (CSS/checklists), ada98e6 (email templates), 17d1c84 (email expansion + residency links)
- Flask routes: Added `/email-templates` endpoint with template grouping by section
- Added urllib.parse import for proper URL encoding

---

## 2026-03-13 — Initial Repository Setup

### Added
- Full folder structure for Registrar's Office work notes
- transcripts/ — transcript processing notes and procedures
- residency-tuition/ — residency and tuition policies and procedures
- admissions/ — admissions notes and requirements
- personal-data/ — FERPA reference and data handling guidelines
- graduation/ — full graduation coordinator hub
- meetings/ — meeting notes by date
- daily-logs/ — day-to-day work logs
- assets/ — shared images, spreadsheets, and documents
- updates/ — policy, technology, workflow, and graduation updates log
- _links.md — central quick links and resources
- SETUP.md — Google Drive + GitHub setup and workflow guide
- academic-calendar.md — key academic dates and deadlines
- contacts.md — internal and external contacts directory
- faq.md — frequently asked questions and standard answers
- recurring-tasks.md — master list of recurring tasks by frequency
- glossary.md — terms, acronyms, and status codes
- email-templates.md — master email template collection
- exceptions-and-edge-cases.md — log of unusual situations and resolutions
- reports.md — notes on regularly run reports
- CHANGELOG.md — this file
- .github/ISSUE_TEMPLATE/ — issue templates for Task, Follow-Up, and Exception

---
*Last updated: 2026-03-14*