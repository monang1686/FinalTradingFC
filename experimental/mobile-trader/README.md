# FUT Trader 27 — Mobile test (branch only)

Mobile-first static UI, no credentials, no EA interaction, no live production source enabled.

Open `experimental/mobile-trader/index.html` via GitHub Pages test preview if configured, or serve locally. The UI requests optional `prices-live.json` in the same folder; that file is intentionally absent until an authorized data integration is enabled. No sample/demo values are presented as live. A user may import a real DataFluxor response JSON manually; it is not uploaded or persisted.

Provider documentation: https://datafluxor.com/fut-data. Provider claims ~45-minute refresh for most cards and ~10-minute refresh for top 500, $29/month, 100k requests. Sandbox is illustrative only. API key must never be committed to GitHub or exposed in browser JavaScript. Before activation verify live API response, license/reuse permission, key handling, and deployment architecture.

No real trading signals are generated yet. 15-minute freshness threshold is intentionally stricter than provider's typical 45-minute refresh.
