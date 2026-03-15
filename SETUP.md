# ⚙️ Setup & Workflow Guide

How to set up and use this repository with Google Drive on your work PC, host the web app free online, and access it from any device — including Android.

---

## 🖥️ Prerequisites

### 1. Find Your Google Drive Folder
On your work PC, open **File Explorer** and look in the left sidebar for one of these:
- 📁 `Google Drive`
- 📁 `My Drive`
- 📁 A drive letter like `G:\` or `H:\` labeled "Google Drive"

> If you don't see it, check your system tray (bottom right of taskbar) for the Google Drive icon ☁️

---

### 2. Check if Git is Installed
1. Open **Command Prompt** (search "cmd" in the Start menu)
2. Type the following and hit Enter:
   ````
git --version
   ````
3. If you see a version number → ✅ already installed!
4. If not → download from **[git-scm.com/download/win](https://git-scm.com/download/win)**

---

## 🚀 First-Time Setup (Do This Once)

### Clone the Repo Into Google Drive

1. Open **Command Prompt**
2. Navigate to your Google Drive folder:
   ````
   cd "G:\My Drive"
   ````
   *(replace `G:\My Drive` with your actual Google Drive path)*
3. Clone the repository:
   ````
   git clone https://github.com/JeffreyLebowsk1/work-notes.git
   ````
4. You'll now have a `work-notes` folder inside Google Drive ✅

---

## 📋 Day-to-Day Workflow

```
Edit a file in the work-notes folder
        ↓
Google Drive syncs it automatically ☁️
        ↓
When ready, open Command Prompt and push to GitHub:

  cd "G:\My Drive\work-notes"
  git add .
  git commit -m "describe what you changed"
  git push
        ↓
GitHub is updated too ✅
```

---

## 🗒️ Quick Reference Cheat Sheet

| Action | Command |
|---|---|
| Go to your repo folder | `cd "G:\My Drive\work-notes"` |
| See what files have changed | `git status` |
| Stage all changes | `git add .` |
| Save changes with a message | `git commit -m "your message here"` |
| Push changes to GitHub | `git push` |
| Pull latest changes from GitHub | `git pull` |
| See recent commit history | `git log --oneline` |

---

## 💡 Tips for Good Commit Messages

Make your commit messages descriptive so you can find things later:

| ✅ Good | ❌ Not as helpful |
|---|---|
| `updated spring 2026 graduation checklist` | `update` |
| `added meeting notes from 2026-03-13` | `notes` |
| `added residency policy links to _links.md` | `links` |
| `ceremony day checklist - checked off 3 items` | `stuff` |

---

## ⚠️ Things to Watch Out For

- Always **finish your `git push`** before closing your laptop
- Don't edit the same file in two places at once (e.g., on your phone via Google Drive and on your PC via Git simultaneously)
- If you ever see a **merge conflict**, don't panic — message IT or come back here for help

---

## 🆘 Common Issues

### "Permission denied" when pushing
- Make sure you're logged into GitHub — run `git config --global user.email "your@email.com"` and `git config --global user.name "Your Name"`

### "Not a git repository" error
- You're probably not in the right folder — run `cd "G:\My Drive\work-notes"` first

### Google Drive is showing a sync error on the repo folder
- Wait for any `git` commands to finish before Drive syncs — they usually resolve on their own

### Web app shows `ERR_CONNECTION_TIMED_OUT` from another device
- The Linux firewall is blocking the port. Run `sudo ufw allow 4200/tcp && sudo ufw reload` on the machine running the app, then retry. See the **Troubleshooting (Linux web app)** section below for more detail.

---

## 🐧 Run the Web App Locally on Linux

Use these steps to clone the repo and launch the browser UI on any Linux machine (Ubuntu, Debian, Fedora, etc.) — no cloud hosting required.

> ⚡ **Shortcut — automated setup script:**
> Once you have the repo cloned, a single script handles everything below (venv, dependencies, `.env` scaffold, port check, and app launch):
> ```bash
> bash tools/linux-setup.sh              # default port 4200
> bash tools/linux-setup.sh --port 8080  # use a different port
> ```
> The manual steps are documented below if you prefer to run them yourself or need to troubleshoot.

---

### Prerequisites

- **Git** — check with `git --version`; install with `sudo apt-get install git` if missing
- **Python 3.10+** — check with `python3 --version`; install with `sudo apt-get install python3 python3-pip python3-venv` if missing

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/JeffreyLebowsk1/work-notes.git
cd work-notes
```

