# ⚙️ Setup & Workflow Guide

How to set up and use this repository with Google Drive on your work PC.

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