"""
tests/test_helpers.py — Unit tests for tools/_helpers.py utility functions.
"""

import sys
from pathlib import Path

# Ensure tools/ is importable without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from _helpers import (  # noqa: E402
    REPO_ROOT,
    _asset_meta,
    _parse_note,
    _read_pdf_text,
    _relative,
    pending_inbox_files,
)


# ---------------------------------------------------------------------------
# _relative
# ---------------------------------------------------------------------------

class TestRelative:
    def test_path_inside_repo(self, tmp_path, monkeypatch):
        """A path under REPO_ROOT returns a relative string."""
        fake_root = tmp_path / "repo"
        fake_root.mkdir()
        monkeypatch.setattr("_helpers.REPO_ROOT", fake_root)

        import _helpers
        monkeypatch.setattr(_helpers, "REPO_ROOT", fake_root)

        target = fake_root / "daily-logs" / "2026-03.md"
        result = _helpers._relative(target)
        assert result == str(Path("daily-logs") / "2026-03.md")

    def test_path_outside_repo_returns_absolute(self, tmp_path):
        """A path outside REPO_ROOT falls back to the absolute path."""
        outside = tmp_path / "outside.md"
        result = _relative(outside)
        assert result == str(outside)

    def test_repo_root_itself(self):
        """REPO_ROOT relative to itself is '.'"""
        result = _relative(REPO_ROOT)
        assert result == "."


# ---------------------------------------------------------------------------
# _parse_note
# ---------------------------------------------------------------------------

class TestParseNote:
    def _write(self, tmp_path, name, content):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_title_from_h1(self, tmp_path):
        p = self._write(tmp_path, "2026-03-14-standup.md", "# My Standup Note\n\nBody text.")
        meta = _parse_note(p)
        assert meta["title"] == "My Standup Note"

    def test_title_fallback_to_stem(self, tmp_path):
        p = self._write(tmp_path, "my-note-file.md", "No heading here.")
        meta = _parse_note(p)
        assert meta["title"] == "My Note File"

    def test_title_strips_emoji(self, tmp_path):
        p = self._write(tmp_path, "note.md", "# 🎓 Graduation Plan\n")
        meta = _parse_note(p)
        assert meta["title"] == "Graduation Plan"

    def test_word_count_positive(self, tmp_path):
        p = self._write(tmp_path, "words.md", "# Title\n\nHello world, this is a test.")
        meta = _parse_note(p)
        assert meta["words"] > 0

    def test_open_and_done_items(self, tmp_path):
        content = (
            "# Tasks\n"
            "- [ ] Open item one\n"
            "- [ ] Open item two\n"
            "- [x] Done item\n"
        )
        p = self._write(tmp_path, "tasks.md", content)
        meta = _parse_note(p)
        assert len(meta["open_items"]) == 2
        assert len(meta["done_items"]) == 1

    def test_dates_in_text(self, tmp_path):
        content = "Meeting on 2026-03-14 and follow-up 2026-04-01.\n"
        p = self._write(tmp_path, "dates.md", content)
        meta = _parse_note(p)
        assert "2026-03-14" in meta["dates_in_text"]
        assert "2026-04-01" in meta["dates_in_text"]

    def test_headings_extracted(self, tmp_path):
        content = "# H1\n## H2\n### H3\n"
        p = self._write(tmp_path, "heads.md", content)
        meta = _parse_note(p)
        levels = [level for level, _ in meta["headings"]]
        assert levels == [1, 2, 3]

    def test_folder_root_note(self, tmp_path, monkeypatch):
        import _helpers
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        p = tmp_path / "readme.md"
        p.write_text("# Root", encoding="utf-8")
        meta = _helpers._parse_note(p)
        assert meta["folder"] == "(root)"

    def test_folder_subdirectory(self, tmp_path, monkeypatch):
        import _helpers
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        sub = tmp_path / "graduation"
        sub.mkdir()
        p = sub / "checklist.md"
        p.write_text("# Checklist", encoding="utf-8")
        meta = _helpers._parse_note(p)
        assert meta["folder"] == "graduation"


# ---------------------------------------------------------------------------
# _asset_meta
# ---------------------------------------------------------------------------

