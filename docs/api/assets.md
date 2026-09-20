# Asset catalog

Every asset in `price_schm.assets` — what to pass as `?asset=`, what comes back
as `asset.symbol`, and which currency it is quoted in.

- **You always pass the `slug`** (lowercase): `?asset=gold-18k`.
- **You get back `asset.symbol`** — the standard instrument code where one has
  been agreed (`XAU750g`, `XAG999g`, `XCU9999g`), otherwise the internal code
  (`GOLD_OUNCE`). It is a label, never an input.
- **Quoted in** is the `?currency=` slug that asset's prices carry. Most are
  `irt` (تومان); the global ounces and LME copper are `usd`.
- **Feed** says which endpoint serves it: `platforms` =
  `/v1/technical/prices/platforms/latest`, `suppliers` =
  `/v1/technical/prices/suppliers/latest`.

- **Sources** is how many distinct sources delivered a *usable* quote for that
  asset in a live check on **2026-08-15** (the `-1` "no quote" sentinel
  excluded). It moves as crawlers are added or a site goes down — treat it as
  "roughly how much cross-source depth to expect", not a guarantee.

**Every source counted here is live.** Most publish every **1–2 minutes**;
`copper-lme` is on an **hourly** cycle — an active feed on a slower schedule,
not a lagging one (the LME 3-month contract simply does not move minute to
minute). Read `crawled_at` on any item to see how old that particular number
is.

> Rows marked **no feed** exist in the catalog but no source publishes them
> today, so the API returns an empty list for them. They are listed here so you
> know the slug is valid but unfed — not missing by mistake. The eight of them
> were confirmed against live data, not assumed.

## Gold

| slug | فارسی | English | unit | `asset.symbol` | quoted in | feed | sources |
|------|-------|---------|------|----------------|-----------|------|---------|
| `gold-18k` | طلای ۱۸ عیار | Gold 18K | gram | `XAU750g` | `irt` | platforms + suppliers | **22** |
| `gold-ounce` | اونس جهانی طلا | Gold Global Ounce | ounce | `GOLD_OUNCE` | `usd` | platforms | 4 |
| `gold-24k` | طلای ۲۴ عیار | Gold 24K | gram | `GOLD_24K` | — | **no feed** | 0 |
| `gold-melted` | طلای آب‌شده | Melted Gold (Mazneh) | gram | `GOLD_MELTED` | — | **no feed** | 0 |

`gold-18k` is by far the deepest asset in the system — 18 platforms plus 4
suppliers — which is why `prices/stats` and the competitive report are built
around it. Everything else is thinner: `silver-999` has 11 platforms, the
ounces 4 each, and most currencies and crypto have a single source, so their
"market statistics" are really one source's number.

## Silver

| slug | فارسی | English | unit | `asset.symbol` | quoted in | feed | sources |
|------|-------|---------|------|----------------|-----------|------|---------|
| `silver-999` | نقره ۹۹۹ | Silver 999 | gram | `XAG999g` | `irt` | platforms | 11 |
| `silver-ounce` | اونس جهانی نقره | Silver Global Ounce | ounce | `SILVER_OUNCE` | `usd` | platforms | 4 |

## Copper & other metals

| slug | فارسی | English | unit | `asset.symbol` | quoted in | feed | sources |
|------|-------|---------|------|----------------|-----------|------|---------|
| `copper` | مس | Copper | gram | `XCU9999g` | `irt` | platforms | 4 |
| `copper-lme` | مس ال‌ام‌ای | LME Copper (3M) | ton | `COPPER_LME` | `usd` | platforms | 1 |
| `platinum-ounce` | انس پلاتین | Platinum Global Ounce | ounce | `PLATINUM_OUNCE` | `usd` | platforms | 1 |
| `palladium-ounce` | انس پالادیوم | Palladium Global Ounce | ounce | `PALLADIUM_OUNCE` | `usd` | platforms | 1 |

