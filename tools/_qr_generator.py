"""
_qr_generator.py — Scan markdown files for important links and generate QR codes.

Watches for configured links in the repository and auto-generates CCCC-branded QR codes
via the qoder API when they're detected.
"""

import base64
import json
import re
from pathlib import Path
from typing import Optional

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
QR_OUTPUT_DIR = REPO_ROOT / "assets" / "images" / "qr-codes"
QR_CONFIG_FILE = Path(__file__).resolve().parent / "qr_config.json"
CCCC_LOGO = REPO_ROOT / "assets" / "images" / "logos" / "central-carolina-community-college_logo.png"

# Default CCCC branding
CCCC_BRAND = {
    "fg_color": "#1d3557",
    "bg_color": "#FFFFFF",
    "module_style": "circle",
    "eye_style": "rounded",
    "error_correction": "H",
    "box_size": 20,
    "border": 4,
    "logo_size_percent": 22,
    "logo_border": 8,
    "logo_shape": "circle",
    "logo_corner_radius": 0,
}

# Default important links — can be overridden by qr_config.json
DEFAULT_IMPORTANT_LINKS = {
    "cfnc": "https://www.cfnc.org",
    "diplomasender": "https://www.diplomasender.com",
    "cccc-scholarships": "https://www.cccc.edu/scholarships",
    "cccc-financial-aid": "https://www.cccc.edu/paying-college",
    "civic-center": "https://www.cccc.edu/about/locations/civic-center/",
    "ce-schedule": "https://www.cccc.edu/ecd/schedule/",
    "academic-calendar": "https://calendar.cccc.edu/",
}


def _load_config() -> dict:
    """Load important links from qr_config.json, or return defaults."""
    if QR_CONFIG_FILE.exists():
        try:
            with open(QR_CONFIG_FILE) as f:
                config = json.load(f)
            return config.get("important_links", DEFAULT_IMPORTANT_LINKS)
        except Exception as e:
            print(f"Warning: Could not load {QR_CONFIG_FILE}: {e}")
    return DEFAULT_IMPORTANT_LINKS


def _sanitize_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    return re.sub(r"[^a-z0-9_-]", "", name.lower())


def _find_urls_in_content(content: str) -> dict[str, str]:
    """
    Extract URLs from markdown links and plain URLs.
    Returns a dict of {url: label}.
    """
    urls = {}

    # Markdown links: [label](url)
    markdown_links = re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", content)
    for label, url in markdown_links:
        if url.startswith(("http://", "https://")):
            urls[url] = label

    # Plain URLs
    plain_urls = re.findall(r"https?://[^\s\)]+", content)
    for url in plain_urls:
        if url not in urls:
            urls[url] = url.split("//")[1].split("/")[0]

    return urls


# Cached base64 data URI for the CCCC logo — computed once on first use.
_LOGO_DATA_URI: str | None = None


def _logo_data_uri() -> str:
    """Read the CCCC logo PNG and return it as a base64 data URI."""
    global _LOGO_DATA_URI
    if _LOGO_DATA_URI is None:
        raw = CCCC_LOGO.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        _LOGO_DATA_URI = f"data:image/png;base64,{b64}"
    return _LOGO_DATA_URI


def _build_payload(url: str) -> dict:
    """Build the qoder API payload for a URL, including the logo if available."""
    payload = {"data": url, **CCCC_BRAND}
    if CCCC_LOGO.exists():
        payload["logo_path"] = _logo_data_uri()
    return payload


def generate_qr_codes(
    qoder_url: str = "http://localhost:8080",
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, str]:
    """
    Scan repository for important links and generate QR codes if missing.

    Args:
        qoder_url: Base URL of the qoder API (e.g. http://localhost:8080 or https://qoder.ngrok.app)
        dry_run: If True, only report what would be done, don't create files
        force: If True, regenerate all codes even if they already exist

    Returns:
        Dictionary of {filename: status} (e.g. "created", "skipped", "error")
    """
    important_links = _load_config()
    qr_output_dir = QR_OUTPUT_DIR
    qr_output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for name, url in important_links.items():
        filename = f"{_sanitize_filename(name)}.png"
        filepath = qr_output_dir / filename

        if filepath.exists() and not force:
            results[filename] = "skipped (file exists)"
            print(f"  ▫ {filename} — file exists (use --force to regenerate)")
            continue

        if dry_run:
            results[filename] = "would create"
            print(f"  ✓ {filename} — would create for {url}")
            continue

        # Call qoder API — logo is embedded server-side via base64 data URI
        try:
            payload = _build_payload(url)
            response = requests.post(
                f"{qoder_url}/api/qr/text",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            filepath.write_bytes(response.content)
            size_kb = filepath.stat().st_size / 1024
            results[filename] = "created"
            print(f"  ✓ {filename} — created ({size_kb:.1f}KB)")

        except requests.exceptions.RequestException as e:
            results[filename] = f"error: {str(e)}"
            print(f"  ✗ {filename} — error: {e}")

    return results


def cmd_generate_qr(args) -> int:
    """CLI command: generate QR codes for important links."""
    try:
        print(f"Scanning for important links to generate QR codes...")
        print(f"  Qoder API: {args.qoder_url}")
        if args.dry_run:
            print(f"  DRY RUN — no files will be created")
        if args.force:
            print(f"  FORCE — will regenerate all codes")
        print()

        results = generate_qr_codes(
            qoder_url=args.qoder_url,
            dry_run=args.dry_run,
            force=args.force,
        )

        print()
        print(f"Results:")
        created = sum(1 for v in results.values() if v == "created")
        skipped = sum(1 for v in results.values() if "skipped" in v)
        errors = sum(1 for v in results.values() if "error" in v)

        if created:
            print(f"  ✓ {created} created")
        if skipped:
            print(f"  ▫ {skipped} skipped")
        if errors:
            print(f"  ✗ {errors} errors")

        return 0 if errors == 0 else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1
