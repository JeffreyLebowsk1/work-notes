"""
app.py — Work Notes web GUI.

Run from the repo root:
    python3 tools/app.py

Or from the tools/ directory:
    python3 app.py

Then open http://localhost:4200 in your browser.
"""

import logging
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import markdown as md
from flask import (
    Flask, Response, jsonify, redirect, render_template,
    request, send_from_directory, url_for,
)
from flask_compress import Compress
from markupsafe import Markup
from werkzeug.utils import secure_filename

# Ensure tools/ is on sys.path so sibling modules resolve correctly.
_TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS_DIR))

import ai_providers  # noqa: E402
import config  # noqa: E402
from _helpers import REPO_ROOT, _all_notes, _parse_note, _relative  # noqa: E402

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES

# Gzip compression for all responses > 500 bytes
Compress(app)
app.config["COMPRESS_MIMETYPES"] = [
    "text/html", "text/css", "application/javascript",
    "application/json", "image/svg+xml",
]
app.config["COMPRESS_MIN_SIZE"] = 500

# Seconds to wait before opening the browser after the dev server starts.
# The delay lets Flask finish binding to the port before the browser hits it.
_BROWSER_OPEN_DELAY = 1.0

# ---------------------------------------------------------------------------
# Section definitions — top-level folders with display metadata
# ---------------------------------------------------------------------------

SECTIONS = {
    "graduation": {
        "title": "Graduation",
        "icon": "🎓",
        "description": "Graduation coordinator hub — ceremonies, checklists, timelines, and student tracking.",
        "color": "blue",
    },
    "meetings": {
        "title": "Meetings",
        "icon": "📅",
        "description": "Meeting notes organized by date.",
        "color": "teal",
    },
    "daily-logs": {
        "title": "Daily Logs",
        "icon": "📓",
        "description": "Day-to-day logs organized by month.",
        "color": "green",
    },
    "transcripts": {
        "title": "Transcripts",
        "icon": "📄",
        "description": "Transcript processing procedures and templates.",
        "color": "orange",
    },
    "admissions": {
        "title": "Admissions",
        "icon": "✏️",
        "description": "Admissions notes and requirements.",
        "color": "blue",
    },
    "residency-tuition": {
        "title": "Residency & Tuition",
        "icon": "🏠",
        "description": "Residency determinations and tuition classifications.",
        "color": "teal",
    },
    "continuing-education": {
        "title": "Continuing Education",
        "icon": "📚",
        "description": "CE scholarship processes and workforce programs.",
        "color": "green",
    },
    "personal-data": {
        "title": "Personal Data",
        "icon": "🔒",
        "description": "FERPA and data handling guidelines.",
        "color": "orange",
    },
    "updates": {
        "title": "Updates",
        "icon": "📣",
        "description": "Running log of policy, technology, and workflow changes.",
        "color": "blue",
    },
    "financial-aid": {
        "title": "Financial Aid",
        "icon": "💰",
        "description": "Financial aid coordination and notes.",
        "color": "teal",
    },
}

# Pre-computed section directories — keyed by section name.
# Values are built from SECTIONS (a module-level constant) and REPO_ROOT,
# so no path ever depends on user-supplied input.
_SECTION_DIRS: dict[str, Path] = {
    key: REPO_ROOT / key for key in SECTIONS
}

@app.after_request
def _add_cache_headers(response):
    """Set cache headers to reduce redundant fetches over the tunnel."""
    if request.path.startswith("/static/"):
        # Static assets: cache 1 hour (cache-busted via ?v= query param)
        response.headers["Cache-Control"] = "public, max-age=3600, immutable"
    elif request.path.startswith("/repo-assets/"):
        # Repo assets (images, docs): cache 10 minutes
        response.headers["Cache-Control"] = "public, max-age=600"
    else:
        # HTML pages: allow browser back/forward cache, revalidate on navigate
        response.headers["Cache-Control"] = "private, no-cache"
    return response


