<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Hosting ProtoPost on Railway

Railway connects to your GitHub repo, detects the `Dockerfile`, and deploys in about 2 minutes. Persistent volumes keep provider config and email logs safe across restarts and redeploys.

> [!NOTE]
> **The free trial works fine.** Railway gives $5 of free credits on signup (no card needed). A continuously-running ProtoPost instance costs roughly $0.50–1/month on the Hobby plan — well within hackathon budget. Cold starts **do not lose data** — the volume is always mounted.

---

## Prerequisites

- Your code pushed to a **GitHub repository** (public or private)
- A [Railway account](https://railway.app) — sign up with GitHub
- That's it. No CLI required.

---

## Step 1 — Push the code to GitHub

If you haven't already:

```bash
git init
git add .
git commit -m "initial commit"
gh repo create protopost --public --push --source .
```

Or create a repo manually on GitHub and push to it.

---

## Step 2 — Create a new project on Railway

1. Go to [railway.app/new](https://railway.app/new)
2. Click **Deploy from GitHub repo**
3. Authorise Railway to access your GitHub account if prompted
4. Select the `protopost` repo

Railway detects the `Dockerfile` automatically and starts building.

---

## Step 3 — Add a persistent volume

1. In your project, click the **protopost** service tile
2. Open the **Volumes** tab
3. Click **Add Volume**
4. Set:

| Setting | Value |
|---|---|
| **Mount Path** | `/data` |
| **Size** | 1 GB |

5. Click **Add** — Railway redeploys automatically.

Without this volume, data survives container restarts but is wiped when Railway redeploys the service (e.g. after a code push). With it, nothing is ever lost.

---

## Step 4 — Set environment variables

1. In the service, open the **Variables** tab
2. Add:

| Name | Value |
|---|---|
| `CONFIG_PATH` | `/data/config.json` |
| `DB_PATH` | `/data/emails.db` |
| `AUTH_TOKEN` | Any secret string — **recommended** when hosting publicly |

> [!TIP]
> `AUTH_TOKEN` is optional. If you skip it, the API is open to anyone with the URL. Set it to any password-like string (e.g. `openssl rand -hex 16`). The dashboard will prompt you to enter it on first visit.

3. Click **Deploy** to apply — or wait for Railway to auto-redeploy.

---

## Step 5 — Expose a public URL

1. Open the **Settings** tab of your service
2. Under **Networking**, click **Generate Domain**

Railway assigns a URL like:

```
https://protopost-production.up.railway.app
```

---

## Step 6 — Open the dashboard

Visit your Railway URL. The ProtoPost dashboard loads. Provider config and logs are stored on `/data` and persist permanently.

---

## Step 7 — Add a provider and send a test

1. Click **Providers** → **Add Provider**, fill in your credentials
2. Click **Test Send**, send a test email
3. Check **Outbox & Logs** — the entry should show `success`

Config is written to `/data/config.json` and survives all future deploys.

---

## Step 8 — Point your app at the Railway URL

Replace `http://localhost:8000` with your Railway URL:

```python
# Python
import requests

requests.post("https://protopost-production.up.railway.app/api/send", json={
    "from": "you@example.com",
    "to": ["recipient@example.com"],
    "subject": "Hello from Railway",
    "body_text": "It works!",
}).raise_for_status()
```

```javascript
// JavaScript / Node.js
await fetch("https://protopost-production.up.railway.app/api/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        from: "you@example.com",
        to: ["recipient@example.com"],
        subject: "Hello from Railway",
        body_text: "It works!",
    }),
});
```

---

## Redeploying after a code change

Push to your GitHub branch — Railway auto-deploys on every push.  
Or click **Deploy** manually in the Railway dashboard.

Your volume is **never touched** during a redeploy.

---

## Free tier and pricing

| Thing | Details |
|---|---|
| Signup credits | $5 free on signup, no card needed |
| Hobby plan | $5/month, needed for always-on services |
| Estimated ProtoPost cost | ~$0.50–1/month (low memory/CPU usage) |
| Persistent volume | ~$0.25/GB/month |
| Cold starts | **None** — Railway keeps the container running on paid plans |

> [!TIP]
> The $5 signup credit alone covers a full hackathon weekend. No card needed until the credits run out.

---

## Viewing logs

In the Railway dashboard, open your service and click the **Logs** tab. Live logs stream in the browser — no CLI needed.

---

## How it works

```
Browser / Your App
       │
       │  HTTPS  →  https://protopost-production.up.railway.app
       ▼
┌───────────────────────────────────────────────┐
│  Railway Service (Docker container)           │
│                                               │
│  uvicorn backend.main:app                     │
│                                               │
│  /data/config.json  ──┐                       │
│  /data/emails.db    ──┴── Persistent Volume   │
│                           (1 GB)              │
└───────────────────────────────────────────────┘
```

Railway runs the full Docker container continuously. The volume is always mounted — no data loss on restarts, redeploys, or anything else.

---

## See Also

- [docs/AUTH.md](AUTH.md) — Token generation, app integration examples (Python / JS / Node)
- [docs/HOSTING.md](HOSTING.md) — Compare all hosting options
- [docs/RENDER.md](RENDER.md) — Alternative cloud host with the same persistence model
- [docs/DOCKER.md](DOCKER.md) — Run locally with Docker
- [docs/HACKATHON_QUICKSTART.md](HACKATHON_QUICKSTART.md) — Get email working in 5 minutes
