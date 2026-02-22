<!-- Last updated: when this project was generated -->

[← Back to README](../README.md)

# API Reference

ProtoPost is a local HTTP server. There's no authentication — it's designed to run on your machine, not exposed to the internet.

---

## Base URL

```
http://localhost:8000
```

If you started the server on a different port, replace `8000` accordingly.

---

## Request format

All request bodies are JSON. Always include the `Content-Type: application/json` header.

---

## Endpoints

### POST /v1/send

Send an email through the gateway. This is the only endpoint your app needs to call.

**Request Body**

| Field | Type | Required | Description |
|---|---|---|---|
| `from` | string (email) | Yes | Sender address |
| `to` | array[string] | Yes | Recipient addresses (min 1, max 50) |
| `subject` | string | Yes | Email subject line |
| `body_text` | string | No* | Plain text body |
| `body_html` | string | No* | HTML body |
| `reply_to` | string (email) | No | Reply-to address |

*At least one of `body_text` or `body_html` must be provided.

**Example Request**

```bash
curl -X POST http://localhost:8000/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "from": "you@example.com",
    "to": ["recipient@example.com"],
    "subject": "Hello from the gateway",
    "body_html": "<h1>It works!</h1>",
    "body_text": "It works!"
  }'
```

**Success Response (200)**

```json
{
  "status": "success",
  "message": "Email sent successfully via My Resend Provider",
  "provider": {
    "id": "a1b2c3d4-...",
    "name": "My Resend Provider",
    "type": "resend"
  },
  "log_id": "e5f6g7h8-...",
  "processing_time_ms": 412.3,
  "message_id": "msg_abc123"
}
```

**Sandbox Response (200)**

```json
{
  "status": "sandbox",
  "message": "Email intercepted by Sandbox Mode. Not sent.",
  "log_id": "e5f6g7h8-...",
  "processing_time_ms": 1.8
}
```

**Error Responses**

`422 Unprocessable Entity` — Validation error (missing required field, invalid email, etc.):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "subject"],
      "msg": "Field required"
    }
  ]
}
```

`502 Bad Gateway` — All providers failed:

```json
{
  "detail": "All providers failed. Errors: Resend: 403 Forbidden; Gmail: SMTPAuthenticationError"
}
```

`503 Service Unavailable` — No providers configured or all disabled:

```json
{
  "detail": "No providers configured. Add a provider in the dashboard."
}
```

---

### GET /v1/logs

Get a list of all sent (and sandbox) emails. Sorted by most recent first.

**Query Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 100 | Max results to return (max 500) |
| `offset` | integer | 0 | Pagination offset |

**Example Request**

```bash
curl "http://localhost:8000/v1/logs?limit=20&offset=0"
```

**Success Response (200)**

```json
{
  "logs": [
    {
      "id": "a1b2c3d4-...",
      "timestamp": "2026-02-22T12:04:32.123Z",
      "from_address": "you@example.com",
      "to_addresses": ["recipient@example.com"],
      "subject": "Hello!",
      "provider_name": "My Resend Provider",
      "provider_type": "resend",
      "status": "success",
      "processing_time_ms": 412.3
    }
  ],
  "total": 142,
  "limit": 20,
  "offset": 0
}
```

---

### GET /v1/logs/{log_id}

Get full details for a single log entry, including the email body.

**Example Request**

```bash
curl "http://localhost:8000/v1/logs/a1b2c3d4-e5f6-..."
```

**Success Response (200)**

```json
{
  "id": "a1b2c3d4-...",
  "timestamp": "2026-02-22T12:04:32.123Z",
  "from_address": "you@example.com",
  "to_addresses": ["recipient@example.com"],
  "subject": "Hello!",
  "body_text": "It works!",
  "body_html": "<h1>It works!</h1>",
  "reply_to": null,
  "provider_name": "My Resend Provider",
  "provider_type": "resend",
  "status": "success",
  "error_message": null,
  "message_id": "msg_abc123",
  "processing_time_ms": 412.3
}
```

**Error Response (404)**

```json
{
  "detail": "Log entry not found"
}
```

---

### GET /v1/stats

Get aggregate statistics for all emails sent.

**Example Request**

```bash
curl "http://localhost:8000/v1/stats"
```

**Success Response (200)**

```json
{
  "total_sent": 142,
  "total_failed": 2,
  "total_sandbox": 58,
  "avg_processing_time_ms": 340.1,
  "by_provider": {
    "My Resend Provider": {
      "sent": 98,
      "failed": 1
    },
    "My Gmail": {
      "sent": 44,
      "failed": 1
    }
  }
}
```

---

### GET /v1/config

Get the current gateway configuration.

**Example Request**

```bash
curl "http://localhost:8000/v1/config"
```

**Success Response (200)**

```json
{
  "providers": [
    {
      "id": "a1b2c3d4-...",
      "name": "My Resend Provider",
      "type": "resend",
      "enabled": true,
      "weight": 100
    }
  ],
  "routing": {
    "mode": "smart",
    "sandbox": false
  },
  "version": 1
}
```

> [!NOTE]
> Credential fields (API keys, passwords) are masked in this response. They are never returned in plaintext via the API.

---

### PUT /v1/config

Replace the entire configuration. Use this to restore a saved config or reset to defaults.

**Example Request**

```bash
curl -X PUT http://localhost:8000/v1/config \
  -H "Content-Type: application/json" \
  -d '{
    "providers": [],
    "routing": {
      "mode": "smart",
      "sandbox": true
    }
  }'
