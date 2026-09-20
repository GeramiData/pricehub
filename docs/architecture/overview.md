# Architecture overview

## What PriceHub is

A **separate, read-only partner API** over the Gerami pricing data. It is not part
of pricing-copilot — it is its own repo, Docker image, GitHub workflows, secrets,
and domain (`api.gerami.online`). It reuses the **same** crawler database
(`pricing_db`) through a dedicated, SELECT-only role, so partners get live data
without any second copy to keep in sync.

Why a separate service rather than a router inside the copilot backend:
- **Stability** — the copilot API changes for product reasons; the partner API
  must stay stable for outside consumers.
- **Blast radius** — the partner path connects as a role that can only read data
  and only write usage counters. A bug or leak here cannot touch prices, users,
  or the copilot app.
- **Independent ops** — deploy, rate limits, and keys evolve on their own cadence.

## The pieces

```
                          Internet
                             │  HTTPS
                             ▼
        ┌──────────────── TLS reverse proxy (your edge) ───────────────┐
        │  copilot.gerami.online → pricing-front (SPA + /api)          │
        │  api.gerami.online     → 127.0.0.1:8100  (pricehub) ◀── NEW  │
        └──────────────────────────────┬───────────────────────────────┘
                                        │ pricing-net (shared docker network)
             ┌──────────────────────────┼───────────────────────────┐
             ▼                          ▼                            ▼
      pricehub-api (FastAPI)     pricehub-redis            postgres-crawlers
      partner_api_usr  ─────────▶ rate-limit windows        pricing_db
       reads price/news          + counters                 ├ price_schm  (read)
       writes usage only                                    ├ news_schm   (read)
                                                            └ partner_schm(auth+usage)
                                        ▲
                          crawlers (Airflow) write prices/news
```

- **pricehub-api** — the FastAPI service. Authenticates keys, enforces rate
  limits, serves per-partner GET endpoints, records usage.
- **pricehub-redis** — holds the per-second/per-minute rate-limit counters (and,
  later, a response cache). Internal-only, password-protected. See
  [redis.md](redis.md).
- **postgres-crawlers / pricing_db** — the existing crawler DB. PriceHub connects
  as `partner_api_usr`: SELECT on `price_schm`/`news_schm`, and write only on
  `partner_schm.partner_usage_daily` (+ touch `last_used_at`).

## Request lifecycle

For `GET https://api.gerami.online/v1/technical/prices/platforms/latest` with header
`X-API-Key: ph_live_…`:

1. **TLS proxy** terminates HTTPS and forwards to `127.0.0.1:8100`.
2. **Auth dependency** (`app/api/deps.py`):
   - reads `X-API-Key`; hashes it (SHA-256); looks up an **active** key on an
     **active** partner (one indexed query);
   - checks **tenant isolation** — the key's partner slug must equal the module
     (`technical`), else `403`;
   - checks the route's **scope** against the key's scopes (relaxed while internal);
   - checks **rate limits** in Redis (per-second + per-minute), else `429`;
   - stashes a `PartnerContext` on `request.state`.
3. **Handler** runs the partner's service, which reads through the shared data
   helpers (`app/shared/data/`) as `partner_api_usr`.
4. **Response** is wrapped in the standard envelope.
5. **Usage middleware** (`app/main.py`), after the response, records the call in
   `partner_usage_daily` using a fresh DB session — so accounting never breaks a
   request.

## Directory map (code ↔ responsibility)

| Path | Responsibility |
|------|----------------|
| `app/core/config.py` | env-driven settings (DB, Redis, rate-limit defaults) |
| `app/core/security.py` | API-key generate / hash / verify |
| `app/core/redis.py` | shared async Redis client |
| `app/db/session.py` | async engine as `partner_api_usr` |
| `app/api/deps.py` | `require_partner()` — auth + scope + rate limit |
| `app/usage/ratelimit.py` | Redis fixed-window limiter |
| `app/usage/recorder.py` | durable per-partner usage counting |
| `app/shared/data/` | reusable, correct SQL over price/news |
| `app/shared/refs.py` | the response standard — source/asset/currency refs, quote items, list wrapper |
| `app/partners/<slug>/` | one code module per partner (router + service + README) |
| `app/main.py` | app wiring, envelope, usage middleware, health |
