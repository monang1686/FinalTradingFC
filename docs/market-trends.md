# Verifica Fase 1 — 16 novembre 2026

## Repository iniziale

Base test: 0247da268b4fd3b64d16b70fb1de69dc665eb9ba.
Main osservato: 7d1ef64ff935986f2be1c176f4dbafecdded6e27.
README iniziale minimale; prices.json v1 vuoto, aggiornamento null.
index.html conservava dati manuali in localStorage e generava target +15% e soglia -10%
per i prezzi del feed: rimosso questo comportamento dal percorso automatico.
Il calcolatore manuale e il CSV restano strumenti dell'utente, senza certificazione.
L'importatore CSV ora revoca esplicitamente il flag verified.

Workflow esaminati:
- market-trends-test.yml: in origine smoke test e artefatto, nessuna raccolta periodica.
- fc27-connector-test.yml: fixture offline esplicitamente fittizia, ricerca non certificata.
- fc27-live-probe.yml: probe di ricerca, piattaforma unverified; non modificato né avviato.
- telegram-test.yml: invia messaggi; non modificato né avviato.
- Due copie di fc27-live-probe.yml annidate sotto .github/workflows/.github: non sono workflow attivi.
Nessun workflow di deployment presente nel branch esaminato.

## Fonti e blocco

https://fc27-market.val.run/latest è configurato in fetch-fc27-market.py.
Il connettore si aspetta updated, groups, eaId/name/price; deduplica per eaId,
ma questa è una struttura attesa dal codice, non verificata sulla risposta corrente.
Il probe HTTP dell'ambiente termina con CONNECT tunnel failed, response 403:
è un blocco del proxy, non una risposta dell'endpoint e non prova che sia offline.
Anche il lettore web non ottiene il contenuto. La pagina pubblica
https://www.val.town/x/bowli/fut-market-api/code/main.ts identifica il progetto,
ma non espone nel testo consultabile provenienza, licenza, mercato e timestamp
sufficienti a certificare l'alimentazione. Fonte non approvata.
Il connettore resta research-only; aggiunto divieto di output su prices.json.

Alternative consultate:
- https://futflipper.com/price-api
- https://datafluxor.com/fut-data

DataFluxor documenta prezzi console/PC distinti, identificativi di versione EA,
observed_at e accesso API con chiave, da 29 USD/mese. La pagina distingue il
sandbox pubblico (dati fissi illustrativi) dalla produzione a pagamento.
Le due pagine riportano frequenze di aggiornamento diverse: occorre misurare
la produzione e non adottare come garanzia le frequenze promozionali.
Non disponibili chiave, risposta di produzione o verifica completa di provenienza
per questo progetto. Nessun acquisto, iscrizione o uso del sandbox come dato reale.
Questa è una candidata legittimamente automatizzabile, non una fonte già validata.
Non sono stati aggirati CAPTCHA, protezioni o limiti.

## Infrastruttura effettiva

market_engine.ingest accetta solo un contratto normalizzato di produzione con
source_id, game esatto EA Sports FC 27, platform console, players non vuoto.
Ogni carta: id di versione EA numerico stringa, name, tradeable true, price intero
positivo <=15 milioni, timestamp ISO con timezone della rilevazione effettiva.
La configurazione richiede endpoint, prove di permesso e provenienza e verified_at.
Un booleano non costituisce verifica: update-market.py rifiuta anche enabled=true
finché non è stato implementato e revisionato un adapter specifico.

Validazione atomica del batch: rifiuta duplicati, conflitti allo stesso timestamp,
regressioni temporali, dati futuri o più vecchi di 60 minuti e salti >50%.
Quest'ultima è una soglia prudenziale configurata nel codice: anche un movimento
reale può richiedere revisione. Nessuna correzione automatica inventata.
Le osservazioni ripetute non producono nuovi punti; il tempo di download non
sostituisce quello di osservazione. Storico nel campo history per carta,
7 giorni / massimo 336 punti; il contratto attuale assume snapshot completo.
Un provider con risposte parziali richiederà un archivio separato per le carte
assenti prima di essere attivato. Nessun backfill inventato.

Variazioni rispetto all'ultima osservazione: punto al massimo 15 minuti precedente
alla soglia 1/6/24h; nessuna interpolazione; null quando manca il punto.
Scanner: mediana superiore di almeno 3 punti precedenti nelle ultime 24h come
rivendita ipotetica; netto = target * 95 // 100 - acquisto; ROI sul costo.
Minimi: 800 crediti e 5%. Richiede sales_1h >=5 e sales_observed_at coincidente
con la quotazione. Conteggio vendite della fonte, non numero di snapshot/listing.
Liquidità assente = sconosciuta, nessuna opportunità. Nessuna garanzia di esecuzione.

Il report contiene freshness, variazioni e risk_flags; il browser rilegge il report
su richiesta, verifica età <=60 minuti e non importa quotazioni nel portafoglio.
La UI manuale rimane distinta dal report JSON dello scanner automatico.
In stato bloccato non vengono effettuate richieste di mercato né scritture ai prezzi.

## Pianificazione e attivazione futura

Nessun cron attivo perché manca una fonte verificata. Workflow limitato tramite
branch, job guard e checkout esplicito a fut-trader-27-test, contents read.
I workflow schedule GitHub devono esistere sul default branch; un cron nel solo
branch test non garantisce esecuzioni. Per 30 minuti usare, dopo verifica fonte,
un dispatcher esterno autorizzato sul branch test o un repository test separato.
Non modificare main per abilitare il cron. Nessun deployment, merge o PR creato.

Prima dell'attivazione: accesso legittimo, campione produzione e verifica timestamp,
versioni EA, console condiviso e scambiabilità; termini di riuso e limiti; adapter
specifico, archivio per risposte parziali e test integrazione. Errori HTTP/schema,
rate limit e anomalie devono lasciare invariata l'ultima quotazione valida e
registrare separatamente lo stato di errore; niente retry aggressivi.
L'importatore di rete di produzione non è implementato né dichiarato funzionante.

## Verifiche

14 test unitari offline: fonte disabilitata, gioco/mercato errati, sandbox, timestamp,
prezzi invalidi, duplicati, idempotenza, conflitti, anomalie, regressione, atomicità,
variazioni 1/6/24h, commissione e ROI, liquidità assente, fonte cambiata e feed vuoto.
Fixture sintetiche solo in tests/, nessuna scrittura in prices.json.
Smoke test CLI: report bloccato, trends/results vuoti. update-market preserva prices.json.
Controllo sintassi Python/JavaScript e git diff --check. Test live non superato:
accesso endpoint bloccato dal proxy. Esiti GitHub Actions da verificare separatamente.