> **`copper-lme` is a live feed on an hourly cycle.** It always has a current
> price in `platforms/latest` — its `crawled_at` is just up to an hour old by
> design. The one place this bites is `prices/stats`, which excludes sources
> older than `max_age_seconds` (default `180`), so with the default the pair
> comes back with empty stats. Ask for a window that matches its cadence:
> `?asset=copper-lme&max_age_seconds=3600`.

## Coins

All coin slugs are valid but **unfed** today: the supplier boards that carry
them keep those lines inactive, so nothing is stored. Enabling one is a
configuration change on the crawler side, not an API change.

| slug | فارسی | English | unit | `asset.symbol` | quoted in | feed | sources |
|------|-------|---------|------|----------------|-----------|------|---------|
| `coin-emami` | سکه امامی | Emami Gold Coin | unit | `COIN_EMAMI` | — | **no feed** | 0 |
| `coin-bahar` | سکه بهار آزادی | Bahar Azadi Gold Coin | unit | `COIN_BAHAR` | — | **no feed** | 0 |
| `coin-half` | نیم سکه | Half Gold Coin | unit | `COIN_HALF` | — | **no feed** | 0 |
| `coin-quarter` | ربع سکه | Quarter Gold Coin | unit | `COIN_QUARTER` | — | **no feed** | 0 |
| `coin-gerami` | سکه گرمی | Gerami Gold Coin | unit | `COIN_GERAMI` | — | **no feed** | 0 |

The coins are catalogued but **not crawled yet** — no source feeds them, so no
endpoint returns a coin quote. They become available through the normal price
feeds as soon as a source is wired up for them.

## Currencies (ارز آزاد)

Free-market rates, all quoted in Toman (`irt`), all `unit`-based. `asset.symbol`
is the code itself (`USD`, `EUR`, …).

| slug | فارسی | English | feed | sources |
|------|-------|---------|------|---------|
| `usd` | دلار | US Dollar | platforms | 1 |
| `eur` | یورو | Euro | platforms | 1 |
| `gbp` | پوند انگلیس | British Pound | platforms | 1 |
| `aed` | درهم | UAE Dirham | platforms | 1 |
| `try` | لیر ترکیه | Turkish Lira | platforms | 2 |
| `omr` | ریال عمان | Omani Rial | platforms | 1 |
| `chf` | فرانک سوئیس | Swiss Franc | platforms | 1 |
| `cny` | یوان چین | Chinese Yuan | platforms | 1 |
| `jpy` | ین ژاپن (۱۰۰ ین) | Japanese Yen — quoted **per 100 JPY** | platforms | 1 |
| `krw` | وون کره جنوبی | South Korean Won | platforms | 1 |
| `cad` | دلار کانادا | Canadian Dollar | platforms | 1 |
| `aud` | دلار استرالیا | Australian Dollar | platforms | 1 |
| `nzd` | دلار نیوزیلند | New Zealand Dollar | platforms | 1 |
| `sgd` | دلار سنگاپور | Singapore Dollar | platforms | 1 |
| `inr` | روپیه هند | Indian Rupee | platforms | 1 |
| `pkr` | روپیه پاکستان | Pakistani Rupee | platforms | 1 |
| `iqd` | دینار عراق | Iraqi Dinar | platforms | 1 |
| `syp` | پوند سوریه | Syrian Pound | platforms | 1 |
| `afn` | افغانی | Afghan Afghani | platforms | 1 |
| `irr` | ریال | Iranian Rial | **no feed** — it is a quote currency, not a traded asset | 0 |

## Crypto

Quoted in Toman (`irt`) unless noted. `unit`-based; `asset.symbol` is the ticker.

