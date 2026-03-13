#!/usr/bin/env python3
"""
notes_helper.py — Analyze, sort, and organize your work notes.

Usage:
    python3 tools/notes_helper.py analyze [FILE]
    python3 tools/notes_helper.py sort [--by date|size|name] [--folder FOLDER]
    python3 tools/notes_helper.py organize [--output FILE]
    python3 tools/notes_helper.py search KEYWORD [--folder FOLDER]
    python3 tools/notes_helper.py agent
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
IGNORED_DIRS = {".git", "tools", "assets"}


def _all_notes(root: Path = REPO_ROOT) -> list[Path]:
    """Return all Markdown files in the repository, sorted by path."""
    notes = []
    for path in root.rglob("*.md"):
        if not any(part in IGNORED_DIRS for part in path.parts):
            notes.append(path)
    return sorted(notes)


def _relative(path: Path) -> str:
    """Return path relative to the repo root."""
    return str(path.relative_to(REPO_ROOT))


def _parse_note(path: Path) -> dict:
    """Extract metadata from a single Markdown file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    # Title: first H1 heading or filename stem
    title = path.stem.replace("-", " ").replace("_", " ").title()
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip().lstrip("🎓📄🏠🔒📅📓📁📣").strip()
            break

    # All headings
    headings = [
        (len(m.group(1)), line.lstrip("# ").strip())
        for line in lines
        if (m := re.match(r"^(#{1,6})\s", line))
    ]

    # Word count (non-empty lines, strip markdown syntax)
    words = len(re.findall(r"\b\w+\b", re.sub(r"[#*`_>\[\]()!|]", " ", text)))

    # Action items — Markdown task list items  (- [ ] and - [x])
    open_items = [
        line.strip()
        for line in lines
        if re.match(r"^\s*-\s+\[ \]", line)
    ]
    done_items = [
        line.strip()
        for line in lines
        if re.match(r"^\s*-\s+\[x\]", line, re.IGNORECASE)
    ]

    # Dates mentioned in the file (YYYY-MM-DD)
    dates_in_text = sorted(set(re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)))

    # File dates
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime)

    return {
        "path": path,
        "relative": _relative(path),
        "title": title,
        "headings": headings,
        "words": words,
        "open_items": open_items,
        "done_items": done_items,
        "dates_in_text": dates_in_text,
        "modified": modified,
        "folder": path.parent.relative_to(REPO_ROOT).parts[0]
        if path.parent != REPO_ROOT
        else "(root)",
    }


# ---------------------------------------------------------------------------
# Subcommand: analyze
# ---------------------------------------------------------------------------


def cmd_analyze(args: argparse.Namespace) -> None:
    """Print a detailed analysis of one note or all notes."""
    if args.file:
        target = Path(args.file)
        if not target.is_absolute():
            target = REPO_ROOT / target
        if not target.exists():
            sys.exit(f"File not found: {args.file}")
        notes = [target]
    else:
        notes = _all_notes()

    for path in notes:
        meta = _parse_note(path)
        print(f"\n{'='*60}")
        print(f"  📄 {meta['relative']}")
        print(f"{'='*60}")
        print(f"  Title    : {meta['title']}")
        print(f"  Folder   : {meta['folder']}")
        print(f"  Words    : {meta['words']}")
        print(f"  Modified : {meta['modified'].strftime('%Y-%m-%d %H:%M')}")
        if meta["headings"]:
            print(f"  Headings :")
            for level, heading in meta["headings"]:
                print(f"    {'  ' * (level - 1)}{'#' * level} {heading}")
        if meta["open_items"]:
            print(f"  Open action items ({len(meta['open_items'])}):")
            for item in meta["open_items"][:5]:
                print(f"    {item}")
            if len(meta["open_items"]) > 5:
                print(f"    … and {len(meta['open_items']) - 5} more")
        if meta["done_items"]:
            print(
                f"  Completed items : {len(meta['done_items'])}"
            )
        if meta["dates_in_text"]:
            print(f"  Dates found  : {', '.join(meta['dates_in_text'])}")
    print()


# ---------------------------------------------------------------------------
# Subcommand: sort
# ---------------------------------------------------------------------------