@app.before_request
def _basic_auth_check():
    """Enforce HTTP Basic Auth when APP_USERNAME is configured.

    Set APP_USERNAME and APP_PASSWORD in tools/.env (or as hosting env vars)
    to password-protect the app when deployed to a public URL.
    Leave both blank for local/dev use with no auth prompt.
    """
    if not config.APP_USERNAME:
        return  # Auth disabled — local use
    auth = request.authorization
    if (
        auth is None
        or auth.username != config.APP_USERNAME
        or auth.password != config.APP_PASSWORD
    ):
        return Response(
            "CCCC Notes — Authentication required.",
            401,
            {"WWW-Authenticate": 'Basic realm="CCCC Notes"'},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _notes_in_section(section_key: str) -> list[dict]:
    """Return parsed metadata for every note in a section folder, sorted by path.

    ``section_key`` is validated against the pre-computed ``_SECTION_DIRS``
    dict so the resulting path never depends on user-supplied input.
    """
    section_dir = _SECTION_DIRS.get(section_key)
    if section_dir is None or not section_dir.is_dir():
        return []
    paths = sorted(
        p for p in section_dir.rglob("*.md")
        if p.name.lower() != "readme.md"
    )
    return [_parse_note(p) for p in paths]


def _render_markdown(text: str) -> Markup:
    """Convert a markdown string to safe HTML.

    The ``text`` argument must come from a trusted source (repo notes only).
    """
    if not text:
        return Markup("")
    html = md.markdown(
        text,
        extensions=["fenced_code", "tables", "toc"],
    )
    # Wrap tables in a scroll container without changing table semantics
    html = html.replace(
        "<table>", '<div class="table-wrapper"><table>'
    ).replace("</table>", "</table></div>")
    # Convert fenced mermaid code blocks to <pre class="mermaid"> for Mermaid.js
    import re
    html = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        r'<pre class="mermaid">\1</pre>',
        html,
        flags=re.DOTALL,
    )
    return Markup(html)


def _parse_email_templates() -> list[dict]:
    """Parse email templates from all template files in the repo.
    
    Scans multiple locations:
    - email-templates.md (main)
    - graduation/communications/*.md
    - transcripts/templates/*.md
    - continuing-education/personal-enrichment.md
    - admissions/homeschool-transcripts.md
    
    Returns a list of template dicts with mailto_url for quick sending.
    """
    templates = []
    template_files = [
        REPO_ROOT / "email-templates.md",
        REPO_ROOT / "graduation" / "communications" / "internal-communications.md",
        REPO_ROOT / "graduation" / "communications" / "student-announcements.md",
        REPO_ROOT / "transcripts" / "templates" / "attendance-roster-audit-emails.md",
        REPO_ROOT / "transcripts" / "templates" / "never-attended-letter.md",
        REPO_ROOT / "transcripts" / "templates" / "withdrawal-instructions.md",
        REPO_ROOT / "continuing-education" / "personal-enrichment.md",
        REPO_ROOT / "admissions" / "homeschool-transcripts.md",
    ]
    
    for template_file in template_files:
        if not template_file.exists():
            continue
        
        try:
            content = template_file.read_text(encoding="utf-8")
            file_templates = _parse_template_file(content, template_file.name)
            templates.extend(file_templates)
        except Exception as e:
            app.logger.warning(f"Error parsing {template_file}: {e}")
    
    return templates


def _parse_template_file(content: str, source_filename: str) -> list[dict]:
    """Parse templates from a single file content string.
    
    Handles both:
    - Subject: line format
    - **Subject:** format (markdown bold)
    """
    templates = []
    lines = content.split("\n")
    
    current_section = None
    current_category = None
    current_subject = None
    body_lines = []
    in_body = False
    
    for i, line in enumerate(lines):
        # Section header (##)
        if line.startswith("## "):
            current_section = line[3:].strip()
            current_category = None
            continue
        
        # Category header (###)
        if line.startswith("### "):
            # Save previous template if exists
            if current_category and current_subject and body_lines:
                template = _build_template(
                    current_section, current_category, current_subject, body_lines, source_filename
                )
                if template:
                    templates.append(template)
            
            current_category = line[4:].strip()
            current_subject = None
            body_lines = []
            in_body = False
            continue
        
        # Subject line — plain format: "Subject: ..."
        if line.startswith("Subject:"):
            current_subject = line[8:].strip()
            in_body = False
            continue
        
        # Subject line — markdown bold format: "**Subject:** ..."
        if line.startswith("**Subject:**"):
            current_subject = line[12:].strip()
            in_body = False
            continue
        
        # Separator (---)
        if line.strip() == "---":
            if current_subject:
                in_body = True
            continue
        
        # Also treat "---" at start of line or end as section break? Let's be more careful
        # Body collection
        if in_body and current_subject:
            # Skip metadata lines, empty lines at start
            if line.strip():  # Non-empty line
                body_lines.append(line)
    
    # Save last template
    if current_category and current_subject and body_lines:
        template = _build_template(
            current_section, current_category, current_subject, body_lines, source_filename
        )
        if template:
            templates.append(template)
    
    return templates


