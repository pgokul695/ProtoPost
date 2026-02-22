# 📧 Hackathon Email Gateway

A production-quality local proxy server that lets you route, mock, and load-balance outbound emails **without changing a single line of your application code**. Perfect for development, testing, and hackathons.

## ✨ Features

- 🚀 **Zero-config proxy** — Works as a drop-in replacement for any email service
- 🎯 **Multiple provider support** — Resend, Mailtrap, Gmail, Custom SMTP
- ⚖️ **Load balancing** — Manual weighted distribution or smart failover
- 🧪 **Sandbox mode** — Intercept all emails locally for safe testing
- 📊 **Real-time dashboard** — Monitor all sent emails with detailed logs
- 🔄 **Live config reload** — No server restart needed
- 🎨 **Beautiful dark-mode UI** — Built with Tailwind CSS

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd hackathon-email-gateway
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn backend.main:app --reload --port 8000
```

*Note: You can use any port you prefer. The dashboard automatically detects the server URL.*

### 3. Open the Dashboard

Navigate to `http://localhost:8000` in your browser.

---

## 📤 Sending Emails via the API

### Using cURL

```bash
curl -X POST http://localhost:8000/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "from": "dev@yourdomain.com",
    "to": ["recipient@example.com"],
    "subject": "Hello from Gateway",
    "body_html": "<h1>It works!</h1>",
    "body_text": "It works!"
  }'
```

### Using Python (httpx)

```python
import httpx
import asyncio

async def send_email():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8000/v1/send',
            json={
                'from': 'dev@yourdomain.com',
                'to': ['recipient@example.com'],
                'subject': 'Hello from Gateway',
                'body_html': '<h1>It works!</h1>',
                'body_text': 'It works!'
            }
        )
        print(response.json())

asyncio.run(send_email())
```

### Using Python (requests)

```python
import requests

response = requests.post(
    'http://localhost:8000/v1/send',
    json={
        'from': 'dev@yourdomain.com',
        'to': ['recipient@example.com'],
        'subject': 'Hello from Gateway',
        'body_html': '<h1>It works!</h1>'
    }
)
print(response.json())
```

---

## 📋 Provider Setup Guide

### Resend

