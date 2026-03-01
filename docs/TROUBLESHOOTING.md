<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Troubleshooting

Every error listed here includes the exact symptom, the most likely cause, and step-by-step fix instructions.

---

## Executable issues

**macOS: “ProtoPost-macos cannot be opened because it is from an unidentified developer”**
Right-click the file → Open → click Open in the dialog.
You only need to do this once. After that it launches normally.

**Windows: SmartScreen warning (“Windows protected your PC”)**
Click “More info” → “Run anyway”. This appears because the binary is not
code-signed. It is safe to proceed.

**The wizard appeared but I want to change my port or auth token**
Delete `init_config.json` from the same folder as the executable and relaunch.
The wizard will run again.

**The browser didn’t open automatically**
The server is still running. Manually open http://localhost:8000 (or whatever
port you chose during setup). The auto-open uses a 1.5s delay and may miss on
very slow machines.

**The executable crashes immediately with no error**
Launch from a terminal instead of double-clicking so you can see the error output:
- Windows → open PowerShell, drag the .exe into it, press Enter
- macOS → open Terminal, drag the binary into it, press Enter
- Linux → `chmod +x ProtoPost-linux && ./ProtoPost-linux`

**Port already in use**
Delete `init_config.json` and relaunch. Pick a different port in the wizard,
such as 8001 or 9000.

---

### ❌ `uvicorn: command not found`

**What's happening:**
The `uvicorn` command isn't on your system PATH.

**Most likely cause:**
Either uvicorn wasn't installed, or it was installed in a Python environment that isn't active.

**Fix:**

```bash
# Install uvicorn explicitly
pip install uvicorn

# Then try again
uvicorn backend.main:app --reload --port 8000
```

If that still fails, run it as a Python module instead:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

**If that didn't work:**
Check that you're in the right directory and that your Python environment (venv, conda, etc.) is activated.

---

### ❌ `Address already in use — port 8000`

**What's happening:**
Something else is already running on port 8000.

**Most likely cause:**
A previous instance of the server didn't stop, or another app is using that port.

**Fix:**

Find and stop the process:

```bash
# On macOS / Linux
lsof -ti :8000 | xargs kill -9

# On Windows (PowerShell)
netstat -ano | findstr :8000
# Then kill the PID shown:
taskkill /PID <the_pid> /F
```

Or just use a different port:

```bash
uvicorn backend.main:app --reload --port 8001
```

Then open `http://localhost:8001` in your browser.

---

### ❌ Dashboard shows "Cannot connect to server" (red dot)

**What's happening:**
The browser can't reach the ProtoPost server.

**Most likely cause:**
The server isn't running, or it's running on a different port than the one you're accessing.

**Fix:**

1. Check your terminal — is the `uvicorn` process still running? Look for: `INFO: Uvicorn running on http://0.0.0.0:8000`
2. If it crashed, scroll up for the error message and restart it
3. Make sure the URL in your browser matches the port you started the server on

**If that didn't work:**
Try accessing `http://localhost:8000/api/health` directly. If you see `{"status": "healthy"}`, the server is running fine and the issue is a browser cache or CORS problem — try a hard refresh (Ctrl+Shift+R).

---

### ❌ Email sends return 200 but no email arrives

**What's happening:**
Your app gets a success response, but the email never shows up in the inbox.

**Most likely cause:**
Sandbox Mode is turned on. Check the toggle in the ProtoPost dashboard header.

**Fix:**

1. Open the ProtoPost dashboard
2. Look at the **Sandbox Mode** toggle in the header — if it's lit up/on, that's the cause
3. Toggle it off
4. Re-send the email

Also check the **Outbox & Logs** tab. If emails show `[sandbox]` as the provider, that confirms Sandbox Mode intercepted them.

**If that didn't work:**
Sandbox Mode is off, but delivery is still failing silently — check the **Status** column in the Outbox tab. If it says `failed`, click **View** to see the full error from the provider.

---

### ❌ Gmail: `SMTPAuthenticationError`

