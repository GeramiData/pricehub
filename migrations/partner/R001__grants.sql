-- =============================================================================
-- partner/R001__grants.sql   (Repeatable — safe to re-run)
--
-- Creates/updates the partner_api_usr LOGIN role and grants it EXACTLY the
-- privileges PriceHub needs:
--   * SELECT on the price + news data (read-only feed);
--   * SELECT on partners + partner_api_keys (auth lookups);
--   * SELECT/INSERT/UPDATE on partner_usage_daily (durable usage counting);
--   * UPDATE only of last_used_at on partner_api_keys (touch on use).
-- It can NOT write price/news data and can NOT forge partner rows or keys — so
-- the public-facing service has a deliberately tiny blast radius.
--
-- The role password is NOT hard-coded here (keeps the secret out of git). Pass
-- it at apply time via a psql variable, matching crawlers/.env PARTNER_DB_PASSWORD:
--
--   docker exec -e PGPASSWORD="$COPILOT_DB_PASSWORD" -i pricing-postgres-crawlers \
--     psql -U copilot_usr -d pricing_db -v ON_ERROR_STOP=1 \
--          -v partner_pw="'FDf@26dgD==0FfgpD=@l6@7ldndk'" \
--     < migrations/partner/R001__grants.sql
--
-- NOTE the value is wrapped in single quotes inside the -v (…="'…'") so it is a
-- SQL string literal. Run V001__partner_schm.sql FIRST (this grants on its tables).
-- =============================================================================

\connect pricing_db
\set ON_ERROR_STOP on

-- Create the login role once; set/rotate its password every run.
SELECT 'CREATE ROLE "partner_api_usr" LOGIN'
 WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'partner_api_usr')\gexec

ALTER ROLE "partner_api_usr" WITH LOGIN PASSWORD :partner_pw;

-- Resolve unqualified names (price_latest, sources, …) into the data schemas.
ALTER ROLE "partner_api_usr"
    SET search_path = "price_schm", "news_schm", "partner_schm", public;

-- Connect + schema usage.
GRANT CONNECT ON DATABASE pricing_db TO "partner_api_usr";
GRANT USAGE ON SCHEMA "price_schm", "news_schm", "partner_schm" TO "partner_api_usr";

-- Read-only on all price + news data (current tables/views).
GRANT SELECT ON ALL TABLES IN SCHEMA "price_schm", "news_schm" TO "partner_api_usr";

-- Auth lookups: read partners + keys.
GRANT SELECT ON "partner_schm"."partners"         TO "partner_api_usr";
GRANT SELECT ON "partner_schm"."partner_api_keys" TO "partner_api_usr";

-- Durable usage counting: the ONLY data write PriceHub can do.
GRANT SELECT, INSERT, UPDATE ON "partner_schm"."partner_usage_daily" TO "partner_api_usr";
-- Touch-on-use: allow updating last_used_at only (column-level), nothing else.
GRANT UPDATE ("last_used_at") ON "partner_schm"."partner_api_keys" TO "partner_api_usr";

-- Auto-grant SELECT on FUTURE price/news tables (everything is owned by
-- copilot_usr), so a new crawler table is readable without another grant pass.
ALTER DEFAULT PRIVILEGES FOR ROLE "copilot_usr" IN SCHEMA "price_schm", "news_schm"
    GRANT SELECT ON TABLES TO "partner_api_usr";