def _build_template(section: str | None, category: str, subject: str, body_lines: list[str], source: str) -> dict | None:
    """Build a single template dict with mailto URL."""
    if not category or not subject or not body_lines:
        return None
    
    # Clean up body
    body_text = "\n".join(body_lines).strip()
    body_text = re.sub(r"\n\n+", "\n\n", body_text)  # Normalize multiple newlines
    
    # Truncate very long bodies (mailto has URL length limits)
    if len(body_text) > 1800:
        body_text = body_text[:1800] + "\n\n[… template truncated in email client …]"
    
    # Create mailto URL with proper encoding
    subject_encoded = urllib.parse.quote(subject)
    body_encoded = urllib.parse.quote(body_text)
    mailto_url = f"mailto:?subject={subject_encoded}&body={body_encoded}"
    
    return {
        "section": section or "Templates",
        "category": category,
        "subject": subject,
        "body": body_text,
        "source": source,
        "mailto_url": mailto_url,
    }


@app.context_processor
def inject_static_asset_url():
    """Provide a cache-busted static asset URL helper and global UI vars."""
    def static_asset_url(filename):
        static_path = os.path.join(app.static_folder, filename)
        if os.path.isfile(static_path):
            version = int(os.path.getmtime(static_path))
            return url_for("static", filename=filename, v=version)
        return url_for("static", filename=filename)

    cccc_logo_url = (
        url_for("repo_asset", asset_path=_CCCC_LOGO_REL)
        if _CCCC_LOGO_REL
        else None
    )

    return {"static_asset_url": static_asset_url, "cccc_logo_url": cccc_logo_url}



# ---------------------------------------------------------------------------
# Asset index — whitelist of all files in the repo assets/ folder.
# Keyed by POSIX-style path relative to assets/ (e.g. "images/logo.png").
# Used by /repo-assets/ to serve files without trusting user input.
# ---------------------------------------------------------------------------

_ASSETS_DIR: Path = REPO_ROOT / "assets"
_ASSET_SKIP = {".gitkeep", "README.md"}
_ASSET_INDEX: dict[str, Path] = {}
if _ASSETS_DIR.is_dir():
    for _ap in _ASSETS_DIR.rglob("*"):
        if _ap.is_file() and _ap.name not in _ASSET_SKIP:
            _rel = str(_ap.relative_to(_ASSETS_DIR)).replace("\\", "/")
            _ASSET_INDEX[_rel] = _ap

# Relative path to the CCCC logo within the asset index
_CCCC_LOGO_REL = next(
    (r for r in _ASSET_INDEX if r.lower().startswith("images/cccc")),
    None,
)

# ---------------------------------------------------------------------------
# Note index — whitelist of all known .md files, built once at startup.
# Keyed by POSIX-style repo-relative path (e.g. "graduation/2025-ceremony.md").
# Used by the /note/ route to prevent path injection: full_path is always
# obtained from this pre-enumerated dict, never constructed from user input.
# ---------------------------------------------------------------------------

_NOTE_INDEX: dict[str, Path] = {
    str(p.relative_to(REPO_ROOT)).replace("\\", "/"): p
    for p in _all_notes()
}

# ---------------------------------------------------------------------------
# Write helpers — used by the note-creation and asset-upload routes.
# ---------------------------------------------------------------------------

# Allowed subfolders for asset uploads — validated server-side.
_ASSET_SUBFOLDERS: frozenset[str] = frozenset({
    "images",
    "documents",
    "spreadsheets",
    "screenshots/admissions",
    "screenshots/continuing-education",
    "screenshots/graduation",
    "screenshots/residency-tuition",
    "screenshots/transcripts",
    "screenshots/tools",
    "screenshots/updates",
})

# Grouped structure for the upload UI — drives <optgroup> display.
_ASSET_SUBFOLDER_GROUPS: dict[str, list[str]] = {
    "General": ["documents", "images", "spreadsheets"],
    "Screenshots": [
        "screenshots/admissions",
        "screenshots/continuing-education",
        "screenshots/graduation",
        "screenshots/residency-tuition",
        "screenshots/transcripts",
        "screenshots/tools",
        "screenshots/updates",
    ],
}