**What's happening:**
Gmail rejected the username/password combination.

**Most likely cause:**
You're using your regular Gmail password instead of an App Password.

**Fix:**

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Create a new App Password named `Email Gateway`
3. Copy the 16-character result
4. In the ProtoPost dashboard, edit your Gmail provider and replace the password with the App Password

> [!NOTE]
> App Passwords look like: `abcd efgh ijkl mnop` — spaces are fine to include or remove.

**If that didn't work:**
Your Google account may have "Less secure app access" policies in place (common for Workspace accounts). Contact your Google Workspace admin.

---

### ❌ Gmail: `Application-specific password required`

**What's happening:**
Google is explicitly telling you that an App Password is needed.

**Most likely cause:**
You're using your regular Gmail password on an account that has 2-Step Verification enabled.

**Fix:**
Same as `SMTPAuthenticationError` above — create an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

---

### ❌ Resend: `403 Forbidden — domain not verified`

**What's happening:**
Resend rejected the send because the `from` address domain isn't verified in your Resend account.

**Most likely cause:**
You're sending from `you@yourdomain.com` but `yourdomain.com` isn't in your Resend verified domains list.

**Fix:**

Option A — Verify your domain in Resend:
1. Go to the Resend dashboard → **Domains**
2. Add your domain and follow the DNS instructions
3. Wait for verification (usually a few minutes)

Option B — Use the Resend sandbox domain for testing:
- Change your `from` address to: `onboarding@resend.dev`
- This works without domain verification

> [!WARNING]
> When using `onboarding@resend.dev`, you can only send to email addresses you've verified in your Resend account. It's for testing only.

---

### ❌ Resend: `422 — from address does not match verified domain`

**What's happening:**
The `from` field in your email uses a domain that isn't verified.

**Most likely cause:**
You verified `yourdomain.com` in Resend but your `from` address is something like `noreply@subdomain.yourdomain.com` — subdomains must be separately verified.

**Fix:**
Either verify the subdomain in Resend, or change your `from` address to use the exact domain you verified.

---

### ❌ Mailtrap: `401 Unauthorized`

**What's happening:**
Mailtrap rejected the API token.

**Most likely cause:**
You're using a **Testing** API token instead of a **Sending** API token. These are different products.

**Fix:**

1. In Mailtrap, click **Email Sending** (left sidebar)
2. Click **Transactional Stream**
3. Click **API Tokens**
4. Generate a new token from **this** section
5. Update your ProtoPost provider with the new token

> [!WARNING]
> Do **not** use the token from `Testing → Inboxes`. That's for a different Mailtrap product that won't deliver real emails.

---

### ❌ Custom SMTP: `Connection refused` on port 587

**What's happening:**
The server can't open a TCP connection to your SMTP host on port 587.

**Most likely cause:**
Outbound port 587 is blocked by your ISP or cloud VM provider. This is very common on AWS EC2, Google Cloud, and similar platforms.

**Fix:**

Try port 2525 instead:

```json
{
  "smtp_port": 2525,
  "smtp_use_tls": true
}
```

Most providers (SendGrid, Mailgun, etc.) also support port 2525 for exactly this reason. Check your provider's documentation.

---

### ❌ Custom SMTP: `SSL: WRONG_VERSION_NUMBER`

**What's happening:**
The TLS handshake failed because the server expected a different protocol version.

**Most likely cause:**
You have both `smtp_use_tls` and `smtp_use_ssl` set to `true` at the same time. Only one should be active.

**Fix:**

For port 587 (STARTTLS):
```json
{
  "smtp_use_tls": true,
  "smtp_use_ssl": false
}
```

For port 465 (SSL):
```json
{
  "smtp_use_tls": false,
  "smtp_use_ssl": true
}
```

---

### ❌ `502 — All providers failed` with empty error list

**What's happening:**
The gateway tried every provider and all failed, but there's no useful error message.

**Most likely cause:**
All providers are disabled or have weight 0.

**Fix:**

