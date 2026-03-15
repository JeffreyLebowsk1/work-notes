#!/usr/bin/env bash
# linux-setup.sh — One-shot setup and launch for the CCCC Notes web app on Linux.
#
# Run this script from the repository root:
#   bash tools/linux-setup.sh
#   bash tools/linux-setup.sh --port 8080
#   bash tools/linux-setup.sh --ngrok
#
# What it does:
#   1. Verifies prerequisites (Python 3.10+, pip, git)
#   2. Creates a Python virtual environment at .venv/ (skipped if it already exists)
#   3. Installs all Python dependencies from tools/requirements-web.txt
#   4. Scaffolds tools/.env from tools/.env.example (skipped if it already exists)
#   5. Checks that the chosen port is free
#   6. Starts the web app at http://localhost:<PORT>
#   7. (--ngrok only) Runs `ngrok http <PORT>` to create a public HTTPS tunnel
#
# Options:
#   --port PORT, -p PORT   Port to run the web app on (default: 4200)
#   --ngrok                After starting the app, expose it via ngrok on the same port
#   --help, -h             Show this help message
#
# Environment variables (alternative to flags):
#   APP_USERNAME   — set a login username (recommended for shared/public machines)
#   APP_PASSWORD   — set a login password (required when using ngrok or Render)
#   PORT           — override the default port (default: 4200; --port takes precedence)
#
# Examples:
#   bash tools/linux-setup.sh
#   bash tools/linux-setup.sh --port 8080
#   bash tools/linux-setup.sh --ngrok
#   APP_USERNAME=registrar APP_PASSWORD=secret bash tools/linux-setup.sh --ngrok
#   APP_USERNAME=registrar APP_PASSWORD=secret bash tools/linux-setup.sh --port 8080
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
# Parse CLI arguments
# ---------------------------------------------------------------------------
PORT="${PORT:-4200}"  # default; can be overridden by env var or --port flag
USE_NGROK=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --port|-p)
      if [[ -z "${2:-}" || ! "${2}" =~ ^[0-9]+$ ]]; then
        error "--port requires a numeric argument (e.g. --port 8080)"
        exit 1
      fi
      PORT="$2"
      shift 2
      ;;
    --ngrok)
      USE_NGROK=1
      shift
      ;;
    --help|-h)
      echo "Usage: bash tools/linux-setup.sh [--port PORT] [--ngrok]"
      echo ""
      echo "Options:"
      echo "  --port PORT, -p PORT   Port to run the web app on (default: 4200)"
      echo "  --ngrok                Expose the app publicly via ngrok after starting"
      echo "  --help, -h             Show this help message"
      exit 0
      ;;
    *)
      error "Unknown argument: $1"
      echo "Usage: bash tools/linux-setup.sh [--port PORT] [--ngrok]" >&2
      exit 1
      ;;
  esac
done

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
# 5a. Check ngrok prerequisites (only when --ngrok was passed)
# ---------------------------------------------------------------------------
if [ "$USE_NGROK" -eq 1 ]; then
  if ! command -v ngrok &>/dev/null; then
    error "ngrok is not installed (or not on your PATH)."
    error "Install it with one of the following:"
    error "  curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \\"
    error "    | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \\"
    error "    && echo \"deb https://ngrok-agent.s3.amazonaws.com buster main\" \\"
    error "    | sudo tee /etc/apt/sources.list.d/ngrok.list \\"
    error "    && sudo apt update && sudo apt install ngrok"
    error "  # or:  sudo snap install ngrok"
    error "See SETUP.md Step 7 for full instructions."
    exit 1
  fi
  success "ngrok $(ngrok version 2>/dev/null | head -1)"

  if [ -z "${APP_USERNAME:-}" ] || [ -z "${APP_PASSWORD:-}" ]; then
    warn "⚠️  No APP_USERNAME/APP_PASSWORD set — your notes will be publicly"
    warn "   readable once the ngrok tunnel is open.  Set them before continuing:"
    warn "     export APP_USERNAME=registrar"
    warn "     export APP_PASSWORD=choose-a-strong-password"
  fi
