<!-- Last updated: when this project was generated -->

[← Back to README](../README.md)

# Provider Setup Guide

This guide covers every email provider supported by ProtoPost. If you're not sure which one to use, read the comparison table below first.

---

## Which provider should I pick?

| Provider | Free Tier | Best For | Setup Time | Needs Domain | Reliability |
|---|---|---|---|---|---|
| Resend | 3,000/month | Production-quality sends | ~5 min | Yes (or use sandbox domain) | High |
| Mailtrap | 1,000/month | Testing & staging | ~3 min | No | High |
| Gmail | ~500/day | Personal projects, quick starts | ~5 min | No | Medium (rate limits) |
| Custom SMTP | Depends on provider | When you already have SMTP creds | ~2 min | Depends | Depends |

> [!TIP]
> **Quick recommendation:** If you have 5 minutes, use Resend. If you have 3 minutes, use Mailtrap. If you have 2 minutes and a Gmail account, use Gmail. If you need to get email working in 30 seconds, turn on Sandbox Mode and come back to this later.

---

## How to set up Resend (5 minutes)

Resend is a developer email API. It has a generous free tier, excellent deliverability, and a clean API. It's the recommended provider for most hackathon use cases.

### Step 1 — Create your account

Go to [resend.com/signup](https://resend.com/signup). No credit card required.

### Step 2 — Add a sending domain

In your Resend dashboard, click **Domains** → **Add Domain**. Enter your domain and follow the DNS instructions to verify it.

> [!NOTE]
> **Don't have a domain yet?** Use `onboarding@resend.dev` as your `from` address to test immediately. This sandbox domain works without any DNS setup, but you can **only send to email addresses you have verified** in your Resend account. It's not for production use.

### Step 3 — Create an API key

In your Resend dashboard, click **API Keys** → **Create API Key**.

- Name: `Email Gateway` (or anything you'll remember)
- Permission: **Full Access**

Copy the key — it starts with `re_` and is only shown once.

### Step 4 — Add the provider in ProtoPost

Open the ProtoPost dashboard → **Providers** tab → **Add Provider**.

- **Type:** Resend API
- **API Key:** Paste your `re_...` key
- **Weight:** 100 (or adjust if you have multiple providers)

The dashboard has a built-in guided setup walkthrough. Click **Start Setup Guide** when you select Resend as the type.

### Example request using Resend

```json
{
  "from": "you@yourdomain.com",
  "to": ["recipient@example.com"],
  "subject": "Hello!",
  "body_html": "<h1>It works</h1>"
}
```

### Common mistakes with Resend

- **`403 Forbidden`** — Your `from` address domain is not verified in Resend. Either verify your domain or use `onboarding@resend.dev` for testing.
- **`422 — from address does not match verified domain`** — Same issue. The `from` field must match a domain you've verified.
- **API key scope too narrow** — If you created an API key with "Sending Access only", it might not support all operations. Use Full Access.
- **Daily rate limits** — Resend's free tier allows 100 emails/day. If you hit this, emails silently fail. Check your Resend dashboard usage.

**Resend documentation:** [resend.com/docs](https://resend.com/docs)

---

## How to set up Mailtrap (3 minutes)

Mailtrap has two completely separate products that beginners often confuse:

| Product | What it does |
|---|---|
| **Email Testing** | Fake inboxes. Emails go into Mailtrap's server, never to real recipients. |
| **Email Sending** | Real delivery. Emails actually go to recipients. |

> [!WARNING]
> **Most common mistake:** Using the "Testing" API token for actual sending. Testing tokens don't deliver emails. Make sure you're in the **Sending** section of your Mailtrap dashboard.

### Step 1 — Create your account

Go to [mailtrap.io](https://mailtrap.io) and sign up for free.

### Step 2 — Get the Sending API token

In your Mailtrap dashboard:

1. Click **Email Sending** (left sidebar)
2. Click **Transactional Stream**
3. Click **API Tokens**
4. Click **Generate Token**
5. Copy the token

```
Navigate to:
  Sending → Transactional → API Tokens → Generate Token

NOT:
  Testing → Inboxes → API tokens   ← this is the wrong one
```

### Step 3 — Add the provider in ProtoPost

Open the ProtoPost dashboard → **Providers** tab → **Add Provider**.

- **Type:** Mailtrap API
- **API Key:** Paste your Mailtrap API token
- **Weight:** 100

### Free tier limits

- 1,000 emails/month on the free plan
- Up to 200 recipients/email

### Common mistakes with Mailtrap

- **`401 Unauthorized`** — Almost always means you used a Testing token instead of a Sending token. See the navigation path above.
- **Emails not arriving** — Double-check you're not in Testing mode (which captures emails in a fake inbox).

**Mailtrap documentation:** [mailtrap.io/blog/api-email-sending](https://mailtrap.io/blog/api-email-sending/)

---

## How to set up Gmail App Password (5 minutes)

Gmail lets you send up to ~500 emails per day from a personal account using an App Password. It requires no domain setup, which makes it fast to get started.

> [!WARNING]
> **Hard requirement:** 2-Step Verification must be enabled on your Google Account before App Passwords become available.

### Step 1 — Enable 2-Step Verification

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Scroll to "How you sign in to Google"
4. Click **2-Step Verification** → **Get Started**
5. Follow the prompts to verify your phone number

### Step 2 — Find App Passwords

Once 2-Step Verification is active:

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   (Or: Google Account → Security → search "App Passwords")

> [!NOTE]
> If "App Passwords" doesn't appear, 2-Step Verification isn't active yet. Complete Step 1 first.

### Step 3 — Create the App Password

1. In the **App name** field, type `Email Gateway`
2. Click **Create**
3. Google shows a 16-character password like: `xxxx xxxx xxxx xxxx`
4. Copy it immediately — it's only shown once. Spaces are fine to include.

### Step 4 — Add the provider in ProtoPost

Open the ProtoPost dashboard → **Providers** tab → **Add Provider**.

- **Type:** Gmail App Password
- **Gmail Address:** Your full Gmail address
- **App Password:** Paste the 16-character password (with or without spaces)

The dashboard has a built-in 5-step guided walkthrough for Gmail setup.

### Gmail sending limits

```
Gmail sending limits:
   Personal account:    ~500 emails/day
   Google Workspace:    ~2,000 emails/day

   Hit the limit? Gmail silently queues or drops emails.
   Use Resend or Mailtrap for anything above 100 emails/day.
```

> [!WARNING]
> Gmail App Passwords are account-level credentials. Anyone who has this password can send emails as you. Store it carefully and revoke it after your hackathon if needed.

### Common mistakes with Gmail

- **`SMTPAuthenticationError`** — Wrong password, or using your regular Gmail password instead of the App Password.
- **`Application-specific password required`** — The same: you need an App Password, not your regular password.
- **App Passwords not appearing** — 2-Step Verification isn't enabled on the account.

**Google App Passwords docs:** [support.google.com/accounts/answer/185833](https://support.google.com/accounts/answer/185833)

---

## How to set up Custom SMTP (2 minutes)

Use this if you already have SMTP credentials for any service — SendGrid, Mailgun, AWS SES, Zoho, Office 365, etc.

### Port reference

| Port | Protocol | Use When |
|---|---|---|
| 25 | SMTP (no auth) | Legacy, mostly blocked by ISPs |
| 465 | SMTPS (SSL) | SSL from the start — set `smtp_use_ssl: true` |
| 587 | SMTP + STARTTLS | Modern standard — set `smtp_use_tls: true` |
| 2525 | SMTP (fallback) | When 587 is blocked, common on cloud VMs |

### Common SMTP providers pre-filled

| Provider | Host | Port | Use TLS | Use SSL |
|---|---|---|---|---|
| SendGrid | smtp.sendgrid.net | 587 | ✓ | ✗ |
| Mailgun | smtp.mailgun.org | 587 | ✓ | ✗ |
| AWS SES | email-smtp.[region].amazonaws.com | 587 | ✓ | ✗ |
| Zoho Mail | smtp.zoho.com | 587 | ✓ | ✗ |
| Office 365 | smtp.office365.com | 587 | ✓ | ✗ |

### Add the provider in ProtoPost

Open the ProtoPost dashboard → **Providers** tab → **Add Provider**.

- **Type:** Custom SMTP Server
- **SMTP Host:** Your provider's SMTP hostname
- **SMTP Port:** Usually 587
- **Username:** Your SMTP username (often your email address)
- **Password:** Your SMTP password
- **Use TLS:** ✓ (for port 587)
- **Use SSL:** ✗ (unless using port 465)

### Common mistakes with Custom SMTP

- **Connection refused on port 587** — Your cloud VM or ISP is likely blocking outbound port 587. Try port 2525 or 465.
- **`SSL: WRONG_VERSION_NUMBER`** — You have both TLS and SSL enabled at the same time. Enable only one.
- **Auth failed** — Double-check username and password. For SendGrid, the username is literally `apikey` and the password is your SendGrid API key.

---

## How to test your provider

After adding a provider, run this from your terminal:

```bash
curl -X POST http://localhost:8000/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "from": "you@example.com",
    "to": ["you@example.com"],
    "subject": "Gateway Test",
    "body_text": "If you see this, it works!"
  }'
```

Expected success response:

```json
{
  "status": "success",
  "provider": "resend",
  "message_id": "msg_abc123",
  "processing_time_ms": 412
}
```

If you get an error, check the `detail` field in the response body. The full error from the provider is always included.

---

## How to switch providers without touching your app

1. Open the ProtoPost dashboard
2. Go to **Providers** tab
3. Disable your current provider (toggle the switch)
4. Enable your new provider

Your app keeps calling `POST /v1/send` at the same URL. Nothing else changes.

---

## See Also

- [docs/ROUTING.md](ROUTING.md) — How to use multiple providers together
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Provider-specific error fixes
- [docs/HACKATHON_QUICKSTART.md](HACKATHON_QUICKSTART.md) — Get any provider working in 5 minutes
