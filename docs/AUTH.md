<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Authentication Guide

ProtoPost uses **optional bearer-token authentication**. It is off by default so local development is completely frictionless. When you host the gateway on a public URL, you should enable auth so only your own apps can use it.

---

## Setting your auth token

**If you're using the executable:**
The first-run wizard asks for your auth token. Paste it in when prompted.
To change it later, delete `init_config.json` next to the executable and relaunch.

**If you're using a .env file (Docker / cloud / advanced):**
```
AUTH_TOKEN=your-secret-token-here
```
The wizard is skipped automatically when a .env file is present.

---

## How it works

| State | `AUTH_TOKEN` env var | Behaviour |
|---|---|---|
| **Local / development** | _not set_ | All `/api/*` requests succeed with no credentials |
| **Production / public host** | set to any secret string | All `/api/*` requests must include `Authorization: Bearer <token>`. Requests without a valid token receive `401 Unauthorized`. |

The one exception is `GET /api/health`, which is always open (no auth required). This lets uptime monitors and load-balancer health checks work without needing credentials.

---

### Disabling Authentication

When `auth_token` is set to an empty string in `config.json`, authentication
is disabled entirely. All endpoints become publicly accessible without any
token header. This is the default state on first run.

Only enable authentication when deploying ProtoPost to a shared or
internet-accessible environment.

### Failed Authentication Response

```
HTTP 401 Unauthorized

{
  "detail": "Unauthorized"
}
```

This response is returned when the `Authorization` header is missing, empty,
or does not match the configured token.

---

## Generating a token

Use `openssl` to generate a cryptographically random token:

```bash
openssl rand -hex 32
```

Example output: `a3f1c8e2d94b7056e3a1d2f8c0b4e7a9d2c5f8b1e4a7d0c3f6b9e2d5a8c1f4b7`

Any strong random string works. Avoid reusing passwords or predictable values.

---

## Setting the token on the server

### Render

In the Render dashboard → your service → **Environment**:

| Key | Value |
|---|---|
| `AUTH_TOKEN` | your generated token |

See [docs/RENDER.md](RENDER.md) for the full setup guide.

### Railway

In the Railway dashboard → your service → **Variables**:

| Key | Value |
|---|---|
| `AUTH_TOKEN` | your generated token |

See [docs/RAILWAY.md](RAILWAY.md) for the full setup guide.

### Docker (docker-compose.yml)

In `docker-compose.yml` under `environment`, or in a `.env` file in the project root:

```yaml
# docker-compose.yml
services:
  protopost:
    environment:
      - AUTH_TOKEN=your-secret-token
```

Or using a `.env` file (recommended — never commit the token to git):

```bash
# .env
AUTH_TOKEN=a3f1c8e2d94b7056e3a1d2f8c0b4e7a9
```

```yaml
# docker-compose.yml
services:
  protopost:
    env_file:
      - .env
```

See [docs/DOCKER.md](DOCKER.md) for the full guide.

### Running locally with `uvicorn`

```bash
AUTH_TOKEN=your-secret-token uvicorn backend.main:app --reload
```

---

## Dashboard usage

The dashboard automatically handles authentication:

1. Open the dashboard in your browser.
2. Click the **🔓 lock icon** in the top-right corner of the header.
3. Enter the token when prompted and press **Save**.
4. The icon changes to 🔒.

### Dashboard Token Storage

The ProtoPost dashboard stores the authentication token in memory via the
`AuthToken` object defined in `js/auth.js`. The token is attached to every
API request as the `Authorization` header by the `GatewayAPI` fetch wrapper
in `js/api.js`.

The token is not written to `localStorage` or `sessionStorage`. It is held
only for the duration of the browser session. Refreshing the page will prompt
you to re-enter it.

To clear the token (e.g. to switch deployments), click the 🔒 icon and leave the prompt blank, then press **Save**.

---

## Integrating in your app

### Golden rule

> **Never hardcode the token in source code.**  
> Store it as an environment variable and read it at runtime. This keeps it out of your git history and lets you change it without a code change.

---

### Python — `requests`

```python
import os
import requests

PROTOPOST_URL = os.getenv("PROTOPOST_URL", "http://localhost:8000")
PROTOPOST_TOKEN = os.getenv("PROTOPOST_TOKEN")  # same value as AUTH_TOKEN on the server

def build_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if PROTOPOST_TOKEN:
        headers["Authorization"] = f"Bearer {PROTOPOST_TOKEN}"
    return headers

def send_email(to: str, subject: str, body_html: str) -> dict:
    payload = {
        "to": to,
        "subject": subject,
        "body_html": body_html,
    }
    response = requests.post(
        f"{PROTOPOST_URL}/api/send",
        json=payload,
        headers=build_headers(),
    )
    response.raise_for_status()
    return response.json()
```

Set env vars before running:

```bash
export PROTOPOST_URL=https://protopost.onrender.com
export PROTOPOST_TOKEN=a3f1c8e2d94b7056e3a1d2f8c0b4e7a9
python your_app.py
```

---

### Python — `httpx` (async)

```python
import os
import httpx

PROTOPOST_URL = os.getenv("PROTOPOST_URL", "http://localhost:8000")
PROTOPOST_TOKEN = os.getenv("PROTOPOST_TOKEN")

def build_headers() -> dict:
    headers = {}
    if PROTOPOST_TOKEN:
        headers["Authorization"] = f"Bearer {PROTOPOST_TOKEN}"
    return headers

async def send_email(to: str, subject: str, body_html: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PROTOPOST_URL}/api/send",
            json={"to": to, "subject": subject, "body_html": body_html},
            headers=build_headers(),
        )
        response.raise_for_status()
        return response.json()
```

