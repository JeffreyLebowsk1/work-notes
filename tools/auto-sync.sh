#!/usr/bin/env bash
# auto-sync.sh — Watch a cloned repo folder and auto-commit + push every change.
#
# Designed for a Linux machine (e.g. Jetson Orin Nano) where the repo is cloned
# inside a Google Drive folder mounted via rclone.  Any time a file is created
# or modified in the repo directory, this script stages everything, commits with
# an automatic message, and pushes to the remote.
#
# Dependencies (install once):
#   sudo apt-get install inotify-tools git
#
# Usage:
#   chmod +x tools/auto-sync.sh
#   ./tools/auto-sync.sh                        # watches the current directory
#   REPO_DIR=/path/to/work-notes ./tools/auto-sync.sh   # explicit path
#
# To run as a persistent background service, see tools/auto-sync.service.
# ---------------------------------------------------------------------------

set -euo pipefail

# ------------------------------------------------------------------
# Configuration — override any of these with environment variables.
# ------------------------------------------------------------------
REPO_DIR="${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
DEBOUNCE_SECONDS="${DEBOUNCE_SECONDS:-5}"   # wait this many seconds after the
                                             # last event before committing
GIT_USER_NAME="${GIT_USER_NAME:-auto-sync}"
GIT_USER_EMAIL="${GIT_USER_EMAIL:-auto-sync@localhost}"
COMMIT_PREFIX="${COMMIT_PREFIX:-auto: sync from Google Drive}"

# ------------------------------------------------------------------
# Sanity checks
# ------------------------------------------------------------------
if ! command -v inotifywait &>/dev/null; then
  echo "ERROR: inotifywait not found. Install it with:" >&2
  echo "       sudo apt-get install inotify-tools" >&2
  exit 1
fi

if ! command -v git &>/dev/null; then
  echo "ERROR: git not found. Install it with:" >&2
  echo "       sudo apt-get install git" >&2
  exit 1
fi

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "ERROR: $REPO_DIR is not a git repository." >&2
  exit 1
fi

cd "$REPO_DIR"

# Apply git identity for this repo only (does not touch global config)
git config user.name  "$GIT_USER_NAME"
git config user.email "$GIT_USER_EMAIL"

echo "=== auto-sync started ==="
echo "  Watching : $REPO_DIR"
echo "  Debounce : ${DEBOUNCE_SECONDS}s"
echo "  Remote   : $(git remote get-url origin 2>/dev/null || echo 'n/a')"
echo ""

# ------------------------------------------------------------------
# Helper — commit and push whatever is currently staged/unstaged.
# ------------------------------------------------------------------
do_sync() {
  cd "$REPO_DIR"

  # Pull any upstream changes first to reduce conflict chance
  if git pull --rebase --autostash --quiet 2>/dev/null; then
    :
  else
    echo "$(date '+%F %T') WARNING: git pull failed — skipping this sync cycle" >&2
    return
  fi

  git add -A

  if git diff --cached --quiet; then
    echo "$(date '+%F %T') No changes to commit."
    return
  fi

  # Build a meaningful commit message listing added/changed files
  local changed
  changed=$(git diff --cached --name-only | head -10 | paste -sd ', ' -)
  local msg="${COMMIT_PREFIX} — ${changed}"

  git commit -m "$msg"
  git push
  echo "$(date '+%F %T') Pushed: $msg"
}

# ------------------------------------------------------------------
# Watch loop — inotifywait streams one event per line.
# We debounce: after any event we wait DEBOUNCE_SECONDS for the
# stream to go quiet before committing, so rapid saves/uploads
# are batched into a single commit.
# ------------------------------------------------------------------
PENDING=0

inotifywait \
  --monitor \
  --recursive \
  --quiet \
  --format '%e %w%f' \
  --event create,modify,delete,move \
  --exclude '/\.git/' \
  "$REPO_DIR" |
while IFS= read -r line; do
  echo "$(date '+%F %T') Change detected: $line"
  PENDING=1

  # Drain any events that arrive within DEBOUNCE_SECONDS
  while IFS= read -r -t "$DEBOUNCE_SECONDS" further_line; do
    echo "$(date '+%F %T') Batching: $further_line"
  done

  if [ "$PENDING" -eq 1 ]; then
    do_sync
    PENDING=0
  fi
done