def cmd_sort(args: argparse.Namespace) -> None:
    """List notes sorted by the chosen criterion."""
    notes_meta = [_parse_note(p) for p in _all_notes()]

    if args.folder:
        notes_meta = [m for m in notes_meta if m["folder"] == args.folder]
        if not notes_meta:
            sys.exit(
                f"No notes found in folder '{args.folder}'. "
                f"Available folders: {sorted({m['folder'] for m in [_parse_note(p) for p in _all_notes()]})}"
            )

    by = args.by
    if by == "date":
        notes_meta.sort(key=lambda m: m["modified"], reverse=True)
        col_header = "Modified"
        col_fn = lambda m: m["modified"].strftime("%Y-%m-%d %H:%M")
    elif by == "size":
        notes_meta.sort(key=lambda m: m["words"], reverse=True)
        col_header = "Words"
        col_fn = lambda m: str(m["words"])
    else:  # name
        notes_meta.sort(key=lambda m: m["relative"])
        col_header = "Folder"
        col_fn = lambda m: m["folder"]

    col_w = max(len(col_fn(m)) for m in notes_meta) if notes_meta else 10
    path_w = max(len(m["relative"]) for m in notes_meta) if notes_meta else 20

    header = f"{'Path':<{path_w}}  {col_header}"
    print(f"\n{header}")
    print("-" * (len(header) + 4))
    for m in notes_meta:
        print(f"{m['relative']:<{path_w}}  {col_fn(m)}")
    print(f"\n{len(notes_meta)} note(s) found.\n")


# ---------------------------------------------------------------------------
# Subcommand: organize
# ---------------------------------------------------------------------------


