---
description: "Use when writing or running pytest tests for the work-notes tools."
applyTo: "tests/**/*.py"
---

# Test Guidelines

- Tests use pytest with `tmp_path` fixtures and monkeypatching — they never touch the real repo.
- Run all tests: `python -m pytest tests/ -v`
- Test files cover: app.py helpers (`test_helpers.py`), CLI commands (`test_commands.py`), helpers (`test_helpers.py`), importer logic (`test_importer.py`), and parser registration (`test_notes_helper.py`).
- When adding new routes or helpers in `app.py`, add corresponding tests.
- Import paths use `tools.` prefix (e.g., `from tools._helpers import ...`).
