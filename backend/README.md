# Backend

BIST Katılım AI Predictor backend service.

## News feeds

The `/news` endpoint collects configured RSS/Atom feeds, validates and deduplicates entries, and can filter by ticker symbol. It uses bounded HTTP timeouts and returns source errors without provider response bodies.

The default feeds are Google News RSS searches used by the earlier BIST Katılım AI Robot:

- Borsa Istanbul
- BIST shares
- KAP / Borsa

Override them with a comma- or newline-separated `NEWS_RSS_URLS` environment variable. The `KAP_RSS_URLS` setting is reserved for a feed supplied by an authorized KAP data distributor. KAP's official Data Dissemination Service uses a contracted REST API; these RSS adapters do not bypass that service or claim to be an official KAP integration.

Optional settings:

- `NEWS_FETCH_TIMEOUT_SECONDS` (default: `10`)
- `KAP_RSS_URLS` (empty by default)

