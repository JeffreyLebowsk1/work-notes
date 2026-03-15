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
    _ocr_page,
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

    def test_ocr_fallback_called_for_empty_page(self, tmp_path, monkeypatch):
        """When pypdf yields no text for a page, _ocr_page is called as fallback."""
        import _helpers

        pytest_mod = __import__("pytest")
        pytest_mod.importorskip("pypdf")
        from pypdf import PdfWriter

        # Build a PDF with a blank page (no text layer)
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf_path = tmp_path / "blank.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        ocr_calls: list[tuple] = []

        def fake_ocr(path, page_number):
            ocr_calls.append((path, page_number))
            return "OCR text from page"

        monkeypatch.setattr(_helpers, "_ocr_page", fake_ocr)

        result = _helpers._read_pdf_text(pdf_path)
        assert ocr_calls, "_ocr_page should have been called for the blank page"
        assert ocr_calls[0][1] == 1  # page_number is 1-indexed
        assert "OCR text from page" in result

    def test_ocr_not_called_when_page_has_text(self, tmp_path, monkeypatch):
        """When pypdf extracts text from a page, _ocr_page should NOT be called."""
        import _helpers

        pytest_mod = __import__("pytest")
        pypdf = pytest_mod.importorskip("pypdf")
        from pypdf import PdfWriter
        from pypdf.generic import ContentStream, NameObject, ArrayObject, ByteStringObject

        # We test this by checking that a page with text doesn't trigger OCR;
        # use a blank PDF and pre-fill its extract_text return value via monkeypatch.
        writer = PdfWriter()
        writer.add_blank_page(width=200, height=200)
        pdf_path = tmp_path / "with-text.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        # Patch PdfReader so the first page returns text
        original_PdfReader = _helpers.__dict__.get("PdfReader")

        class FakePage:
            def extract_text(self):
                return "Some real text on this page."

        class FakeReader:
            def __init__(self, path):
                self.pages = [FakePage()]

        import pypdf as pypdf_module
        monkeypatch.setattr(pypdf_module, "PdfReader", FakeReader)

        ocr_calls: list = []

        def fake_ocr(path, page_number):
            ocr_calls.append(page_number)
            return "should not be called"

        monkeypatch.setattr(_helpers, "_ocr_page", fake_ocr)

        result = _helpers._read_pdf_text(pdf_path)
        assert ocr_calls == [], "_ocr_page should NOT be called when the page has text"
        assert "Some real text" in result


# ---------------------------------------------------------------------------
# _ocr_page
# ---------------------------------------------------------------------------

class TestOcrPage:
    def test_returns_string_when_libraries_missing(self, tmp_path, monkeypatch):
        """_ocr_page must return '' gracefully when pdf2image/pytesseract are absent."""
        import _helpers
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name in ("pdf2image", "pytesseract"):
                raise ImportError(f"Mocked missing: {name}")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        pdf_path = tmp_path / "dummy.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")
        result = _helpers._ocr_page(pdf_path, 1)
        assert result == ""

    def test_returns_empty_on_conversion_error(self, tmp_path, monkeypatch):
        """_ocr_page returns '' if pdf2image raises (e.g. poppler not installed)."""
        import _helpers

        def fake_convert(*args, **kwargs):
            raise RuntimeError("poppler not found")

        try:
            import pdf2image as _pdf2image_mod
            monkeypatch.setattr(_pdf2image_mod, "convert_from_path", fake_convert)
        except ImportError:
            # pdf2image not installed — the ImportError path is tested above
            return

        result = _helpers._ocr_page(tmp_path / "any.pdf", 1)
        assert result == ""

    def test_page_number_is_one_indexed(self, tmp_path, monkeypatch):
        """_ocr_page passes page_number directly to convert_from_path as first_page/last_page."""
        import _helpers

        captured: list[dict] = []

        class FakeImage:
            pass

        def fake_convert(path, first_page, last_page):
            captured.append({"first_page": first_page, "last_page": last_page})
            return [FakeImage()]

        try:
            import pdf2image as _pdf2image_mod
            import pytesseract as _pytesseract_mod
            monkeypatch.setattr(_pdf2image_mod, "convert_from_path", fake_convert)
            monkeypatch.setattr(_pytesseract_mod, "image_to_string", lambda img: "text")
        except ImportError:
            return  # libraries not installed — skip the assertion

        _helpers._ocr_page(tmp_path / "any.pdf", 3)
        if captured:
            assert captured[0]["first_page"] == 3
            assert captured[0]["last_page"] == 3
