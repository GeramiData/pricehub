"""SEO partner data logic.

The SEO team publishes price/news content, so this module serves a focused feed:
the newest quote for the assets they write about (platform quotes only, no
supplier noise) and recent metals news. It reads through the shared data helpers
so the SQL stays correct and in one place.

Neither function is mounted right now — see `router.py`. The scraped price-page
feed that used to live here was dropped together with its crawler and the
`seo_schm` schema.

The items themselves follow the same standard as every other partner — the refs
and list wrapper come from `app.shared.refs`, so an `asset` here is byte-for-byte
the `asset` the technical feed returns.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.data import news as news_data
from app.shared.data import prices as price_data
from app.shared.refs import listing, news_source_ref, quote_item

# The assets the SEO team writes about most; keeps their feed focused.
SEO_FEATURED_ASSETS = [
    "gold-18k",
    "gold-24k",
    "gold-melted",
    "gold-ounce",
    "silver-999",
    "silver-ounce",
    "coin-emami",
    "coin-bahar",
    "coin-half",
    "coin-quarter",
]


def _pos(v: Any) -> bool:
    """A usable quote: present and > 0 (drops null and the `-1` sentinel)."""
    return v is not None and float(v) > 0


def _seo_item(r: dict[str, Any]) -> dict[str, Any]:
    """One featured price in the standard quote shape.

    Most SEO sources publish a single number rather than a buy/sell split, so it
    is reported as `bid == ask` — the same rule the technical feed follows. For
    display, read `ask` (فروش).
    """
    price = r["price"] if _pos(r["price"]) else None
    bid = r["bid"] if _pos(r["bid"]) else price
    ask = r["ask"] if _pos(r["ask"]) else price
    return quote_item(r, bid=bid, ask=ask, is_single_rate=r["is_single_rate"])


async def featured_prices(
    session: AsyncSession, *, asset: Optional[str] = None
) -> dict[str, Any]:
    """Latest platform price for each featured asset (or one asset if given)."""
    rows = await price_data.latest_prices(session, asset=asset)
    allowed = {asset} if asset else set(SEO_FEATURED_ASSETS)
    items = [
        _seo_item(r)
        for r in rows
        if r["asset_slug"] in allowed and r["source_role"] != "supplier"
    ]
    return listing(items)


async def recent_news(
    session: AsyncSession, *, symbol: Optional[str] = None, limit: int = 20
) -> dict[str, Any]:
    """Recent metals news headlines (title/summary/link/published_at)."""
    limit = max(1, min(limit, 50))  # hard ceiling
    rows = await news_data.latest_news(session, symbol=symbol, limit=limit)
    items = [
        {
            "source": news_source_ref(r),
            "title": r["title"],
            "summary": r["summary"],
            "url": r["url"],
            "publisher": r["publisher"],
            "image_url": r["image_url"],
            "published_at": r["published_at"],
        }
        for r in rows
    ]
    return listing(items)
