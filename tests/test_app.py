"""
tests/test_app.py — Unit tests for tools/app.py helpers.

Tests focus on _safe_note_filename and the daily-log subdirectory routing
logic used by the /note/new route.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import app  # noqa: E402


# ---------------------------------------------------------------------------
# _safe_note_filename
# ---------------------------------------------------------------------------

class TestSafeNoteFilename:
    def test_valid_date_only(self):
        assert app._safe_note_filename("2026-03-14.md") == "2026-03-14.md"

    def test_valid_date_with_topic(self):
        assert app._safe_note_filename("2026-03-14-staff-meeting.md") == "2026-03-14-staff-meeting.md"

    def test_valid_simple(self):
        assert app._safe_note_filename("my-note.md") == "my-note.md"

    def test_lowercases_input(self):
        assert app._safe_note_filename("MyNote.md") == "mynote.md"

    def test_strips_whitespace(self):
        assert app._safe_note_filename("  note.md  ") == "note.md"

    def test_rejects_path_traversal(self):
        assert app._safe_note_filename("../secret.md") is None

    def test_rejects_no_md_extension(self):
        assert app._safe_note_filename("note.txt") is None

    def test_rejects_empty(self):
        assert app._safe_note_filename("") is None

    def test_rejects_uppercase_only(self):
        # After lowercasing, "NOTE.MD" becomes "note.md" which is valid
        assert app._safe_note_filename("NOTE.MD") == "note.md"


# ---------------------------------------------------------------------------
# Daily-log subdirectory routing (the regex used in note_new)
# ---------------------------------------------------------------------------

_DAILY_LOG_DATE_RE = re.compile(r"^(\d{4}-\d{2})-\d{2}")


class TestDailyLogSubdirRouting:
    """Verify that any YYYY-MM-DD[-…].md filename is routed into YYYY-MM/."""

    def _subdir(self, filename: str) -> str | None:
        """Return the YYYY-MM subfolder, or None if no date prefix found."""
        m = _DAILY_LOG_DATE_RE.match(filename)
        return m.group(1) if m else None

    def test_date_only_filename(self):
        assert self._subdir("2026-03-14.md") == "2026-03"

    def test_date_with_topic_suffix(self):
        assert self._subdir("2026-03-14-staff-meeting.md") == "2026-03"

    def test_date_with_long_topic(self):
        assert self._subdir("2026-03-14-graduation-coordinator-notes.md") == "2026-03"

    def test_no_date_returns_none(self):
        assert self._subdir("my-note.md") is None

    def test_partial_date_returns_none(self):
        # YYYY-MM.md has no day component — should not match
        assert self._subdir("2026-03.md") is None

    def test_different_month(self):
        assert self._subdir("2025-12-01.md") == "2025-12"

    def test_first_of_month(self):
        assert self._subdir("2026-01-01.md") == "2026-01"
