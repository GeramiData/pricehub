"""PriceHub FastAPI entrypoint — the partner API served at api.gerami.online.

Responsibilities wired up here:
  * uniform {success, message, responseCode, data} envelope for every response;
  * public /health and root meta (no key needed) for probes/liveness;
  * every partner router mounted at /v1/<slug> (see app.partners registry);
  * a middleware that records each authenticated call durably AFTER the response
    (via app.usage.recorder), using a fresh DB session so accounting never
    interferes with the request's own session.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import router as health_router
from app.core.config import settings
from app.core.redis import close_redis
from app.db.session import SessionLocal
from app.partners import PARTNER_ROUTERS
from app.shared.schemas import envelope, ok
from app.usage.recorder import record_request

app = FastAPI(
    title="PriceHub Partner API",
    version="0.1.0",
    description="Read-only partner API for Gerami pricing data (api.gerami.online).",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,     # key auth is header-based, not cookie-based
        allow_methods=["GET"],
        allow_headers=["X-API-Key", "Content-Type"],
    )

# Public health/readiness (no key) — shown in the OpenAPI docs so consumers can
# probe the service before calling data endpoints.
app.include_router(health_router)

# Mount each partner's router under its own /v1/<slug> namespace.
for mount_path, partner_router in PARTNER_ROUTERS:
    app.include_router(partner_router, prefix=f"/v1/{mount_path}")


# --- Durable usage recording ------------------------------------------------

@app.middleware("http")
async def record_usage(request: Request, call_next):
    """After the response, record the call if it was an authenticated partner hit.

    The auth dependency stashes a PartnerContext on request.state only once a key
    has passed auth + rate limiting, so its presence means "a real partner call
    was served." We use the matched route template (e.g. /v1/technical/prices/stats)
    as the stable endpoint label so usage groups cleanly.
    """
    response = await call_next(request)
    ctx = getattr(request.state, "partner_ctx", None)
    if ctx is not None:
        route = request.scope.get("route")
        endpoint = getattr(route, "path", request.url.path)
        async with SessionLocal() as session:
            await record_request(session, ctx.api_key_id, endpoint)
    return response


@app.on_event("shutdown")
async def _shutdown() -> None:
    await close_redis()


# --- Public meta / health ----------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    return ok(
        {
            "service": "pricehub",
            "version": app.version,
            "partners": [slug for slug, _ in PARTNER_ROUTERS],
            "docs": "/docs",
            "health": "/health",
            "readiness": "/health/ready",
        },
        message="PriceHub partner API",
    )


# --- Error envelope handlers -------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return envelope(False, str(exc.detail), exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return envelope(False, "Validation error", 422, {"errors": jsonable_encoder(exc.errors())})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return envelope(False, "Internal server error", 500)
