"""
AI provider abstraction for Work Notes.

Supported providers
-------------------
  perplexity  – Perplexity Sonar (REST API)
  gemini      – Google Gemini 2.5 Flash (google-genai)  ← default

The active provider is chosen by:
  1. The ``provider`` argument passed to ask()
  2. config.AI_PROVIDER  (set AI_PROVIDER= in tools/.env)
  3. First provider whose API key is configured
"""

import requests

import config

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

PROVIDER_LABELS = {
    "gemini": "Google Gemini 2.5 Flash",
    "perplexity": "Perplexity Sonar",
}

REGISTRAR_SYSTEM_PROMPT = (
    "You are a knowledgeable assistant for the Student Records Registrar's Office at "
    "Central Carolina Community College. You help staff with questions about student "
    "records procedures, FERPA compliance, graduation requirements, transcript "
    "processing, residency determinations, tuition classifications, financial aid "
    "coordination, admissions processes, and continuing education programs. "
    "Provide clear, accurate, and practical guidance. When referencing policies or "
    "procedures, remind the user to verify against current official sources. "
    "Keep responses concise but thorough."
)


class ProviderError(Exception):
    """Raised when an AI provider call fails."""

    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.status_code = status_code


def get_available_providers():
    """Return a list of provider names whose API keys are configured."""
    available = []
    if config.GEMINI_API_KEY:
        available.append("gemini")
    if config.PERPLEXITY_API_KEY:
        available.append("perplexity")
    return available


def resolve_provider(requested=None):
    """
    Determine which provider to use.

    Priority: explicitly requested → config default → first with a key → 'gemini'
    """
    valid = set(PROVIDER_LABELS)
    if requested and requested in valid:
        return requested
    if config.AI_PROVIDER in valid:
        return config.AI_PROVIDER
    available = get_available_providers()
    return available[0] if available else "gemini"


def ask(message, system_prompt=None, provider=None):
    """
    Send a single message to the selected AI provider.

    Parameters
    ----------
    message : str
    system_prompt : str | None  – defaults to REGISTRAR_SYSTEM_PROMPT
    provider : str | None       – "perplexity" | "gemini" | None

    Returns
    -------
    str  – the model's reply text

    Raises
    ------
    ProviderError
    """
    if system_prompt is None:
        system_prompt = REGISTRAR_SYSTEM_PROMPT
    provider = resolve_provider(provider)
    if provider == "gemini":
        return _ask_gemini(message, system_prompt)
    return _ask_perplexity(message, system_prompt)


# ---------------------------------------------------------------------------
# Perplexity  (REST API)
# ---------------------------------------------------------------------------

_PERPLEXITY_BASE_URL = "https://api.perplexity.ai/chat/completions"
_PERPLEXITY_CHAT_MODEL = "sonar"


def _ask_perplexity(message, system_prompt):
    if not config.PERPLEXITY_API_KEY:
        raise ProviderError(
            "Perplexity API key not configured. "
            "Set PERPLEXITY_API_KEY in tools/.env to enable AI.",
            503,
        )
    try:
        resp = requests.post(
            _PERPLEXITY_BASE_URL,
            headers={
                "Authorization": f"Bearer {config.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": _PERPLEXITY_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                "max_tokens": 4096,
                "temperature": 0.7,
            },
            timeout=30,
        )
        if resp.status_code == 401:
            raise ProviderError("Invalid Perplexity API key.", 401)
        if resp.status_code == 429:
            raise ProviderError(
                "Perplexity rate limit exceeded. Try again in a moment.", 429
            )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except ProviderError:
        raise
    except Exception:
        raise ProviderError("Perplexity request failed. Please try again.", 500)


# ---------------------------------------------------------------------------
# Google Gemini
# ---------------------------------------------------------------------------

_GEMINI_MODEL = "gemini-2.5-flash"


def _ask_gemini(message, system_prompt):
    from google import genai
    from google.genai import types

    if not config.GEMINI_API_KEY:
        raise ProviderError(
            "Gemini API key not configured. "
            "Set GEMINI_API_KEY in tools/.env to enable AI.",
            503,
        )
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=4096,
                temperature=0.7,
            ),
        )
        return response.text
    except Exception as exc:
        _raise_gemini_error(exc)


def _raise_gemini_error(exc):
    msg = str(exc).lower()
    if any(k in msg for k in ("api_key", "invalid", "403", "permission")):
        raise ProviderError("Invalid Gemini API key.", 401)
    if any(k in msg for k in ("quota", "429", "resource_exhausted")):
        raise ProviderError(
            "Gemini quota exceeded. Try again in a moment.", 429
        )
    raise ProviderError("Gemini request failed. Please try again.", 500)
