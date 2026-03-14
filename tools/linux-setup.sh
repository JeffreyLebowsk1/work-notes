#!/usr/bin/env bash
# linux-setup.sh — One-shot setup and launch for the CCCC Notes web app on Linux.
#
# Run this script from the repository root:
#   bash tools/linux-setup.sh
#
# What it does:
#   1. Verifies prerequisites (Python 3.10+, pip, git)
#   2. Creates a Python virtual environment at .venv/ (skipped if it already exists)
#   3. Installs all Python dependencies from tools/requirements-web.txt
#   4. Scaffolds tools/.env from tools/.env.example (skipped if it already exists)
#   5. Starts the web app at http://localhost:5000
#
# Environment variables you can set before running:
#   APP_USERNAME   — set a login username (recommended for shared/public machines)
#   APP_PASSWORD   — set a login password (required when using ngrok or Render)
#   PORT           — override the default port (default: 5000)
#
# Examples:
#   bash tools/linux-setup.sh
#   APP_USERNAME=registrar APP_PASSWORD=secret bash tools/linux-setup.sh
#   PORT=8080 bash tools/linux-setup.sh
# ---------------------------------------------------------------------------

set -euo pipefail

# ---------------------------------------------------------------------------
# Colour helpers (disabled automatically when stdout is not a terminal)
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

info()    { echo -e "${CYAN}[setup]${RESET} $*"; }
success() { echo -e "${GREEN}[setup]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[setup]${RESET} $*"; }
error()   { echo -e "${RED}[setup] ERROR:${RESET} $*" >&2; }

# ---------------------------------------------------------------------------
# Locate the repository root (the script may be invoked from anywhere)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo -e "${BOLD}🐧 CCCC Notes — Linux Setup${RESET}"
echo "   Repository : $REPO_ROOT"
echo ""

# ---------------------------------------------------------------------------
# 1. Check prerequisites
# ---------------------------------------------------------------------------
info "Checking prerequisites..."

# git
if ! command -v git &>/dev/null; then
  error "git is not installed. Run:  sudo apt-get install git"
  exit 1
fi
success "git $(git --version | awk '{print $3}')"

# python3
if ! command -v python3 &>/dev/null; then
  error "python3 is not installed. Run:  sudo apt-get install python3 python3-pip python3-venv"
  exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
  error "Python 3.10+ is required (found $PYTHON_VERSION). Install a newer version:"
  error "  sudo apt-get install python3.10  (or python3.11 / python3.12)"
  exit 1
fi
success "python3 $PYTHON_VERSION"

# ---------------------------------------------------------------------------
# 2. Create virtual environment (idempotent — skip if .venv already exists)
# ---------------------------------------------------------------------------
VENV_DIR="$REPO_ROOT/.venv"

if [ -d "$VENV_DIR" ]; then
  info "Virtual environment already exists at .venv/ — skipping creation."
else
  info "Creating virtual environment at .venv/ ..."
  python3 -m venv "$VENV_DIR"
  success "Virtual environment created."
fi

# Activate it for the rest of this script
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# ---------------------------------------------------------------------------
# 3. Install / upgrade dependencies
# ---------------------------------------------------------------------------
info "Installing Python dependencies from tools/requirements-web.txt ..."
pip install --quiet --upgrade pip
pip install --quiet -r "$REPO_ROOT/tools/requirements-web.txt"
success "Dependencies installed."

# ---------------------------------------------------------------------------
# 4. Scaffold tools/.env (skip if the user already has one)
# ---------------------------------------------------------------------------
ENV_FILE="$REPO_ROOT/tools/.env"
ENV_EXAMPLE="$REPO_ROOT/tools/.env.example"

if [ -f "$ENV_FILE" ]; then
  info "tools/.env already exists — leaving it unchanged."
else
  if [ -f "$ENV_EXAMPLE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    success "Created tools/.env from tools/.env.example."
    warn "Open tools/.env and add your GEMINI_API_KEY or PERPLEXITY_API_KEY to"
    warn "enable the AI Assistant tab.  Browsing and search work without a key."
  else
    warn "tools/.env.example not found — skipping .env creation."
  fi
fi

# ---------------------------------------------------------------------------
# 5. Auth reminder
# ---------------------------------------------------------------------------
if [ -z "${APP_USERNAME:-}" ] || [ -z "${APP_PASSWORD:-}" ]; then
  warn "No password is set.  The app will be accessible to anyone on your"
  warn "network.  To add a password, set APP_USERNAME and APP_PASSWORD before"
  warn "running this script, or export them in your shell:"
  warn "  export APP_USERNAME=registrar"
  warn "  export APP_PASSWORD=your-password"
  warn "This is strongly recommended if you plan to expose the app with ngrok."
fi

# ---------------------------------------------------------------------------
# 6. Start the app
# ---------------------------------------------------------------------------
PORT="${PORT:-5000}"

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
success "Setup complete.  Starting the web app on port ${PORT} …"
echo -e "   ${BOLD}Open in your browser:${RESET}  http://localhost:${PORT}"
echo -e "   Press ${BOLD}Ctrl+C${RESET} to stop."
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

export PORT
python3 "$REPO_ROOT/tools/app.py"
