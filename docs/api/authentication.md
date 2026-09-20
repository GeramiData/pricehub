# Authentication

Every data endpoint requires an API key. Public, unauthenticated paths are only
`GET /` (meta) and `GET /health`.

## Sending the key

Send it in the **`X-API-Key` header**. Never in the query string (query strings
leak into proxy logs, browser history, and referrer headers).

```bash
curl -H "X-API-Key: ph_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
     https://api.gerami.online/v1/technical/prices/platforms/latest
```

## Key format

```
ph_live_<43 url-safe chars>
```
- `ph_` brands the key; `live` leaves room for a future `ph_test_` class.
- The part after the prefix is 256 bits of entropy.
- The whole string is the credential. We store only its **SHA-256 hash** plus a
  short **prefix** (`ph_live_AbCdEf12`) for identification — never the key itself.

You receive the full key **once**, when it is minted. If it is lost, it cannot be
recovered: mint a new one and revoke the old (see
[../partners/onboarding.md](../partners/onboarding.md)).

## Tenant isolation

Each key belongs to exactly one **partner** (e.g. `seo` or `technical`). A key can
only call **its own** partner's endpoints:

- `seo` key → `GET /v1/seo/...` ✅
- `seo` key → `GET /v1/technical/...` → `403 Forbidden`

This is enforced server-side on every request, independent of scopes.

## Scopes

A key carries a list of **scopes** (e.g. `prices:read`, `news:read`,
`reference:read`). Each endpoint declares the scope it needs. While consumers are
internal, scope checks are relaxed — but keys are still minted with the correct
scopes so tightening later is just a config change, not a redesign.

| Scope | Grants access to |
|-------|------------------|
| `prices:read` | price + supplier price endpoints |
| `news:read` | news endpoints |
| `reference:read` | catalog endpoints (assets, sources) |

## Revocation & status

Two independent switches turn access off, both effective immediately (the auth
check is per request):

- **Per key** — set `revoked_at` or `is_active = false` on the key row.
- **Per partner** — set the partner's `status` to `suspended`/`disabled`; this
  cuts off *all* of that partner's keys at once.
