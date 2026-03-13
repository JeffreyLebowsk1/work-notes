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

## 🔒 Repository Privacy

This repository **must be kept private** at all times. It contains internal work notes that may include information subject to FERPA and other confidentiality requirements.

### How to Set the Repository to Private (Do This Now If It Isn't Already)

1. Go to the repository on GitHub: [https://github.com/JeffreyLebowsk1/work-notes](https://github.com/JeffreyLebowsk1/work-notes)
2. Click the **Settings** tab (top of the page, gear icon)
3. Scroll down to the **Danger Zone** section at the bottom of the page
4. Click **Change visibility**
5. Select **Make private**
6. Type the repository name (`JeffreyLebowsk1/work-notes`) to confirm
7. Click **I understand, change repository visibility**

> If you don't see the Settings tab, you may not have admin access to the repository. Contact the repository owner to make this change.

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
*Last updated: 2026-03-13*