---

### Step 2 — Install dependencies

Using a **virtual environment** is recommended so the packages don't affect your system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/requirements-web.txt
```

> 💡 Skip the `venv` lines if you prefer to install globally — just run `pip install -r tools/requirements-web.txt` directly.

#### OCR support for scanned PDFs (optional)

The inbox processor can OCR scanned PDFs automatically, but this requires two **system packages** in addition to the Python dependencies above:

| Package | Purpose | Install |
|---|---|---|
| **Tesseract OCR** | Text recognition engine | `sudo apt install tesseract-ocr` (Linux) · `brew install tesseract` (macOS) |
| **Poppler** | PDF-to-image renderer | `sudo apt install poppler-utils` (Linux) · `brew install poppler` (macOS) |

Without these, the inbox processor still works — it just won't be able to read scanned/image-only pages. Digital-native PDFs always work with pypdf alone.

---

### Step 3 — (Optional) Configure an AI key

Browsing and search work without any API key. The **AI Assistant** tab requires one.

```bash
cp tools/.env.example tools/.env
# Open tools/.env in a text editor and add your key:
#   PERPLEXITY_API_KEY=...   or   GEMINI_API_KEY=...
```

Get an API key at <https://www.perplexity.ai/settings/api> (Perplexity) or <https://aistudio.google.com/app/apikey> (Gemini) — check each platform for current availability and pricing.

---

### Step 4 — Run the app

```bash
python3 tools/app.py
```

Then open **http://localhost:4200** in your browser.

> 💡 **Find your LAN IP:** run `hostname -I` and note the `192.168.x.x` address — that is the address other devices on the same network can use (see Step 5 below).

---

### Step 5 — (Optional) Allow access from other devices on your network

By default, Linux's firewall (`ufw`) blocks incoming connections on port 4200, so other machines on the same Wi-Fi or LAN will get `ERR_CONNECTION_TIMED_OUT` even though the app is running. Open the port to fix this:

```bash
sudo ufw allow 4200/tcp
sudo ufw reload
```

Then open **http://\<your-LAN-IP\>:4200** (e.g. `http://192.168.1.146:4200`) in a browser on any other device on the same network.

> ⚠️ Only do this on a trusted private network. When you no longer need remote access, close the port again:
> ```bash
> sudo ufw delete allow 4200/tcp && sudo ufw reload
> ```

> 💡 If `ufw` is not installed or is inactive (`sudo ufw status` shows `Status: inactive`), no firewall rule is needed — the port is already reachable on the LAN.

---

### Step 6 — (Optional) Set a password

If other users share your machine or network, protect the app with HTTP Basic Auth:

```bash
export APP_USERNAME=registrar
export APP_PASSWORD=choose-a-strong-password
python3 tools/app.py
```

The browser will prompt for the username and password before showing any notes.

---

### Step 7 — (Optional) Share publicly with ngrok

Use this when you need to reach the app from **outside your local network** (e.g. from a phone on mobile data, or a colleague on a different network). **ngrok** creates a temporary public `https://` URL that tunnels straight to your running app.

> ⚠️ **Always set `APP_USERNAME` and `APP_PASSWORD` before exposing the app publicly.** Without a password, anyone with the ngrok URL can read your notes.

**1. Install ngrok**

```bash
# Recommended — download the official binary:
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update && sudo apt install ngrok

# Alternative — Snap (Ubuntu/Debian with snapd):
sudo snap install ngrok
# ⚠️ After a snap install, log out and back in (or run `export PATH=$PATH:/snap/bin`)
# so the `ngrok` command is on your PATH.
```

**2. Authenticate ngrok** *(one-time setup — free account required)*

