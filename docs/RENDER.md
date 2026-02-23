<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Hosting ProtoPost on Render

Render runs ProtoPost as a real Docker container — not a serverless function. Provider config and email logs are stored on a **persistent disk** that survives restarts and redeploys.

> [!NOTE]
> **The free tier works fine.** Cold starts (after 15 min of inactivity) do not lose any data — the container just needs a moment to wake up. Data is only lost on a **redeploy** if you skip the persistent disk setup in Step 4. With the disk in place, nothing is ever lost.

---

## Prerequisites

- Your code pushed to a **GitHub repository** (public or private)
- A free [Render account](https://render.com) — sign up with GitHub for the smoothest experience
- That's it. No CLI, no local tooling needed.

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

## Step 2 — Create a new Web Service on Render

1. Go to your [Render dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Under **Connect a repository**, choose your GitHub account and select the `protopost` repo
4. Click **Connect**

---

## Step 3 — Configure the service

Fill in the settings on the next screen:

| Setting | Value |
|---|---|
| **Name** | `protopost` (or anything you like) |
| **Region** | Closest to you |
| **Branch** | `main` |
| **Runtime** | **Docker** |
| **Instance Type** | Free (for hackathons) |

Leave everything else as default — Render detects the `Dockerfile` automatically.

Click **Deploy Web Service** at the bottom.

---

## Step 4 — Add a persistent disk

> Cold starts on the free tier **do not lose data** — the container wakes back up with everything intact. The only time data is lost without a disk is during a **redeploy** (when Render replaces the container). The disk eliminates that too, making storage permanently safe.

1. After the service is created, open its page and click **Disks** in the left sidebar
2. Click **Add Disk**
3. Fill in:

| Setting | Value |
|---|---|
| **Name** | `protopost-data` |
| **Mount Path** | `/data` |
| **Size** | 1 GB |

4. Click **Save**

> **Cost:** Persistent disks cost **$0.25 / GB / month** — that's 25 cents for 1 GB. Free-tier web services are $0. Total for a hackathon: essentially free.

Render redeploys the service automatically with the disk attached.

---

## Step 5 — Set environment variables

1. In your service page, click **Environment** in the left sidebar
2. Add these two variables:

| Key | Value |
|---|---|
| `CONFIG_PATH` | `/data/config.json` |
| `DB_PATH` | `/data/emails.db` |
| `AUTH_TOKEN` | Any secret string — **recommended** when hosting publicly |

> [!TIP]
> `AUTH_TOKEN` is optional. If you skip it, the API is open to anyone with the URL. Set it to any password-like string (e.g. `openssl rand -hex 16`). The dashboard will prompt you to enter it on first visit.

3. Click **Save Changes** — Render redeploys automatically.

---

## Step 6 — Open the dashboard

Once the deployment is green (usually under 2 minutes), click the URL at the top of the service page:

```
https://protopost.onrender.com
```

The ProtoPost dashboard loads. Your provider config and email logs are now stored on `/data` and persist forever.

---

## Step 7 — Add a provider and send a test

1. Click **Providers** → **Add Provider**, fill in your credentials
2. Click **Test Send**, send a test email
3. Check **Outbox & Logs** — the entry should show `success`

Provider config is written to `/data/config.json` and survives all future deploys and restarts.

---

## Step 8 — Point your app at the Render URL

Replace `http://localhost:8000` with your Render URL:

```python
# Python
import requests

requests.post("https://protopost.onrender.com/api/send", json={
    "from": "you@example.com",
    "to": ["recipient@example.com"],
    "subject": "Hello from Render",
    "body_text": "It works!",
}).raise_for_status()
```

```javascript
// JavaScript / Node.js
await fetch("https://protopost.onrender.com/api/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        from: "you@example.com",
        to: ["recipient@example.com"],
        subject: "Hello from Render",
        body_text: "It works!",
    }),
});
```

---

## Redeploying after a code change

Push to your GitHub branch — Render auto-deploys on every push.  
Or trigger a manual deploy from the **Deploys** tab.

Your persistent disk is **never touched** during a redeploy.

---

## Free tier considerations

| Thing | Free tier behaviour |
|---|---|
| Service uptime | Spins down after **15 min of inactivity**. First request after that takes ~30 s (cold start). Data is **not lost** on a cold start. |
| Persistent disk | Not included in the free tier — costs $0.25/GB/month separately. Without it, data survives cold starts but is wiped on redeploys. |
| Logs | Available in the Render dashboard under **Logs**. |

> [!TIP]
> For a demo or hackathon, the 30-second cold start on the free tier is rarely an issue — just open the dashboard URL a minute before you present and the service will be warm.

---

## Viewing logs

In the Render dashboard, open your service and click **Logs** in the left sidebar. Live logs stream directly in the browser — no CLI needed.

---

## How it works

```
Browser / Your App
       │
       │  HTTPS  →  https://protopost.onrender.com
       ▼
┌──────────────────────────────────────────┐
│  Render Web Service (Docker container)   │
│                                          │
│  uvicorn backend.main:app                │
│                                          │
│  /data/config.json  ──┐                  │
│  /data/emails.db    ──┴── Persistent     │
│                           Disk (1 GB)    │
└──────────────────────────────────────────┘
```

Unlike Vercel or other serverless platforms, Render keeps the container running. The filesystem persists between requests, and the disk persists between restarts and redeploys.

---

## See Also

- [docs/AUTH.md](AUTH.md) — Token generation, app integration examples (Python / JS / Node)
- [docs/HOSTING.md](HOSTING.md) — Compare all hosting options
- [docs/RAILWAY.md](RAILWAY.md) — Alternative cloud host with the same persistence model
- [docs/DOCKER.md](DOCKER.md) — Run locally with Docker
- [docs/HACKATHON_QUICKSTART.md](HACKATHON_QUICKSTART.md) — Get email working in 5 minutes
- [docs/API.md](API.md) — Full REST API reference
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — If something isn't working
