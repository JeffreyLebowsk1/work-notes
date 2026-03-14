"""
app.py — Work Notes web GUI.

Run from the repo root:
    python3 tools/app.py

Or from the tools/ directory:
    python3 app.py

Then open http://localhost:5000 in your browser.
"""

import os
import re
import sys
from pathlib import Path

import markdown as md
from flask import Flask, jsonify, render_template, request, url_for
from markupsafe import Markup

# Ensure tools/ is on sys.path so sibling modules resolve correctly.
_TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS_DIR))

import ai_providers  # noqa: E402
import config  # noqa: E402
from _helpers import REPO_ROOT, _all_notes, _parse_note, _relative  # noqa: E402

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.SECRET_KEY

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _notes_in_section(section_key: str) -> list[dict]:
    """Return parsed metadata for every note in a section folder, sorted by path."""
    section_dir = REPO_ROOT / section_key
    if not section_dir.is_dir():
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
    """Provide a cache-busted static asset URL helper for templates."""
    def static_asset_url(filename):
        static_path = os.path.join(app.static_folder, filename)
        if os.path.isfile(static_path):
            version = int(os.path.getmtime(static_path))
            return url_for("static", filename=filename, v=version)
        return url_for("static", filename=filename)
    return {"static_asset_url": static_asset_url}


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
                    "Add your GEMINI_API_KEY (or OPENAI_API_KEY / PERPLEXITY_API_KEY) "
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


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    port = config.PORT
    debug = config.DEBUG or os.environ.get("FLASK_DEBUG", "0") == "1"
    print(f"\n📋 Work Notes — starting on http://localhost:{port}\n")
    app.run(debug=debug, host="0.0.0.0", port=port)
