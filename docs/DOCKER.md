<!-- Last updated: February 2026 -->

[← Back to README](../README.md)

# Running ProtoPost with Docker

Docker is the fastest way to run ProtoPost on any machine — no Python installation, no dependency conflicts, one command to start.

---

## Prerequisites

- [Docker Desktop](https://docs.docker.com/get-docker/) (Mac / Windows) **or** Docker Engine (Linux)
- The ProtoPost source code (cloned or downloaded)

Check Docker is working:
```bash
docker --version
# Docker version 24.x.x or higher
```

---

## Option A — Docker Compose (recommended)

Docker Compose handles the build, volume, and restart policy in one command.

### Step 1 — Start the server

From the project root:
```bash
docker compose up -d
```

That's it. ProtoPost is now running at **http://localhost:8000**.

> **What `-d` does:** Runs the container in detached mode (background). Your terminal is free while the server runs.

### Step 2 — Open the dashboard

Visit **http://localhost:8000** in your browser. The dashboard loads immediately.

### Step 3 — Stop the server

```bash
docker compose down
```

Your email logs and provider config are preserved in the `protopost_data` Docker volume and will be there the next time you `docker compose up`.

---

## Option B — Docker CLI (without Compose)

If you prefer plain Docker commands:

### Build the image

```bash
docker build -t protopost .
```

### Run the container

```bash
docker run -d \
  --name protopost \
  -p 8000:8000 \
  -v protopost_data:/data \
  -e CONFIG_PATH=/data/config.json \
  -e DB_PATH=/data/emails.db \
  protopost
```

### Stop and remove the container

```bash
docker stop protopost
docker rm protopost
```

### Remove saved data (optional)

```bash
docker volume rm protopost_data
```

---

## Enabling auth (optional)

By default the API is open to anyone who can reach the server. To enable bearer token auth, pass `AUTH_TOKEN` as an environment variable:

```bash
# Docker Compose — add to docker-compose.yml environment block
environment:
  - CONFIG_PATH=/data/config.json
  - DB_PATH=/data/emails.db
  - AUTH_TOKEN=your-secret-token

# Docker CLI
docker run -d \
  -p 8000:8000 \
  -v protopost_data:/data \
  -e CONFIG_PATH=/data/config.json \
  -e DB_PATH=/data/emails.db \
  -e AUTH_TOKEN=your-secret-token \
  protopost
```

Once set, every `/api/*` request must include `Authorization: Bearer your-secret-token`. The dashboard prompts you to enter the token on first load and stores it in `localStorage`. See [docs/API.md](API.md#authentication) for full details.

---

## Changing the port

If port 8000 is already in use, map a different host port:

```bash
# Docker Compose — edit docker-compose.yml
ports:
  - "9000:8000"   # access via http://localhost:9000

# Docker CLI
docker run -d -p 9000:8000 ...
```

---

## Viewing logs

```bash
# Docker Compose
docker compose logs -f

# Docker CLI
docker logs -f protopost
```

---

## Where data is stored

| File | Location inside container | Persisted by |
|---|---|---|
| Email logs | `/data/emails.db` | `protopost_data` Docker volume |
| Provider config | `/data/config.json` | `protopost_data` Docker volume |

The volume survives `docker compose down`. It is only deleted if you explicitly remove it with `docker volume rm protopost_data` or run `docker compose down -v`.

---

## Updating to a new version

```bash
docker compose down
git pull
docker compose up -d --build
```

The `--build` flag rebuilds the image with the latest code. Your data volume is untouched.

---

## Pointing your app at the containerised server

Your app should call `POST http://localhost:8000/api/send` exactly as it would with the local dev server. No changes needed.

When running inside another Docker container on the same machine, use the host's internal IP or Docker network name instead of `localhost`. If you add ProtoPost to an existing `docker-compose.yml` alongside your app:

```yaml
services:
  myapp:
    depends_on:
      - protopost
    environment:
      - EMAIL_GATEWAY=http://protopost:8000/api/send

  protopost:
    build: ./protopost
    ports:
      - "8000:8000"
    volumes:
      - protopost_data:/data
    environment:
      - CONFIG_PATH=/data/config.json
      - DB_PATH=/data/emails.db

volumes:
  protopost_data:
```

Then in your app code, call `http://protopost:8000/api/send` instead of `localhost`.

---

## See Also

- [docs/HOSTING.md](HOSTING.md) — Compare all cloud hosting options
- [docs/RENDER.md](RENDER.md) — Deploy to Render (shared / persistent cloud access)
- [docs/RAILWAY.md](RAILWAY.md) — Deploy to Railway (shared / persistent cloud access)
- [docs/HACKATHON_QUICKSTART.md](HACKATHON_QUICKSTART.md) — Get email working in 5 minutes
- [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) — If something isn't working
