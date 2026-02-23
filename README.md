<!-- Last updated: when this project was generated -->

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Works%20on-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Hackathon Ready](https://img.shields.io/badge/Hackathon-Ready-brightgreen)

# 📧 ProtoPost — Hackathon Email Gateway

A local email proxy that lets you switch providers, mock sends, and debug emails — without touching your app code.

---

## Why this exists

Building at a hackathon and need email working in the next hour? You've got two problems: setting up an email provider is annoying, and debugging why your emails aren't sending is even more annoying.

ProtoPost solves both. Run one server locally, point your app at it, and you get:

- A dashboard to see every email your app tries to send
- Sandbox mode that captures emails without sending anything (great for testing)
- Automatic switching to a backup provider if your primary one fails
- Support for Resend, Mailtrap, Gmail, and any custom SMTP server

---

## Dashboard Preview

```
┌─────────────────────────────────────────────────────────────────┐
│  📧 ProtoPost               [SANDBOX MODE: OFF  ○──────●  ON]  │
├─────────────────────────────────────────────────────────────────┤
│  [Outbox & Logs]  [Providers]  [Routing]  [Test Send]           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Total Sent   Failed   Sandbox   Avg Time                      │
│      142          2        58      340ms                        │
│                                                                  │
│  Timestamp    To                Subject         Provider  Status │
│  12:04:32     user@example.com  Welcome!        Resend    ✓     │
│  12:03:11     test@test.com     Reset link      Resend    ✓     │
│  12:01:44     admin@co.com      Alert: down     [sandbox] 📦   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

> **Prefer Docker?** Skip the Python setup entirely — see [docs/DOCKER.md](docs/DOCKER.md).  
> **Need a shared team URL?** Deploy to Render or Railway — see [docs/HOSTING.md](docs/HOSTING.md).

### Requirements

- Python 3.11 or higher ([download](https://python.org/downloads))
- pip (comes with Python)
- A terminal (Terminal on Mac, PowerShell or CMD on Windows)

### 1. Clone or download this project

```bash
git clone https://github.com/yourname/protopost.git
cd protopost
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the server

```bash
uvicorn backend.main:app --reload --port 8000
```

> [!NOTE]
> **Windows users:** If `uvicorn` isn't found, run:
> ```bash
> python -m uvicorn backend.main:app --reload --port 8000
> ```

### 4. Open the dashboard

Visit: **http://localhost:8000**

That's it. The dashboard opens in your browser. No config file to edit first.

---

## What you can do

| Feature | What it means for you |
|---|---|
| Sandbox Mode | Emails get captured, never sent. Safe for testing. |
| Provider Switching | Change from Resend to Gmail in 2 clicks. No code changes. |
| Automatic Failover | If Resend fails, it tries Gmail automatically. |
| Load Balancing | Split traffic 70/30 across two providers. |
| Email Logs | See every email your app sent, with full payload. |
| Zero App Changes | Your app keeps calling the same endpoint. |
| Setup Wizards | Guided steps for Gmail and Resend setup — built into the UI. |

---

## How to send an email

Point your app at `POST http://localhost:8000/api/send`:

```json
{
  "from": "you@yourdomain.com",
  "to": ["recipient@example.com"],
  "subject": "Hello!",
  "body_html": "<h1>It works</h1>",
  "body_text": "It works"
}
```

That's the only integration step. Your app never needs to know which provider is in use.

---

## Architecture

```
Your App Code
     │
     │  POST /api/send  (JSON payload)
     ▼
┌─────────────────────────────┐
│    ProtoPost Server         │  ← runs at localhost:8000
│                             │
│  ┌─────────────────────┐    │
│  │   config.json       │    │  ← updated live from dashboard
│  └────────┬────────────┘    │
│           │                 │
│  ┌────────▼────────────┐    │
│  │   Routing Engine    │    │
│  │                     │    │
│  │  Sandbox? → Log it  │    │
│  │  Manual  → Weighted │    │
│  │  Smart   → Failover │    │
│  └────────┬────────────┘    │
│           │                 │
└───────────┼─────────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
  Resend API    Custom SMTP      ... (any configured provider)
```

The server reads `config.json` on every request. Change a provider in the dashboard and the next email uses it — no restart needed.

---

## Documentation

| Doc | What's in it |
|---|---|
| [docs/HACKATHON_QUICKSTART.md](docs/HACKATHON_QUICKSTART.md) | Get email working in 5 minutes — start here if you're in a hurry |
| [docs/PROVIDERS.md](docs/PROVIDERS.md) | How to set up Resend, Mailtrap, Gmail, and custom SMTP |
| [docs/ROUTING.md](docs/ROUTING.md) | Load balancing and failover explained |
| [docs/API.md](docs/API.md) | Full REST API reference with code examples |
| [docs/SANDBOX.md](docs/SANDBOX.md) | Sandbox mode — what it does and when to use it |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Exact fixes for the most common errors |
| [docs/DOCKER.md](docs/DOCKER.md) | Run with Docker — one command, no Python install needed |
| [docs/HOSTING.md](docs/HOSTING.md) | All cloud hosting options compared (Render, Railway, Fly.io, VPS, and more) |
| [docs/RENDER.md](docs/RENDER.md) | Step-by-step guide: deploy to Render with persistent storage |
| [docs/RAILWAY.md](docs/RAILWAY.md) | Step-by-step guide: deploy to Railway with persistent storage |

---

## Project Structure

```
protopost/
├── backend/
│   ├── main.py              # FastAPI app + all endpoints
│   ├── router.py            # Routing logic + load balancing
│   ├── config_manager.py    # config.json read/write
│   ├── database.py          # SQLite operations
│   ├── providers.py         # Email sending implementations
│   └── models.py            # Pydantic schemas
├── frontend/
│   └── dashboard.html       # Complete single-file SPA
├── docs/                    # This documentation suite
├── config.json              # Runtime configuration (auto-created)
├── emails.db                # SQLite database (auto-created)
└── requirements.txt         # Python dependencies
```

---

## Creators

| Name | Role | Website | Email |
|---|---|---|---|
| Gokul P | Developer | [gokulp.in](https://gokulp.in) | [me@gokulp.in](mailto:me@gokulp.in) |
| Devika P Sajith | QA | [devikapsajith.netlify.app](https://devikapsajith.netlify.app/) | [devikasajith710@gmail.com](mailto:devikasajith710@gmail.com) |

---

## License

MIT — use it however you want, including at your hackathon.

See [CONTRIBUTING.md](CONTRIBUTING.md) if you want to add a provider or fix something.

