<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Routing & Load Balancing

ProtoPost has two routing modes: **Manual Load Balancing** and **Smart Failover**. There's also **Sandbox Mode**, which overrides both and captures all emails locally.

Read the Sandbox section first — it's the most important thing to understand before your demo.

---

## Read this first — Sandbox Mode

Sandbox Mode is a "capture all" switch. When it's on, every email your app tries to send gets saved to the local database and the gateway returns a success response — but **nothing is actually sent**. No API calls. No SMTP connections. Nothing leaves your machine.

Use it whenever you're developing or testing. Switch it off only when you're ready for real delivery.

> [!WARNING]
> Sandbox Mode overrides everything — Manual mode, Smart Failover, every provider. Even if all your providers are perfectly configured, emails will not send while Sandbox Mode is on.

**How to enable Sandbox Mode:**

Option 1 — Dashboard: Toggle the **Sandbox Mode** switch in the header bar.

Option 2 — API:

```bash
curl -X POST http://localhost:8000/api/config/routing \
  -H "Content-Type: application/json" \
  -d '{"mode": "smart", "sandbox": true}'
```

**How to tell if Sandbox Mode is on:**

- The toggle in the header is lit up
- Emails in the Outbox tab show `[sandbox]` as the provider, not a real provider name
- The response from `POST /api/send` has `"status": "sandbox"` instead of `"status": "success"`

See [docs/SANDBOX.md](SANDBOX.md) for the full Sandbox Mode guide.

---

## Manual Load Balancing

You have two providers: Resend (weight 70) and Mailtrap (weight 30). For every 10 emails your app sends, roughly 7 go through Resend and 3 through Mailtrap. The split isn't perfectly exact — it's probabilistic — but it averages out over time.

```
Resend     [███████████████████░░░░░░░░]  70%
Mailtrap   [████████░░░░░░░░░░░░░░░░░░░]  30%
```

**How it works technically:** A random number between 0 and the sum of all weights is generated for each email. The provider whose weight range the number falls in handles that email.

**Best for:**
- Splitting traffic between two accounts of the same provider (to stay under rate limits)
- A/B testing delivery rates across providers
- Cost optimization where you want one cheap provider to handle the bulk

**How to configure:**

1. Open the ProtoPost dashboard
2. Click the **Routing** tab
3. Select **Manual Load Balancing**
4. Set the **Weight** for each provider in the **Providers** tab

> [!NOTE]
> Weights don't have to sum to 100. A weight of 70/30 is identical to 7/3 or 14/6. What matters is the ratio, not the absolute values.

> [!WARNING]
> If all provider weights are 0, no emails can be routed. Set at least one provider's weight above 0.

---

## Smart Failover Mode

Smart Failover tries providers in order of weight (highest first). If the first provider fails, it moves to the next. If that fails, it tries the next. Only when all providers have failed does the gateway return an error.

```
Email arrives
     ↓
Try Provider #1 (highest weight)
     ↓
Success? → Done ✓
     ↓ (fail)
Log error, try Provider #2
     ↓
Success? → Done ✓
     ↓ (fail)
Log error, try Provider #3
     ↓
All failed? → Return 502 with error details
```

**Best for:**
- High availability — you want email to succeed even if one provider is down
- Demo day — Resend as primary, Gmail as backup
- Any situation where delivery is more important than precise traffic splitting

**How to configure:**

1. Open the ProtoPost dashboard
2. Click the **Routing** tab
3. Select **Smart Failover**
4. Add at least two providers with different weights (higher weight = higher priority)

> [!NOTE]
> In Smart Failover mode, the provider with the **highest weight** is tried first. Use weights to set priority — there's no separate "primary/secondary" setting.

---

## How to switch between routing modes

**Via dashboard:**

1. Click the **Routing** tab
2. Click either **Manual Load Balancing** or **Smart Failover** — the selection saves immediately

**Via API:**

```bash
# Switch to Smart Failover
curl -X POST http://localhost:8000/api/config/routing \
  -H "Content-Type: application/json" \
  -d '{"mode": "smart", "sandbox": false}'

# Switch to Manual Load Balancing
curl -X POST http://localhost:8000/api/config/routing \
  -H "Content-Type: application/json" \
  -d '{"mode": "manual", "sandbox": false}'
```

The change applies to the next email sent. No server restart needed.

---

## Real hackathon scenarios

### Scenario 1: "I'm still building and don't want to spam anyone"

**Problem:** You need to test your app's email flow, but you don't want to actually send emails to test addresses.

**Recommended setup:**
- Turn on **Sandbox Mode**
- Add providers in the Providers tab, but leave Sandbox Mode on
- Your app works end-to-end, emails show up in the Outbox tab, nothing gets sent

When you're ready for real sends, toggle Sandbox Mode off. No other changes needed.

---

### Scenario 2: "Demo day in 2 hours, need email to actually work"

**Problem:** You need reliable delivery with a backup in case your primary provider fails.

**Recommended setup:**

| Provider | Type | Weight |
|---|---|---|
| Resend | Resend API | 100 |
| My Gmail | Gmail App Password | 50 |

- Routing mode: **Smart Failover**
- Sandbox Mode: **OFF**

Resend handles everything. If it fails (rate limit, outage, wrong API key), Gmail automatically picks it up. The weight difference (100 vs 50) just controls priority — both are enabled.

---

### Scenario 3: "Two teammates each have a free Resend account"

**Problem:** You're worried about hitting the 100 emails/day free tier limit.

**Recommended setup:**

| Provider | Type | Weight |
|---|---|---|
| Alice's Resend | Resend API | 50 |
| Bob's Resend | Resend API | 50 |

- Routing mode: **Manual Load Balancing**
- Sandbox Mode: **OFF**

Traffic splits 50/50 across both accounts. You effectively double your daily sending limit.

---

## See Also

- [docs/SANDBOX.md](SANDBOX.md) — Full Sandbox Mode reference
- [docs/PROVIDERS.md](PROVIDERS.md) — How to set up each provider
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — What to do when routing fails
