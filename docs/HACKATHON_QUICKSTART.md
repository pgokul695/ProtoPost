<!-- Last updated: February 2026 -->
[← Back to README](../README.md)

# 🚀 Hackathon Quick Start — Email Working in 5 Minutes

No backstory. No theory. Pick your path and follow the steps.

---

## Pick your path

```
Not sure which to pick? Use this:

Just testing / don't want to spam anyone  →  Path A (Sandbox)    ← 2 min
Need real email delivery (and have a domain), have 5 min      →  Path B (Resend)     ← recommended for people with a domain
Already have a Gmail account              →  Path C (Gmail) ← recommended for people not having domain
Don't want to install Python              →  Path D (Docker)     ← 1 min
Need a shared URL for the whole team      →  Path E (Render / Railway)  ← 5 min
```

---

## Path A — Testing without real sends (2 minutes)

### Step 1 — Start the server

```bash
uvicorn backend.main:app --reload --port 8000
```

### Step 2 — Open the dashboard

Go to **http://localhost:8000**

### Step 3 — Turn on Sandbox Mode

Click the **Sandbox Mode** toggle in the top-right of the header bar.

**Done.** Your app can now call `POST /api/send` and it will work. Emails are captured in the Outbox tab, not sent. Nothing needs a provider configured.

> [!TIP]
> Sandbox Mode returns HTTP 200 just like a real send. Your app doesn't need special error handling. Test everything normally.

---

## Path B — Real email via Resend (5 minutes)

### Step 1 — Create a free Resend account (1 min)

