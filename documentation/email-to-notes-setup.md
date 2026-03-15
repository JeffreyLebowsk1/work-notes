# 📧 Email-to-Notes Setup (Gmail Label Workflow)

How to flag emails in Gmail with a label and import them as notes in the work-notes app.

---

## How It Works

1. You apply a **"Work-Notes"** label to any email in Gmail.
2. The app connects via IMAP and fetches **only** emails with that label.
3. You review the messages in the web UI, edit content (scrub PII / FERPA data), choose the destination folder, and approve.
4. Approved messages are saved as markdown notes in the repo.

---

## Step 1 — Create the Gmail Label

1. Open **Gmail** in your browser ([mail.google.com](https://mail.google.com)).
2. In the left sidebar, scroll down and click **"+ Create new label"**.
   - If you don't see the option, click the **⋮ More** link at the bottom of the sidebar to expand it.
3. Type **`Work-Notes`** (exactly — capital W, capital N, hyphen in the middle).
4. Leave "Nest label under" empty — it should be a top-level label.
5. Click **Create**.

The label now appears in your sidebar. You can also assign a color to it for quick visual identification:
- Right-click the label → **Label color** → pick a color (green is a good choice).

---

## Step 2 — Enable IMAP Access in Gmail

IMAP must be enabled for the app to connect.

1. In Gmail, click the **⚙️ gear icon** (top-right) → **See all settings**.
2. Go to the **Forwarding and POP/IMAP** tab.
3. Under **IMAP access**, select **Enable IMAP**.
4. Click **Save Changes** at the bottom.

---

## Step 3 — Generate a Google App Password

Gmail requires an **App Password** instead of your regular password when IMAP clients connect. This requires 2-Step Verification to be enabled on your Google account.

### Enable 2-Step Verification (if not already on)

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security).
2. Under **"How you sign in to Google"**, click **2-Step Verification**.
3. Follow the prompts to set it up (you'll need your phone).

### Generate the App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
   - If you don't see this page, make sure 2-Step Verification is enabled first.
2. In the **"App name"** field, type **`work-notes`** (this is just a label for your reference).
3. Click **Create**.
4. Google will show a **16-character password** (formatted as four groups of four letters, e.g. `abcd efgh ijkl mnop`).
5. **Copy this password** — you'll need it in the next step. You won't be able to see it again.

> **Important:** Use the 16-character app password in your `.env` file, NOT your regular Gmail password. Remove the spaces — enter it as one continuous string (e.g. `abcdefghijklmnop`).

---

## Step 4 — Configure the `.env` File

Edit `tools/.env` on the server and add these variables:

```
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_ADDRESS=mdilw269@cccc.edu
EMAIL_PASSWORD=abcdefghijklmnop
EMAIL_FOLDER=Work-Notes
EMAIL_ALLOWED_SENDERS=
```

| Variable | Value | Notes |
|----------|-------|-------|
| `EMAIL_IMAP_HOST` | `imap.gmail.com` | Always this for Gmail / Google Workspace |
| `EMAIL_IMAP_PORT` | `993` | Standard IMAPS port (SSL) |
| `EMAIL_ADDRESS` | `mdilw269@cccc.edu` | The account to connect as |
| `EMAIL_PASSWORD` | The 16-char app password | From Step 3 — no spaces |
| `EMAIL_FOLDER` | `Work-Notes` | Must match the label name exactly (case-sensitive) |
| `EMAIL_ALLOWED_SENDERS` | *(blank or comma-separated)* | Leave blank to accept all senders. Set to e.g. `boss@cccc.edu,dean@cccc.edu` to only import from specific people. |

---

## Step 5 — Restart the Service

After editing `.env`, restart the web app so it picks up the new config:

```bash
ssh madmatter-lan "systemctl --user restart work-notes-web"
```

---

## Day-to-Day Usage

### Flagging an email for import

- **Desktop (Gmail web):** Open or select the email → click the **Labels** button (tag icon, 🏷️) → check **Work-Notes** → click **Apply**.
- **Mobile (Gmail app):** Open the email → tap **⋮** (three dots, top-right) → **Label** → check **Work-Notes** → tap **OK**.
- **Keyboard shortcut (web):** Select the email and press **`l`** (lowercase L) to open the label picker, type `Work`, select **Work-Notes**, press **Enter**.

### Importing flagged emails

Open the web app and go to the **Email Inbox** page. Flagged emails appear in a batch list — review, edit, and approve the ones you want to save.

---

## Optional: Auto-Label with a Gmail Filter

If you want certain emails to be auto-labeled (e.g., everything from a specific sender):

1. In Gmail, click the **search options** icon (▼) in the search bar.
2. Fill in criteria (e.g., **From:** `dean@cccc.edu`, **Subject:** `registrar update`).
3. Click **Create filter**.
4. Check **Apply the label** → select **Work-Notes**.
5. Optionally check **Also apply filter to matching conversations** to label existing emails.
6. Click **Create filter**.

---

## Subject-Line Tags for Folder Routing

When composing or forwarding an email to yourself, add a `[tag]` prefix to the subject line to control which folder the note is filed into:

| Tag | Destination folder |
|-----|--------------------|
| `[daily]` or `[log]` | `daily-logs/` |
| `[meeting]` | `meetings/` |
| `[update]` | `updates/` |
| `[graduation]` | `graduation/` |
| `[admissions]` | `admissions/` |
| `[transcript]` | `transcripts/` |
| `[residency]` | `residency-tuition/` |
| `[ce]` | `continuing-education/` |
| `[financial]` | `financial-aid/` |
| `[ferpa]` | `personal-data/` |

**Example:** An email with subject `[meeting] Advising Policy Discussion` routes to `meetings/`. Without a tag, the system uses keyword-based detection (same logic as the `import` command).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Email is not configured" | Make sure `EMAIL_IMAP_HOST`, `EMAIL_ADDRESS`, and `EMAIL_PASSWORD` are all set in `tools/.env`. Restart the service after editing. |
| "Failed to connect" / authentication error | Double-check the app password (no spaces). Make sure IMAP is enabled in Gmail settings. If using `@cccc.edu` via Google Workspace, your admin may need to allow app passwords. |
| No messages found | Make sure you applied the **Work-Notes** label to at least one email. Check that `EMAIL_FOLDER` in `.env` matches the label name exactly (case-sensitive). |
| Messages from some senders missing | If `EMAIL_ALLOWED_SENDERS` is set, only those addresses are fetched. Clear it or add the missing sender. |
| Label doesn't appear in IMAP | In rare cases, go to Gmail Settings → **Labels** tab and make sure "Show in IMAP" is checked for the Work-Notes label. |