| slug | فارسی | English | quoted in | sources |
|------|-------|---------|-----------|---------|
| `usdt` | تتر | Tether | `irt` | 3 |
| `btc` | بیت‌کوین | Bitcoin | `irt` and `usdt` | 2 |
| `eth` | اتریوم | Ethereum | `irt` and `usdt` | 2 |
| `ltc` | لایت کوین | Litecoin | `irt` | 1 |
| `bch` | بیت‌کوین کش | Bitcoin Cash | `irt` | 1 |
| `trx` | ترون | Tron | `irt` | 1 |
| `bnb` | بایننس کوین | Binance Coin | `irt` | 1 |
| `xlm` | استلار | Stellar | `irt` | 1 |
| `xrp` | ریپل | Ripple | `irt` | 1 |
| `doge` | دوج کوین | Dogecoin | `irt` | 1 |
| `dash` | دش | Dash | `irt` | 1 |
| `ada` | کاردانو | Cardano | `irt` | 1 |
| `dot` | پولکادات | Polkadot | `irt` | 1 |
| `sol` | سولانا | Solana | `irt` | 1 |
| `avax` | آوالانچ | Avalanche | `irt` | 1 |
| `shib` | شیبا اینو | Shiba Inu | `irt` | 1 |
| `ton` | تون‌کوین | Toncoin | `irt` | 1 |

`btc` and `eth` come from two sources on different bases — a Toman quote and a
Tether quote. They are separate rows, told apart by `currency.slug`; filter with
`?currency=irt` or `?currency=usdt` if you want only one.

## Commodities

| slug | فارسی | English | unit | quoted in | feed | sources |
|------|-------|---------|------|-----------|------|---------|
| `oil-brent` | نفت برنت | Brent Crude Oil | barrel | `usd` | platforms | 1 |

## Who quotes the main metals

The sources behind the deepest assets, as of the same live check:

| asset | feed | sources |
|-------|------|---------|
| `gold-18k` | platforms | daric, digikala, gerami, goldika, invi, melligold, milligold, myshemsh, talair, talair_api, talasea, taline, technogold, tgju, tochalgold, wallgold, zarafza, zarpay |
| `gold-18k` | suppliers | abshodeasil, mehregangold, rokhgold, zariran |
| `silver-999` | platforms | charisma, daric, digikala, gerami, invi, melligold, myshemsh, noghresea, tgju, tochalgold, zarpay |
| `copper` | platforms | charisma, gerami, meschi, zarpay |
| `gold-ounce` / `silver-ounce` | platforms | rahavard, talair, tgju, tradingview |
| `usdt` | platforms | nobitex, talair, tgju |

Everything else is single-source and comes from **`tgju`** — every currency in
the ارز آزاد table and every crypto in Toman — with four exceptions:
`try` adds `talair`, and `omr`, `oil-brent` and the `usdt`-based `btc`/`eth`
come from `talair` alone; `copper-lme` comes from `lme`.

Filter to one of them with `?source=`, or read `source.slug` on each item.

## Quote currencies

What can appear in `currency.slug` / be passed as `?currency=`:

| slug | code | symbol | meaning |
|------|------|--------|---------|
| `irt` | `IRT` | تومان | Iranian Toman — the default basis for domestic prices |
| `usd` | `USD` | `$` | US Dollar — global ounces, LME copper, Brent |
| `usdt` | `USDT` | `₮` | Tether — the crypto pair basis for `btc` / `eth` |

## Filtering by group

`?type=` selects a whole family in one call — the values are
`gold`, `silver`, `copper`, `coin`, `platinum`, `palladium`, `currency`,
`crypto`, `commodity`:

```bash
# every gold row (18k + ounce), every source
curl -H "X-API-Key: $KEY" \
  "https://api.gerami.online/v1/technical/prices/platforms/latest?type=gold"

# a hand-picked set
curl -H "X-API-Key: $KEY" \
  ".../prices/platforms/latest?assets=gold-18k,silver-999,copper"
```

## Checking what is live right now

This page describes the catalog; the API is the live truth. One call lists every
(asset, currency) pair currently being served:

```bash
curl -s -H "X-API-Key: $KEY" \
  "https://api.gerami.online/v1/technical/prices/platforms/latest" \
  | jq -r '.data.items[] | "\(.asset.slug)\t\(.currency.slug)"' | sort -u
```

Source counts above are as of this writing and change as crawlers are added.
