"""
tests/test_importer.py — Unit tests for tools/_importer.py.

Covers folder detection, filename suggestion, and destination-directory
resolution without touching the real repo on disk.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from _importer import (  # noqa: E402
    FOLDER_KEYWORDS,
    _detect_folder,
    _suggest_dest_dir,
    _suggest_filename,
)


# ---------------------------------------------------------------------------
# _detect_folder
# ---------------------------------------------------------------------------

class TestDetectFolder:
    def test_graduation_keyword(self):
        folder, conf = _detect_folder("note.md", "The graduation ceremony is scheduled.")
        assert folder == "graduation"
        assert conf > 0

    def test_meetings_keyword(self):
        folder, conf = _detect_folder("note.md", "Meeting agenda and action items for follow-up.")
        assert folder == "meetings"
        assert conf > 0

    def test_daily_logs_keyword(self):
        folder, conf = _detect_folder("note.md", "Today I completed the daily log.")
        assert folder == "daily-logs"
        assert conf > 0

    def test_transcripts_keyword(self):
        folder, conf = _detect_folder("note.md", "Requesting an official transcript evaluation.")
        assert folder == "transcripts"
        assert conf > 0

    def test_residency_keyword(self):
        folder, conf = _detect_folder("note.md", "Residency determination for in-state tuition.")
        assert folder == "residency-tuition"
        assert conf > 0

    def test_admissions_keyword(self):
        folder, conf = _detect_folder("note.md", "New student application for admissions enrollment.")
        assert folder == "admissions"
        assert conf > 0

    def test_ferpa_personal_data(self):
        folder, conf = _detect_folder("note.md", "FERPA privacy policy for student data handling.")
        assert folder == "personal-data"
        assert conf > 0

    def test_no_match_returns_root(self):
        folder, conf = _detect_folder("note.md", "zzz xyzzy quux blargh")
        assert folder == "(root)"
        assert conf == 0.0

    def test_filename_contributes_to_score(self):
        # Keyword in filename should also be scored
        folder, conf = _detect_folder("graduation-checklist.md", "Some generic text.")
        assert folder == "graduation"

    def test_confidence_between_zero_and_one(self):
        _, conf = _detect_folder("meeting.md", "Meeting agenda and action items.")
        assert 0.0 <= conf <= 1.0


# ---------------------------------------------------------------------------
# _suggest_filename
# ---------------------------------------------------------------------------

class TestSuggestFilename:
    def _path(self, name):
        return Path("/tmp") / name

    def test_daily_log_with_date_in_stem(self):
        result = _suggest_filename(self._path("2026-03-14-log.md"), "daily-logs", "")
        assert result == "2026-03-14.md"

    def test_daily_log_without_date_uses_stem(self):
        result = _suggest_filename(self._path("my daily notes.md"), "daily-logs", "")
        assert result == "my-daily-notes.md"

    def test_meeting_with_date_and_topic(self):
        result = _suggest_filename(self._path("2026-03-14-standup.md"), "meetings", "")
        assert result.startswith("2026-03-14-")
        assert result.endswith(".md")
        assert "standup" in result

    def test_meeting_date_from_content(self):
        result = _suggest_filename(self._path("standup.md"), "meetings", "Date: 2026-03-15")
        assert result.startswith("2026-03-15-")

    def test_other_folder_kebab_case(self):
        result = _suggest_filename(self._path("My Cool Note.md"), "graduation", "")
        assert result == "my-cool-note.md"

    def test_preserves_non_md_extension(self):
        result = _suggest_filename(self._path("report.txt"), "updates", "")
        assert result.endswith(".txt")

    def test_no_extension_defaults_to_md(self):
        result = _suggest_filename(self._path("report"), "updates", "")
        assert result.endswith(".md")

    def test_daily_log_date_from_content(self):
        result = _suggest_filename(self._path("log.md"), "daily-logs", "Log for 2026-04-01")
        assert result == "2026-04-01.md"


# ---------------------------------------------------------------------------
# _suggest_dest_dir
# ---------------------------------------------------------------------------

class TestSuggestDestDir:
    def test_daily_log_has_year_month_subdir(self, monkeypatch):
        import _importer
        fake_root = Path("/fake/repo")
        monkeypatch.setattr(_importer, "REPO_ROOT", fake_root)
        result = _importer._suggest_dest_dir("daily-logs", "2026-03-14.md")
        assert result == fake_root / "daily-logs" / "2026-03"

    def test_daily_log_no_date_falls_back(self, monkeypatch):
        import _importer
        fake_root = Path("/fake/repo")
        monkeypatch.setattr(_importer, "REPO_ROOT", fake_root)
        result = _importer._suggest_dest_dir("daily-logs", "log.md")
        assert result == fake_root / "daily-logs"

    def test_meetings_goes_to_meetings_dir(self, monkeypatch):
        import _importer
        fake_root = Path("/fake/repo")
        monkeypatch.setattr(_importer, "REPO_ROOT", fake_root)
        result = _importer._suggest_dest_dir("meetings", "2026-03-14-standup.md")
        assert result == fake_root / "meetings"

    def test_root_folder_returns_repo_root(self, monkeypatch):
        import _importer
        fake_root = Path("/fake/repo")
        monkeypatch.setattr(_importer, "REPO_ROOT", fake_root)
        result = _importer._suggest_dest_dir("(root)", "note.md")
        assert result == fake_root

    def test_empty_folder_returns_repo_root(self, monkeypatch):
        import _importer
        fake_root = Path("/fake/repo")
        monkeypatch.setattr(_importer, "REPO_ROOT", fake_root)
        result = _importer._suggest_dest_dir("", "note.md")
        assert result == fake_root

    def test_generic_folder(self, monkeypatch):
        import _importer
        fake_root = Path("/fake/repo")
        monkeypatch.setattr(_importer, "REPO_ROOT", fake_root)
        result = _importer._suggest_dest_dir("graduation", "checklist.md")
        assert result == fake_root / "graduation"


# ---------------------------------------------------------------------------
# FOLDER_KEYWORDS integrity
# ---------------------------------------------------------------------------

class TestFolderKeywords:
    def test_all_expected_folders_present(self):
        expected = {
            "graduation", "meetings", "daily-logs", "transcripts",
            "residency-tuition", "admissions", "continuing-education",
            "personal-data", "updates",
        }
        assert expected.issubset(set(FOLDER_KEYWORDS.keys()))

    def test_every_folder_has_at_least_one_keyword(self):
        for folder, keywords in FOLDER_KEYWORDS.items():
            assert len(keywords) >= 1, f"{folder} has no keywords"