Sign up at <https://ngrok.com>, copy your authtoken from the dashboard, then run **one** of these:

```bash
# Option A — save permanently to ngrok's config file:
ngrok config add-authtoken <YOUR_AUTHTOKEN>

# Option B — set as an environment variable (for this shell session only):
export NGROK_AUTHTOKEN=<YOUR_AUTHTOKEN>
```

> 💡 The environment variable is named **`NGROK_AUTHTOKEN`** (no underscore between AUTH and TOKEN).

**3. Start the app with a password and open the ngrok tunnel — one command**

```bash
APP_USERNAME=registrar APP_PASSWORD=choose-a-strong-password \
  bash tools/linux-setup.sh --ngrok
```

The script starts the web app in the background and then runs `ngrok http 4200` in the foreground. ngrok prints a public URL like `https://abc123.ngrok-free.app` — open that link in any browser on any device.

> 💡 **Manual alternative:** If you prefer two separate terminals, start the app first, then run `ngrok http 4200` in a second terminal.

```bash
# Terminal 1
APP_USERNAME=registrar APP_PASSWORD=choose-a-strong-password python3 tools/app.py

# Terminal 2
ngrok http 4200
```

> 💡 **The URL changes every time** you restart ngrok on the free plan. Upgrade to a paid plan for a stable custom subdomain — check current pricing at <https://ngrok.com/pricing>.

> 💡 **Free-tier browser warning:** ngrok may show a "You are about to visit…" interstitial page on the first visit. Click **Visit Site** to continue. This does not appear for the app owner when using the ngrok dashboard.

---

### Quick Reference (Linux local)

| Goal | Command |
|---|---|
| Activate the virtual environment | `source .venv/bin/activate` |
| Start the app (default port 4200) | `python3 tools/app.py` |
| Start on a different port | `bash tools/linux-setup.sh --port 8080` |
| Run setup script (default port) | `bash tools/linux-setup.sh` |
| Run setup script on a different port | `bash tools/linux-setup.sh --port 8080` |
| Start with password protection | `APP_USERNAME=registrar APP_PASSWORD=secret bash tools/linux-setup.sh` |
| Find your LAN IP | `hostname -I` |
| Allow LAN access through firewall | `sudo ufw allow 4200/tcp && sudo ufw reload` |
| Remove LAN firewall rule | `sudo ufw delete allow 4200/tcp && sudo ufw reload` |
| Pull latest notes from GitHub | `git pull` |
| Stop the app | Press `Ctrl+C` in the terminal |
| Expose publicly via ngrok (one command) | `APP_USERNAME=registrar APP_PASSWORD=secret bash tools/linux-setup.sh --ngrok` |
| Expose publicly via ngrok (manual) | `ngrok http 4200` *(app must already be running)* |

---

### Troubleshooting (Linux web app)

**`ERR_CONNECTION_TIMED_OUT` when accessing from another machine on the same network**
The app is running but the Linux firewall is blocking the port. Fix:
```bash
sudo ufw allow 4200/tcp
sudo ufw reload
```
Then try `http://<your-LAN-IP>:4200` again. Find your LAN IP with `hostname -I`.

**`ngrok: command not found` after `snap install ngrok`**
The snap bin directory may not be on your PATH yet. Fix:
```bash
export PATH=$PATH:/snap/bin
```
Add that line to `~/.bashrc` to make it permanent, or log out and back in.

**`ngrok` exits immediately with "authentication failed" or "Your account is not authorized"`**
Every ngrok account (including free) requires an authtoken. Run:
```bash
ngrok config add-authtoken <YOUR_AUTHTOKEN>
# or:  export NGROK_AUTHTOKEN=<YOUR_AUTHTOKEN>
```
Get your token at <https://dashboard.ngrok.com/get-started/your-authtoken>.

**ngrok shows a browser warning page ("You are about to visit…")**
This is ngrok's free-tier interstitial. Click **Visit Site** to continue — it only appears once per browser session. It does not affect the app itself.

---

## 🐧 Linux / Jetson Orin Nano Setup (Automatic Sync)

Use your home Jetson Orin Nano (or any Linux machine) to keep the repo in sync
with your work Google Drive folder automatically — no manual `git push` required.

---

### Overview

```
Google Drive (work PC)
        ↓  syncs via Google Drive desktop app
