# FC 27 console price feed — provider decision (2026-11-17)

**Decision:** no automatic live collection is authorized or enabled. Do not change main.

## Candidates (public claims; not independently audited)

| Provider | Public capability | Cost / access | Current decision |
|---|---|---|---|
| DataFluxor FUT Data | API: exact EA card IDs, console vs PC, per-price observed_at, price history. Says 45-minute general refresh, ~10-minute refresh for top 500. | $29/month, 100,000 requests; sample sandbox is fixed, not live. | **Preferred technical candidate, not yet authorized**: $29/month for 100,000 requests; up to 500 cards per price request; public sandbox contains fixed sample data, not live prices. Provider offers 250 free monthly credits, but production entitlement and reuse/storage rights require confirmation. No API key in repository. |
| FUT-DB | JSON REST API with player and price information. | Free account/API key offered; **current player-price endpoints are premium only**. | **Rejected as a free price feed**: premium player-price endpoints, €79/month advertised; refresh 30 minutes–24 hours; one request per player. |
| FCData | Public console and PC lowest BIN observations, timestamps and historical changes. | No public automation/API permission verified. | **Blocked** for automated extraction. Browsing is not API authorization. |
| EA Community API | EA approved FUT.GG, FUTBIN, FUTWIZ for certain account data. | Not a general public market-price API. | **Not available** for this project's automated market prices. |

References:
- https://datafluxor.com/fut-data
- https://fut-db.com/
- https://api.futdatabase.com/api/doc/index.html
- https://fcdata.io/about/
- https://www.ea.com/it/games/ea-sports-fc/news/pitch-notes-fc26-community-api-update

## Admission gate before switching any provider on

1. Verify permission for programmatic access, intended usage, local/remote retention and display in an independent application.
2. Record written terms, URL, date, owner, allowed polling cadence, storage duration and rate limits.
3. Verify price coverage for PS5/console and exact EA item IDs including promo versions.
4. Check individual observed_at timestamps (not HTTP retrieval times), measured freshness distribution, anomalies, missing/untradeable cards and price changes over several days.
5. Confirm what a quote represents (lowest BIN vs executable listing vs completed sale). Never infer fill from quote.
6. Evaluate API costs, failure rates, 429 policy, outage behavior and security of API key storage.
7. Start with offline sample fixture and read-only sandbox. Live polling requires explicit user authorization.
8. Keep 'insufficient_data' if any authorization or observation gate fails.

## Technical constraints

Existing `market_sources.py` requires an explicitly enabled and verified source with documented rights. Current Val Town source remains disabled. The DataFluxor example JSON is **not** the canonical `market_engine.ingest` format and must not be fed to the engine without a separately tested adapter. An API subscription alone does not prove downstream redistribution rights.

## Questions for providers

- May one independently developed, private FC 27 trading assistant programmatically retrieve console prices every 30–60 minutes?
- May it retain timestamped quotes for 90 days for private backtesting and display signals in a personal dashboard?
- Which plan provides price, observed_at, exact EA item ID, card version, tradeability, recent executed sales or measured liquidity, and card-specific price bounds?
- What are quota, latency, refresh cadence, retention, attribution and redistribution restrictions?

**No API keys, scraping, scheduled requests or public dashboard changes in this research phase.**

## Verification update — 2026-11-17

- FUT-DB documentation labels both `GET /api/players/{playerId}/price` and `GET /api/players/prices` **premium only**. Its published premium price is €79/month and its FAQ says bulk player-price requests are not supported. Therefore a free API key does **not** unlock usable console-price collection.
- DataFluxor's published API supports `GET /api/v1/fut/prices?ea_ids=…&platform=ps` with up to 500 exact EA IDs, and describes price timestamps and source. Public sandbox samples are fixed and must never be labelled live.
- FUT-DB terms reserve rights in the API content and restrict reproduction/distribution without permission. Obtain explicit terms for archival and dashboard use before collection.

Sources checked:
- https://api.fut-db.com/api/doc/index.html
- https://app.futdatabase.com/
- https://fut-db.com/terms
- https://datafluxor.com/fut-data

## Terms and vendor-contact update — 2026-11-17

Official DataFluxor terms (last updated 10 Nov 2026): https://datafluxor.com/terms

- FUT Data is a **separate** subscription from the general Free/Starter/Pro/Scale plans. The 250 free monthly credits do **not** establish free live FUT price access.
- The provider permits using results in one's own products subject to its terms, but forbids resale, sublicensing or raw third-party API access without written agreement. It explicitly assigns responsibility for complying with EA game terms to the customer.
- FUT Data observations are provided as-is and may be delayed or incomplete; no accuracy or availability guarantee.
- Section 4 allows **complimentary FUT Data trial by individual arrangement**, without a card, with a defined end date and no automatic conversion to a paid subscription. This is the preferred next step; it is not guaranteed.
- Vendor contact published in terms: support@datafluxor.com. Do not send API credentials by email.

Before enabling a pilot, request written confirmation of: (a) private dashboard use; (b) automated polling at 30–60 minutes; (c) retention of per-card quotes for 90 days and backtesting; (d) any attribution, source-data and EA-related constraints; (e) exact schema and measured freshness; (f) whether complimentary FUT Data trial is possible. No activation or purchase is authorized by this document.
