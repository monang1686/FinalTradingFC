# Audit fonti e scanner sperimentale

Verifiche del 16–17 novembre 2026, ora italiana. Branch esclusivo
fut-trader-27-test, base remota acquisita bc931d330f5ea672a932686adeb01c7864825b3e.
Nessun push, merge, deployment, nuovo progetto o avvio di workflow. I commit di
questa attività rimangono locali. main non modificato.

## Esito per l'utilizzo quotidiano

Il progetto ha infrastruttura di analisi funzionante offline, ma non un'app di
trading automatica utilizzabile con prezzi reali. Copertura autorizzata attiva:
zero carte. Il feed Val Town di 589 record e il confronto invariato a 60 secondi
sono risultati riferiti dall'utente: non equivalgono a 589 versioni uniche
certificate, a tutto il mercato o a un controllo dell'accuratezza delle quotazioni.
In questo turno non sono stati scaricati o archiviati prezzi reali; sviluppo e
test utilizzano soltanto fixture sintetiche.

## Stato del codice esaminato

| Componente | Funziona | Limiti e interventi |
|---|---|---|
| market_engine.py | Validazione ingest, storico per carta, variazioni, fee/ROI e filtro liquidità | All-or-nothing per batch; un outlier blocca anche gli altri record. Finestra 15m precedente alla soglia può produrre null su snapshot orari sfasati. Target mediana superiore storica, non una previsione validata. |
| market_pipeline.py | Isolamento provider, conservazione feed parziali, mantenimento snapshot su errore, conteggio item ID unici | Non acquisisce pagine multiple né riconcilia divergenze fra fonti. Stato di errore poco dettagliato. Un record ripetuto con timestamp nuovo non prova un nuovo prezzo a monte. |
| market_sources.py | Check dei permessi prima delle richieste, JSON/HTTPS, timeout/limite bytes, rifiuto redirect | Connettori per contratto canonico, non API universali. I flag sono attestazioni umane, non prove legali. Nessuna fonte configurata abilitata. |
| valtown_adapter.py | Report di qualità in memoria, senza prezzi nell'output | Non converte il feed in quotazioni autorizzate. Aggiunti controllo limite prezzo, item ID canonico, duplicati dello stesso item anche con rarity diversa. Conta presenza dei timestamp, non ne certifica la semantica. |
| valtown_compare.py | Confronto aggregato di due risposte | Corretto confronto temporale: differenza non significa avanzamento. Aggiunta regressione e durata misurata; due campioni non stimano la frequenza. Non eseguito live. |
| diagnose_valtown.py | Analisi strutturale senza stampare carte | Corretto exit status: JSON valido ma schema invalido ora fallisce. Errori limitati al tipo. Non eseguito live. Qualità dei prezzi separata dalla validità strutturale. |
| fetch-fc27-market.py | Import legacy research-only e fixture offline | Il timestamp globale è copiato sulle carte: non è una prova di osservazione individuale. Non usare come feed di trading; nessuna esecuzione live in questo turno. |
| import-prices.py | CSV con scrittura atomica e revoca verified | Manuale, non soluzione automatica. Namespace piattaforme e conflitti temporali richiedono ulteriore uniformazione prima dell'integrazione production. |
| market-trends.py / update-market.py | CLI sul motore / runner dello stato sperimentale | Il primo legge prices.json vuoto; il secondo resta bloccato dalla fonte disabilitata. Nessun collegamento production Val Town. |
| experimental/index.html | Vista stato, freschezza, report e collegamento alla nuova demo | Non pubblicata né installata su iPhone. Aggiornare il file locale non equivale a raccogliere prezzi a monte. |
| index.html / scanner-pro.html | Calcolatori e dati manuali locali | Non scanner automatici. Identità per nome e target manuali non adatti al futuro archivio versionato. Lasciati invariati. |
| JSON/config/README/docs/.gitignore | Esaminati file di stato e documentazione preesistente | Due configurazioni (singola legacy e multipla corrente); documentazione storica va letta insieme a questo audit. Nessuna fixture salvata nei prezzi reali. |

Esaminati anche test, codex-connection-test.txt e workflow annidati.

### Workflow

- market-trends-test.yml: solo test e artefatto. Ora la demo scanner è sintetica e
  il workflow non invoca update-market.py, così la CI non diventa incidentalmente
  una raccolta quando cambierà una configurazione. Nessun schedule.
- fc27-connector-test.yml: fixture esplicitamente fittizia per il connettore legacy;
  nessuna chiamata prezzi. Non avviato da questa attività.
- fc27-live-probe.yml: esiste un probe attivabile da push sul relativo file;
  non modificato né avviato. Prima di qualsiasi futuro push o attivazione verificare
  e rimuovere/gated questo percorso live finché manca il permesso.
- valtown-diagnostic.yml: diagnostica manuale sul branch di test; non avviata.
- telegram-test.yml: invia messaggi su dispatch/push relativo: non modificato e non
  avviato. Non è un sistema di alert automatici verificati.
