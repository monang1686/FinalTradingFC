# Market Trends 2.0 — 16 novembre 2026

## Esito reale

Zero fonti prezzi autorizzate e funzionanti, zero carte reali raccolte, zero
raccolte periodiche attive. Nessuna quotazione inventata. Nessun aggiornamento
a prices.json, index.html pubblico o main; nessun deployment.

Val Town https://fc27-market.val.run/latest:
- Lettore web: URL non accessibile. Prova HTTP ordinaria senza impersonazione:
  CONNECT tunnel failed, response 403, HTTP 000. Il proxy impedisce la verifica;
  non è un HTTP 403 emesso dall'endpoint e non dimostra che il servizio sia offline.
- README pubblico https://www.val.town/x/bowli/fut-market-api: dichiara FC27 PS5,
  prezzi player-prices-ps5.json e metadati FUT.GG. /latest è top 100 per gruppo
  (sei gruppi), non tutti gli oltre 20mila prezzi dichiarati a monte.
- Lo storico dichiarato è orario, con snapshot primo prezzo dell'ora; il tempo
  della raccolta non certifica la data di osservazione a monte.
- Struttura legacy attesa dal connettore preesistente: updated, groups,
  eaId/name/price. Non verificata contro una risposta attuale. Mancano prove di
  scambiabilità, timestamp per carta e licenza dati applicabile alla redistribuzione.
- Termini FUT.GG https://stormstrike.gg/terms sezione License to Use Our Services:
  automazione vietata salvo permesso espresso. Accesso pubblico e CORS * non
  concedono diritti. Nessun consenso documentato per questo riuso.
- Fonte registrata ma DISABILITATA. Nessun adapter che promuova arbitrariamente
  il suo payload a contratto certificato. Non vengono importati forecast.

Le verifiche precedenti di DataFluxor e FUT-DB non hanno individuato prezzi
production inclusi nei piani gratuiti. SDK MIT o wrapper FUTBIN non autorizzano
l'estrazione dei dati. Nessun altro connettore specifico attivato senza permesso.

## Architettura

Riutilizzato market_engine.py: ingest e report, prezzi interi <=15 milioni,
EA item ID della versione, tradeable esplicito, console condiviso, FC27 esatto,
origine production, timestamp con timezone, rifiuto di futuri/obsoleti oltre 60m,
conflitti e regressioni; variazioni >50% bloccano il batch per revisione.
ID canonici: niente alias 01/1; variazione della versione dichiarata rifiutata.
Nomi non identificano le carte. Nessuna conversione implicita PC/console.

market_sources.py: registro json_api e public_json. Entrambi richiedono contratto
normalizzato esplicito; feed pubblico richiede anche evidenza della licenza dati.
Prima di ogni chiamata: enabled/verified, free, automation_allowed, storage_allowed,
URL di permesso e provenienza, verifica non più vecchia di 90 giorni, frequenza
minima di 30 minuti. Questi campi sono un registro di revisione umana, non una
verifica legale automatica. Non abilitarli senza evidenze e prova produzione.
Rete: HTTPS, niente destinazioni private, redirect rifiutati, timeout 20s,
8 MB massimi, JSON HTTP 200, nessun retry o gestione CAPTCHA; 403/429/errori
interrompono la fonte. Nessun cookie, token EA o browser impersonato.
I connettori non effettuano paginazione o mapping proprietario: un provider con
schema diverso richiede un adapter revisionato, senza inventare campi mancanti.

market_pipeline.py: stato unico atomico in experimental/market-state.json,
archivi per fonte; nessuna fusione di serie di provider diversi. Batch valido
solo se interamente verificato; errore preserva snapshot precedente, registra il
tipo di errore senza corpo/URL potenzialmente sensibili e sopprime i segnali.
Carte assenti da feed parziale mantenute fino a 7 giorni: non vengono ricontate
come nuove osservazioni e la freschezza dipende dalla loro data. Duplicati nello
stesso batch rifiutati, replay identici idempotenti. Massimo 336 punti per carta.
La copertura aggregata conta EA item ID unici, senza sommare doppioni tra fonti.
La pipeline rispetta interval_minutes e non richiede nuovi dati prima della soglia.
Non ci sono stime della copertura totale basate su numeri promozionali.