fi

# ---------------------------------------------------------------------------
# 6. Check the chosen port is not already in use
# ---------------------------------------------------------------------------
port_in_use() {
  # Try ss first (iproute2, available on all modern Linux distros),
  # then fall back to lsof (installed on many systems but not all).
  if command -v ss &>/dev/null; then
    ss -tlnp 2>/dev/null | awk '{print $4}' | grep -qE ":${PORT}$"
  elif command -v lsof &>/dev/null; then
    lsof -ti ":${PORT}" &>/dev/null
  else
    return 1  # can't tell — let Flask try
  fi
}

if port_in_use; then
  error "Port ${PORT} is already in use by another process."
  error "Choose a free port with the --port flag, for example:"
  error "  bash tools/linux-setup.sh --port 8080"
  exit 1
fi

# ---------------------------------------------------------------------------
# 7. Start the app (and optionally ngrok)
# ---------------------------------------------------------------------------

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
success "Setup complete.  Starting the web app on port ${PORT} …"
echo -e "   ${BOLD}Local:${RESET}              http://localhost:${PORT}"

# Show the LAN IP so the user knows the address to share on the local network.
LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -n "$LAN_IP" ]; then
  echo -e "   ${BOLD}On your network:${RESET}    http://${LAN_IP}:${PORT}"
fi

if [ "$USE_NGROK" -eq 1 ]; then
  echo -e "   ${BOLD}ngrok:${RESET}              tunnel will open after the app starts"
fi

echo -e "   Press ${BOLD}Ctrl+C${RESET} to stop."
echo ""

# If ufw is installed and active, check whether the chosen port is allowed.
if command -v ufw &>/dev/null; then
  UFW_STATUS=$(sudo ufw status 2>/dev/null || true)
  if echo "$UFW_STATUS" | grep -q "Status: active"; then
    if ! echo "$UFW_STATUS" | grep -qE "^${PORT}[^0-9]"; then
      warn "ufw firewall is active and port ${PORT} is not open."
      warn "Other devices on your network will see ERR_CONNECTION_TIMED_OUT."
      warn "To allow LAN access:  sudo ufw allow ${PORT}/tcp && sudo ufw reload"
    fi
  fi
fi

echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

export PORT
if [ "$USE_NGROK" -eq 1 ]; then
  # Start the Flask app in the background, then bring ngrok to the foreground
  # so that Ctrl+C stops ngrok first; the app is then cleaned up on EXIT.
  python3 "$REPO_ROOT/tools/app.py" &
  APP_PID=$!
  # Wait until Flask is actually listening on PORT (up to 15 s) before tunnelling.
  WAITED=0
  until ss -tlnp 2>/dev/null | awk '{print $4}' | grep -qE ":${PORT}$" || \
        lsof -ti ":${PORT}" &>/dev/null 2>&1; do
    sleep 1
    WAITED=$((WAITED + 1))
    if [ "$WAITED" -ge 15 ]; then
      error "Flask did not start within 15 seconds — aborting ngrok."
      kill "$APP_PID" 2>/dev/null || true
      exit 1
    fi
  done
  # Trap Ctrl+C / EXIT so the background Flask process is always cleaned up.
  cleanup() {
    kill "$APP_PID" 2>/dev/null || true
    wait "$APP_PID" 2>/dev/null || true
  }
  trap cleanup EXIT INT TERM
  # Kill any existing ngrok sessions to avoid ERR_NGROK_3200 (free-tier cap).
  EXISTING_NGROK_PIDS=$(pgrep -x ngrok 2>/dev/null || true)
  if [ -n "$EXISTING_NGROK_PIDS" ]; then
    info "Stopping existing ngrok session(s) to free up agent slots …"
    for pid in $EXISTING_NGROK_PIDS; do
      kill "$pid" 2>/dev/null || true
    done
    sleep 1
  fi
  info "Starting ngrok tunnel on port ${PORT} …"
  ngrok http "${PORT}"
else
  python3 "$REPO_ROOT/tools/app.py"
fi