1. Open the dashboard → **Providers** tab
2. Make sure at least one provider has the **Enabled** toggle turned on
3. Make sure that provider's **Weight** is greater than 0
4. Try sending again

**If that didn't work:**
Click **View** on the failed log entry in the Outbox tab — the full provider error is stored there.

---

### ❌ Weight changes don't seem to affect routing

**What's happening:**
You changed provider weights but traffic still seems to go to the same provider.

**Most likely cause:**
You're in Smart Failover mode, not Manual Load Balancing. In Smart Failover mode, the highest-weight provider always handles everything until it fails — weights are for priority ordering, not traffic splitting.

**Fix:**

To split traffic, switch to **Manual Load Balancing** mode:
1. Open the **Routing** tab
2. Click **Manual Load Balancing**

---

### ❌ `config.json` is corrupt or can't be parsed

**What's happening:**
The server starts but returns errors on every request, or the dashboard shows no providers/settings.

**Most likely cause:**
The `config.json` file has invalid JSON — either from a direct edit or an interrupted write.

**Fix:**

Delete it and let the server recreate the defaults:

```bash
rm config.json
```

Then restart the server. You'll need to re-add your providers.

> [!TIP]
> Take a backup of your config.json before making manual edits: `cp config.json config.json.bak`

---

### ❌ Logs table is empty even though emails were sent

**What's happening:**
The Outbox & Logs tab shows nothing.

**Most likely cause:**
The database file wasn't created in the expected location, or the app is pointing to a different file.

**Fix:**

```bash
# Check if the database file exists
ls -la emails.db

# If it doesn't exist, the server might be creating it elsewhere
find . -name "*.db" 2>/dev/null
```

Restart the server from the project root directory, not a subdirectory.

---

### ❌ `ModuleNotFoundError: No module named 'aiosmtplib'`

**What's happening:**
A required Python package isn't installed.

**Most likely cause:**
The dependencies were installed in a different Python environment, or the install was incomplete.

**Fix:**

```bash
pip install -r requirements.txt
```

If you're using a virtual environment, make sure it's activated first:

```bash
# Create and activate (if not done yet)
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Then install
pip install -r requirements.txt
```

---

### ❌ Running on a cloud VM — dashboard not accessible from browser

**What's happening:**
The server starts fine on the VM, but you can't reach it from your laptop's browser.

**Most likely cause:**
The server is listening on `127.0.0.1` (localhost only) instead of `0.0.0.0` (all interfaces). Also, the VM's firewall may be blocking port 8000.

**Fix:**

Start the server with the correct host binding:

```bash
uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0
```

Then open your VM's firewall to allow inbound TCP on port 8000. On AWS, add an inbound Security Group rule. On GCP, add a Firewall rule. On DigitalOcean, configure the droplet's firewall.

Access the dashboard at `http://<your-vm-ip>:8000`.

---

### ❌ Windows: `asyncio.exceptions.CancelledError` on startup

**What's happening:**
The server crashes immediately on Windows with an asyncio error.

**Most likely cause:**
Windows uses a different asyncio event loop policy by default that's incompatible with uvicorn's default settings.

**Fix:**

Use this command to start the server on Windows:

```bash
python -m uvicorn backend.main:app --reload --port 8000 --loop asyncio
```

If that doesn't work, install the `pywin32` package:

```bash
pip install pywin32
```

Then retry the standard start command.

---

### ❌ `401 Unauthorized` on every API call

**What's happening:**
Every request to `/api/*` returns a 401 response.

**Most likely cause:**
The server has `AUTH_TOKEN` set as an environment variable, but your app (or the dashboard) isn't sending the `Authorization: Bearer <token>` header.

**Fix for the dashboard:**

1. Open the ProtoPost dashboard
2. Click the 🔓 lock icon in the top-right of the header
3. Enter your `AUTH_TOKEN` value in the prompt
4. Click OK — the icon turns 🔒 green
5. Refresh the page

The token is saved in `localStorage` and sent automatically on every request after that.

