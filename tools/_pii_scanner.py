"""
_pii_scanner.py — Scan staged files for potential student PII before commit.

Designed for a public GitHub repository belonging to a college Registrar's
Office.  Catches real PII risks (SSNs, bulk student IDs, student record
fragments) without flagging legitimate staff contact information.

Usage:
    python tools/_pii_scanner.py              # scan staged files only
    python tools/_pii_scanner.py --all        # scan entire repo
    python tools/_pii_scanner.py FILE ...     # scan specific files
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# SSN: 3-2-4 digits with dashes or spaces.  Excludes phone-like patterns
# (area codes in parens) and ISO dates (YYYY-MM-DD).
_SSN_RE = re.compile(
    r"(?<!\d)(?<!\()"           # not preceded by digit or open-paren
    r"\b(\d{3})[-\s](\d{2})[-\s](\d{4})\b"
    r"(?!\s*\))",               # not followed by close-paren (phone)
)

# Loose SSN: 9 consecutive digits that could be a no-delimiter SSN.
_SSN_NODASH_RE = re.compile(r"(?<!\d)\b\d{9}\b(?!\d)")

# Student / Colleague IDs: 7-8 digit numbers (CCCC uses 7-digit Colleague IDs).
_STUDENT_ID_RE = re.compile(r"\b\d{7,8}\b")

# PII-adjacent keywords — when these appear near numbers it's a red flag.
_PII_KEYWORDS_RE = re.compile(
    r"\b("
    r"social\s*security|SSN|student\s*ID|colleague\s*ID"
    r"|date\s*of\s*birth|DOB|birth\s*date"
    r"|GPA|grade\s*point"
    r"|street\s*address|home\s*address|mailing\s*address"
    r"|FERPA\s*(?:waiver|release|consent)"
    r")\b",
    re.IGNORECASE,
)

# Bulk data indicators: lines that look like CSV/TSV student records.
# Pattern: a name-like string followed by an ID-like number on the same line.
_RECORD_ROW_RE = re.compile(
    r"[A-Z][a-z]+[\s,]+[A-Z][a-z]+"    # First Last (or Last, First)
    r".*\b\d{7,9}\b",                   # followed by a 7-9 digit number
)

# Binary / spreadsheet extensions that should never be committed.
_BLOCKED_EXTENSIONS = frozenset({
    ".xlsx", ".xls", ".xlsm", ".xlsb",
    ".csv",   # CSVs can contain bulk student data
    ".accdb", ".mdb",
    ".sav", ".dta",   # SPSS, Stata
})

# Files / paths to always skip (never scan).
_SKIP_PATTERNS = [
    re.compile(r"\.git/"),
    re.compile(r"__pycache__/"),
    re.compile(r"\.pyc$"),
    re.compile(r"node_modules/"),
    re.compile(r"\.venv/"),
    re.compile(r"assets/images/"),    # binary images, not text PII
    re.compile(r"\.png$|\.jpg$|\.jpeg$|\.gif$|\.svg$|\.ico$"),
]


# ---------------------------------------------------------------------------
# Scanning logic
# ---------------------------------------------------------------------------

class Finding:
    """A single PII finding in a file."""

    def __init__(self, filepath: str, line_num: int, category: str, detail: str):
        self.filepath = filepath
        self.line_num = line_num
        self.category = category
        self.detail = detail

    def __str__(self):
        return f"  {self.filepath}:{self.line_num}  [{self.category}] {self.detail}"


def _is_date_like(g1: str, g2: str, g3: str) -> bool:
    """Check if a 3-2-4 digit group looks like a date (YYYY-MM-DD or MM-DD-YYYY)."""
    # YYYY-MM-DD: first group 19xx or 20xx
    if g1.startswith(("19", "20")) and 1 <= int(g2) <= 12:
        return True
    # MM-DD-YYYY: last group is a year
    if g3.startswith(("19", "20")) and 1 <= int(g1[:2]) <= 12:
        return True
    return False


def _should_skip(filepath: str) -> bool:
    """Check if a file path should be skipped entirely."""
    for pat in _SKIP_PATTERNS:
        if pat.search(filepath):
            return True
    return False


def scan_file(filepath: str) -> list[Finding]:
    """Scan a single file for PII patterns. Returns a list of Findings."""
    findings: list[Finding] = []
    rel = filepath

    # Check extension first — block dangerous file types outright.
    ext = Path(filepath).suffix.lower()
    if ext in _BLOCKED_EXTENSIONS:
        findings.append(Finding(rel, 0, "BLOCKED_FILE",
                                f"File type {ext} should not be committed (may contain bulk student data)"))
        return findings

    # Only scan text-like files.
    if ext not in ("", ".md", ".txt", ".py", ".html", ".css", ".js",
                   ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini",
                   ".sh", ".bat", ".ps1", ".env", ".conf"):
        return findings

    abs_path = Path(filepath)
    if not abs_path.is_absolute():
        abs_path = REPO_ROOT / filepath
    if not abs_path.is_file():
        return findings

    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    lines = content.splitlines()
    record_row_count = 0     # track how many lines look like bulk records

    for i, line in enumerate(lines, start=1):
        # --- SSN with delimiters ---
        for m in _SSN_RE.finditer(line):
            g1, g2, g3 = m.group(1), m.group(2), m.group(3)
            if not _is_date_like(g1, g2, g3):
                # Extra check: skip if it's clearly a phone number context
                context = line[max(0, m.start() - 5):m.end() + 5]
                if "(" not in context and "ext" not in context.lower():
                    findings.append(Finding(rel, i, "SSN",
                                           f"Possible SSN: {g1}-{g2}-****"))

        # --- SSN without delimiters (9 consecutive digits) ---
        for m in _SSN_NODASH_RE.finditer(line):
            val = m.group()
            # Skip obvious non-SSNs: zip+4 (5+4), dates, program codes
            if not val.startswith(("000", "999", "666")):
                # Only flag if a PII keyword is nearby
                window = line[max(0, m.start() - 40):m.end() + 40]
                if _PII_KEYWORDS_RE.search(window):
                    findings.append(Finding(rel, i, "SSN_NODASH",
                                           f"Possible undashed SSN near PII keyword: {val[:3]}...{val[-2:]}"))

        # --- PII keywords near numbers ---
        if _PII_KEYWORDS_RE.search(line):
            # Check for numeric data on the same line
            nums = re.findall(r"\b\d{3,}\b", line)
            if nums:
                kw = _PII_KEYWORDS_RE.search(line).group()
                findings.append(Finding(rel, i, "PII_KEYWORD",
                                       f"Keyword '{kw}' appears near numeric data"))

        # --- Bulk record rows ---
        if _RECORD_ROW_RE.search(line):
            record_row_count += 1

    # Flag if file has many record-like rows (suggests a student list).
    if record_row_count >= 5:
        findings.append(Finding(rel, 0, "BULK_RECORDS",
                                f"{record_row_count} lines look like name+ID student records"))

    return findings


def scan_files(file_list: list[str]) -> list[Finding]:
    """Scan a list of file paths for PII."""
    all_findings: list[Finding] = []
    for f in file_list:
        if _should_skip(f):
            continue
        all_findings.extend(scan_file(f))
    return all_findings


# ---------------------------------------------------------------------------
# Git integration
# ---------------------------------------------------------------------------

def get_staged_files() -> list[str]:
    """Get list of files staged for commit (relative to repo root)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except FileNotFoundError:
        return []


def get_all_tracked_files() -> list[str]:
    """Get list of all tracked files in the repo."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            return []
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__.strip())
        return 0

    if "--all" in args:
        files = get_all_tracked_files()
        mode = "all tracked files"
    elif args and args[0] != "--":
        files = [a for a in args if not a.startswith("-")]
        mode = f"{len(files)} specified file(s)"
    else:
        files = get_staged_files()
        mode = "staged files"

    if not files:
        print(f"PII scan ({mode}): no files to scan.")
        return 0

    findings = scan_files(files)

    if not findings:
        print(f"PII scan ({mode}): ✓ clean — {len(files)} file(s) checked.")
        return 0

    # Report findings
    print(f"\n⚠️  PII scan ({mode}): {len(findings)} potential issue(s) found!\n")
    for f in findings:
        print(f)
    print()
    print("If these are false positives, you can bypass with: git commit --no-verify")
    print("But please verify — this repo is PUBLIC on GitHub.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
