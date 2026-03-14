import os
import secrets

from dotenv import load_dotenv

# Load .env from the tools/ directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── Flask ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
PORT = int(os.environ.get("PORT", "5000"))

# ── AI providers ─────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

# Which provider to use by default: "gemini" | "openai" | "perplexity"
AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower()