**Fix for your app code:**

Add the `Authorization` header to every request:

```python
# Python
requests.post("http://your-host/api/send",
    headers={"Authorization": "Bearer your-secret-token"},
    json={...}
)
```

```javascript
// JavaScript
fetch("/api/send", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer your-secret-token"
    },
    body: JSON.stringify({...})
})
```

---

### ❌ Dashboard lock icon is green but API calls still return 401

**What's happening:**
The dashboard shows the token is set (🔒 green), but requests still fail with 401.

**Most likely cause:**
The token stored in `localStorage` doesn't match the `AUTH_TOKEN` on the server — either it was changed on the server or entered incorrectly.

**Fix:**

1. Click the 🔒 lock icon in the dashboard header
2. Clear the field and click OK to remove the old token
3. Click the icon again and enter the correct token
4. Verify the value matches `AUTH_TOKEN` on your server exactly (case-sensitive, no trailing spaces)

To check the current token on Render or Railway, go to the service's **Environment** / **Variables** tab.

---

### ❌ Forgot the AUTH_TOKEN — locked out of the dashboard

**What's happening:**
You set `AUTH_TOKEN` but can't remember what it was, and the dashboard won't load data.

**Fix:**

On Render:
1. Go to your service → **Environment**
2. Find `AUTH_TOKEN` — the value is visible there
3. Copy it and enter it in the dashboard lock icon prompt

On Railway:
1. Go to your service → **Variables**
2. Find `AUTH_TOKEN` and copy the value

If you want to reset it: update `AUTH_TOKEN` to a new value in the environment settings and redeploy. Then enter the new token in the dashboard.

---

### ❌ `AUTH_TOKEN` is set but the API still works without a token

**What's happening:**
You set `AUTH_TOKEN` in a `.env` file, but requests without an `Authorization` header still succeed.

**Most likely cause:**
ProtoPost doesn't automatically load `.env` files — the variable must be passed to the process directly.

**Fix:**

```bash
# Pass it inline
AUTH_TOKEN=your-secret-token uvicorn backend.main:app --port 8000

# Or export it first
export AUTH_TOKEN=your-secret-token
uvicorn backend.main:app --port 8000
```

For Docker, use the `-e` flag or the `environment:` block in `docker-compose.yml` — not a `.env` file inside the container unless you've configured Docker to load it.

---

## Quick reference table

| Symptom | Almost Always Because | Quick Fix |
|---|---|---|
| No emails arriving | Sandbox Mode is ON | Check the toggle in the header |
| Gmail auth failing | App Password not set up | Enable 2-Step Verification first |
| Resend 403 | Sending from unverified domain | Use `onboarding@resend.dev` for testing |
| Mailtrap 401 | Using Testing token, not Sending | Get token from Email Sending tab |
| Port already in use | Another server on 8000 | Use `--port 8001` |
| Weights ignored | All weights are 0 | Set at least one provider weight > 0 |
| 502 all providers failed | Providers disabled | Enable at least one in the Providers tab |
| SMTP connection refused | Port 587 blocked by VM/ISP | Try port 2525 |
| SSL wrong version | Both TLS and SSL enabled | Enable only one (TLS for 587, SSL for 465) |
| 401 on all API calls | AUTH_TOKEN set but header missing | Enter token in dashboard 🔓 lock icon |
| 401 despite token set in dashboard | Token doesn't match server's AUTH_TOKEN | Re-enter token via lock icon |
| AUTH_TOKEN ignored | `.env` file not loaded by process | Export env var or use `-e` flag |

---

## See Also

- [docs/AUTH.md](AUTH.md) — Full auth integration guide (token generation, app env vars, code examples)
- [docs/PROVIDERS.md](PROVIDERS.md) — Provider-specific setup steps
- [docs/SANDBOX.md](SANDBOX.md) — Sandbox Mode reference
- [docs/API.md](API.md) — Full error response formats
- [docs/API.md](API.md#authentication) — Auth token setup and header format