---

### JavaScript / TypeScript (browser or Node.js)

Store the token in an environment variable and pass it to the frontend at build time (e.g. via Vite's `import.meta.env` or Next.js's `process.env`), or keep it server-side only and call the gateway from your backend.

**Option A — Backend proxy (recommended for security)**

Keep `PROTOPOST_TOKEN` on the server. Your frontend calls your own backend, which forwards to ProtoPost with the token. The token is never exposed to the browser.

```typescript
// server-side Node.js / Next.js API route
const PROTOPOST_URL = process.env.PROTOPOST_URL ?? "http://localhost:8000";
const PROTOPOST_TOKEN = process.env.PROTOPOST_TOKEN;  // server env only

export async function sendEmail(to: string, subject: string, bodyHtml: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (PROTOPOST_TOKEN) {
    headers["Authorization"] = `Bearer ${PROTOPOST_TOKEN}`;
  }

  const res = await fetch(`${PROTOPOST_URL}/api/send`, {
    method: "POST",
    headers,
    body: JSON.stringify({ to, subject, body_html: bodyHtml }),
  });

  if (!res.ok) throw new Error(`ProtoPost error: ${res.status}`);
  return res.json();
}
```

**Option B — Direct browser call (internal / hackathon use, no sensitive data)**

Only acceptable on intranet or short-lived hackathon deployments where exposing the token to the browser is acceptable.

```javascript
const PROTOPOST_URL = import.meta.env.VITE_PROTOPOST_URL ?? "http://localhost:8000";
const PROTOPOST_TOKEN = import.meta.env.VITE_PROTOPOST_TOKEN;  // set in .env.local

async function sendEmail(to, subject, bodyHtml) {
  const headers = { "Content-Type": "application/json" };
  if (PROTOPOST_TOKEN) {
    headers["Authorization"] = `Bearer ${PROTOPOST_TOKEN}`;
  }

  const res = await fetch(`${PROTOPOST_URL}/api/send`, {
    method: "POST",
    headers,
    body: JSON.stringify({ to, subject, body_html: bodyHtml }),
  });

  if (!res.ok) throw new Error(`ProtoPost error: ${res.status}`);
  return res.json();
}
```

---

### Node.js — `axios`

```javascript
const axios = require("axios");

const PROTOPOST_URL = process.env.PROTOPOST_URL || "http://localhost:8000";
const PROTOPOST_TOKEN = process.env.PROTOPOST_TOKEN;

const client = axios.create({
  baseURL: PROTOPOST_URL,
  headers: PROTOPOST_TOKEN
    ? { Authorization: `Bearer ${PROTOPOST_TOKEN}` }
    : {},
});

async function sendEmail(to, subject, bodyHtml) {
  const { data } = await client.post("/api/send", {
    to,
    subject,
    body_html: bodyHtml,
  });
  return data;
}
```

---

### curl

```bash
# With auth
curl -X POST https://protopost.onrender.com/api/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PROTOPOST_TOKEN" \
  -d '{"to":"user@example.com","subject":"Hello","body_html":"<p>Hi</p>"}'

# Without auth (local only)
curl -X POST http://localhost:8000/api/send \
  -H "Content-Type: application/json" \
  -d '{"to":"user@example.com","subject":"Hello","body_html":"<p>Hi</p>"}'
```

---

## Environment variable naming convention

| Variable | Set on | Purpose |
|---|---|---|
| `AUTH_TOKEN` | **ProtoPost server** | Token the server checks against |
| `PROTOPOST_TOKEN` | **Your app** | Token your app sends to the server (must match `AUTH_TOKEN`) |
| `PROTOPOST_URL` | **Your app** | The base URL of your ProtoPost deployment |

Using different names (`AUTH_TOKEN` vs `PROTOPOST_TOKEN`) keeps the two sides clearly separate. In a `.env` file for your app:

```bash
# .env in your app (not in the ProtoPost repo)
PROTOPOST_URL=https://protopost.onrender.com
PROTOPOST_TOKEN=a3f1c8e2d94b7056e3a1d2f8c0b4e7a9   # same value as AUTH_TOKEN on the server
```

---

## Rotating the token

1. Generate a new token: `openssl rand -hex 32`
2. Update `AUTH_TOKEN` on the server (Render / Railway / Docker env var).
3. Update `PROTOPOST_TOKEN` in each app that calls the gateway.
4. The old token is immediately invalid after the server restarts with the new value.

---

## Checklist

Before going live with auth enabled:

- [ ] `AUTH_TOKEN` set on the server (Render / Railway / Docker)
- [ ] `PROTOPOST_TOKEN` set in every app that calls the gateway
- [ ] Token not committed to git (add `.env` to `.gitignore`)
- [ ] Dashboard unlocked with the correct token (🔒 icon in header)
- [ ] Test: `curl -H "Authorization: Bearer $PROTOPOST_TOKEN" https://your-url/api/health` returns `{"status":"ok"}`

---

## See Also

- [docs/API.md](API.md#authentication) — Bearer token header format and 401 response shape
- [docs/HOSTING.md](HOSTING.md) — Where to set `AUTH_TOKEN` per platform (Render, Railway, Docker, VPS)
- [docs/DOCKER.md](DOCKER.md) — Docker env var setup
- [docs/RENDER.md](RENDER.md) — Render env var setup
- [docs/RAILWAY.md](RAILWAY.md) — Railway variables setup
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 401 errors, "green lock but still 401", and forgotten token
