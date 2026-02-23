<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Hosting Options for ProtoPost

ProtoPost needs two things to run in the cloud: a **Python/Docker runtime** and a **persistent filesystem** (for `config.json` and `emails.db`). Serverless and edge platforms that don't provide these won't work.

This page compares every viable option. The ones with full step-by-step guides are linked.

---

## Quick comparison

| Platform | Persistent storage | Free tier | Setup friction | Full guide |
|---|---|---|---|---|
| **Render** | ✅ Persistent disk | ✅ Yes ($0.25/GB disk add-on) | Low — UI only | [docs/RENDER.md](RENDER.md) |
| **Railway** | ✅ Persistent volume | ✅ $5 signup credit, no card | Low — UI only | [docs/RAILWAY.md](RAILWAY.md) |
| **Fly.io** | ✅ Persistent volumes | ✅ Generous free allowance | Medium — CLI required | See notes below |
| **DigitalOcean App Platform** | ✅ Storage add-on | ❌ $5/month minimum | Low — UI only | See notes below |
| **Any VPS** (Hetzner, Linode, DO Droplet) | ✅ VM disk | ✅ Cheapest long-term | Medium — SSH + Docker | See notes below |
| **Docker local / self-hosted** | ✅ Docker volume | ✅ Free | None | [docs/DOCKER.md](DOCKER.md) |
| **Cloudflare Workers / Pages** | ❌ No Python, no disk | — | — | ❌ Not compatible |
| **Vercel** | ❌ Ephemeral `/tmp` only | — | — | ❌ Not compatible |
| **Netlify Functions** | ❌ No Python runtime | — | — | ❌ Not compatible |
| **AWS Lambda / GCP Cloud Run** | ⚠️ Needs external DB | — | High | Not recommended for hackathons |

---

## Render — recommended for most teams

Render deploys straight from GitHub with no CLI. Add the persistent disk and set two environment variables — done.

**Best for:** Teams that want a zero-friction shared URL with guaranteed persistence.  
**Guide:** [docs/RENDER.md](RENDER.md)

---

## Railway — recommended if you want even faster setup

Railway is marginally faster to set up than Render (fewer clicks to get a public URL). The $5 signup credit covers a full hackathon weekend with no card required.

**Best for:** Individuals or teams that want the absolute fastest cloud deploy.  
**Guide:** [docs/RAILWAY.md](RAILWAY.md)

---

## Fly.io

Fly.io is Docker-native and has excellent persistent volumes. It requires the `flyctl` CLI, which adds a little friction compared to Render/Railway.

**Setup overview:**
1. Install the CLI: `brew install flyctl` / `curl -L https://fly.io/install.sh | sh`
2. Log in: `fly auth login`
3. Launch: `fly launch` (detects the Dockerfile automatically)
4. Create a volume: `fly volumes create protopost_data --size 1`
5. Mount it in `fly.toml`:
   ```toml
   [mounts]
     source = "protopost_data"
     destination = "/data"
   ```
6. Set env vars: `fly secrets set CONFIG_PATH=/data/config.json DB_PATH=/data/emails.db`
7. Deploy: `fly deploy`

**Pricing:** Generous free allowance; ~$3–5/month after that.  
**Docs:** [fly.io/docs](https://fly.io/docs)

---

## DigitalOcean App Platform

Supports Docker deployments with a storage add-on. Slightly more expensive than Render/Railway but very reliable.

**Setup overview:**
1. Push code to GitHub
2. Create a new App in the DO console, connect the repo, select **Dockerfile**
3. Under **Resources**, add a **Storage** component and mount it at `/data`
4. Add env vars `CONFIG_PATH` and `DB_PATH` pointing to `/data`
5. Deploy

**Pricing:** $5/month minimum for the app + storage add-on cost.  
**Docs:** [docs.digitalocean.com/products/app-platform](https://docs.digitalocean.com/products/app-platform/)

---

## VPS (Hetzner, Linode, DigitalOcean Droplet, etc.)

The cheapest long-term option. SSH into the server, install Docker, and run:

```bash
git clone https://github.com/yourname/protopost.git
cd protopost
docker compose up -d
```

Provider config and logs live on the VPS disk — fully persistent. Put the server's IP (or a domain pointing to it) in your app's email URL.

**Pricing:** Hetzner starts at €4/month; Linode/DO at $4–6/month.  
**Docs:** [docs/DOCKER.md](DOCKER.md) covers everything needed once Docker is installed.

---

## Authentication

By default the API is completely open — no token needed. This is fine for local development.

When hosting on a public URL (Render, Railway, VPS, etc.) it is **strongly recommended** to set the `AUTH_TOKEN` environment variable. Once set, every `/api/*` request must include:

```
Authorization: Bearer <your-token>
```

The dashboard handles this automatically — click the 🔓 lock icon in the header to enter your token. It is stored in `localStorage` and sent with every request.

**Generate a token:**
```bash
openssl rand -hex 16
```

**Where to set it:**

| Platform | Where |
|---|---|
| Render | Service page → **Environment** → add `AUTH_TOKEN` |
| Railway | Service → **Variables** tab → add `AUTH_TOKEN` |
| Docker Compose | `environment:` block in `docker-compose.yml` |
| Docker CLI | `-e AUTH_TOKEN=...` flag |
| Local | Uncomment `AUTH_TOKEN` in your `.env` file |

See [docs/API.md](API.md#authentication) for the full auth reference.

---

## Why serverless platforms don't work

| Platform | Problem |
|---|---|
| **Cloudflare Workers** | JavaScript/WASM only — no Python runtime |
| **Vercel** | Python serverless functions have a read-only filesystem; `/tmp` is wiped on cold starts |
| **Netlify Functions** | No Python runtime; JavaScript only |
| **AWS Lambda** | No persistent filesystem; would need to replace SQLite with RDS/DynamoDB |

ProtoPost uses SQLite + a JSON config file on disk. Any platform that doesn't provide a writable, persistent filesystem requires a significant rewrite (replacing both with a hosted database) and is not worth the effort for a hackathon.

---

## See Also

- [docs/RENDER.md](RENDER.md) — Full Render deployment guide
- [docs/RAILWAY.md](RAILWAY.md) — Full Railway deployment guide
- [docs/DOCKER.md](DOCKER.md) — Local and self-hosted Docker guide
- [docs/HACKATHON_QUICKSTART.md](HACKATHON_QUICKSTART.md) — Get email working in 5 minutes