class TestAssetMeta:
    def _make(self, tmp_path, name, content=b"data"):
        p = tmp_path / name
        p.write_bytes(content)
        return p

    def test_image_kind(self, tmp_path):
        p = self._make(tmp_path, "photo.png")
        meta = _asset_meta(p)
        assert meta["kind"] == "image"

    def test_pdf_kind(self, tmp_path):
        p = self._make(tmp_path, "form.pdf")
        meta = _asset_meta(p)
        assert meta["kind"] == "document"

    def test_spreadsheet_kind(self, tmp_path):
        p = self._make(tmp_path, "data.xlsx")
        meta = _asset_meta(p)
        assert meta["kind"] == "spreadsheet"

    def test_text_kind(self, tmp_path):
        p = self._make(tmp_path, "notes.txt")
        meta = _asset_meta(p)
        assert meta["kind"] == "text"

    def test_size_display_bytes(self, tmp_path):
        p = self._make(tmp_path, "tiny.bin", b"x" * 500)
        meta = _asset_meta(p)
        assert meta["size_display"].endswith(" B")

    def test_size_display_kb(self, tmp_path):
        p = self._make(tmp_path, "medium.bin", b"x" * 2048)
        meta = _asset_meta(p)
        assert meta["size_display"].endswith(" KB")

    def test_size_display_mb(self, tmp_path):
        p = self._make(tmp_path, "large.bin", b"x" * (2 * 1024 * 1024))
        meta = _asset_meta(p)
        assert meta["size_display"].endswith(" MB")

    def test_subfolder_root(self, tmp_path, monkeypatch):
        import _helpers
        fake_assets = tmp_path / "assets"
        fake_assets.mkdir()
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        p = fake_assets / "file.png"
        p.write_bytes(b"img")
        meta = _helpers._asset_meta(p)
        assert meta["subfolder"] == "(root)"

    def test_subfolder_named(self, tmp_path, monkeypatch):
        import _helpers
        fake_assets = tmp_path / "assets"
        sub = fake_assets / "images"
        sub.mkdir(parents=True)
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        p = sub / "photo.jpg"
        p.write_bytes(b"img")
        meta = _helpers._asset_meta(p)
        assert meta["subfolder"] == "images"


# ---------------------------------------------------------------------------
# pending_inbox_files
# ---------------------------------------------------------------------------

class TestPendingInboxFiles:
    def test_returns_empty_when_no_inbox(self, tmp_path, monkeypatch):
        import _helpers
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        assert _helpers.pending_inbox_files() == []

    def test_returns_md_and_txt_only(self, tmp_path, monkeypatch):
        import _helpers
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        (inbox / "note.md").write_text("# Note")
        (inbox / "draft.txt").write_text("draft")
        (inbox / "image.png").write_bytes(b"img")
        (inbox / ".hidden").write_text("hidden")
        (inbox / "README.md").write_text("# Readme")
        files = _helpers.pending_inbox_files()
        names = {f.name for f in files}
        assert names == {"note.md", "draft.txt"}

    def test_returns_pdf_files(self, tmp_path, monkeypatch):
        import _helpers
        monkeypatch.setattr(_helpers, "REPO_ROOT", tmp_path)
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        (inbox / "form.pdf").write_bytes(b"%PDF-1.4 fake")
        (inbox / "image.png").write_bytes(b"img")
        files = _helpers.pending_inbox_files()
        names = {f.name for f in files}
        assert "form.pdf" in names
        assert "image.png" not in names


# ---------------------------------------------------------------------------
# _read_pdf_text
# ---------------------------------------------------------------------------

class TestReadPdfText:
    def test_returns_string_for_valid_pdf(self, tmp_path):
        """A real single-page PDF should return extracted text (may be empty for minimal PDFs)."""
        pytest = __import__("pytest")
        pypdf = pytest.importorskip("pypdf")
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf_path = tmp_path / "blank.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        result = _read_pdf_text(pdf_path)
        assert isinstance(result, str)

    def test_returns_empty_string_for_garbage_file(self, tmp_path):
        """A non-PDF binary file should return an empty string (not raise)."""
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf at all")
        result = _read_pdf_text(bad)
        assert result == ""
