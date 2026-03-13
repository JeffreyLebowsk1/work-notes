"""
_agent.py — Interactive agent mode for notes_helper.

Accepts plain-language requests and dispatches them to the
appropriate subcommand function.
"""

import argparse
import re

from _commands import cmd_analyze, cmd_organize, cmd_search, cmd_sort
from _importer import cmd_import, cmd_process_inbox


# ---------------------------------------------------------------------------
# Agent constants
# ---------------------------------------------------------------------------

_AGENT_HELP = """\
Notes Helper Agent — type a request in plain language and I'll do it for you.

Examples:
  process inbox
  process inbox dry-run
  process inbox organize
  import /path/to/note.md
  import /path/to/note.md to meetings
  import /path/to/note.md --dry-run
  analyze all notes
  analyze daily-logs/2026-03/2026-03-13.md
  sort by date
  sort by size in graduation
  sort assets by date
  sort assets by size
  organize
  organize to tools/index.md
  organize check-inbox
  organize check-inbox to tools/index.md
  search FERPA
  search deadline in graduation
  help
  quit
"""

_INTENT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bprocess.?inbox\b|\binbox\b", re.I), "process-inbox"),
    (re.compile(r"\bimport\b|\bupload\b|\bingest\b|\badd\s+file\b", re.I), "import"),
    (re.compile(r"\banalyze\b", re.I), "analyze"),
    (re.compile(r"\bsort\b|\blist\b|\border\b", re.I), "sort"),
    (re.compile(r"\borganize\b|\bindex\b|\bmaster\b", re.I), "organize"),
    (re.compile(r"\bsearch\b|\bfind\b|\blook\b|\bgrep\b", re.I), "search"),
]


# ---------------------------------------------------------------------------
# Natural-language parser
# ---------------------------------------------------------------------------


def _parse_agent_input(text: str) -> argparse.Namespace | None:
    """Turn a natural-language request into an argparse Namespace, or None if unrecognised."""
    text = text.strip()
    if not text:
        return None

    # Detect intent
    intent = None
    for pattern, name in _INTENT_PATTERNS:
        if pattern.search(text):
            intent = name
            break

    if intent is None:
        return None

    ns = argparse.Namespace()

    if intent == "process-inbox":
        ns.func = cmd_process_inbox
        ns.dry_run = bool(re.search(r"\bdry.?run\b", text, re.I))
        ns.force = bool(re.search(r"\bforce\b|\boverwrite\b", text, re.I))
        ns.organize = bool(re.search(r"\borganize\b|\bindex\b", text, re.I))
        return ns

    if intent == "import":
        # "import <file>" or "upload <file>"
        m = re.search(r"\b(?:import|upload|ingest|add\s+file)\b\s+(\S+)", text, re.I)
        file_arg = m.group(1).strip() if m else None
        if not file_arg:
            print("Please specify a file path, e.g.: import /path/to/note.md")
            return None
        dest_m = re.search(r"\b(?:to|into|dest(?:ination)?)\s+(\S+)", text, re.I)
        ns.func = cmd_import
        ns.file = file_arg
        ns.dest = dest_m.group(1) if dest_m else None
        ns.dry_run = bool(re.search(r"\bdry.?run\b", text, re.I))
        ns.force = bool(re.search(r"\bforce\b|\boverwrite\b", text, re.I))
        ns.organize = bool(re.search(r"\borganize\b|\bindex\b", text, re.I))
        return ns

    if intent == "analyze":
        # "analyze <file>" or "analyze all"
        m = re.search(r"\banalyze\b\s+(.+)", text, re.I)
        file_arg = m.group(1).strip() if m else None
        if file_arg and file_arg.lower() in ("all", "all notes", "everything"):
            file_arg = None
        ns.func = cmd_analyze
        ns.file = file_arg
        return ns

    if intent == "sort":
        by = "name"
        for word in ("date", "size", "name"):
            if re.search(rf"\b{word}\b", text, re.I):
                by = word
                break
        folder_m = re.search(r"\bin\s+(\S+)", text, re.I)
        if folder_m:
            folder = folder_m.group(1)
        elif re.search(r"\bassets\b", text, re.I):
            folder = "assets"
        else:
            folder = None
        ns.func = cmd_sort
        ns.by = by
        ns.folder = folder
        return ns

    if intent == "organize":
        output_m = re.search(r"\b(?:to|into|output|file)\s+(\S+)", text, re.I)
        ns.func = cmd_organize
        ns.output = output_m.group(1) if output_m else None
        ns.check_inbox = bool(re.search(r"\bcheck.?inbox\b", text, re.I))
        return ns

    if intent == "search":
        # Extract keyword: everything after the verb, strip trailing folder hint
        kw_m = re.search(r"\b(?:search|find|look\s+for|grep)\b\s+(.+)", text, re.I)
        if not kw_m:
            return None
        keyword_part = kw_m.group(1).strip()
        folder = None
        folder_m = re.search(r"\s+in\s+(\S+)\s*$", keyword_part, re.I)
        if folder_m:
            folder = folder_m.group(1)
            keyword_part = keyword_part[: folder_m.start()].strip()
        # Strip surrounding quotes if present
        keyword_part = keyword_part.strip('"\'')
        if not keyword_part:
            return None
        ns.func = cmd_search
        ns.keyword = keyword_part
        ns.folder = folder
        ns.context = 2
        return ns

    return None


# ---------------------------------------------------------------------------
# Subcommand: agent
# ---------------------------------------------------------------------------


def cmd_agent(_args: argparse.Namespace) -> None:
    """Start an interactive agent session."""
    print(_AGENT_HELP)
    while True:
        try:
            raw = input("notes> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        lower = raw.lower()
        if lower in ("quit", "exit", "bye", "q"):
            print("Goodbye!")
            break
        if lower in ("help", "?", "h"):
            print(_AGENT_HELP)
            continue

        ns = _parse_agent_input(raw)
        if ns is None:
            print(
                "Sorry, I didn't understand that. Try 'help' for examples, "
                "or use one of: analyze, sort, organize, search."
            )
            continue

        try:
            ns.func(ns)
        except SystemExit as exc:
            # cmd_* may call sys.exit() on errors — show the message gracefully
            if exc.code:
                print(f"Error: {exc.code}")
