<!-- Last updated: when this project was generated -->

[← Back to README](../README.md)

# 🚀 Hackathon Quick Start — Email Working in 5 Minutes

No backstory. No theory. Pick your path and follow the steps.

---

## Pick your path

```
Not sure which to pick? Use this:

Just testing / don't want to spam anyone  →  Path A (Sandbox)    ← 2 min
Need real email delivery, have 5 min      →  Path B (Resend)     ← recommended
Already have a Gmail account              →  Path C (Gmail)
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

**Done.** Your app can now call `POST /v1/send` and it will work. Emails are captured in the Outbox tab, not sent. Nothing needs a provider configured.

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

## Integrate with your app — minimum code

Replace `http://localhost:8000/v1/send` with your URL if you changed the port.

### Python

```python
import requests

def send_email(to: str, subject: str, body: str) -> None:
    requests.post("http://localhost:8000/v1/send", json={
        "from": "you@example.com",
        "to": [to],
        "subject": subject,
        "body_text": body,
    }).raise_for_status()
```

### JavaScript

```javascript
async function sendEmail(to, subject, body) {
    const res = await fetch("http://localhost:8000/v1/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ from: "you@example.com", to: [to], subject, body_text: body }),
    });
    if (!res.ok) throw new Error(await res.text());
}
```

### Node.js

```javascript
const axios = require("axios");

const sendEmail = (to, subject, body) =>
    axios.post("http://localhost:8000/v1/send", {
        from: "you@example.com",
        to: [to],
        subject,
        body_text: body,
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
- [ ] Your app's email calls point to `http://localhost:8000/v1/send`
- [ ] You know how to check the Outbox tab if something fails during the demo

---

> [!TIP]
> **Running out of time?** Turn Sandbox Mode ON. Your app works end-to-end, emails don't get sent, and no one will notice the email part isn't wired to a real provider. You can fix it after the demo.

---

## See Also

- [docs/PROVIDERS.md](PROVIDERS.md) — Full provider setup guides
- [docs/SANDBOX.md](SANDBOX.md) — Everything about Sandbox Mode
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — If something isn't working
- [docs/API.md](API.md) — All endpoints and integration examples
