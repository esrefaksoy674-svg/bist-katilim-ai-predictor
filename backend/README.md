# Backend

BIST Katılım AI Predictor backend service.

## Phone app and automatic outcome tracking

The dashboard is an installable Progressive Web App for Android and iPhone. Open the dashboard in the phone browser and use **Add to Home Screen** (Safari: Share → Add to Home Screen; Chrome: menu → Install app). It can show the last cached dashboard while offline; fresh prices and results need a connection.

The scheduled end-of-day scan records the previous session's realized close-to-close outcome for every saved forecast targeting that session. The dashboard's hit rate counts only evaluated forecasts and treats an actual return of **+5.00% or more** as successful. The scheduled training job runs afterward and refreshes the model from the daily historical BIST dataset. It does not trade or place orders.

## Dated context snapshots and shadow evaluation

The daily scan saves numeric technical, matched-news count, cross-universe momentum, and optional sector-peer summaries to the backend-only `context_snapshots` table. Context collection is best-effort and does not affect the active model's predictions. Set `SECTOR_MAP` as comma-separated `SYMBOL:SECTOR` pairs (for example `AAA:ENERGY,BBB:BANK`) to enable peer summaries.

The weekly **Context Shadow Evaluation** workflow waits for at least 60 distinct snapshot dates and 70% feature coverage before comparing technical-only and context-enriched candidates on shared walk-forward windows. It reports results without promoting a model. Because the context table starts collecting only after migration 006 is installed, historical context will accumulate prospectively; the workflow reports a collecting state until the minimum coverage is reached.

## End-of-day KAP and news collection

The existing daily scan runs after the market close. It queries the public KAP search page once per Katılım ticker, at a throttled pace, keeps only disclosures published on the scan date, and stores their headline metadata in Supabase. Per-ticker search results are cached for 15 minutes. The daily collection is capped at 100 symbols and 10 results per symbol.

The `/news?symbol=THYAO` endpoint remains available for a single on-demand lookup. The scheduled daily scan is the whole-universe collection path; it does not continuously poll KAP.

The three default Google News RSS searches come from the earlier BIST Katılım AI Robot. Override them with comma- or newline-separated `NEWS_RSS_URLS`.

For a new Supabase project, run the SQL files in order: `001_learning_events.sql` through `006_context_snapshots.sql`. If migrations 001-005 are already installed, run only the new `006_context_snapshots.sql` migration. These tables are backend-only; do not expose the Supabase secret key to browser or mobile clients.

For KAP's supported high-volume and real-time integration, use the contracted KAP Data Dissemination REST API. The official service requires a data distribution agreement and provisioned API key. The public-page collector is limited to this once-daily, throttled use.

Optional settings:

- `NEWS_FETCH_TIMEOUT_SECONDS` (default: `10`)
- `KAP_RSS_URLS` (authorized distributor RSS feeds; empty by default)
- `SECTOR_MAP` (optional `SYMBOL:SECTOR` pairs for context summaries)