Go to [resend.com/signup](https://resend.com/signup). No credit card needed.

### Step 2 — Get an API key (1 min)

In your Resend dashboard → **API Keys** → **Create API Key**

- Name: `Email Gateway`
- Permission: Full Access

Copy the key — it starts with `re_` and is only shown once.

### Step 3 — Add the provider in ProtoPost (1 min)

1. Open **http://localhost:8000** (start the server first if it's not running)
2. Click **Providers** tab → **Add Provider**
3. Select **Resend API** from the type dropdown
4. Click **Start Setup Guide** for a step-by-step walkthrough, or click **Skip — I have my key** to paste directly
5. Enter a name, paste your API key, click **Add Provider**

### Step 4 — Send a test email (30 sec)

1. Click the **Test Send** tab in the dashboard
2. Fill in a recipient, subject, and message
3. Click **Send Test Email**

### Step 5 — Check your inbox (30 sec)

The email should arrive within 10–30 seconds.

> [!NOTE]
> If you don't have a custom domain, use `onboarding@resend.dev` as the **From** address in your app. You can only send to email addresses you've verified in your Resend account with this address, but it works immediately without DNS setup.

---

## Path C — Real email via Gmail (5 minutes)

### Step 1 — Enable 2-Step Verification on your Google Account (2 min)

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Find **"2-Step Verification"** and turn it on
3. Verify your phone number when prompted

### Step 2 — Create an App Password (1 min)

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Type `Email Gateway` in the **App name** field
3. Click **Create**
4. Copy the 16-character password Google shows you

### Step 3 — Add the provider in ProtoPost (1 min)

1. Open **http://localhost:8000**
2. Click **Providers** tab → **Add Provider**
3. Select **Gmail App Password** from the type dropdown
4. Click **Start Setup Guide** to follow the built-in walkthrough, or skip to paste directly
5. Enter your Gmail address and the 16-character App Password
6. Click **Add Provider**

### Step 4 — Send a test and check your inbox (1 min)

Use the **Test Send** tab. Set the `from` address to your Gmail address.

---

## Path D — Docker (1 minute, no Python needed)

If you have Docker installed and don't want to deal with Python environments, this is the fastest path to a running server.

### Step 1 — Build and start

```bash
docker compose up -d
```

### Step 2 — Open the dashboard

Visit **http://localhost:8000** — the dashboard is ready.

Provider config and email logs are saved in a Docker volume and survive restarts.

➜ Full Docker reference: [docs/DOCKER.md](DOCKER.md)

---

## Path E — Render / Railway (5 minutes, shared team URL + persistent storage)

Use this if you want the whole team to share one ProtoPost URL with provider config and logs that stick around permanently. Both platforms work identically for ProtoPost — pick whichever you prefer. Full guides: [docs/RENDER.md](RENDER.md) · [docs/RAILWAY.md](RAILWAY.md) · [docs/HOSTING.md](HOSTING.md)

### Step 1 — Push your code to GitHub

```bash
git add . && git commit -m "deploy" && git push
```

### Step 2 — Create a Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Set **Runtime** to **Docker**, leave everything else as default
4. Click **Deploy Web Service**

### Step 3 — Add a persistent disk

1. In the service page, click **Disks → Add Disk**
2. Set **Mount Path** to `/data`, size to `1 GB`
3. Click **Save** (Render redeploys automatically)

### Step 4 — Set environment variables

In **Environment**, add:
- `CONFIG_PATH` = `/data/config.json`
- `DB_PATH` = `/data/emails.db`
- `AUTH_TOKEN` = any secret string — **recommended** to protect your public URL

> [!TIP]
> Generate a token: `openssl rand -hex 16`. Enter it in the dashboard 🔓 lock icon on first visit — it's stored automatically.

Click **Save Changes**.

### Step 5 — Open the dashboard and add a provider

Render gives you a URL like `https://protopost.onrender.com`. Open it, add your provider under **Providers**, and send a test via **Test Send**. Config is saved to the persistent disk and survives every future redeploy.

➜ Full Render reference: [docs/RENDER.md](RENDER.md)

---

## Integrate with your app — minimum code

Replace `http://localhost:8000/api/send` with your server URL if different.

> [!NOTE]
> **Using AUTH_TOKEN?** Add `Authorization: Bearer <your-token>` to every request. See examples below and [docs/API.md](API.md#authentication) for full details.

### Python

```python
import requests

def send_email(to: str, subject: str, body: str) -> None:
    requests.post("http://localhost:8000/api/send",
        headers={"Authorization": "Bearer YOUR_TOKEN"},  # omit if AUTH_TOKEN not set
        json={
            "from": "you@example.com",
            "to": [to],
            "subject": subject,
            "body_text": body,
        }
    ).raise_for_status()
```

### JavaScript

```javascript
async function sendEmail(to, subject, body) {
    const res = await fetch("http://localhost:8000/api/send", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_TOKEN",  // omit if AUTH_TOKEN not set
        },
        body: JSON.stringify({ from: "you@example.com", to: [to], subject, body_text: body }),
    });
    if (!res.ok) throw new Error(await res.text());
}
```

### Node.js

```javascript
const axios = require("axios");

const sendEmail = (to, subject, body) =>
    axios.post("http://localhost:8000/api/send", {
        from: "you@example.com",
        to: [to],
        subject,
        body_text: body,
    }, {
        headers: { "Authorization": "Bearer YOUR_TOKEN" },  // omit if AUTH_TOKEN not set
    });
```

---

## Verify it's working

After sending a test email:

1. Open **http://localhost:8000**
2. Click **Outbox & Logs**
3. Your email should appear at the top

Check the **Status** column:
- `success` — Email was sent via a real provider ✓
- `sandbox` — Email was captured (Sandbox Mode is on)
- `failed` — Something went wrong — click **View** for details

---

## ✅ Demo Day Checklist

Run through this before you present:

- [ ] Sandbox Mode is **OFF** (header toggle is grey/off)
- [ ] At least one provider is configured and enabled
- [ ] Test email sent via the **Test Send** tab and received in your inbox
- [ ] Outbox tab shows `success` status (not `sandbox`)
- [ ] Server is running (`uvicorn` command active in terminal)
- [ ] Your app's email calls point to `http://localhost:8000/api/send`
- [ ] If using `AUTH_TOKEN`: token is entered in the dashboard 🔒 lock icon and your app sends the `Authorization` header
- [ ] You know how to check the Outbox tab if something fails during the demo

---

> [!TIP]
> **Running out of time?** Turn Sandbox Mode ON. Your app works end-to-end, emails don't get sent, and no one will notice the email part isn't wired to a real provider. You can fix it after the demo.

---

## See Also

- [docs/AUTH.md](AUTH.md) — Full auth integration guide (token generation, app env vars, code examples)
- [docs/PROVIDERS.md](PROVIDERS.md) — Full provider setup guides
- [docs/SANDBOX.md](SANDBOX.md) — Everything about Sandbox Mode
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — If something isn't working
- [docs/API.md](API.md) — All endpoints and integration examples
- [docs/API.md](API.md#authentication) — Auth token setup and the `Authorization` header
- [docs/DOCKER.md](DOCKER.md) — Run with Docker (no Python install needed)
- [docs/HOSTING.md](HOSTING.md) — All cloud hosting options compared
- [docs/RENDER.md](RENDER.md) — Deploy to Render (persistent cloud)
- [docs/RAILWAY.md](RAILWAY.md) — Deploy to Railway (persistent cloud)
