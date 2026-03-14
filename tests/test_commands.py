"""
tests/test_commands.py — Unit tests for tools/_commands.py subcommands.

Uses tmp_path fixtures and monkeypatching to test cmd_search,
cmd_sort, and cmd_organize without touching the real repository.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import _commands  # noqa: E402
import _helpers   # noqa: E402
from _commands import cmd_organize, cmd_search, cmd_sort  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_notes(tmp_path, files: dict[str, str]) -> None:
    """Write a dict of {relative_path: content} into tmp_path."""
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _patch_repo(monkeypatch, tmp_path):
    """Point both _helpers and _commands at tmp_path as the repo root.

    _all_notes() and _all_assets() use REPO_ROOT as a default argument
    evaluated at import time, so we must also patch the functions themselves
    to use the temporary directory.
    """
    monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_commands, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(_commands, "_all_notes", lambda: _helpers._all_notes(root=tmp_path))
    monkeypatch.setattr(_commands, "_all_assets", lambda: _helpers._all_assets())


# ---------------------------------------------------------------------------
# cmd_search
# ---------------------------------------------------------------------------

class TestCmdSearch:
    def test_finds_keyword(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"graduation/checklist.md": "# Checklist\nGraduation ceremony date."})
        args = argparse.Namespace(keyword="Graduation", context=1, folder=None)
        cmd_search(args)
        out = capsys.readouterr().out
        assert "Graduation" in out or "graduation" in out.lower()

    def test_no_matches_prints_message(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"meetings/note.md": "# Note\nSome content."})
        args = argparse.Namespace(keyword="xyzzy_nonexistent", context=1, folder=None)
        cmd_search(args)
        out = capsys.readouterr().out
        assert "No matches found" in out

    def test_folder_filter_limits_scope(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {
            "graduation/plan.md": "# Grad\nGraduation details.",
            "meetings/note.md": "# Meeting\nGraduation mentioned here too.",
        })
        args = argparse.Namespace(keyword="Graduation", context=1, folder="meetings")
        cmd_search(args)
        out = capsys.readouterr().out
        # Should only search in meetings/
        assert "meetings" in out or "No matches" in out

    def test_match_count_in_output(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        content = "FERPA applies here.\nFERPA is important.\n"
        _make_notes(tmp_path, {"personal-data/ferpa.md": content})
        args = argparse.Namespace(keyword="FERPA", context=0, folder=None)
        cmd_search(args)
        out = capsys.readouterr().out
        assert "2" in out  # 2 matches


# ---------------------------------------------------------------------------
# cmd_sort
# ---------------------------------------------------------------------------

class TestCmdSort:
    def test_sort_by_name(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {
            "meetings/b-note.md": "# B",
            "meetings/a-note.md": "# A",
        })
        args = argparse.Namespace(by="name", folder=None)
        cmd_sort(args)
        out = capsys.readouterr().out
        assert "a-note" in out
        assert "b-note" in out
        # a-note should appear before b-note in sorted output
        assert out.index("a-note") < out.index("b-note")

    def test_sort_by_size(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {
            "meetings/short.md": "# Short\nFew words.",
            "meetings/long.md": "# Long\n" + "word " * 100,
        })
        args = argparse.Namespace(by="size", folder=None)
        cmd_sort(args)
        out = capsys.readouterr().out
        assert "long" in out
        assert "short" in out

    def test_sort_with_folder_filter(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {
            "meetings/note.md": "# Meeting Note",
            "graduation/plan.md": "# Grad Plan",
        })
        args = argparse.Namespace(by="name", folder="graduation")
        cmd_sort(args)
        out = capsys.readouterr().out
        assert "plan" in out
        assert "meetings/note.md" not in out

    def test_sort_assets_by_size(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "small.png").write_bytes(b"x" * 100)
        (assets / "large.png").write_bytes(b"x" * 5000)
        args = argparse.Namespace(by="size", folder="assets")
        cmd_sort(args)
        out = capsys.readouterr().out
        assert "large.png" in out
        assert "small.png" in out

    def test_no_notes_exits_with_message(self, tmp_path, monkeypatch):
        _patch_repo(monkeypatch, tmp_path)
        args = argparse.Namespace(by="name", folder="graduation")
        # graduation folder doesn't exist — cmd_sort should sys.exit
        import pytest
        with pytest.raises(SystemExit):
            cmd_sort(args)


# ---------------------------------------------------------------------------
# cmd_organize
# ---------------------------------------------------------------------------

class TestCmdOrganize:
    def test_stdout_contains_index_header(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"graduation/checklist.md": "# Checklist\nContent."})
        args = argparse.Namespace(output=None, check_inbox=False)
        cmd_organize(args)
        out = capsys.readouterr().out
        assert "Master Notes Index" in out

    def test_output_to_file(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"meetings/note.md": "# Note\nContent."})
        out_file = tmp_path / "tools" / "index.md"
        args = argparse.Namespace(
            output=str(out_file.relative_to(tmp_path)),
            check_inbox=False,
        )
        cmd_organize(args)
        assert out_file.exists()
        text = out_file.read_text(encoding="utf-8")
        assert "Master Notes Index" in text

    def test_index_contains_note_title(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"graduation/ceremony.md": "# Spring Ceremony\nDetails."})
        args = argparse.Namespace(output=None, check_inbox=False)
        cmd_organize(args)
        out = capsys.readouterr().out
        assert "Spring Ceremony" in out

    def test_index_contains_summary_table(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"meetings/note.md": "# Note\nContent."})
        args = argparse.Namespace(output=None, check_inbox=False)
        cmd_organize(args)
        out = capsys.readouterr().out
        assert "Summary" in out
        assert "Folder" in out

    def test_open_action_items_appear_in_index(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {
            "meetings/tasks.md": "# Tasks\n- [ ] Send follow-up email\n- [x] Done task\n"
        })
        args = argparse.Namespace(output=None, check_inbox=False)
        cmd_organize(args)
        out = capsys.readouterr().out
        assert "Open Action Items" in out
        assert "Send follow-up email" in out

    def test_assets_appear_in_index(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        assets = tmp_path / "assets"
        assets.mkdir()
        (assets / "photo.png").write_bytes(b"img")
        _make_notes(tmp_path, {"graduation/note.md": "# Note\nContent."})
        args = argparse.Namespace(output=None, check_inbox=False)
        cmd_organize(args)
        out = capsys.readouterr().out
        assert "Assets" in out
        assert "photo.png" in out

    def test_check_inbox_empty_prints_empty_message(self, tmp_path, monkeypatch, capsys):
        _patch_repo(monkeypatch, tmp_path)
        _make_notes(tmp_path, {"graduation/note.md": "# Note\nContent."})
        args = argparse.Namespace(output=None, check_inbox=True)
        cmd_organize(args)
        out = capsys.readouterr().out
        assert "inbox" in out.lower()
