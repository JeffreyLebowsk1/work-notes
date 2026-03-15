#!/usr/bin/env python3
"""
notes_helper.py — Analyze, sort, and organize your work notes.

Usage:
    python3 tools/notes_helper.py analyze [FILE]
    python3 tools/notes_helper.py sort [--by date|size|name] [--folder FOLDER]
    python3 tools/notes_helper.py organize [--output FILE]
    python3 tools/notes_helper.py search KEYWORD [--folder FOLDER]
    python3 tools/notes_helper.py import FILE [--dest DIR] [--dry-run] [--force] [--organize]
    python3 tools/notes_helper.py agent
    python3 tools/notes_helper.py sync-calendar [--year YEAR] [--dry-run]
    python3 tools/notes_helper.py sync-directory [--dry-run] [--with-detail]
"""

import argparse
import sys
from pathlib import Path

# Ensure the tools/ directory is on sys.path so the sibling modules resolve
# whether the script is called as `python3 tools/notes_helper.py` or via a
# workflow runner that sets a different working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _agent import cmd_agent        # noqa: E402
from _commands import (             # noqa: E402
    cmd_analyze,
    cmd_organize,
    cmd_search,
    cmd_sort,
)
from _calendar_sync import cmd_sync_calendar  # noqa: E402
from _directory_sync import cmd_sync_directory  # noqa: E402
from _email_receiver import cmd_check_email  # noqa: E402
from _importer import (             # noqa: E402
    cmd_import,
    cmd_process_inbox,
)


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
  python3 tools/notes_helper.py sort --by size --folder assets
  python3 tools/notes_helper.py organize
  python3 tools/notes_helper.py organize --output tools/index.md
  python3 tools/notes_helper.py search "action item"
  python3 tools/notes_helper.py search FERPA --context 3
  python3 tools/notes_helper.py import /path/to/note.md
  python3 tools/notes_helper.py import /path/to/note.md --dest meetings --organize
  python3 tools/notes_helper.py import /path/to/note.md --dry-run
  python3 tools/notes_helper.py process-inbox --organize
  python3 tools/notes_helper.py process-inbox --dry-run
  python3 tools/notes_helper.py agent
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
    p_org.add_argument(
        "--check-inbox",
        action="store_true",
        default=False,
        help=(
            "Process any pending inbox/ files before generating the index. "
            "Equivalent to running process-inbox followed by organize."
        ),
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

    # import
    p_import = sub.add_parser(
        "import",
        help="Import a file: auto-detect its destination, rename, and copy it into the repo",
    )
    p_import.add_argument(
        "file",
        metavar="FILE",
        help="Path to the file to import (absolute or relative to current directory)",
    )
    p_import.add_argument(
        "--dest",
        metavar="DIR",
        help=(
            "Override the auto-detected destination. "
            "Can be a directory (e.g. meetings) or a full file path. "
            "Relative paths are resolved from the repo root."
        ),
    )
    p_import.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without copying any files",
    )
    p_import.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination file if it already exists",
    )
    p_import.add_argument(
        "--organize",
        action="store_true",
        help="Refresh tools/index.md after a successful import",
    )
    p_import.set_defaults(func=cmd_import)

    # process-inbox
    p_inbox = sub.add_parser(
        "process-inbox",
        help="Import all files from the inbox/ folder, then remove them from inbox; metadata logged to tools/import-log.csv",
    )
    p_inbox.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without copying or deleting any files",
    )
    p_inbox.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination files that already exist",
    )
    p_inbox.add_argument(
        "--organize",
        action="store_true",
        help="Refresh tools/index.md after all files are processed",
    )
    p_inbox.set_defaults(func=cmd_process_inbox)

    # agent
    p_agent = sub.add_parser(
        "agent",
        help="Interactive agent mode — type requests in plain language",
    )
    p_agent.set_defaults(func=cmd_agent)

    # sync-calendar
    p_sync = sub.add_parser(
        "sync-calendar",
        help="Sync academic-calendar.md from calendar.cccc.edu",
    )
    p_sync.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Academic year to sync (default: 2026)",
    )
    p_sync.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated markdown without writing to disk",
    )
    p_sync.add_argument(
        "--detail",
        action="store_true",
        help="Include tier-3 detail events (orientations, sub-sessions, payment deadlines)",
    )
    p_sync.add_argument(
        "--all",
        action="store_true",
        help="Include every academic event (tiers 1-4, no filtering)",
    )
    p_sync.set_defaults(func=cmd_sync_calendar)

    # sync-directory
    p_dir = sub.add_parser(
        "sync-directory",
        help="Sync faculty/staff and department directories from cccc.edu",
    )
    p_dir.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated markdown without writing to disk",
    )
    p_dir.add_argument(
        "--with-detail",
        action="store_true",
        help="Fetch detail pages for contact info (phone, email, campus)",
    )
    p_dir.set_defaults(func=cmd_sync_directory)

    # check-email
    p_email = sub.add_parser(
        "check-email",
        help="Check configured IMAP inbox and import unread emails as notes",
    )
    p_email.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without saving any files",
    )
    p_email.add_argument(
        "--limit",
        type=int,
        default=25,
        metavar="N",
        help="Maximum number of unread messages to fetch (default: 25)",
    )
    p_email.set_defaults(func=cmd_check_email)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