```

**Success Response (200)** — Returns the updated config (same format as GET /v1/config).

---

### POST /v1/config/providers

Add a new provider.

**Request Body (Resend)**

```json
{
  "name": "My Resend Provider",
  "type": "resend",
  "enabled": true,
  "weight": 100,
  "api_key": "re_xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

**Request Body (Gmail)**

```json
{
  "name": "My Gmail",
  "type": "gmail",
  "enabled": true,
  "weight": 50,
  "gmail_address": "you@gmail.com",
  "gmail_app_password": "xxxx xxxx xxxx xxxx"
}
```

**Request Body (Custom SMTP)**

```json
{
  "name": "My SMTP",
  "type": "custom_smtp",
  "enabled": true,
  "weight": 100,
  "smtp_host": "smtp.sendgrid.net",
  "smtp_port": 587,
  "smtp_username": "apikey",
  "smtp_password": "SG.xxxxxx",
  "smtp_use_tls": true,
  "smtp_use_ssl": false
}
```

**Success Response (201)** — Returns the created provider object with its generated `id`.

---

### PUT /v1/config/providers/{provider_id}

Update an existing provider. The request body is the same format as POST /v1/config/providers.

**Example Request**

```bash
curl -X PUT "http://localhost:8000/v1/config/providers/a1b2c3d4-..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Resend Provider",
    "type": "resend",
    "enabled": false,
    "weight": 100,
    "api_key": "re_new_key_here"
  }'
```

**Success Response (200)** — Returns the updated provider.

**Error Response (404)**

```json
{
  "detail": "Provider not found"
}
```

---

### DELETE /v1/config/providers/{provider_id}

Delete a provider permanently.

**Example Request**

```bash
curl -X DELETE "http://localhost:8000/v1/config/providers/a1b2c3d4-..."
```

**Success Response (200)**

```json
{
  "message": "Provider deleted successfully"
}
```

---

### POST /v1/config/routing

Update routing mode and sandbox status.

**Request Body**

| Field | Type | Values | Description |
|---|---|---|---|
| `mode` | string | `"smart"`, `"manual"` | Routing algorithm |
| `sandbox` | boolean | `true`, `false` | Enable/disable sandbox mode |

**Example Request**

```bash
curl -X POST http://localhost:8000/v1/config/routing \
  -H "Content-Type: application/json" \
  -d '{"mode": "smart", "sandbox": false}'
```

**Success Response (200)**

```json
{
  "mode": "smart",
  "sandbox": false
}
```

---

### GET /v1/health

Health check. Use this to verify the server is running.

**Example Request**

```bash
curl "http://localhost:8000/v1/health"
```

**Success Response (200)**

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

If you get a connection error, the server isn't running.

---

## Integration examples

### Python (httpx — async)

```python
import httpx

async def send_email(to: str, subject: str, html: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/send",
            json={
                "from": "you@example.com",
                "to": [to],
                "subject": subject,
                "body_html": html,
            }
        )
        response.raise_for_status()
        return response.json()
```

### Python (requests — sync)

```python
import requests

def send_email(to: str, subject: str, html: str) -> dict:
    response = requests.post(
        "http://localhost:8000/v1/send",
        json={
            "from": "you@example.com",
            "to": [to],
            "subject": subject,
            "body_html": html,
        }
    )
    response.raise_for_status()
    return response.json()
```

### JavaScript (fetch API)

```javascript
async function sendEmail(to, subject, html) {
    const response = await fetch('http://localhost:8000/v1/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            from: 'you@example.com',
            to: [to],
            subject,
            body_html: html
        })
    });
    if (!response.ok) {
        throw new Error(`Email failed: ${await response.text()}`);
    }
    return response.json();
}
```

### Node.js (axios)

```javascript
const axios = require('axios');

const sendEmail = async (to, subject, html) => {
    const { data } = await axios.post('http://localhost:8000/v1/send', {
        from: 'you@example.com',
        to: [to],
        subject,
        body_html: html,
    });
    return data;
};
```

### curl

```bash
curl -X POST http://localhost:8000/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "from": "you@example.com",
    "to": ["recipient@example.com"],
    "subject": "Hello from the gateway",
    "body_html": "<h1>It works!</h1>",
    "body_text": "It works!"
  }'
```

---

## See Also

- [docs/PROVIDERS.md](PROVIDERS.md) — Provider-specific fields for POST /v1/config/providers
- [docs/SANDBOX.md](SANDBOX.md) — What the sandbox response means
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Fixing common 502 / 422 errors
