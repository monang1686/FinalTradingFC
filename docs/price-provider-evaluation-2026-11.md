# FC 27 console price feed — provider decision (2026-11-17)

**Decision:** no automatic live collection is authorized or enabled. Do not change main.

## Candidates (public claims; not independently audited)

| Provider | Public capability | Cost / access | Current decision |
|---|---|---|---|
| DataFluxor FUT Data | API: exact EA card IDs, console vs PC, per-price observed_at, price history. Says 45-minute general refresh, ~10-minute refresh for top 500. | $29/month, 100,000 requests; sample sandbox is fixed, not live. | **Candidate for authorized pilot** after user opts into paid service and written confirmation of storage/reuse rights. No API key in repository. |
| FUT-DB | JSON REST API with player and price information. | Free account/API key offered; some price fields premium. | **Candidate for free access check**: determine whether console prices and history are included, quotas and reuse terms. |
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
