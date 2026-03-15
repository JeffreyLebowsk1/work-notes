---
description: "Use when editing Python files in the tools directory — Flask routes, CLI commands, helpers, config, AI providers, importers, or test files."
applyTo: "tools/**/*.py"
---

# Flask App & Tools Python Guidelines

- The Flask app runs on a Jetson Orin Nano via gunicorn — never test by running locally on Windows.
- All routes are in `tools/app.py`. Templates extend `base.html`. Static assets are cache-busted via `static_asset_url()`.
- Use stdlib where possible — avoid adding new pip dependencies unless essential. If you must, update `tools/requirements-web.txt`.
- Configuration comes from `tools/config.py` which loads `tools/.env`. Never hardcode secrets.
- Markdown rendering uses the `markdown` library with `tables`, `fenced_code`, and `toc` extensions.
- Run `python -m pytest tests/ -v` before committing changes.
- After changes, deploy via: git push → SSH pull on Jetson → `systemctl --user restart work-notes-web`.
