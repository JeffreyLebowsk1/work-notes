import os
import secrets

from dotenv import load_dotenv

# Load .env from the tools/ directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
PORT = int(os.environ.get("PORT", "4200"))

# ── AI providers ─────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

# Which provider to use by default: "gemini" | "perplexity"
AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower()

# Maximum file size for asset uploads (bytes). Exposed to Flask via MAX_CONTENT_LENGTH.
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "16"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

# ── Email Receiver (IMAP — optional) ─────────────────────────────────────────
EMAIL_IMAP_HOST = os.environ.get("EMAIL_IMAP_HOST", "")
EMAIL_IMAP_PORT = int(os.environ.get("EMAIL_IMAP_PORT", "993"))
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_FOLDER = os.environ.get("EMAIL_FOLDER", "Work-Notes")
EMAIL_ALLOWED_SENDERS = os.environ.get("EMAIL_ALLOWED_SENDERS", "")

# ── HTTP Basic Auth (optional — leave blank for no auth) ─────────────────────
APP_USERNAME = os.environ.get("APP_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")