Variazioni 1/6/24 ore relative all'ultima osservazione: punto non successivo alla
soglia e al massimo 15m precedente; null se manca. Nessuna interpolazione.
Target = mediana superiore di almeno tre osservazioni precedenti nelle ultime
24h; margine netto = target * 95 // 100 - prezzo; ROI sul costo. Segnali soltanto
con vendite misurate sales_1h >=5 e data coerente, profitto >=800, ROI >=5%.
La liquidità assente resta sconosciuta. Target storico, non promessa di vendita.

Pagina experimental/index.html: fonte, esito, copertura recente, attendibilità,
età calcolata nel browser, variazioni, liquidità e rischi, margini stimati se
ammissibili. Nessun inserimento nel portafoglio pubblico; nessun contenuto remoto
iniettato come HTML. Il refresh ogni minuto rilegge solo il file locale: non è una
raccolta mercato. Nessun deployment della pagina effettuato.

## Pianificazione gratuita predisposta, non attiva

.github/workflows/market-trends-test.yml verifica il branch test e produce artefatti.
Non raccoglie dati da fonti disabilitate, non pubblica prezzi, contents read.
Non aggiunto cron inefficace al branch: GitHub esegue schedule dal default branch.

Il template docs/collector-workflow.yml.example NON è un workflow attivo. È
pensato per un altro repository pubblico gratuito, con il proprio default branch,
checkout esplicito fut-trader-27-test e push solo su quel branch. Ogni 30m ai minuti
7/37 UTC, con possibili ritardi GitHub; nessuno SLA di puntualità. Nessuna creazione
di repository, token o variabile eseguita. Dopo autorizzazione fonte e collaudo,
installare il template nel repository separato e configurare token con permessi
minimi e AUTHORIZED_FREE_SOURCE_READY=true. Verificare le condizioni correnti
GitHub per runner pubblici; non assumere gratuità illimitata dei repository privati.
Richiedere anche il diritto di pubblicazione prima di salvare osservazioni in un
repository pubblico, oppure utilizzare archivio privato compatibile col budget.
Il campo automations_active resta false: questo codice non può verificare scheduler
esterni e non ne deduce l'attivazione dalla sola configurazione della fonte.

## Test e riproduzione

python -m unittest discover -s tests -v
python update-market.py
python -m py_compile market_engine.py market_sources.py market_pipeline.py update-market.py

30 test offline (fixture sintetiche solo nei test, mai quotazioni pubblicate),
più controlli sintassi Python/JS e diff. Nessuna richiesta prezzi nei test.
Verifica HTML con parser standard e sintassi JS; nessun collaudo grafico browser.
La CLI in configurazione reale produce stato bloccato e zero carte.
GitHub Actions non dichiarato passato senza esito del runner remoto.

## Limiti e attivazione

Non soddisfatta la raccolta live gratuita: servono fonte e diritti dimostrati,
timestamp reali per carta, identità delle versioni e scambiabilità, campioni di
produzione e adapter specifico dove necessario. Non basta abilitare Val Town:
fallirebbe comunque il contratto normalizzato e la validazione dei campi.
Contratto API canonico: game='EA Sports FC 27', platform='console', data_kind=
'production', source_id corrispondente; players con id stringa canonica EA item ID,
name, tradeable=true, price intero, timestamp ISO con timezone; version opzionale,
sales_1h e sales_observed_at opzionali. Non usare player_id del calciatore al posto
dell'item ID della singola versione. Prima di attivare autorizzare espressamente
raccolta, storico e redistribuzione; verificare la quota gratuita a 48 cicli/giorno.