Google Drive cloud
        ↓  rclone mounts the drive
~/gdrive/work-notes  (on your Jetson)
        ↓  inotifywait detects new / changed files
auto-sync.sh commits + pushes to GitHub automatically ✅
```

---

### Step 1 — Install dependencies

```bash
sudo apt-get update
sudo apt-get install -y git inotify-tools
```

Install **rclone** (the recommended tool for mounting Google Drive on Linux):

```bash
sudo -v && curl https://rclone.org/install.sh | sudo bash
```

---

### Step 2 — Authenticate rclone with Google Drive

```bash
rclone config
```

Follow the interactive prompts:

1. Press `n` to create a **new remote**
2. Name it `gdrive`
3. Choose **Google Drive** as the storage type
4. Leave Client ID and Client Secret blank (use the defaults)
5. Choose scope **1** (full access to all files)
6. Complete the browser-based OAuth flow (you may need to copy the URL to a desktop browser if the Jetson has no display)
7. Answer `n` when asked if this is a team drive

Test it:

```bash
rclone ls gdrive:
```

---

### Step 3 — Mount Google Drive and clone the repo

Create a local mount point:

```bash
mkdir -p ~/gdrive
```

Mount Google Drive (add `--daemon` to run in the background):

```bash
rclone mount gdrive: ~/gdrive --vfs-cache-mode writes --daemon
```

> 💡 **To mount automatically on login**, add the command above to `~/.bashrc` or
> create a systemd user service for rclone (see the rclone docs).

Clone the repo **inside the mount**:

```bash
cd ~/gdrive
git clone https://github.com/JeffreyLebowsk1/work-notes.git
```

You should now see `~/gdrive/work-notes/` with all the repository files.

---

### Step 4 — Configure Git credentials

The auto-sync script pushes to GitHub on your behalf.  Set up a **Personal
Access Token (PAT)** so it can authenticate without a password prompt:

1. Go to <https://github.com/settings/tokens> → **Generate new token (classic)**
2. Give it a name (e.g. `jetson-auto-sync`) and enable the **repo** scope
3. Copy the token

Store it as your Git credential on the Jetson:

```bash
git config --global credential.helper store
cd ~/gdrive/work-notes
git pull   # enter your GitHub username and the token when prompted — stored for future use
```

---

### Step 5 — Install and enable the auto-sync service

Make the script executable:

```bash
chmod +x ~/gdrive/work-notes/tools/auto-sync.sh
```

Copy the systemd service file and **edit the three paths** inside it:

```bash
mkdir -p ~/.config/systemd/user
cp ~/gdrive/work-notes/tools/auto-sync.service ~/.config/systemd/user/auto-sync.service
nano ~/.config/systemd/user/auto-sync.service
```

Change every occurrence of `/home/YOUR_USERNAME/gdrive/work-notes` to your actual
path (e.g. `/home/jetson/gdrive/work-notes`).

Enable and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now auto-sync.service
```

Check that it is running:

```bash
systemctl --user status auto-sync.service
```

Follow live logs:

```bash
journalctl --user -u auto-sync.service -f
```

---

### How it works after setup

1. You add or edit a file in the `work-notes` folder on your **work PC**
2. Google Drive syncs the change to the cloud ☁️
3. rclone reflects the change in `~/gdrive/work-notes` on the **Jetson**
4. `auto-sync.sh` detects the change via `inotifywait` and, after a short
   debounce window, runs:
   ```
   git pull --rebase
   git add -A
   git commit -m "auto: sync from Google Drive — <changed files>"
   git push
   ```
5. GitHub is updated automatically ✅

---

### Optional — Tune the debounce delay

By default the script waits **5 seconds** after the last detected change before
committing.  To change it, edit the service file:

```ini
Environment=DEBOUNCE_SECONDS=10
```

Then reload the service:

