# Backend

BIST Katılım AI Predictor backend service.

## News and KAP

The `/news` endpoint collects the three Google News RSS searches used by the earlier BIST Katılım AI Robot. It validates, deduplicates, and optionally filters headlines by ticker. Feed requests use bounded timeouts.

When called with one ticker, for example `/news?symbol=THYAO`, the backend also performs one low-volume search against KAP's public search page. It extracts disclosure titles, links, and displayed publication times. Results are cached per ticker for 15 minutes. The collector does not poll every company or download disclosure attachments.

For KAP's supported high-volume and real-time integration, use the contracted KAP Data Dissemination REST API. The service requires a data distribution agreement and a provisioned API key. Do not use the public page for bulk polling.

Override the default Google News sources with comma- or newline-separated `NEWS_RSS_URLS`. Optional settings:

- `NEWS_FETCH_TIMEOUT_SECONDS` (default: `10`)
- `KAP_RSS_URLS` (authorized distributor feed URLs; empty by default)