1. Sign up at [resend.com](https://resend.com)
2. Navigate to **API Keys** in the dashboard
3. Create a new API key
4. Add domain verification (required for production sending)
5. In the gateway dashboard: **Providers → Add Provider**
   - Type: **Resend API**
   - API Key: Paste your key
   - Weight: Set traffic percentage (e.g., 100)

### Mailtrap

1. Sign up at [mailtrap.io](https://mailtrap.io)
2. Navigate to **Sending Domains** → **API Tokens**
3. Copy your API token (starts with a long string)
4. In the gateway dashboard: **Providers → Add Provider**
   - Type: **Mailtrap API**
   - API Key: Paste your token
   - Weight: Set traffic percentage

### Gmail (App Password)

⚠️ **Requirements:**
- Gmail account with 2-Factor Authentication enabled
- App Password generated (regular password will NOT work)

**Steps:**
1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled
3. Search for **App Passwords** (or go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords))
4. Generate a new app password:
   - App: **Mail**
   - Device: **Other (Custom name)** → "Email Gateway"
5. Copy the 16-character password (remove spaces)
6. In the gateway dashboard: **Providers → Add Provider**
   - Type: **Gmail App Password**
   - Gmail Address: Your full Gmail address
   - App Password: Paste the 16-character code

### Custom SMTP Server

For any SMTP-compatible service (SendGrid, Mailgun, Postmark, etc.):

**Common Port Reference:**
- `25` — Standard SMTP (often blocked by ISPs)
- `587` — SMTP with STARTTLS (recommended)
- `465` — SMTP with SSL/TLS
- `2525` — Alternative non-standard port

**Configuration:**
1. Get SMTP credentials from your provider
2. In the gateway dashboard: **Providers → Add Provider**
   - Type: **Custom SMTP Server**
   - Host: `smtp.example.com`
   - Port: `587` (or provider-specific)
   - Username: Your SMTP username
   - Password: Your SMTP password
   - Use TLS: ✅ (for port 587)
   - Use SSL: ❌ (unless using port 465)

---

## 🧪 Sandbox Mode

**What is Sandbox Mode?**

When enabled, ALL emails are intercepted locally and logged — **no external API calls are made**. Perfect for:
- Local development
- CI/CD pipelines
- Testing email logic without spam
- Demo environments

**How to Enable:**

1. **Via Dashboard:** Toggle the **Sandbox Mode** switch in the header
2. **Via API:**
   ```bash
   curl -X POST http://localhost:8000/v1/config/routing \
     -H "Content-Type: application/json" \
     -d '{"mode": "smart", "sandbox": true}'
   ```

**What Happens:**
- Emails are logged with status `sandbox`
- No providers are contacted
- Processing time is still recorded
- All logs visible in dashboard

---

## ⚖️ Load Balancing Guide

### Manual Mode (Weighted Distribution)

Traffic is split randomly based on provider weights:

**Example:**
- Provider A: Weight 70
- Provider B: Weight 30

**Result:** Provider A receives ~70% of emails, Provider B gets ~30%

**Use Cases:**
- Gradual migration between providers
- A/B testing email deliverability
- Cost optimization (cheaper provider gets more traffic)

**Setup:**
1. Navigate to **Routing** tab
2. Select **Manual Load Balancing**
3. Set weights for each provider in the **Providers** tab

### Smart Mode (Automatic Failover)

Providers are tried in order of weight (highest first). If the primary fails, the next provider is attempted automatically.

**Example:**
- Provider A: Weight 100 (Primary)
- Provider B: Weight 50 (Secondary)
- Provider C: Weight 25 (Tertiary)

**Result:** Always try A first → If fails, try B → If fails, try C

**Use Cases:**
- High availability
- Backup provider configuration
- Regional fallbacks

**Setup:**
1. Navigate to **Routing** tab
2. Select **Smart Failover**
3. Set weights to define priority order

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Your App      │
│  (any language) │
└────────┬────────┘
         │
         │ POST /v1/send
         ▼
┌─────────────────────────────────┐
│   FastAPI Gateway (port 8000)   │
│                                  │
│  1. Read config.json             │
│  2. Check Sandbox Mode?          │
│     ├─ Yes → Log + Return        │
│     └─ No  → Route to provider   │
│                                  │
│  3. Load Balancer:               │
│     ├─ Manual: Weighted random   │
│     └─ Smart: Try by priority    │
│                                  │
│  4. Provider Dispatch            │
└───┬─────────┬─────────┬─────────┘
    │         │         │
    ▼         ▼         ▼
┌─────┐  ┌────────┐  ┌──────┐
│SMTP │  │Resend  │  │Gmail │
│     │  │  API   │  │SMTP  │
└─────┘  └────────┘  └──────┘
    │         │         │
    └─────────┴─────────┘
              │
         Log Result
              ▼
        ┌──────────┐
        │ SQLite   │
        │ Database │
        └──────────┘
```

---

## 📂 Project Structure

```
hackathon-email-gateway/
│
├── backend/
│   ├── main.py              # FastAPI app + all endpoints
│   ├── router.py            # Routing logic + load balancing
│   ├── config_manager.py    # config.json read/write
│   ├── database.py          # SQLite operations
│   ├── providers.py         # Email sending implementations
│   └── models.py            # Pydantic schemas
│
├── frontend/
│   └── dashboard.html       # Complete single-file SPA
│
├── config.json              # Runtime configuration (auto-created)
├── emails.db                # SQLite database (auto-created)
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

---

## 🔌 API Reference

### `POST /v1/send`
Send an email through the gateway.

**Request Body:**
```json
{
  "from": "sender@example.com",
  "to": ["recipient@example.com"],
  "subject": "Email subject",
  "body_text": "Plain text body",
  "body_html": "<h1>HTML body</h1>",
  "reply_to": "reply@example.com"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Email sent successfully via Provider Name",
  "provider": {
    "id": "uuid",
    "name": "Provider Name",
    "type": "resend"
  },
  "log_id": "uuid",
  "processing_time_ms": 234.56,
  "message_id": "provider-message-id"
}
```

### `GET /v1/logs`
Retrieve email logs with pagination.

**Query Parameters:**
- `limit` (default: 100, max: 500)
- `offset` (default: 0)

### `GET /v1/logs/{log_id}`
Get detailed information for a single log entry.

### `GET /v1/stats`
Get aggregate statistics (total sent, failed, sandbox, avg time).

### `GET /v1/config`
Get current configuration (providers, routing, sandbox state).

### `PUT /v1/config`
Update entire configuration.

### `POST /v1/config/providers`
Add a new provider.

### `PUT /v1/config/providers/{provider_id}`
Update a provider by ID.

### `DELETE /v1/config/providers/{provider_id}`
Delete a provider by ID.

### `POST /v1/config/routing`
Update routing configuration (mode and sandbox toggle).

### `GET /v1/health`
Health check endpoint.

---

## 🛠️ Configuration File Format

`config.json` is auto-created and can be edited manually (changes apply on next request):

```json
{
  "providers": [
    {
      "id": "uuid",
      "name": "My Resend Provider",
      "type": "resend",
      "enabled": true,
      "weight": 100,
      "api_key": "re_xxxxxxxxxxxx"
    }
  ],
  "routing": {
    "mode": "smart",
    "sandbox": false
  },
  "version": 1
}
```

---

## 🐛 Troubleshooting

### Server won't start
- Ensure port 8000 is not in use: `lsof -i :8000`
- Check Python version: `python --version` (requires 3.11+)
- Verify dependencies: `pip list | grep fastapi`

### Emails not sending
- Check provider credentials in dashboard
- View detailed error in **Outbox & Logs** tab → **View Details**
- Test provider independently (use their web UI or docs)
- Enable Sandbox Mode to test routing logic without external calls

### Dashboard not loading
- Ensure `frontend/dashboard.html` exists
- Check browser console for errors (F12)
- Verify server is running: `curl http://localhost:8000/v1/health` (adjust port if different)

### Gmail "Authentication failed"
- Must use App Password, not regular password
- 2FA must be enabled on the Google account
- Remove spaces from the 16-character app password

---

## 📝 License

MIT License - Free for personal and commercial use.

---

## 🤝 Contributing

This is a hackathon project scaffold. Fork it, customize it, break it, fix it — make it yours!

---

## 🎯 Use Cases

- **Hackathons** — Focus on features, not email infrastructure
- **Development** — Test email logic without spam
- **CI/CD** — Validate email content in tests
- **Multi-provider setups** — Load balance or failover between services
- **Cost optimization** — Route to cheaper providers for bulk emails
- **email migration** — Gradually shift traffic from old to new provider

---

## 🚀 What's Next?

- Add webhook support for delivery status
- Implement email templates
- Add rate limiting per provider
- Support for attachments
- Email preview in dashboard
- Export logs to CSV
- Provider health checks
- Scheduled email sending

---

**Built with ❤️ for developers who just want to send emails without the hassle.**
