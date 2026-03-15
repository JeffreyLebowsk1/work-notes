---
description: "Use when editing CSS or JavaScript static assets for the Flask web application."
applyTo: tools/static/**
---

# Static Asset Guidelines

- Main stylesheet: `tools/static/css/style.css` — single file, keep organized by section with comments.
- Main script: `tools/static/js/main.js` — handles dark mode, search, nav, and shared UI behavior.
- Assets are cache-busted via `static_asset_url()` in templates — no manual versioning needed.
- Support both light and dark mode — use CSS custom properties or `.dark-mode` class overrides.
- Mobile-first responsive design — test at 768px and below breakpoints.
