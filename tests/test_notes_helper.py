"""
tests/test_notes_helper.py — Unit tests for the CLI parser in notes_helper.py.

Verifies that all subcommands and their arguments are correctly registered
so that the argument parser never silently drops a command.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import pytest  # noqa: E402
from notes_helper import build_parser  # noqa: E402


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------

class TestBuildParser:
    def setup_method(self):
        self.parser = build_parser()

    def _parse(self, *args):
        return self.parser.parse_args(list(args))

    # ── analyze ──────────────────────────────────────────────────────────────

    def test_analyze_no_file(self):
        args = self._parse("analyze")
        assert args.command == "analyze"
        assert args.file is None

    def test_analyze_with_file(self):
        args = self._parse("analyze", "daily-logs/2026-03-14.md")
        assert args.file == "daily-logs/2026-03-14.md"

    # ── sort ─────────────────────────────────────────────────────────────────

    def test_sort_defaults(self):
        args = self._parse("sort")
        assert args.command == "sort"
        assert args.by == "name"
        assert args.folder is None

    def test_sort_by_date(self):
        args = self._parse("sort", "--by", "date")
        assert args.by == "date"

    def test_sort_by_size(self):
        args = self._parse("sort", "--by", "size")
        assert args.by == "size"

    def test_sort_with_folder(self):
        args = self._parse("sort", "--folder", "graduation")
        assert args.folder == "graduation"

    def test_sort_invalid_by_raises(self):
        with pytest.raises(SystemExit):
            self._parse("sort", "--by", "invalid")

    # ── organize ─────────────────────────────────────────────────────────────

    def test_organize_no_output(self):
        args = self._parse("organize")
        assert args.command == "organize"
        assert args.output is None
        assert args.check_inbox is False

    def test_organize_with_output(self):
        args = self._parse("organize", "--output", "tools/index.md")
        assert args.output == "tools/index.md"

    def test_organize_check_inbox(self):
        args = self._parse("organize", "--check-inbox")
        assert args.check_inbox is True

    # ── search ───────────────────────────────────────────────────────────────

    def test_search_keyword_required(self):
        with pytest.raises(SystemExit):
            self._parse("search")

    def test_search_with_keyword(self):
        args = self._parse("search", "FERPA")
        assert args.keyword == "FERPA"
        assert args.context == 2
        assert args.folder is None

    def test_search_custom_context(self):
        args = self._parse("search", "FERPA", "--context", "5")
        assert args.context == 5

    def test_search_with_folder(self):
        args = self._parse("search", "graduation", "--folder", "graduation")
        assert args.folder == "graduation"

    # ── import ───────────────────────────────────────────────────────────────

    def test_import_file_required(self):
        with pytest.raises(SystemExit):
            self._parse("import")

    def test_import_with_file(self):
        args = self._parse("import", "/tmp/note.md")
        assert args.file == "/tmp/note.md"
        assert args.dry_run is False
        assert args.force is False
        assert args.organize is False
        assert args.dest is None

    def test_import_dry_run(self):
        args = self._parse("import", "/tmp/note.md", "--dry-run")
        assert args.dry_run is True

    def test_import_force(self):
        args = self._parse("import", "/tmp/note.md", "--force")
        assert args.force is True

    def test_import_dest(self):
        args = self._parse("import", "/tmp/note.md", "--dest", "meetings")
        assert args.dest == "meetings"

    def test_import_organize(self):
        args = self._parse("import", "/tmp/note.md", "--organize")
        assert args.organize is True

    # ── process-inbox ────────────────────────────────────────────────────────

    def test_process_inbox_defaults(self):
        args = self._parse("process-inbox")
        assert args.command == "process-inbox"
        assert args.dry_run is False
        assert args.force is False
        assert args.organize is False

    def test_process_inbox_dry_run(self):
        args = self._parse("process-inbox", "--dry-run")
        assert args.dry_run is True

    # ── agent ────────────────────────────────────────────────────────────────

    def test_agent_subcommand(self):
        args = self._parse("agent")
        assert args.command == "agent"

    # ── no subcommand ────────────────────────────────────────────────────────

    def test_no_subcommand_raises(self):
        with pytest.raises(SystemExit):
            self._parse()
