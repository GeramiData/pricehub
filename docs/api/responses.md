# Response format

Every response — success or error — uses one envelope:

```json
{
  "success": true,
  "message": "OK",
  "responseCode": 200,
  "data": { }
}
```

| Field | Type | Meaning |
|-------|------|---------|
| `success` | bool | `true` on 2xx, `false` on any error |
| `message` | string | human-readable status / error text |
| `responseCode` | int | mirrors the HTTP status code |
| `data` | object / null | the payload (shape depends on the endpoint) |

The HTTP status code always equals `responseCode`, so clients can branch on either.

## The response standard

Every endpoint follows the same three rules. They are implemented once, in
[`app/shared/refs.py`](../../app/shared/refs.py) — no endpoint defines its own
version of a source, an asset or a currency.

### 1. Lists always look the same

```json
"data": { "items": [ … ], "count": 12, "generated_at": "2026-07-19T08:41:20.123456+00:00" }
```

`count` is the number of items returned; `generated_at` is when the server built
the response (ISO-8601 UTC). Endpoint-specific metadata sits between the two
(e.g. `gold_18k_source` on the SEO price page).

### 2. Entities are nested objects with fixed keys

Wherever a response names a source, an asset or a currency, it embeds **exactly**
these objects — never a flattened `asset_title_fa`, never a partial subset:

```json
"source":   { "slug": "gerami", "title_fa": "گرمی", "title_en": "Gerami", "role": "platform" }
"asset":    { "slug": "gold-18k", "symbol": "XAU750g",
              "title_fa": "طلای ۱۸ عیار", "title_en": "Gold 18K", "type": "gold", "unit": "gram" }
"currency": { "slug": "irt", "code": "IRT", "symbol": "تومان",
              "title_fa": "تومان ایران", "title_en": "Iranian Toman", "type": "fiat" }
```

| Field | Meaning |
|-------|---------|
| `source.role` | `platform` · `reference` · `supplier` — what kind of quote this is |
| `asset.slug` | the **input** key: `?asset=gold-18k` |
| `asset.symbol` | the **standard** instrument code, purity + unit qualified — `XAU750g` (gold 750, per gram), `XAG999g` (silver 999), `XCU9999g` (copper 9999). Assets with no standard code agreed yet fall back to the internal code (`GOLD_24K`, `COIN_EMAMI`) so the field is always a usable identifier |
| `currency.slug` | the **input** key: `?currency=irt` — the lowercase `code`, so both inputs are spelled the same way (an uppercase `IRT` is still accepted) |
| `currency.code` | the standard currency code the quote is denominated in (`IRT`, `IRR`, `USD`) |
| `currency.symbol` | its display sign (`تومان`, `﷼`, `$`), `null` when the catalog has none |
| `currency.type` | `fiat` · `crypto` |

Both `asset` and `currency` carry `title_fa` **and** `title_en`, like every other
ref in the API.

Keys are **always present**. An unknown value is `null` — never an absent key —
so one parser works across every endpoint.

### 3. Quotes are always `bid` / `ask`

There is **no bare `price` field** anywhere in the API.

| Field | Meaning |
|-------|---------|
| `bid` | خرید — the price the source **buys** at (for a supplier: its `buy_price`) |
| `ask` | فروش — the price the source **sells** at (for a supplier: its `sell_price`) |
| `is_single_rate` | `true` when the source publishes one number for both sides — it is then reported as `bid == ask` |

A value is either a usable quote (> 0) or `null`; the `-1` "no quote" sentinel
from the crawlers is never exposed. Prices are exact decimal **strings** (never
floats — large rial amounts would lose precision) and timestamps are ISO-8601
UTC.

Because platform and supplier rows share this shape, one parser reads both feeds
and `source.role` is what tells them apart.

## Success payload shapes

### Example — a quote feed (`/v1/technical/prices/platforms/latest`, `/v1/technical/prices/suppliers/latest`)

Both return the identical item shape:

```json
{
  "success": true,
  "message": "OK",
  "responseCode": 200,
  "data": {
    "items": [
      {
        "source":   { "slug": "gerami", "title_fa": "گرمی", "title_en": "Gerami", "role": "platform" },
        "asset":    { "slug": "gold-18k", "symbol": "XAU750g",
                      "title_fa": "طلای ۱۸ عیار", "title_en": "Gold 18K", "type": "gold", "unit": "gram" },
        "currency": { "slug": "irt", "code": "IRT", "symbol": "تومان",
                      "title_fa": "تومان ایران", "title_en": "Iranian Toman", "type": "fiat" },
        "is_single_rate": false,
        "bid": "3820000.00000000",
        "ask": "3830000.00000000",
        "crawled_at": "2026-07-19T08:41:12+00:00"
      }
    ],
    "count": 1,
    "generated_at": "2026-07-19T08:41:20.123456+00:00"
  }
}
```

For a supplier row only the source differs — `"role": "supplier"`, `bid` is its
خرید and `ask` its فروش, and `is_single_rate` is always `false`.

### Example — `/v1/technical/prices/stats`

A list like the others: one item per (asset, currency) pair, each headed by the
same `asset` / `currency` refs, with the shared `params` as list metadata. See
[endpoints-technical.md](endpoints-technical.md).

## Error payload

```json
{
  "success": false,
  "message": "Invalid or inactive API key.",
  "responseCode": 401,
  "data": null
}
```

Validation errors (`422`) carry details:

```json
{
  "success": false,
  "message": "Validation error",
  "responseCode": 422,
  "data": { "errors": [ { "loc": ["query", "limit"], "msg": "...", "type": "..." } ] }
}
```

See [errors.md](errors.md) for the full code list.
