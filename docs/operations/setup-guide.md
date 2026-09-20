# Setup guide — from zero to live

This is the ordered checklist to stand PriceHub up. It assumes the
**pricing-copilot crawler stack is already running** on the VPS (it owns the
`pricing-net` network, the `postgres-crawlers` container, and `pricing_db`).

Legend: 🖥️ your machine · 🐙 GitHub · ☁️ the VPS.

---

## 0. Prerequisites (verify first)

- 🖥️ You have this repo at `/home/erfan/pricehub` and the empty GitHub repo
  `git@github.com:ThisIsErfan/PriceHub.git`.
- ☁️ The crawler stack is up: `docker ps` shows `pricing-postgres-crawlers` and
  the `pricing-net` network exists (`docker network ls | grep pricing-net`).
- ☁️ You know `COPILOT_DB_USER` / `COPILOT_DB_PASSWORD` (the DB owner) and the
  `PARTNER_DB_USER` / `PARTNER_DB_PASSWORD` you set in
  `pricing-copilot/crawlers/.env`.
- DNS: `api.gerami.online` already points at the server (done).

---

## 1. 🖥️ Push the code to GitHub

You run all git yourself (no auto-commits). From `/home/erfan/pricehub`:

```bash
cd /home/erfan/pricehub
git init
git branch -M main
git remote add origin git@github.com:ThisIsErfan/PriceHub.git
git add .
git status          # review — .env files must NOT be listed (see .gitignore)
git commit -m "feat: PriceHub partner API (initial)"
git push -u origin main
```

Pushing to `main` triggers `build-pricehub.yml`, which builds and pushes
`ghcr.io/thisiserfan/pricehub:latest`. Watch it under **Actions**.

---

## 2. ☁️ Create the DB role + schema (one time)

Copy the two migration files to the server (or paste them), then apply as the DB
**owner** (`copilot_usr`). Order matters: schema first, grants second.

**2a. Create schema + tables + seed partners:**
```bash
docker exec -e PGPASSWORD="$COPILOT_DB_PASSWORD" -i pricing-postgres-crawlers \
  psql -U copilot_usr -d pricing_db -v ON_ERROR_STOP=1 \
  < migrations/partner/V001__partner_schm.sql
```

**2b. Create the `partner_api_usr` role + grants.** Pass the password from
`crawlers/.env` as a **quoted** psql variable (note the `="'…'"` wrapping so it
becomes a SQL string literal):
```bash
PARTNER_PW='FDf@26dgD==0FfgpD=@l6@7ldndk'   # == PARTNER_DB_PASSWORD in crawlers/.env

docker exec -e PGPASSWORD="$COPILOT_DB_PASSWORD" -i pricing-postgres-crawlers \
  psql -U copilot_usr -d pricing_db -v ON_ERROR_STOP=1 \
       -v partner_pw="'$PARTNER_PW'" \
  < migrations/partner/R001__grants.sql
```

**2c. Verify** the role can log in and read:
```bash
docker exec -e PGPASSWORD="$PARTNER_PW" -i pricing-postgres-crawlers \
  psql -U partner_api_usr -d pricing_db -c \
  "SELECT count(*) FROM price_latest; SELECT slug FROM partner_schm.partners;"
```
You should see a price count and the two seeded partners (`seo`, `technical`).

> Re-running: `V001` is idempotent (`IF NOT EXISTS` / `ON CONFLICT`); `R001` is
> repeatable and also **rotates** the password to whatever you pass.

---

## 3. 🐙 Add GitHub secrets & vars (repo: PriceHub)

**Settings → Secrets and variables → Actions.** Prod-gated ones go under
**Settings → Environments → `prod`** (the deploy job uses `environment: prod`).

**Secrets** — server/SSH (reuse the same values as pricing-copilot):
| name | value |
|------|-------|
| `VPS_HOST` | server IP/hostname |
| `VPS_USER` | deploy user |
| `VPS_SSH_PASSWORD` | that user's password |
| `VPS_SSH_PORT` | optional (default 22) |

**Secrets** — GHCR pull (PAT with `read:packages`):
| `GHCR_USERNAME` | GitHub username owning the PAT |
| `GHCR_TOKEN` | the PAT |

**Secrets** — PriceHub:
| `PARTNER_DB_USER` | `partner_api_usr` |
| `PARTNER_DB_PASSWORD` | the same value as `PARTNER_PW` above |
| `PRICEHUB_REDIS_PASSWORD` | `openssl rand -hex 32` |

