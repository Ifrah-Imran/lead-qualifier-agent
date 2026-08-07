# Deploying to Oracle Cloud (Always Free)

Target: a single Always Free **Ampere A1 (arm64)** VM running the whole stack via Docker
Compose. The other Always Free shape (`VM.Standard.E2.1.Micro`, 1 GB RAM x86) is too small
for Postgres + ChromaDB + n8n + the API running together — use A1.

All images used (`postgres:16-alpine`, `chromadb/chroma:0.5.23`, `n8nio/n8n:latest`,
`python:3.12-slim`, `node:20-alpine`, `caddy:2-alpine`) publish multi-arch builds
including `arm64`, so no image changes are needed for A1.

## 1. Create the VM

1. Oracle Cloud Console → **Compute → Instances → Create Instance**.
2. Image: **Ubuntu 24.04** (aarch64/arm64 build).
3. Shape: **VM.Standard.A1.Flex** — pick at least 2 OCPU / 12 GB (out of your 4 OCPU / 24 GB
   free allowance; you can run other free-tier things with the rest, or give it all 4/24).
4. Attach/create a VCN with a public subnet, and assign a **public IP** (reserve it as a
   *reserved* public IP if you want it stable across reboots — ephemeral IPs can change).
5. Save the SSH key pair Oracle generates (or supply your own public key).

## 2. Open the firewall — twice

Oracle blocks inbound traffic in **two places**; both need updating or nothing gets
through even with services running:

**a) VCN Security List** (Console → Networking → Virtual Cloud Networks → your VCN →
Security Lists → Default Security List → Add Ingress Rules):
- If using the Caddy overlay (recommended, gets you HTTPS): allow TCP `80`, `443`
- If exposing services directly without Caddy: allow TCP `8000` (api), `5678` (n8n), `3000` (frontend)
- Leave `22` (SSH) open, source restricted to your IP if possible.

**b) The instance's own iptables** — Oracle's Ubuntu images ship with restrictive
iptables rules out of the box. SSH in and run:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save   # persist across reboots
```
(Add `8000`/`5678`/`3000` instead/also if not using Caddy.)

## 3. Install Docker

```bash
sudo apt update && sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER   # log out/in after this
```

Verify: `docker compose version` (need v2.24+ for the `!reset` merge used in
`docker-compose.caddy.yml`).

## 4. Get the code and configure

```bash
git clone <your-repo-url> lead-qualifier-agent
cd lead-qualifier-agent
cp .env.example .env
nano .env
```

Fill in for prod:
- `OPENAI_API_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `ALLOWED_ORIGINS` — your frontend's public URL (e.g. `https://app.yourdomain.com`, or
  `http://<server-ip>:3000` if going domain-less)
- `NEXT_PUBLIC_API_URL` — your API's public URL (`https://api.yourdomain.com` or
  `http://<server-ip>:8000`)
- `N8N_HOST` / `N8N_PROTOCOL` / `WEBHOOK_URL` — same idea, for n8n
- If using the Caddy overlay: `APP_DOMAIN` / `API_DOMAIN` / `N8N_DOMAIN`, each with a DNS
  A record already pointed at the VM's public IP (Caddy needs this to succeed before it
  can issue Let's Encrypt certs)

## 5. Bring the stack up

**Without a domain (plain HTTP, ports exposed directly):**
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

**With a domain (recommended — automatic HTTPS via Caddy):**
```bash
docker compose -f docker-compose.prod.yml -f docker-compose.caddy.yml up -d --build
```

Check everything came up healthy:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
curl http://localhost:8000/health   # {"status":"ok"}
```

## 6. Import and activate the n8n workflow

1. Open `http://<server-ip>:5678` (or `https://n8n.yourdomain.com`) and complete the n8n
   owner account setup (first visit only) — use a strong password, this account has full
   access to your API keys stored in n8n.
2. **Import from File** → `n8n/lead-qualifier-workflow.json`.
3. Open the imported "Lead Qualifier Pipeline" workflow and flip it **Active**.
4. Your production webhook is now `https://n8n.yourdomain.com/webhook/new-lead` (or the
   plain-HTTP equivalent) — see the README for the payload shape.

## 7. Redeploying after changes

```bash
git pull
docker compose -f docker-compose.prod.yml [-f docker-compose.caddy.yml] up -d --build
```
Postgres/ChromaDB/n8n data lives in named Docker volumes and survives redeploys/restarts.
n8n workflow edits made in the UI are **not** in git — after editing a workflow in
production, re-export it (`n8n export:workflow --id=<id> --output=...` inside the
container) and commit the JSON so the repo stays the source of truth.

## 8. Backups

The three stateful volumes are `postgres_data`, `chroma_data`, `n8n_data`. Simplest
approach — periodic `docker run --rm -v <volume>:/data -v $(pwd):/backup alpine tar czf /backup/<volume>-$(date +%F).tar.gz -C /data .`
for each, copied off-box (Oracle Object Storage's Always Free tier — 10 GB — works well
here). Postgres also supports logical dumps: `docker compose -f docker-compose.prod.yml exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql`.

## Notes / things not covered here

- No CI/CD to auto-deploy on push — redeploys above are manual (`git pull` + `up -d --build`).
- No log aggregation/monitoring beyond `docker compose logs`; fine for a single-VM personal
  deploy, worth revisiting if this needs to be reliably up for others.
- Oracle can reclaim idle Always Free VMs after a period of near-zero CPU/network/disk
  usage — keep an eye on the console notification if this sits unused for a while.