def cmd_organize(args: argparse.Namespace) -> None:
    """Generate (or refresh) a master index of all notes."""
    notes_meta = [_parse_note(p) for p in _all_notes()]

    # Group by top-level folder
    folders: dict[str, list[dict]] = {}
    for m in notes_meta:
        folders.setdefault(m["folder"], []).append(m)

    lines = [
        "# 📋 Master Notes Index",
        "",
        "> Auto-generated by `tools/notes_helper.py organize`  ",
        f"> Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Summary table
    lines += [
        "## Summary",
        "",
        f"| Folder | Notes | Total Words |",
        f"|--------|-------|-------------|",
    ]
    for folder in sorted(folders):
        folder_notes = folders[folder]
        total_words = sum(m["words"] for m in folder_notes)
        lines.append(
            f"| {folder} | {len(folder_notes)} | {total_words:,} |"
        )
    lines += [""]

    # Per-folder detail
    lines.append("## Notes by Folder")
    lines.append("")
    for folder in sorted(folders):
        lines.append(f"### {folder}")
        lines.append("")
        folder_notes = sorted(folders[folder], key=lambda m: m["relative"])
        for m in folder_notes:
            rel = m["relative"]
            # Build a relative link from the index file location
            link = f"../{rel}" if args.output else rel
            open_count = len(m["open_items"])
            badge = f" ✅ {len(m['done_items'])} done" if m["done_items"] else ""
            badge += f" 🔲 {open_count} open" if open_count else ""
            lines.append(
                f"- [{m['title']}]({link}) — {m['words']} words{badge}"
            )
        lines.append("")

    # Open action items summary
    all_open = [
        (m["relative"], item)
        for m in notes_meta
        for item in m["open_items"]
    ]
    if all_open:
        lines += [
            "## Open Action Items",
            "",
        ]
        current_file = None
        for rel, item in sorted(all_open, key=lambda x: x[0]):
            if rel != current_file:
                lines.append(f"**{rel}**")
                current_file = rel
            lines.append(f"  {item}")
        lines.append("")

    content = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Master index written to: {_relative(out_path)}")
    else:
        print(content)


# ---------------------------------------------------------------------------
# Subcommand: search
# ---------------------------------------------------------------------------


def cmd_search(args: argparse.Namespace) -> None:
    """Search all notes for a keyword and print matching lines with context."""
    keyword = args.keyword
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    context = args.context

    notes = _all_notes()
    if args.folder:
        notes = [p for p in notes if p.parts[len(REPO_ROOT.parts)] == args.folder]

    total_matches = 0
    for path in notes:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        matches = [
            (i + 1, line)
            for i, line in enumerate(lines)
            if pattern.search(line)
        ]
        if not matches:
            continue

        print(f"\n{'─'*60}")
        print(f"  📄 {_relative(path)}  ({len(matches)} match(es))")
        print(f"{'─'*60}")
        shown_lines: set[int] = set()
        for lineno, _ in matches:
            start = max(0, lineno - 1 - context)
            end = min(len(lines), lineno + context)
            for i in range(start, end):
                if i not in shown_lines:
                    marker = ">>>" if (i + 1) == lineno else "   "
                    snippet = lines[i]
                    # Highlight the keyword
                    snippet = pattern.sub(
                        lambda m: f"\033[1;33m{m.group()}\033[0m", snippet
                    )
                    print(f"  {marker} {i+1:4d} | {snippet}")
                    shown_lines.add(i)
        total_matches += len(matches)

    if total_matches == 0:
        print(f'\nNo matches found for "{keyword}".\n')
    else:
        print(f'\n{total_matches} match(es) for "{keyword}" across {len(notes)} file(s).\n')


# ---------------------------------------------------------------------------
# Subcommand: agent (interactive mode)
# ---------------------------------------------------------------------------

_AGENT_HELP = """\
Notes Helper Agent — type a request in plain language and I'll do it for you.

Examples:
  analyze all notes
  analyze daily-logs/2026-03/2026-03-13.md
  sort by date
  sort by size in graduation
  organize
  organize to tools/index.md
  search FERPA
  search deadline in graduation
  help
  quit
"""

_INTENT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\banalyze\b", re.I), "analyze"),
    (re.compile(r"\bsort\b|\blist\b|\border\b", re.I), "sort"),
    (re.compile(r"\borganize\b|\bindex\b|\bmaster\b", re.I), "organize"),
    (re.compile(r"\bsearch\b|\bfind\b|\blook\b|\bgrep\b", re.I), "search"),
]


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
        ns.func = cmd_sort
        ns.by = by
        ns.folder = folder_m.group(1) if folder_m else None
        return ns

    if intent == "organize":
        output_m = re.search(r"\b(?:to|into|output|file)\s+(\S+)", text, re.I)
        ns.func = cmd_organize
        ns.output = output_m.group(1) if output_m else None
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notes_helper.py",
        description="Work Notes Helper — analyze, sort, and organize your notes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tools/notes_helper.py analyze
  python3 tools/notes_helper.py analyze daily-logs/2026-03/2026-03-13.md
  python3 tools/notes_helper.py sort --by date
  python3 tools/notes_helper.py sort --by size --folder graduation
  python3 tools/notes_helper.py organize
  python3 tools/notes_helper.py organize --output tools/index.md
  python3 tools/notes_helper.py search "action item"
  python3 tools/notes_helper.py search FERPA --context 3
        """,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # analyze
    p_analyze = sub.add_parser(
        "analyze", help="Analyze note(s): word count, headings, action items, dates"
    )
    p_analyze.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="Path to a single note (relative to repo root). Analyzes all notes if omitted.",
    )
    p_analyze.set_defaults(func=cmd_analyze)

    # sort
    p_sort = sub.add_parser(
        "sort", help="List notes sorted by date, size, or name"
    )
    p_sort.add_argument(
        "--by",
        choices=["date", "size", "name"],
        default="name",
        help="Sort criterion (default: name)",
    )
    p_sort.add_argument(
        "--folder",
        metavar="FOLDER",
        help="Limit to a top-level folder (e.g. graduation, meetings)",
    )
    p_sort.set_defaults(func=cmd_sort)

    # organize
    p_org = sub.add_parser(
        "organize", help="Generate a master index of all notes"
    )
    p_org.add_argument(
        "--output",
        metavar="FILE",
        help="Write the index to this file (relative to repo root). Prints to stdout if omitted.",
    )
    p_org.set_defaults(func=cmd_organize)

    # search
    p_search = sub.add_parser(
        "search", help="Search notes for a keyword"
    )
    p_search.add_argument("keyword", help="Keyword or phrase to search for")
    p_search.add_argument(
        "--context",
        type=int,
        default=2,
        metavar="N",
        help="Number of context lines around each match (default: 2)",
    )
    p_search.add_argument(
        "--folder",
        metavar="FOLDER",
        help="Limit search to a top-level folder",
    )
    p_search.set_defaults(func=cmd_search)

    # agent
    p_agent = sub.add_parser(
        "agent",
        help="Interactive agent mode — type requests in plain language",
    )
    p_agent.set_defaults(func=cmd_agent)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
