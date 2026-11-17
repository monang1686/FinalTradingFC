# FUT Trader 27 — Mobile test (branch only)

Mobile-first static UI, no credentials, no EA interaction, no live production source enabled.

Open `experimental/mobile-trader/index.html` via GitHub Pages test preview if configured, or serve locally. The UI requests optional `prices-live.json` in the same folder; that file is intentionally absent until an authorized data integration is enabled. No sample/demo values are presented as live. A user may import a real DataFluxor response JSON manually; it is not uploaded or persisted.

Provider documentation: https://datafluxor.com/fut-data. Provider claims ~45-minute refresh for most cards and ~10-minute refresh for top 500, $29/month, 100k requests. Sandbox is illustrative only. API key must never be committed to GitHub or exposed in browser JavaScript. Before activation verify live API response, license/reuse permission, key handling, and deployment architecture.

No real trading signals are generated yet. 15-minute freshness threshold is intentionally stricter than provider's typical 45-minute refresh.


## Dashboard sperimentale con storico Val Town (iPhone)

Il nuovo file `dashboard.html` e' separato da `index.html` e da GitHub Pages su `main`. Per testarlo: GitHub Actions > FUT Trader 27 - Market Trends > ultima esecuzione riuscita > Artifacts > `market-trends-results`. Scaricare ed estrarre `experimental/mobile-trader/dashboard.html` e `work/valtown-history.json`; aprire l'HTML e importare il JSON tramite il selettore file.

Il file JSON e' letto localmente nel browser; nessuna credenziale o acquisto automatico. I prezzi sono osservazioni non verificate, e il confronto richiede almeno due timestamp distinti. Non ci sono ancora aggiornamenti automatici nella pagina.

Un link HTTPS iPhone permanente, indipendente da `main`, richiede un hosting separato o una configurazione di pubblicazione dedicata. Il workflow non e' schedulato periodicamente.


## Cloudflare Pages — sito di anteprima indipendente

Configurare un **nuovo progetto Cloudflare Pages** con repository GitHub `monang1686/FinalTradingFC`. Usare questi valori esatti:

- Framework preset: `None`
- Production branch **del progetto Cloudflare separato**: `fut-trader-27-test`
- Build command: `python experimental/mobile-trader/build_pages.py`
- Build output directory: `experimental/mobile-trader/dist`
- Root directory: `/` (radice del repository)

La parola 'production' nelle impostazioni Cloudflare indica soltanto il branch che pubblica **quel nuovo progetto Pages**, non il branch `main` di GitHub e non il sito GitHub Pages esistente. Non configurare il nuovo progetto con `main`.

Il builder copia esclusivamente `dashboard.html` come `dist/index.html` e crea intestazioni di sicurezza; non pubblica `prices.json`, le cache o i file di storico. Il sito non ha fetch di rete e non mostra dati live. Per importare uno storico, aprire l'URL Cloudflare in Safari e scegliere il file JSON tramite il selettore. Per dati automatici occorre una fase separata di distribuzione controllata, dopo la verifica di provenienza e diritti d'uso della fonte.
