---
description: "Use when editing Jinja2 HTML templates for the Flask web application — layout, pages, components."
applyTo: "tools/templates/**/*.html"
---

# Template Guidelines

- All templates extend `base.html` which provides navbar, footer, dark mode, bottom nav, and Mermaid.js v11.
- Follow the breadcrumb → page-header → section-content structure used in existing pages.
- Use `{{ static_asset_url('path') }}` for cache-busted static file references.
- Mermaid diagrams render client-side — use `<pre class="mermaid">` blocks.
- Keep JavaScript inline only for page-specific logic; shared behavior goes in `tools/static/js/main.js`.
- Test template changes by deploying to the Jetson — the app does not run on Windows.