- Due copie sotto .github/workflows/.github: non sono workflow attivi.
- docs/collector-workflow.yml.example: template inattivo di una proposta precedente.
  NON installarlo: richiede un altro repository e contrasta col vincolo attuale
  di non creare nuovi progetti. Nessuna periodicità attivata.

## Val Town: risposta alle sei domande

1. **Provenienza:** il README dell'operatore dichiara player-prices-ps5.json per i
   prezzi e FUT.GG per i metadati FC27; non è un'API ufficiale EA. Dichiarazione
   del fornitore, non audit indipendente dell'intera catena upstream.
2. **Mercato:** progetto e nome del file dichiarano PS5/PlayStation. Il mercato
   console condiviso è l'obiettivo; il payload non basta a certificarlo per ogni
   carta senza attestazione e riscontro. PC non deve essere mescolato.
3. **Reali o stimati:** l'operatore presenta price come osservazione del feed;
   i forecast a sette giorni sono esplicitamente stime. Non usare forecast come
   prezzo di rivendita reale. price non è ancora certificato contro il gioco.
4. **Frequenza:** il progetto fut-market-cron dichiara un avvio ogni 15 minuti;
   il collector conserva il primo snapshot dell'ora. Cron, lettura upstream,
   aggiornamento effettivo del valore e storico sono quattro frequenze diverse.
   Zero cambiamenti in 60s è compatibile con mercato stabile, cache o feed fermo:
   non consente di scegliere fra queste ipotesi. updated globale non attesta
   la freschezza di ogni singola carta.
5. **Diritti:** non trovata un'autorizzazione documentata sufficiente per
   raccolta, storico e riutilizzo/redistribuzione. FUT.GG richiede permesso
   espresso per automazione. Un wrapper pubblico e CORS permissivo non concedono
   i diritti dei dati upstream. Fonte disabilitata.
6. **Affidabilità:** dopo il consenso, campione stratificato per tutte le categorie
   e fasce prezzo, item ID/versione esatti, confronto manuale con mercato console
   in istanti vicini; misurare errore relativo, età, copertura, variazioni reali,
   record mancanti e conflitti. Separare timestamp di osservazione upstream,
   aggiornamento feed e fetch. Solo dopo autorizzazione: osservazione almeno
   24–48h a intervalli consentiti, senza riempire i buchi con stime.

Copertura: /latest dichiara massimo 100 per ciascuno dei sei gruppi (massimo
teorico 600 record), storico orario. I 589 record riferiti non coprono l'intero
mercato; i totali di circa 20mila a monte sono dichiarazioni datate del progetto.
Percentuale sul mercato reale non calcolabile con denominatore verificato assente.

## Alternative: verificato, dichiarato, sconosciuto

V = documentazione/termini consultati; D = dichiarazione del provider non
collaudata con prezzi production; ND = informazione non disponibile/verificata.

| Fonte | Mercato/carte/ID | Frequenza | Gratuità e diritti | Esito |
|---|---|---|---|---|
| Val Town | D: PS5, item ID, sei gruppi; 589 riferiti dall'utente | D: cron 15m, snapshot 1h; freschezza upstream ND | Pubblico; permesso dati upstream ND | Promettente sul piano tecnico, bloccato sui diritti e sulla verifica |
| FUT.GG | D: database FC27/prezzi console; dati upstream del wrapper | ND per utilizzo esterno | V: automazione solo se espressamente permessa | Nessun connettore attivato |
| FUTBIN e SDK | D: quotazioni console; client unofficial non certifica anno/versione | ND per API esterna | V: scraping vietato senza permesso scritto; eccezione studenti/creator non assunta applicabile | SDK MIT non autorizza i dati |
| FCData | D: item ID, BIN console/PC separati, timestamp, non scambiabili senza prezzo | D: durante il giorno, SLA 30–60m ND | V: uso personale e limiti automazione; nessuna licenza feed aperto o quota API esterna verificata | Candidata per richiesta di accordo gratuito, non per estrazione ora |
| FCUTeam | D da ricerca: catalogo FC27 e prezzi ogni ora | D: oraria; pagina restituisce 403 al lettore web | API/riuso ND | Nessun tentativo di aggiramento o integrazione |
| FUT-DB | D: catalogo FC27; prezzi premium | V dichiarazione: 30m–24h | V: chiave gratis non include prezzi; premium 79 €/mese | Non soddisfa budget né freschezza uniforme |
| DataFluxor FUT Data | D: versioni EA, console/PC, età per osservazione | D: variabile per carta, nessuna prova production qui | V: FUT Data escluso dal piano gratuito; prova omaggio solo concordata | Possibile test gratuito concordato, non soluzione gratuita permanente |
| FCRadar | V: modalità Carriera, non mercato FUT | Non pertinente | V: 50mila richieste/mese gratis, attribuzione | Inadatto ai prezzi Ultimate Team |
| EA Community API | V: dati account a partner approvati | Feed pubblico prezzi ND | V: accesso riservato, nuove richieste non accettate nella pagina consultata | Non attivabile per il progetto |

Non individuato un feed corrente console con licenza aperta esplicita e raccolta
automatica gratuita autorizzata. Non è una prova universale di inesistenza.

