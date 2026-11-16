# FUT Trader 27 — Fase 1

Sviluppo isolato sul branch `fut-trader-27-test`. Nessun deployment o modifica a main.

**Stato: raccolta automatica bloccata, nessuna fonte prezzi di produzione verificata.**
`prices.json` rimane vuoto e invariato. Nessun prezzo simulato è pubblicato come reale.

Il motore offline valida le osservazioni, conserva fino a 7 giorni / 336 punti per carta,
calcola variazioni 1/6/24 ore solo con dati sufficienti e prepara stime nette dopo il 5% EA.
Lo scanner richiede liquidità misurata: in sua assenza non genera opportunità.

```sh
python -m unittest discover -s tests -v
python update-market.py
python market-trends.py prices.json
```

Il workflow esegue test e produce artefatti, senza scrivere nel repository.
Non è attivo alcun aggiornamento ogni 30 minuti: GitHub esegue i cron dal branch
predefinito; attivarli su main violerebbe l'isolamento richiesto.

Analisi fonti, contratto dati, limiti e risultati: [docs/market-trends.md](docs/market-trends.md).

## Market Trends 2.0 — branch sperimentale

Connettori modulari JSON, permessi prima delle richieste, storico per fonte e
feed parziali, pagina separata `experimental/index.html`. Stato:
**0 fonti autorizzate attive, 0 carte raccolte, 0 raccolte periodiche attive**.
`python update-market.py` ora scrive soltanto `experimental/market-state.json`;
non aggiorna `data/market-trends.json` della Fase 1 né `prices.json`.
Configurazione corrente: `config/market-sources.json` (la vecchia configurazione
singola è conservata come riferimento, non letta dal nuovo runner).
Dettagli, verifiche Val Town e template di pianificazione gratuito disabilitato:
[Market Trends 2.0](docs/market-trends-2.md).

## Scanner offline e audit aggiornato

[Rapporto fonti e stato completo](docs/scanner-audit.md).
Nuova demo in `experimental/scanner.html`, senza connessioni a dati reali:

```sh
mkdir -p work
python experimental_scanner.py --demo > work/scanner-demo.json
```

Caricare il report nella pagina della demo. Prezzi e candidate sono **fixture
sintetiche**, mai segnali operativi. Restano zero fonti autorizzate attive e zero
raccolte periodiche. Nessun nuovo progetto: il precedente template per repository
separato non va installato con i vincoli attuali. I commit di questo intervento
sono locali al branch test, senza push o deployment.
