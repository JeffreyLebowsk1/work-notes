"""
_email_receiver.py — Fetch emails via IMAP for manual review and import.

Provides a **deliberate, review-first** workflow: emails are fetched and
previewed but NEVER auto-imported.  The user must explicitly review each
message, edit the content to remove any PII / FERPA-sensitive data, choose
the destination folder, and approve the import.

Workflow:
  1. fetch_unread()   — connect to IMAP, return message previews (read-only)
  2. preview_message() — show suggested folder + filename (no side effects)
  3. save_note()      — user-approved: write markdown to chosen destination

Environment variables (set in tools/.env):
    EMAIL_IMAP_HOST     — IMAP server hostname (e.g. imap.gmail.com)
    EMAIL_IMAP_PORT     — IMAP port (default: 993)
    EMAIL_ADDRESS       — Full email address to log in with
    EMAIL_PASSWORD      — App password or account password
    EMAIL_ALLOWED_SENDERS — Comma-separated list of allowed sender addresses.
                            If empty, ALL senders are accepted.
    EMAIL_FOLDER        — IMAP folder to check (default: INBOX)
"""

import email
import email.header
import email.utils
import imaplib
import re
import ssl
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from _helpers import REPO_ROOT

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class EmailMessage(TypedDict):
    uid: str
    sender: str
    sender_name: str
    subject: str
    date: str
    body: str
    has_attachments: bool
    attachment_names: list[str]


class ImportResult(TypedDict):
    destination: str
    folder: str
    filename: str
    status: str  # "preview" | "saved" | "error"
    error: str


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_config() -> dict:
    """Read email configuration from environment (loaded by config.py)."""
    import config  # noqa: delay import to respect load order

    return {
        "host": getattr(config, "EMAIL_IMAP_HOST", ""),
        "port": int(getattr(config, "EMAIL_IMAP_PORT", 993)),
        "address": getattr(config, "EMAIL_ADDRESS", ""),
        "password": getattr(config, "EMAIL_PASSWORD", ""),
        "folder": getattr(config, "EMAIL_FOLDER", "INBOX"),
        "allowed": [
            s.strip().lower()
            for s in getattr(config, "EMAIL_ALLOWED_SENDERS", "").split(",")
            if s.strip()
        ],
    }


def is_configured() -> bool:
    """Return True if the minimum email settings are present."""
    cfg = _get_config()
    return bool(cfg["host"] and cfg["address"] and cfg["password"])


# ---------------------------------------------------------------------------
# IMAP helpers
# ---------------------------------------------------------------------------

def _decode_header(raw: str | None) -> str:
    """Decode an RFC-2047 encoded header value into a plain string."""
    if not raw:
        return ""
    parts = email.header.decode_header(raw)
    decoded: list[str] = []
    for data, charset in parts:
        if isinstance(data, bytes):
            decoded.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(data)
    return " ".join(decoded)