Fonti consultate:
- https://www.val.town/x/bowli/fut-market-api
- https://www.val.town/x/bowli/fut-market-cron
- https://stormstrike.gg/terms
- https://www.futbin.com/tos (sezione 13)
- https://fcdata.io/about/ e https://fcdata.io/terms
- https://fcuteam.com/en/about-data (403 al lettore web)
- https://fut-db.com/
- https://datafluxor.com/fut-data e https://datafluxor.com/terms
- https://fcradar.gg/api-pricing
- https://www.ea.com/games/ea-sports-fc/news/pitch-notes-fc26-community-api-update

## Scanner implementato

experimental_scanner.py riusa report del motore. Demo soltanto con data_kind
synthetic: gli output mantengono simulated=true, actionable=false e production_signals
vuoto. Il percorso futuro production richiede source_id coerente, verified e
permessi del registro; non è collegato ad alcuna fonte reale. Dati non autorizzati
producono solo stato bloccato e rischio di fonte, senza valori prezzo nell'output.

Tre fixture sintetiche in memoria: candidata fresca con liquidità misurata fittizia,
carta obsoleta, carta senza liquidità. Nessun prezzo fixture scritto in prices.json
o experimental/market-state.json. CLI solo --demo, nessun fetch o output file interno.

Variazioni a 1/6/24h quando disponibili, target mediana superiore storica, netto
= target * 95 // 100 - acquisto. Minimi 800 crediti / ROI 5%, almeno tre punti
precedenti in 24h e sales_1h >=5 per candidate. Assenza liquidità = nessuna candidata.
Target ipotetico, nessuna previsione di profitto garantita o asta verificata.

Rischio = somma pesi unici, limitata a 100: fonte non verificata 40, prezzo vecchio
35, futuro 50, liquidità ignota/bassa 20, storico insufficiente 20, finestre mancanti
10, anomalie >50% 40, oscillazione recente >25% 20, storico invalido 50. L'indicatore
non è calibrato su perdite reali né costituisce una probabilità. Sono mostrate
motivazioni e severità; sinteticità è etichettata separatamente, non mascherata da
un punteggio basso. Dati vecchi/futuri/anomali/invalidi non sono candidate.

experimental/scanner.html e scanner.js: import locale di report sintetici,
etichettatura permanente, filtro candidate, dati mancanti n.d., rischi e margini,
avviso sulla vecchiaia rispetto all'orologio del browser. Non invia dati a server,
non salva localStorage, non accetta report production e non richiede input prezzi
per carta. È una demo di sviluppo, non la modalità d'uso finale quotidiana.

## Riproduzione e test

Dalla radice del repository:

```sh
python -m unittest discover -s tests -v
mkdir -p work
python experimental_scanner.py --demo > work/scanner-demo.json
python tests/browser_scanner.py
```

Il test browser opzionale richiede Playwright e Chromium /usr/bin/chromium già
installati. Avvia un server temporaneo su loopback, chiuso alla fine del processo;
nessuna pubblicazione né accesso a fonti terze. Aprire localmente scanner.html e
caricare work/scanner-demo.json per ispezionare la demo.

58 test unitari offline superati: precedenti 36, 6 nuovi test diagnostica e 16
scanner; fee/ROI, finestre, identità, timestamp equivalenti con timezone,
regressione, permessi, duplicati, fonte errata, dati mancanti, obsolescenza,
anomalie, no mutazione e separazione synthetic/production.
Browser Chromium: 375/390/1280px, etichette, filtro, overflow, testo HTML reso
inerte, rifiuto report production, svuotamento. Sintassi JS/Python e diff check.
Non collaudato su Safari iPhone reale o browser PS5; nessun test live prezzi,
nessun nuovo esito GitHub Actions perché non effettuato push o dispatch.

## Prossimi interventi

1. Ottenere dall'operatore Val Town e dai titolari upstream un consenso esplicito
   per polling, archivio e uso previsto, oppure un piccolo feed gratuito concordato
   con FCData/FUT.GG/FUTBIN. Nessun contatto inviato automaticamente.
2. Documentare semantica per-card di item ID, mercato, scambiabilità, prezzo e
   timestamp; effettuare campionamento e misurazione su produzione consentita.
3. Integrare l'adapter autorizzato nella pipeline esistente; quarantena per singola
   carta, segnali di errore descrittivi, misura della copertura e limiti fonte.
4. Scegliere l'esecuzione restando nello stesso progetto e senza cambiare main:
   finché non è autorizzato un meccanismo compatibile non attivare periodicità.
   GitHub schedule usa il default branch; nel solo branch test non funziona.
   Un runner locale può eseguire il codice del branch esistente, ma richiede un
   dispositivo acceso: iPhone/PS5 da soli non forniscono un servizio continuo.
5. Solo dopo il consenso a distribuire l'app: collaudo Safari/iPhone, accesso
   sicuro alla preview di test e notifiche esplicitamente richieste. Al momento
   nessun deployment o modifica dell'app online è autorizzato da questa attività.

L'obiettivo gratuito e senza inserimenti continui resta subordinato alla fonte:
le analisi possono essere automatiche, ma non possono creare nuove osservazioni
reali né sostituire il diritto di raccoglierle.
