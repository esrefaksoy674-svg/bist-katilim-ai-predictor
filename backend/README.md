# Backend

BIST Katılım AI Predictor backend service.

## End-of-day KAP and news collection

The existing daily scan runs after the market close. It queries the public KAP search page once per Katılım ticker, at a throttled pace, keeps only disclosures published on the scan date, and stores their headline metadata in Supabase. Per-ticker search results are cached for 15 minutes. The daily collection is capped at 100 symbols and 10 results per symbol.

The `/news?symbol=THYAO` endpoint remains available for a single on-demand lookup. The scheduled daily scan is the whole-universe collection path; it does not continuously poll KAP.

The three default Google News RSS searches come from the earlier BIST Katılım AI Robot. Override them with comma- or newline-separated `NEWS_RSS_URLS`.

For a new Supabase project, run the SQL files in order: `001_learning_events.sql` through `005_backend_table_security.sql`. If migrations 001-004 are already installed, run only the new 005 security migration. These tables are backend-only; do not expose the Supabase secret key to browser or mobile clients.

For KAP's supported high-volume and real-time integration, use the contracted KAP Data Dissemination REST API. The official service requires a data distribution agreement and provisioned API key. The public-page collector is limited to this once-daily, throttled use.

Optional settings:

- `NEWS_FETCH_TIMEOUT_SECONDS` (default: `10`)
- `KAP_RSS_URLS` (authorized distributor RSS feeds; empty by default)

