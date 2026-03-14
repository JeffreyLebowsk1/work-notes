"""
app.py — Work Notes web GUI.

Run from the repo root:
    python3 tools/app.py

Or from the tools/ directory:
    python3 app.py

Then open http://localhost:420 in your browser.
"""

import mimetypes
import os
import re
import sys
import threading
import webbrowser
from pathlib import Path

import markdown as md
from flask import (
    Flask, Response, jsonify, redirect, render_template,
    request, send_from_directory, url_for,
)
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
    return Markup(html)


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
_ASSET_SUBFOLDERS: frozenset[str] = frozenset(
    {"images", "documents", "spreadsheets", "screenshots"}
)

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
                           subfolders=sorted(_ASSET_SUBFOLDERS))


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


# ---------------------------------------------------------------------------
# Routes — search
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
