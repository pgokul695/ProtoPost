<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Sandbox Mode

Sandbox Mode is the single most important feature to understand before you start building. Read this before your first test.

---

## What Sandbox Mode does

> [!NOTE]
> **Using AUTH_TOKEN?** Add `-H "Authorization: Bearer <your-token>"` to every `curl` command shown in this doc. The dashboard handles auth automatically via the 🔒 lock icon. See [docs/API.md](API.md#authentication).

When Sandbox Mode is on:

1. Your app calls `POST /api/send` as normal
2. ProtoPost receives the request and validates it
3. The email is saved to the local database
4. ProtoPost returns a `200 OK` response immediately
5. **No API call is made. No SMTP connection is opened. Nothing leaves your machine.**

The entire process takes about 1–3 milliseconds.

---

## What Sandbox Mode does NOT do

- It does **not** check if your provider credentials are correct
- It does **not** simulate provider errors or bounce responses
- It does **not** verify that your `from` address is valid
- It does **not** send the email to a fake inbox (unlike Mailtrap Email Testing)

Sandbox Mode is purely a capture-and-discard mechanism. The email goes into the database and nowhere else.

---

## The API response in Sandbox Mode

```json
{
  "status": "sandbox",
  "message": "Email intercepted by Sandbox Mode. Not sent.",
  "log_id": "e5f6g7h8-a1b2-c3d4-e5f6-...",
  "processing_time_ms": 1.8
}
```

> [!IMPORTANT]
> This response returns HTTP `200 OK`. Your app receives a success status code — the same as a real send. This is intentional: sandbox mode allows you to test your app's email flow without any special error-handling code or conditionals. Your app behaves exactly as it would in production.

---

## How to enable Sandbox Mode

**Option 1 — Dashboard toggle (recommended):**

Click the **Sandbox Mode** toggle in the ProtoPost header. It saves immediately.

**Option 2 — API:**

```bash
curl -X POST http://localhost:8000/api/config/routing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \  # omit if AUTH_TOKEN not set
  -d '{"mode": "smart", "sandbox": true}'
```

**Option 3 — Edit config.json directly:**

```json
{
  "routing": {
    "mode": "smart",
    "sandbox": true
  }
}
```

The change applies to the next email sent. No server restart needed.

---

## How to verify Sandbox Mode is working

1. Send a test email (either from the Test Send tab or via API)
2. Open the **Outbox & Logs** tab
3. Find your email in the list
4. The **Provider** column shows `[sandbox]` instead of a real provider name
5. The **Status** column shows `sandbox`

If the provider column shows a real provider name (like "My Resend Provider"), Sandbox Mode was off when that email was sent.

---

## What a sandbox log entry looks like

Each intercepted email creates a record like this in the database:

```json
{
  "id": "e5f6g7h8-...",
  "timestamp": "2026-02-22T12:01:44.000Z",
  "from_address": "you@example.com",
  "to_addresses": ["test@test.com"],
  "subject": "Test email",
  "body_text": "Hello!",
  "body_html": "<p>Hello!</p>",
  "provider_name": "[sandbox]",
  "provider_type": "sandbox",
  "status": "sandbox",
  "error_message": null,
  "processing_time_ms": 1.8
}
```

You can view the full body by clicking **View** on any log entry in the dashboard.

---

## When to use Sandbox Mode

```
Development phase:       SANDBOX ON  ✓
Staging / QA:            SANDBOX ON  ✓  (verify config via logs, real providers ready)
Demo / production:       SANDBOX OFF ✓  (after manually testing 1–2 real sends first)
```

> [!TIP]
> Before turning Sandbox Mode off for demo day, go to the **Test Send** tab and send a real email to yourself. Confirm it arrives. Then you know your provider credentials are correct and your routing is configured properly.

---

## Sandbox Mode and provider credentials

You can add providers while Sandbox Mode is on, but ProtoPost won't test whether the credentials work until you actually try to send. This means you can configure everything on a plane (no internet) and only test when you have connectivity.

> [!WARNING]
> Don't assume that because emails logged successfully in sandbox mode, your provider credentials are correct. They haven't been tested yet. Always do a real test send before your demo.

---

## How to turn Sandbox Mode off

Click the **Sandbox Mode** toggle in the dashboard header. It turns grey/off.

Or via API:

```bash
curl -X POST http://localhost:8000/api/config/routing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \  # omit if AUTH_TOKEN not set
  -d '{"mode": "smart", "sandbox": false}'
```

---

## See Also

- [docs/AUTH.md](AUTH.md) — Full auth integration guide (token generation, app env vars, code examples)
- [docs/ROUTING.md](ROUTING.md) — How routing modes interact with Sandbox Mode
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — "Email sends return 200 but nothing arrives"
- [docs/HACKATHON_QUICKSTART.md](HACKATHON_QUICKSTART.md) — Path A: Testing without real sends
- [docs/API.md](API.md#authentication) — Auth token setup
