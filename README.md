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