# Regex that a safe note filename must fully match.
_NOTE_FILENAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*\.md$")


def _safe_note_filename(raw: str) -> str | None:
    """Return a sanitised .md filename, or None if the input is not safe."""
    name = raw.strip().lower()
    if not _NOTE_FILENAME_RE.match(name):
        return None
    if ".." in name:
        return None
    return name


def _reload_indexes() -> None:
    """Rebuild _NOTE_INDEX and _ASSET_INDEX in-place after a write operation."""
    _NOTE_INDEX.clear()
    _NOTE_INDEX.update(
        {
            str(p.relative_to(REPO_ROOT)).replace("\\", "/"): p
            for p in _all_notes()
        }
    )
    _ASSET_INDEX.clear()
    if _ASSETS_DIR.is_dir():
        for _ap in _ASSETS_DIR.rglob("*"):
            if _ap.is_file() and _ap.name not in _ASSET_SKIP:
                _rel = str(_ap.relative_to(_ASSETS_DIR)).replace("\\", "/")
                _ASSET_INDEX[_rel] = _ap


def _screenshot_checklist() -> list[dict]:
    """Return pending screenshot items parsed from assets/screenshots/README.md.

    Reads the '## Capture Status' table and returns one dict per screenshot
    that has not yet been uploaded.  Each dict contains:
        filename   — bare filename (e.g. 'spro-ccpp-student-type.png')
        screen     — Colleague mnemonic (e.g. 'SPRO')
        subfolder  — upload subfolder (e.g. 'screenshots/admissions')
        asset_key  — key to check in _ASSET_INDEX
    """
    readme = _ASSETS_DIR / "screenshots" / "README.md"
    if not readme.exists():
        return []

    pending = []
    in_table = False
    for line in readme.read_text(encoding="utf-8").splitlines():
        if "| File |" in line:
            in_table = True
            continue
        if not in_table:
            continue
        if line.strip().startswith("|---"):
            continue
        if not line.strip().startswith("|"):
            break

        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 2:
            continue

        rel = parts[0].strip("`")          # e.g. "admissions/spro-ccpp-student-type.png"
        screen = parts[1]                  # e.g. "SPRO"
        asset_key = f"screenshots/{rel}"   # key in _ASSET_INDEX

        path_parts = rel.split("/")
        subfolder = f"screenshots/{path_parts[0]}" if len(path_parts) >= 2 else "screenshots/updates"
        filename = path_parts[-1]

        if asset_key not in _ASSET_INDEX:
            pending.append({
                "filename": filename,
                "screen": screen,
                "subfolder": subfolder,
                "asset_key": asset_key,
            })

    return pending

# ---------------------------------------------------------------------------
# Routes — note browser
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    section_data = {}
    for key, meta in SECTIONS.items():
        notes = _notes_in_section(key)
        section_data[key] = {**meta, "note_count": len(notes)}
    return render_template("index.html", sections=section_data)


@app.route("/section/<section_key>")
def section(section_key):
    if section_key not in SECTIONS:
        return render_template("404.html"), 404
    meta = SECTIONS[section_key]
    notes = _notes_in_section(section_key)
    return render_template(
        "section.html", section_key=section_key, meta=meta, notes=notes
    )


@app.route("/note/<path:note_path>")
def note(note_path):
    # Use a whitelist of all known repo notes to resolve the path.
    # This ensures full_path always comes from our own disk enumeration,
    # never from user-supplied input, preventing path injection.
    full_path = _NOTE_INDEX.get(note_path)
    if full_path is None:
        return render_template("404.html"), 404

    parts = Path(note_path).parts
    section_key = parts[0] if parts else ""
    meta = SECTIONS.get(
        section_key,
        {
            "title": section_key.replace("-", " ").title(),
            "icon": "📄",
            "color": "blue",
            "description": "",
        },
    )

    note_meta = _parse_note(full_path)
    content_html = _render_markdown(
        full_path.read_text(encoding="utf-8", errors="replace")
    )

    # Previous / next navigation within the section
    all_section_notes = (
        _notes_in_section(section_key) if section_key in SECTIONS else []
    )
    current_idx = next(
        (i for i, n in enumerate(all_section_notes) if n["path"] == full_path),
        None,
    )
    prev_note = (
        all_section_notes[current_idx - 1]
        if current_idx and current_idx > 0
        else None
    )
    next_note = (
        all_section_notes[current_idx + 1]
        if current_idx is not None and current_idx < len(all_section_notes) - 1
        else None
    )

    return render_template(
        "note.html",
        note=note_meta,
        content_html=content_html,
        section_key=section_key,
        meta=meta,
        prev_note=prev_note,
        next_note=next_note,
    )