**Variables** (optional; sensible defaults if omitted):
| `PARTNER_CORS_ORIGINS` | leave empty (server-to-server) |
| `DEFAULT_RATE_LIMIT_PER_SEC` | `5` |
| `DEFAULT_RATE_LIMIT_PER_MIN` | `120` |

> Everything PriceHub-specific is prefixed `PARTNER_*` / `PRICEHUB_*` and lives
> in this **separate repo**, so it can never collide with pricing-copilot's
> secrets.

---

## 4. 🐙 Deploy PriceHub

Wait for step 1's build to finish, then:

**Actions → "Deploy PriceHub (prod)" → Run workflow** (leave `image_tag=latest`,
or pin `git-<sha>`).

This scp's the compose file to `~/pricehub`, writes `.env` from your secrets, logs
in to GHCR, and runs `compose pull && up -d`. When it finishes:

```bash
# ☁️ on the server
cd ~/pricehub
docker compose -f compose.pricehub.prod.yml ps       # pricehub-api + pricehub-redis up
curl -s http://127.0.0.1:8100/health                 # {"success":true,...}
```

---

## 5. ☁️ Expose api.gerami.online via the TLS reverse proxy

Add a server block to the **same edge reverse proxy** that serves
`copilot.gerami.online`, pointing `api.gerami.online` at `127.0.0.1:8100`, and
issue a certificate. Example (nginx):

```nginx
server {
    listen 443 ssl http2;
    server_name api.gerami.online;

    ssl_certificate     /etc/letsencrypt/live/api.gerami.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.gerami.online/privkey.pem;

    # Partner API — forward the key header and client IP.
    location / {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Optional: redirect http→https
server {
    listen 80;
    server_name api.gerami.online;
    return 301 https://$host$request_uri;
}
```

With Caddy it is a two-liner (`api.gerami.online { reverse_proxy 127.0.0.1:8100 }`)
and TLS is automatic. Reload the proxy, then:

```bash
curl -s https://api.gerami.online/health
```

---

## 6. ☁️ Mint the first internal keys

Generate a key per team, store only its hash, hand the plaintext to the team once.

```bash
# 🖥️ or ☁️ — anywhere with the repo + python (uses stdlib only)
python3 scripts/mint_api_key.py seo       --scopes prices:read,news:read --label "seo prod #1"
python3 scripts/mint_api_key.py technical --scopes prices:read,reference:read --label "technical prod #1"
```

Each run prints the **KEY** (copy it now) and an **INSERT** statement. Apply each
INSERT as the owner:

```bash
docker exec -e PGPASSWORD="$COPILOT_DB_PASSWORD" -i pricing-postgres-crawlers \
  psql -U copilot_usr -d pricing_db -v ON_ERROR_STOP=1 <<'SQL'
-- paste the INSERT block printed by mint_api_key.py here
SQL
```

---

## 7. Verify end to end

```bash
KEY='ph_live_...'   # the technical key you just minted

curl -s -H "X-API-Key: $KEY" \
  "https://api.gerami.online/v1/technical/prices/platforms/latest" | jq

# wrong partner → 403 (a technical key on a reports route)
curl -s -H "X-API-Key: $KEY" \
  "https://api.gerami.online/v1/reports/platform-compare?asset=gold-18k" | jq .responseCode

# no key → 401
curl -s "https://api.gerami.online/v1/technical/prices/platforms/latest" | jq .responseCode
```

Then confirm usage was recorded:
```bash
docker exec -e PGPASSWORD="$COPILOT_DB_PASSWORD" -i pricing-postgres-crawlers \
  psql -U copilot_usr -d pricing_db -c \
  "SELECT p.slug, u.endpoint, u.request_count
   FROM partner_schm.partner_usage_daily u
   JOIN partner_schm.partner_api_keys k ON k.id=u.api_key_id
   JOIN partner_schm.partners p ON p.id=k.partner_id
   ORDER BY u.request_count DESC;"
```

---

## Redeploying after code changes

1. 🖥️ commit + push to `main` (you run git) → image rebuilds.
2. 🐙 **Actions → Deploy PriceHub (prod)**.

Schema changes (new tables in `partner_schm`) are applied on the server the same
way as step 2 — the app image never migrates the DB.

## Roll back

Re-run the deploy with `image_tag = git-<older-sha>`.

---

## Quick reference — what runs where

| Thing | Where | Port |
|-------|-------|------|
| pricehub-api | container on `pricing-net` | `127.0.0.1:8100` |
| pricehub-redis | container on `pricing-net` | internal only |
| pricing_db | `pricing-postgres-crawlers` | `127.0.0.1:5434` (SSH tunnel) |
| public entry | TLS proxy → 8100 | `api.gerami.online` |
