# ProtoPost — Configuration Reference

## Location and Auto-Creation

ProtoPost reads its configuration from `config.json` in the project root.
If this file does not exist when the server starts, it is created automatically
with default values. No manual setup is required for first run.

Config changes made via the dashboard or `POST /api/config` take effect on the
next request. The server reads `config.json` on every send — no restart is needed.

Writes to `config.json` are atomic: the new content is written to a temporary
file first, then renamed over the existing file. This prevents corrupt partial
writes in the event of a crash during save.

`config.json` contains provider credentials. It is already listed in
`.gitignore`. Do not commit it to version control.

## Top-Level Schema

| Field | Type | Default | Description |
|---|---|---|---|
| `auth_token` | string | `""` | Token required in the `Authorization: Bearer` header. Empty string disables auth entirely. |
| `sandbox` | boolean | `false` | If `true`, no providers are called. All emails are logged as sandbox. |
| `mode` | string | `"manual"` | Routing mode: `"manual"` for weighted random, `"smart"` for failover. |
| `providers` | array | `[]` | List of provider configuration objects. See below. |

## Provider Object Schema

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique identifier for this provider. Used in logs and dashboard. |
| `name` | string | yes | Display name shown in the dashboard UI. |
| `type` | string | yes | Provider type: `"resend"`, `"custom_smtp"`, `"gmail"`, or `"mailtrap"`. |
| `weight` | integer | no | Routing weight 0–100. Higher weight = higher selection probability. `0` means never selected. Default: `100`. |
| `enabled` | boolean | no | If `false`, this provider is excluded from routing entirely. Default: `true`. |
| `api_key` | string | no | API key used by Resend and Mailtrap providers. |
| `smtp_host` | string | no | SMTP server hostname (e.g. `smtp.gmail.com`). |
| `smtp_port` | integer | no | SMTP port. Use `587` for STARTTLS, `465` for implicit TLS. |
| `smtp_username` | string | no | SMTP login username (usually your email address). |
| `smtp_password` | string | no | SMTP login password or app password. |
| `smtp_use_tls` | boolean | no | Enable STARTTLS (port 587). Do not combine with `smtp_use_ssl`. |
| `smtp_use_ssl` | boolean | no | Enable implicit TLS (port 465). Do not combine with `smtp_use_tls`. |
| `gmail_address` | string | no | Gmail account address (Gmail provider only). |
| `gmail_app_password` | string | no | Gmail app-specific password (Gmail provider only). |

## TLS Note

`smtp_use_tls` and `smtp_use_ssl` are mutually exclusive. Setting both to
`true` will cause a connection error. Use `smtp_use_tls: true` for port 587
and `smtp_use_ssl: true` for port 465.

## Example config.json

```json
{
  "providers": [
    {
      "id": "resend-primary",
      "name": "Resend (Primary)",
      "type": "resend",
      "weight": 90,
      "enabled": true,
      "api_key": "re_abc123XYZdefGHI456jklMNO"
    },
    {
      "id": "gmail-fallback",
      "name": "Gmail (Fallback)",
      "type": "custom_smtp",
      "weight": 10,
      "enabled": true,
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "smtp_username": "yourname@gmail.com",
      "smtp_password": "abcd efgh ijkl mnop",
      "smtp_use_tls": true,
      "smtp_use_ssl": false
    }
  ],
  "routing": {
    "mode": "smart",
    "sandbox": false
  },
  "version": 1
}
```

In this example, smart mode will try Resend first (weight 90) and fall back
to Gmail if Resend fails.

## Resetting to Defaults

Delete `config.json` from the project root and restart the server. It will be
recreated with an empty provider list, sandbox disabled, manual mode, and no
auth token.
