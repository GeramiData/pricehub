# SEO partner endpoints

Base: `https://api.gerami.online/v1/seo`
Auth: `X-API-Key` for a key on partner `seo`.
One-page index of every endpoint: [endpoints.md](endpoints.md).

## Status: no endpoint is mounted

The partner and its key still exist, but `/v1/seo/*` currently returns `404` —
[`router.py`](../../app/partners/seo/router.py) defines no route.

Its single endpoint used to be `GET /price-page`, a mirror of the gold and coin
tables scraped from `talasea.ir/gold-price` into `seo_schm.talasea_gold_prices`.
That crawler, its schema and this feed were removed: the coin prices it existed
to publish are being brought into the normal `price_schm` catalog instead, from
real market sources, so the SEO feed can be served by the same standard as every
other partner rather than from a scraped copy of someone else's page.

## Bringing the feed back

Reference implementations are preserved in
[`service.py`](../../app/partners/seo/service.py), already on the shared
response standard:

| Function | Serves | Reads |
|---|---|---|
| `featured_prices` | latest platform quote per curated asset — `SEO_FEATURED_ASSETS` already lists `coin-emami`, `coin-bahar`, `coin-half`, `coin-quarter` | `price_schm` |
| `recent_news` | recent metals news headlines | `news_schm` |

Enabling one is a route in `router.py` behind
`require_partner("seo", scope=…)` plus the matching scope on the key — the same
two-line change any other partner endpoint takes.

Responses follow the shared standard — see [responses.md](responses.md).