@app.route("/assets")
def assets_browser():
    """Asset browser — lists all files in the repo assets/ folder by sub-folder."""
    groups: dict[str, list[dict]] = {}
    for rel, path in sorted(_ASSET_INDEX.items()):
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue  # file removed from disk since last index rebuild — skip silently
        parts = rel.split("/")
        folder = parts[0] if len(parts) > 1 else "root"
        groups.setdefault(folder, []).append(
            {
                "rel": rel,
                "name": path.name,
                "size": size,
                "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            }
        )
    return render_template("assets.html", groups=groups,
                           subfolders=sorted(_ASSET_SUBFOLDERS),
                           subfolder_groups=_ASSET_SUBFOLDER_GROUPS,
                           pending_screenshots=_screenshot_checklist())


@app.route("/repo-assets/<path:asset_path>")
def repo_asset(asset_path):
    """Serve a file from the repo assets/ folder, guarded by the whitelist."""
    full_path = _ASSET_INDEX.get(asset_path)
    if full_path is None:
        return render_template("404.html"), 404
    return send_from_directory(str(full_path.parent), full_path.name)


# ---------------------------------------------------------------------------
# Routes — note creation
# ---------------------------------------------------------------------------


@app.route("/note/new", methods=["GET", "POST"])
def note_new():
    """Render and handle the new-note creation form."""
    error: str | None = None
    form_data: dict = {}

    if request.method == "POST":
        section_key = request.form.get("section", "").strip()
        filename = request.form.get("filename", "").strip()
        content = request.form.get("content", "")
        form_data = {"section": section_key, "filename": filename, "content": content}

        if section_key not in _SECTION_DIRS:
            error = "Please select a valid section."
        else:
            safe_name = _safe_note_filename(filename)
            if safe_name is None:
                error = (
                    "Invalid filename. Use lowercase letters, digits, hyphens, "
                    "and end with .md (e.g. 2026-03-14-topic.md)."
                )
            else:
                section_dir = _SECTION_DIRS[section_key]
                # Daily-log notes live in a YYYY-MM/ sub-folder — auto-create it.
                if section_key == "daily-logs":
                    date_match = re.match(r"^(\d{4}-\d{2})-\d{2}\.md$", safe_name)
                    dest = (
                        section_dir / date_match.group(1) / safe_name
                        if date_match
                        else section_dir / safe_name
                    )
                else:
                    dest = section_dir / safe_name

                if dest.exists():
                    error = (
                        f"A note named \"{safe_name}\" already exists in "
                        f"{SECTIONS[section_key]['title']}."
                    )
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    _reload_indexes()
                    if section_key == "daily-logs":
                        repo = str(REPO_ROOT)
                        rel_path = str(dest.relative_to(REPO_ROOT)).replace("\\", "/")
                        date_str = safe_name.removesuffix(".md")
                        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                        commit_msg = f"docs: add daily log {date_str} (via web app) [{ts}]"
                        try:
                            result = subprocess.run(
                                ["git", "-C", repo, "add", rel_path],
                                capture_output=True, text=True, timeout=30,
                            )
                            if result.returncode != 0:
                                logging.warning(
                                    "git add failed for daily log %s: %s",
                                    safe_name, result.stderr.strip(),
                                )
                            else:
                                result = subprocess.run(
                                    ["git", "-C", repo, "commit", "-m", commit_msg],
                                    capture_output=True, text=True, timeout=30,
                                )
                                if result.returncode != 0:
                                    logging.warning(
                                        "git commit failed for daily log %s: %s",
                                        safe_name, result.stderr.strip(),
                                    )
                                else:
                                    result = subprocess.run(
                                        ["git", "-C", repo, "push"],
                                        capture_output=True, text=True, timeout=60,
                                    )
                                    if result.returncode != 0:
                                        logging.warning(
                                            "git push failed for daily log %s: %s",
                                            safe_name, result.stderr.strip(),
                                        )
                        except subprocess.TimeoutExpired:
                            logging.warning(
                                "Git operation timed out while committing daily log %s",
                                safe_name,
                            )
                    note_path = str(dest.relative_to(REPO_ROOT)).replace("\\", "/")
                    return redirect(url_for("note", note_path=note_path))

    preselect = request.args.get("section", "daily-logs")
    if preselect not in SECTIONS:
        preselect = "daily-logs"

    return render_template(
        "note_new.html",
        sections=SECTIONS,
        preselect=form_data.get("section", preselect),
        error=error,
        form_data=form_data,
    )


# ---------------------------------------------------------------------------
# Routes — asset upload
# ---------------------------------------------------------------------------


@app.route("/assets/upload", methods=["POST"])
def asset_upload():
    """Accept a multipart file upload and store it in the assets folder."""
    subfolder = request.form.get("subfolder", "").strip()
    if subfolder not in _ASSET_SUBFOLDERS:
        return redirect(url_for("assets_browser") + "?msg=Invalid+subfolder&msg_type=error")

    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return redirect(url_for("assets_browser") + "?msg=No+file+selected&msg_type=error")

    safe_name = secure_filename(uploaded.filename)
    if not safe_name:
        return redirect(url_for("assets_browser") + "?msg=Invalid+filename&msg_type=error")

    dest_dir = _ASSETS_DIR / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name

    if dest.exists():
        return redirect(
            url_for("assets_browser")
            + f"?msg={safe_name}+already+exists&msg_type=error"
        )

    uploaded.save(str(dest))
    _reload_indexes()
    return redirect(
        url_for("assets_browser") + f"?msg={safe_name}+uploaded+successfully&msg_type=success"
    )


@app.route("/assets/commit", methods=["POST"])
def asset_commit():
    """Stage all pending changes in assets/ and push them to the remote.

    This is the one-click alternative to running ``git add assets/ && git commit
    && git push`` from the terminal after uploading files through the web UI.
    """
    repo = str(REPO_ROOT)
    try:
        # Stage everything inside assets/
        result = subprocess.run(
            ["git", "-C", repo, "add", "assets/"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logging.error("git add failed: %s", result.stderr.strip())
            return redirect(
                url_for("assets_browser") + "?msg=git+add+failed.+Check+server+logs.&msg_type=error"
            )

        # Check whether there is actually anything to commit
        status = subprocess.run(
            ["git", "-C", repo, "diff", "--cached", "--quiet"],
            capture_output=True, timeout=10,
        )
        if status.returncode == 0:
            # Exit code 0 -> no staged changes
            return redirect(
                url_for("assets_browser") + "?msg=Nothing+to+commit+-+assets+already+up+to+date&msg_type=success"
            )

        # Build a commit message that includes a UTC timestamp
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        commit_msg = f"chore: commit uploaded assets via web app ({ts})"

        # Commit
        result = subprocess.run(
            ["git", "-C", repo, "commit", "-m", commit_msg],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logging.error("git commit failed: %s", result.stderr.strip())
            return redirect(
                url_for("assets_browser") + "?msg=git+commit+failed.+Check+server+logs.&msg_type=error"
            )

        # Push
        result = subprocess.run(
            ["git", "-C", repo, "push"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            logging.error("git push failed: %s", result.stderr.strip())
            return redirect(
                url_for("assets_browser") + "?msg=Committed+locally+but+git+push+failed.+Check+server+logs.&msg_type=error"
            )

    except subprocess.TimeoutExpired:
        return redirect(
            url_for("assets_browser") + "?msg=Git+operation+timed+out.+Try+again.&msg_type=error"
        )

    return redirect(
        url_for("assets_browser") + "?msg=Assets+committed+and+pushed+to+GitHub&msg_type=success"
    )


# ---------------------------------------------------------------------------
# Routes — search
# ---------------------------------------------------------------------------
# Routes — important links & QR codes
# ---------------------------------------------------------------------------

# Human-readable labels for each qr_config.json key.
_LINK_LABELS: dict[str, str] = {
    "cfnc":               "CFNC",
    "diplomasender":      "DiplomaSender",
    "cccc-scholarships":  "CCCC Scholarships",
    "cccc-financial-aid": "CCCC Financial Aid",
    "civic-center":       "Civic Center (Venue)",
    "ce-schedule":        "CE Course Schedule",
    "academic-calendar":  "Academic Calendar",
    "registrar-office":   "Registrar's Office",
    "transcript-request": "Transcript Request",
    "fafsa":              "FAFSA",
    "advising-hub":       "Advising Hub",
    "nc-residency":       "NC Residency (RDS)",
    "ce-scholarship":     "CE Scholarship Program",
    "ccr-registration":   "CCR Registration",
}


def _load_important_links() -> dict[str, str]:
    """Load important_links from tools/qr_config.json."""
    import json as _json
    config_path = _TOOLS_DIR / "qr_config.json"
    if config_path.exists():
        try:
            return _json.loads(config_path.read_text(encoding="utf-8")).get(
                "important_links", {}
            )
        except Exception:
            pass
    return {}


@app.route("/links")
def links_page():
    """Important links page — shows each configured URL with its QR code."""
    items = []
    for name, url in _load_important_links().items():
        qr_key = f"images/qr-codes/{name}.png"
        items.append({
            "name":    name,
            "label":   _LINK_LABELS.get(name, name.replace("-", " ").title()),
            "url":     url,
            "qr_key":  qr_key,
            "qr_url":  url_for("repo_asset", asset_path=qr_key)
                       if qr_key in _ASSET_INDEX else None,
        })
    return render_template("links.html", items=items)


# ---------------------------------------------------------------------------


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        for path in _all_notes():
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            matches = []
            for i, line in enumerate(lines):
                if pattern.search(line):
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    # Plain text snippet — Jinja2 auto-escapes it in the template.
                    # Keyword highlighting is applied client-side by search.html JS.
                    matches.append(
                        {"lineno": i + 1, "snippet": "\n".join(lines[start:end])}
                    )
                    if len(matches) >= 3:
                        break
            if matches:
                results.append({"meta": _parse_note(path), "matches": matches})
    return render_template(
        "search.html", query=query, results=results, sections=SECTIONS
    )


# ---------------------------------------------------------------------------
# Routes — AI assistant
# ---------------------------------------------------------------------------


@app.route("/assistant")
def assistant():
    providers = ai_providers.get_available_providers()
    return render_template(
        "assistant.html",
        sections=SECTIONS,
        available_providers=providers,
        provider_labels=ai_providers.PROVIDER_LABELS,
    )


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """AI assistant endpoint used by the assistant page."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    if "message" not in data:
        return jsonify({"error": "Missing message field"}), 400

    user_message = data["message"].strip()
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    if not ai_providers.get_available_providers():
        return jsonify(
            {
                "answer": (
                    "No AI provider is configured. "
                    "Add your GEMINI_API_KEY (or PERPLEXITY_API_KEY) "
                    "to tools/.env to enable AI responses."
                )
            }
        ), 200

    context = data.get("context", "general")
    provider = data.get("provider") or None

    system_prompt = ai_providers.REGISTRAR_SYSTEM_PROMPT
    if context and context != "general":
        section_title = SECTIONS.get(context, {}).get("title", context)
        system_prompt += f" The current context is: {section_title}."

    try:
        answer = ai_providers.ask(
            user_message, system_prompt=system_prompt, provider=provider
        )
        return jsonify({"answer": answer})
    except ai_providers.ProviderError as exc:
        return jsonify({"error": str(exc)}), exc.status_code
    except Exception:
        app.logger.exception("Unexpected error in /api/ask")
        return jsonify({"error": "An internal error occurred. Please try again."}), 500


# ---------------------------------------------------------------------------
# Routes — Email templates
# ---------------------------------------------------------------------------


@app.route("/email-templates")
def email_templates():
    """Display all email templates with mailto: send buttons."""
    templates = _parse_email_templates()
    # Group by section for display
    grouped = {}
    for tpl in templates:
        section = tpl["section"]
        if section not in grouped:
            grouped[section] = []
        grouped[section].append(tpl)
    
    return render_template(
        "email-templates.html",
        sections=SECTIONS,
        templates_by_section=grouped,
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = config.PORT
    debug = config.DEBUG or os.environ.get("FLASK_DEBUG", "0") == "1"
    url = f"http://localhost:{port}"
    print(f"\n📋 Work Notes — starting on {url}\n")
    # Open the browser automatically unless the Werkzeug reloader's child process
    # would do it a second time (only the parent/initial process should open it).
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(_BROWSER_OPEN_DELAY, lambda: webbrowser.open(url)).start()
    app.run(debug=debug, host="0.0.0.0", port=port)