def _extract_body(msg: email.message.Message) -> str:
    """Walk the MIME tree and return the plain-text body (or stripped HTML)."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
        # Fallback: try HTML parts
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
                    # Rough HTML→text: strip tags
                    return re.sub(r"<[^>]+>", "", html).strip()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def _get_attachment_names(msg: email.message.Message) -> list[str]:
    """Return a list of attachment filenames (non-inline parts)."""
    names: list[str] = []
    if not msg.is_multipart():
        return names
    for part in msg.walk():
        disp = str(part.get("Content-Disposition", ""))
        if "attachment" in disp:
            fn = part.get_filename()
            if fn:
                names.append(_decode_header(fn))
    return names


def _save_attachments(msg: email.message.Message, dest_dir: Path) -> list[str]:
    """Save attachment files to *dest_dir* and return saved filenames."""
    from werkzeug.utils import secure_filename as _secure

    saved: list[str] = []
    if not msg.is_multipart():
        return saved
    for part in msg.walk():
        disp = str(part.get("Content-Disposition", ""))
        if "attachment" not in disp:
            continue
        fn = part.get_filename()
        if not fn:
            continue
        safe_name = _secure(_decode_header(fn))
        if not safe_name:
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / safe_name
        dest.write_bytes(payload)
        saved.append(safe_name)
    return saved


# ---------------------------------------------------------------------------
# Fetch unread messages
# ---------------------------------------------------------------------------

def fetch_unread(*, limit: int = 25) -> list[EmailMessage]:
    """Connect via IMAP and return up to *limit* unread messages.

    Only messages from allowed senders are returned (if the allow-list is
    configured).  Messages are NOT marked as read by this function.
    """
    cfg = _get_config()
    if not (cfg["host"] and cfg["address"] and cfg["password"]):
        raise RuntimeError("Email is not configured. Set EMAIL_IMAP_HOST, EMAIL_ADDRESS, and EMAIL_PASSWORD in tools/.env")

    ctx = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL(cfg["host"], cfg["port"], ssl_context=ctx)
    try:
        conn.login(cfg["address"], cfg["password"])
        conn.select(cfg["folder"], readonly=True)

        _status, data = conn.uid("search", None, "UNSEEN")
        uids = data[0].split() if data[0] else []
        if not uids:
            return []

        # Most-recent first, capped
        uids = uids[-limit:][::-1]

        messages: list[EmailMessage] = []
        for uid_bytes in uids:
            uid = uid_bytes.decode()
            _status, msg_data = conn.uid("fetch", uid, "(RFC822)")
            if not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            sender_raw = msg.get("From", "")
            sender_name, sender_addr = email.utils.parseaddr(sender_raw)
            sender_addr = sender_addr.lower()

            # Filter by allowed senders
            if cfg["allowed"] and sender_addr not in cfg["allowed"]:
                continue

            date_raw = msg.get("Date", "")
            try:
                dt = email.utils.parsedate_to_datetime(date_raw)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = date_raw

            att_names = _get_attachment_names(msg)

            messages.append(EmailMessage(
                uid=uid,
                sender=sender_addr,
                sender_name=_decode_header(sender_name) or sender_addr,
                subject=_decode_header(msg.get("Subject", "(no subject)")),
                date=date_str,
                body=_extract_body(msg),
                has_attachments=bool(att_names),
                attachment_names=att_names,
            ))

        return messages
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


# ---------------------------------------------------------------------------
# Process and import messages
# ---------------------------------------------------------------------------

# Subject-line tags that override folder detection.
_TAG_MAP: dict[str, str] = {
    "daily": "daily-logs",
    "log": "daily-logs",
    "meeting": "meetings",
    "update": "updates",
    "graduation": "graduation",
    "admissions": "admissions",
    "transcript": "transcripts",
    "residency": "residency-tuition",
    "ce": "continuing-education",
    "financial": "financial-aid",
    "ferpa": "personal-data",
}


def _detect_tag(subject: str) -> str | None:
    """Check for a ``[tag]`` prefix in the subject line."""
    m = re.match(r"\[(\w+)\]", subject)
    if m:
        tag = m.group(1).lower()
        return _TAG_MAP.get(tag)
    return None


def _subject_to_filename(subject: str, date_str: str) -> str:
    """Convert an email subject into a repository-safe filename."""
    # Strip any [tag] prefix
    clean = re.sub(r"^\[\w+\]\s*", "", subject)
    # Remove fwd/re prefixes
    clean = re.sub(r"^(re|fwd?)\s*:\s*", "", clean, flags=re.IGNORECASE).strip()
    if not clean:
        clean = "email-note"
    # Convert to kebab-case
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", clean).strip("-").lower()
    slug = slug[:60]  # cap length

    # Extract date
    date_m = re.search(r"\d{4}-\d{2}-\d{2}", date_str)
    date_prefix = date_m.group(0) if date_m else datetime.now().strftime("%Y-%m-%d")

    return f"{date_prefix}-{slug}.md"


def _format_note(msg: EmailMessage) -> str:
    """Format an email message as a markdown note."""
    lines = [
        f"# {msg['subject']}",
        "",
        f"> Received from **{msg['sender_name']}** ({msg['sender']}) on {msg['date']}",
        "",
    ]
    if msg["has_attachments"]:
        lines.append(f"> 📎 Attachments: {', '.join(msg['attachment_names'])}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(msg["body"].strip())
    lines.append("")
    return "\n".join(lines)


def process_message(
    msg: EmailMessage,
    *,
    dry_run: bool = False,
    mark_read: bool = True,
) -> ImportResult:
    """Import a single email message as a markdown note.

    Uses subject-line ``[tag]`` for folder routing if present, otherwise
    falls back to the importer's keyword-based detection.
    """
    from _importer import _detect_folder, _suggest_dest_dir

    body = _format_note(msg)

    # Folder routing: tag override → keyword detection
    folder = _detect_tag(msg["subject"])
    if not folder:
        folder, _conf = _detect_folder(msg["subject"], body)

    filename = _subject_to_filename(msg["subject"], msg["date"])

    if folder == "daily-logs":
        # Daily logs use YYYY-MM subdirectories
        date_m = re.search(r"\d{4}-\d{2}", filename)
        ym = date_m.group(0) if date_m else datetime.now().strftime("%Y-%m")
        dest_dir = REPO_ROOT / "daily-logs" / ym
    elif folder in ("(root)", ""):
        dest_dir = REPO_ROOT / "inbox"
    else:
        dest_dir = REPO_ROOT / folder

    dest_path = dest_dir / filename

    if dry_run:
        try:
            from _helpers import _relative
            dest_display = str(_relative(dest_path))
        except ValueError:
            dest_display = str(dest_path)
        return ImportResult(
            destination=dest_display,
            folder=folder or "",
            filename=filename,
            status="preview",
            error="",
        )

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        # Avoid overwriting existing notes
        if dest_path.exists():
            stem = dest_path.stem
            for i in range(2, 100):
                candidate = dest_dir / f"{stem}-{i}.md"
                if not candidate.exists():
                    dest_path = candidate
                    break

        dest_path.write_text(body, encoding="utf-8")

        # Mark as read in IMAP
        if mark_read:
            _mark_as_read(msg["uid"])

        try:
            from _helpers import _relative
            dest_display = str(_relative(dest_path))
        except ValueError:
            dest_display = str(dest_path)

        return ImportResult(
            destination=dest_display,
            folder=folder or "",
            filename=dest_path.name,
            status="saved",
            error="",
        )
    except Exception as exc:
        return ImportResult(
            destination="",
            folder=folder or "",
            filename=filename,
            status="error",
            error=str(exc),
        )


def _mark_as_read(uid: str) -> None:
    """Connect to IMAP and mark a single message as read (\\Seen)."""
    cfg = _get_config()
    if not (cfg["host"] and cfg["address"] and cfg["password"]):
        return
    ctx = ssl.create_default_context()
    conn = imaplib.IMAP4_SSL(cfg["host"], cfg["port"], ssl_context=ctx)
    try:
        conn.login(cfg["address"], cfg["password"])
        conn.select(cfg["folder"], readonly=False)
        conn.uid("store", uid, "+FLAGS", "\\Seen")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def cmd_check_email(args) -> None:
    """CLI handler for ``check-email`` subcommand."""
    if not is_configured():
        print("\n⚠️  Email is not configured.")
        print("   Set EMAIL_IMAP_HOST, EMAIL_ADDRESS, and EMAIL_PASSWORD in tools/.env")
        print("   See tools/.env.example for all available email settings.\n")
        return

    print("\n📧 Checking email inbox…")
    try:
        messages = fetch_unread(limit=getattr(args, "limit", 25))
    except Exception as exc:
        print(f"\n❌ Failed to connect: {exc}\n")
        return

    if not messages:
        print("📭 No unread messages from allowed senders.\n")
        return

    print(f"📬 Found {len(messages)} unread message(s)\n")

    for msg in messages:
        print(f"  From: {msg['sender_name']} <{msg['sender']}>")
        print(f"  Subject: {msg['subject']}")
        print(f"  Date: {msg['date']}")
        if msg["has_attachments"]:
            print(f"  📎 Attachments: {', '.join(msg['attachment_names'])}")

        result = process_message(msg, dry_run=getattr(args, "dry_run", False))
        if result["status"] == "saved":
            print(f"  ✅ → {result['destination']}")
        elif result["status"] == "preview":
            print(f"  📋 Would import → {result['destination']}")
        else:
            print(f"  ❌ Error: {result['error']}")
        print()
