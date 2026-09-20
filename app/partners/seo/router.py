"""SEO partner endpoints — mounted at /v1/seo by app.main.

The partner currently exposes **no route**. Its only surface used to be
`GET /price-page`, which served the scraped `seo_schm.talasea_gold_prices`
snapshot; that crawler and its schema were removed, so the route went with them.

`service.featured_prices` and `service.recent_news` are kept as reference
implementations — already on the shared response standard, and reading the
normal `price_schm` / `news_schm` data. Bringing the SEO feed back is a route
here plus the matching scope on the key; `featured_prices` already lists the
coin assets, so it becomes the natural replacement once coins are crawled into
`price_schm`.
"""

from __future__ import annotations

from fastapi import APIRouter

SLUG = "seo"
router = APIRouter(tags=["seo"])