```bash
systemctl --user daemon-reload && systemctl --user restart auto-sync.service
```

---

### Troubleshooting

| Problem | Solution |
|---|---|
| `inotifywait not found` | `sudo apt-get install inotify-tools` |
| `git push` asks for a password | Re-run `git pull` inside the repo and re-enter your token |
| Service stops after a reboot | Run `loginctl enable-linger $USER` so user services start without a login session |
| rclone mount disappears after reboot | Add `rclone mount gdrive: ~/gdrive --vfs-cache-mode writes --daemon` to a `@reboot` cron entry or a systemd service |
| Changes not detected | Make sure the rclone mount VFS cache is flushing — use `--vfs-cache-mode writes` or `full` |

---

## 📱 Android Setup

Access your work notes on your Android phone or tablet. Three options are available depending on how much you need to do.

---

### Option A — GitHub Mobile App (Read-Only Browsing — Easiest)

Best for quickly looking up a note when you're away from your desk. No extra setup needed beyond a GitHub account.

1. Install the **[GitHub](https://play.google.com/store/apps/details?id=com.github.android)** app from the Google Play Store.
2. Sign in with your GitHub account.
3. Open the **JeffreyLebowsk1/work-notes** repository.
4. Browse and read any `.md` file directly in the app.

> ⚠️ The GitHub app is **read-only** for viewing files — you cannot commit or push changes from it.

---

### Option B — Google Drive App (View & Edit Synced Files)

If you already use Google Drive to sync this repo from your work PC (see [Day-to-Day Workflow](#-day-to-day-workflow) above), the files are already on your Drive. You can read and even edit them from your phone.

1. Install the **[Google Drive](https://play.google.com/store/apps/details?id=com.google.android.apps.docs)** app from the Google Play Store (usually pre-installed).
2. Open the app and navigate to the `work-notes` folder inside **My Drive**.
3. Tap any `.md` file to preview it.
4. To edit, tap the three-dot menu → **Open with** → choose a plain-text or Markdown editor (e.g. **[Markor](https://play.google.com/store/apps/details?id=net.gsantner.markor)**).

> 💡 Edits saved in Google Drive will sync back to your work PC automatically. From there, the Jetson auto-sync service (if enabled) will push the changes to GitHub.

---

### Option C — Termux (Full Git Workflow — Most Powerful)

For committing and pushing changes directly from your Android device.

1. Install **[Termux](https://f-droid.org/en/packages/com.termux/)** from **F-Droid** (recommended) or the Google Play Store.

   > ⚠️ The Play Store version of Termux is outdated. Use the **F-Droid** version for the most up-to-date packages.

2. Open Termux and install Git:

   ```bash
   pkg update && pkg upgrade -y
   pkg install git -y
   ```

3. Set up your Git identity:

   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```

4. Clone the repository:

   ```bash
   mkdir -p ~/storage/shared && termux-setup-storage
   cd ~
   git clone https://github.com/JeffreyLebowsk1/work-notes.git
   ```

5. Configure a **Personal Access Token (PAT)** so you can push without a password prompt (see [Step 4 of the Linux setup](#step-4--configure-git-credentials) for how to create a PAT):

   ```bash
   git config --global credential.helper store
   cd ~/work-notes
   git pull   # enter your GitHub username and PAT when prompted
   ```

After that, the day-to-day workflow is the same as on any other machine:

```bash
cd ~/work-notes
git add .
git commit -m "describe what you changed"
git push
```

---

### Troubleshooting (Android)

| Problem | Solution |
|---|---|
| Can't find the repo in the GitHub app | Make sure you are signed in with the correct GitHub account |
| `.md` files open as a download instead of previewing in Drive | Tap **Open with** and choose a text/Markdown editor app |
| `pkg: command not found` in Termux | Termux environment is not set up — run `pkg update` first |
| `git push` fails with "Authentication failed" | Re-run `git pull` inside the repo and re-enter your PAT |
| Termux can't access internal storage | Run `termux-setup-storage` and grant the permission in the system prompt |

---

## 🌐 Hosting the Web App (Free — Access From Any Browser)

The **CCCC Notes web app** can be hosted for free on [Render.com](https://render.com) so you can open it in any browser — your work PC, a tablet, a phone, or any computer — without running Python locally. Every time you push notes to GitHub, the hosted app updates automatically.

> ⚠️ **Always set a password before hosting.** The app contains internal CCCC work notes. Without authentication, anyone with the URL could read them.

---

### Step 1 — Make Your GitHub Repo Private (Recommended)

Before hosting publicly, make sure the repository is **private**:

1. Go to your repo on GitHub → **Settings** → scroll to **Danger Zone**
2. Click **Change repository visibility** → **Make private**

---

### Step 2 — Set a Password on the App

The app supports HTTP Basic Auth — a simple username/password prompt in the browser.

Set these two environment variables wherever you host the app (see Step 3):

| Variable | Example value |
|---|---|
| `APP_USERNAME` | `registrar` |
| `APP_PASSWORD` | `choose-a-strong-password` |

Leave both blank only for local use on your own machine.

---

### Step 3 — Deploy to Render.com (Free)

A `render.yaml` file is already included in the repo. Render reads it automatically.

1. Go to **[render.com](https://render.com)** and sign in with your GitHub account (free)
2. Click **New** → **Blueprint**
3. Connect your **JeffreyLebowsk1/work-notes** repository
4. Render detects `render.yaml` and pre-fills the settings — click **Apply**
5. Before the first deploy finishes, go to your new service → **Environment**
6. Add the following environment variables:

   | Key | Value |
   |---|---|
   | `APP_USERNAME` | your chosen username |
   | `APP_PASSWORD` | your chosen password |
   | `GEMINI_API_KEY` | *(optional)* your Gemini key to enable the AI assistant |

7. Click **Save Changes** — the service restarts and is live ✅

Your app will be at a URL like `https://cccc-notes.onrender.com`.

> 💡 **Free tier note:** Render's free web services spin down after 15 minutes of inactivity and take ~30 seconds to wake up on the next visit. This is fine for occasional reference use. Upgrade to a paid plan ($7/month) for instant response.

---

### Step 4 — Auto-Deploy on Every Git Push

Once hosted, every `git push` to GitHub automatically triggers a new deploy on Render. Your notes are always up to date within a minute or two of pushing.

```
Edit a note on your PC
        ↓
git add . && git commit -m "updated checklist" && git push
        ↓
Render detects the push → redeploys automatically (~60 sec)
        ↓
Open your app URL in any browser — notes are updated ✅
```

---

### Accessing From Android

Once hosted, open the app URL in **Chrome on Android** and tap:

**⋮ menu → Add to Home screen**

This installs it as a home screen icon that opens full-screen, just like a native app — no App Store needed.

---

### Alternative: Run in GitHub Codespaces (No Hosting Needed)

GitHub Codespaces gives you a browser-based Linux environment — free for 60 hours/month.

1. Go to your repo on GitHub → green **Code** button → **Codespaces** tab → **Create codespace**
2. In the terminal that opens:
   ```bash
   pip install -r tools/requirements-web.txt
   python tools/app.py
   ```
3. GitHub shows a popup: **Open in Browser** — click it
4. The app runs at a temporary `https://` URL, accessible only while the codespace is open

---

## 📁 Repo Structure Reference

```
work-notes/
├── SETUP.md                  ← You are here!
├── README.md                 ← Home page / table of contents
├── _links.md                 ← All important links in one place
├── transcripts/              ← Transcript processing notes
├── residency-tuition/        ← Residency & tuition policies
├── admissions/               ← Admissions notes
├── personal-data/            ← FERPA & data handling
├── graduation/               ← Graduation coordination hub 🎓
│   ├── ceremonies/
│   ├── checklists/
│   ├── timelines/
│   ├── student-tracking/
│   ├── communications/
│   └── assets/
├── meetings/                 ← Meeting notes by date
├── daily-logs/               ← Day-to-day logs
└── assets/                   ← Shared images, spreadsheets, files
```

---
*Last updated: 2026-03-14*