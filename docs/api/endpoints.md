# API index — every endpoint at a glance

One page listing everything PriceHub serves. Each row links to the full
reference (parameters in detail, sample payloads, field notes).

- **Base URL:** `https://api.gerami.online`
- **Auth:** one header — `X-API-Key: ph_live_…` ([authentication.md](authentication.md))
- **Method:** every data endpoint is `GET`
- **Envelope:** every response is `{success, message, responseCode, data}` ([responses.md](responses.md))

## All endpoints

| Partner | Endpoint | Scope | Returns | Shape |
|---------|----------|-------|---------|-------|
| `technical` | [`GET /v1/technical/prices/platforms/latest`](endpoints-technical.md#get-v1technicalpricesplatformslatest) | `prices:read` | Latest quote per platform/asset/currency as `bid`/`ask` | list |
| `technical` | [`GET /v1/technical/prices/suppliers/latest`](endpoints-technical.md#get-v1technicalpricessupplierslatest) | `prices:read` | Latest supplier buy/sell quotes, same item shape as the platform feed | list |
| `technical` | [`GET /v1/technical/prices/stats`](endpoints-technical.md#get-v1technicalpricesstats) | `prices:read` | Cross-source summary (mean/median/σ-trimmed/min/max) per (asset, currency), Gerami separate | list |
| `reports` | [`GET /v1/reports/platform-compare`](endpoints-reports.md#get-v1reportsplatform-compare) | `reports:read` | Competitive report for one asset + a ready-to-post Persian Telegram message | object |
| — | [`GET /health`](health.md#get-health--liveness) | none | Liveness — the process is up | object |
| — | [`GET /health/ready`](health.md#get-healthready--readiness) | none | Readiness — DB + Redis reachable | object |

A key is scoped to **one partner**: a `reports` key calling a `/v1/technical/*`
route gets `403`, not data — see [authentication.md](authentication.md). The
`seo` partner exists but currently mounts no route, see
[endpoints-seo.md](endpoints-seo.md).

## Query parameters at a glance

Everything is optional unless marked **required**. Omitting a filter means "no
filter" — e.g. no `asset` returns every asset.

| Endpoint | Parameters |
|----------|------------|
| `prices/platforms/latest` | `source` · `asset` · `currency` · `type` · `assets` (comma-separated slugs) |
| `prices/suppliers/latest` | `source` · `asset` |
| `prices/stats` | `asset` · `currency` · `max_age_seconds` (30–3600, default `180`) · `role` (`platform`\|`reference`) |
| `reports/platform-compare` | `asset` **required** · `currency` (default `irt`) · `max_age_seconds` (default `180`) · `exclude` (comma-separated source slugs) |

### The two input keys

Both are **lowercase slugs**, so a query string never mixes cases:

| Input | What to pass | Examples |
|-------|--------------|----------|
| `asset` | `assets.slug` | `gold-18k`, `gold-ounce`, `silver-999`, `silver-ounce`, `copper`, `copper-lme`, `usd`, `btc` — [full catalog](assets.md) |
| `currency` | `currencies.slug` — the lowercase code | `irt` (تومان), `usd`, `usdt` |
| `source` | `sources.slug` | `gerami`, `tgju`, `daric`, `goldika`, `zariran` |
| `type` | `assets.type` | `gold`, `silver`, `copper`, `coin`, `platinum`, `palladium`, `currency`, `crypto`, `commodity` |

An uppercase currency (`IRT`) still resolves, but `irt` is the documented form.
Every asset slug, with its unit, symbol and quote currency, is listed in
[assets.md](assets.md).

Most assets are quoted in `irt`; the global ounces (`gold-ounce`,
`silver-ounce`, `platinum-ounce`, `palladium-ounce`), `copper-lme` and
`oil-brent` are quoted in `usd`. That is why `currency` is a filter and not a
fixed assumption — leave it out and each row tells you its own currency.

## Which endpoint do I want?

| I want… | Call |
|---------|------|
| every platform's price for one asset | `prices/platforms/latest?asset=gold-18k` |
| one platform's whole board | `prices/platforms/latest?source=gerami` |
| the global gold ounce from every source | `prices/platforms/latest?asset=gold-ounce` |
| what the suppliers (عمده‌فروش) quote | `prices/suppliers/latest` |
| "where does the market sit" — mean/median/outlier-trimmed | `prices/stats?asset=gold-18k&currency=irt` |
| the same summary for **everything** at once | `prices/stats` |
| a ready Persian message ranking Gerami against competitors | `reports/platform-compare?asset=gold-18k` |

## What every response looks like

Three rules hold across all of the above — the full statement is in
[responses.md](responses.md):

1. **Lists** are always `{items, count, …meta, generated_at}`.
2. **Entities** are always the same nested objects, with every key present
   (`null` when unknown):
   ```json
   "source":   { "slug": "gerami", "title_fa": "گرمی", "title_en": "Gerami", "role": "platform" }
   "asset":    { "slug": "gold-18k", "symbol": "XAU750g",
                 "title_fa": "طلای ۱۸ عیار", "title_en": "Gold 18K", "type": "gold", "unit": "gram" }
   "currency": { "slug": "irt", "code": "IRT", "symbol": "تومان",
                 "title_fa": "تومان ایران", "title_en": "Iranian Toman", "type": "fiat" }
   ```
3. **Quotes** are always `bid` (خرید) / `ask` (فروش) — there is no bare `price`,
   and a single-rate source reports `bid == ask` with `is_single_rate: true`.

## Quick start

```bash
KEY='ph_live_…'

# is the service up?
curl -s https://api.gerami.online/health | jq

# 18k gold across every platform, in Toman
curl -s -H "X-API-Key: $KEY" \
  "https://api.gerami.online/v1/technical/prices/platforms/latest?asset=gold-18k&currency=irt" | jq

# the market summary for the same pair
curl -s -H "X-API-Key: $KEY" \
  "https://api.gerami.online/v1/technical/prices/stats?asset=gold-18k&currency=irt" | jq '.data.items[0].stats'
```

Errors (`401` / `403` / `429` / `422`) and how to react: [errors.md](errors.md).
Rate limits: [rate-limiting.md](rate-limiting.md).
