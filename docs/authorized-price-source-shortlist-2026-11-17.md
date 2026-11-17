# FC27 price-source shortlist — 2026-11-17

## Keep Val Town on standby
- Val Town bowli /latest was reachable via GitHub Actions HTTP 200 on 2026-11-17.
- 589 numeric prices, 589 unique EA IDs, 0 per-card timestamps.
- Remains **disabled**: no verified permission for repeated collection or reuse; upstream origin may be FUT.GG.
- Do not schedule collection or promote these prices into trade signals.

## Provider with explicit integration offering: DataFluxor FUT Data
- Official product: https://futflipper.com/price-api
- Terms: https://datafluxor.com/terms
- Offers API access for own website, bot or trading tool; explicitly allows showing data in own product; no raw API resale.
- Claims ~21,000 FC27 card versions, console and PC, observed_at and age_seconds.
- Advertised $29/month, 100,000 requests/month, 500 cards per batch; free sandbox advertised but coverage and rights for sandbox require verification.
- Requires API key and subscription for production; **no payment or credentials authorized**.
- Distinguish provider's permission to use its API from independent EA rights and applicable game terms.
- Next: request sandbox key from provider, validate JSON, entitlements, and contract before enabling.

## Other candidates
- FUT-DB https://app.futdatabase.com/ : explicitly intended for apps and bots, but prices are premium-only (~€79/month), updated 30min to 24h.
- FUTBIN https://www.futbin.com/tos : automated scraping prohibited without written permission; do not use unofficial SDK as production source.
- EA FC Community API https://www.ea.com/games/ea-sports-fc/news/pitch-notes-fc26-community-api-update : only approved FUT.GG, FUTBIN, FUTWIZ; account data integration, not a public FC27 price API.

## Decision
Do not enable scheduled live collection until a provider grants usable API access and applicable reuse rights. Keep Val Town disabled but configured. No changes to main.
