# FUT Trader 27 — Raccolta in background (sperimentale)

Questo modulo è **separato** dal sito Cloudflare Pages e dal branch GitHub `main`. Non è attivo finché non viene configurato nel proprio account Cloudflare.

## Configurazione Cloudflare

1. Cloudflare Dashboard → Workers & Pages → KV → Create namespace. Nome suggerito: `FUT27_HISTORY`.
2. Workers & Pages → Create → Worker (separato dal progetto Pages esistente). Caricare il contenuto di `experimental/mobile-trader/background-worker.js`.
3. Worker → Settings → Bindings → Add → KV namespace. **Variable name esatto:** `FUT27_HISTORY`; selezionare il namespace appena creato.
4. Worker → Settings → Triggers → Cron Triggers → Add: `*/30 * * * *` (UTC; esecuzione approssimativa ogni 30 minuti).
5. Dopo la prima esecuzione programmata, aprire `https://<nome-worker>.<subdomain>.workers.dev/history`. Deve restituire `schema: fut27-experimental-history-v1` con almeno uno snapshot. Il nome e il sottodominio sono forniti da Cloudflare, non vanno indovinati.

## Avvertenze

- Fonte Val Town di terze parti non verificata per PlayStation, licenza, disponibilità e qualità dei prezzi.
- Il cron non garantisce precisione al minuto; KV è eventualmente consistente e gli aggiornamenti concorrenti potrebbero perdere un campione.
- L'endpoint /history è pubblico e ha CORS ristretto all'origine di anteprima. Non contiene credenziali.
- Conserva al massimo 336 snapshot; dimensione del valore KV e quote del piano Cloudflare possono diventare un limite. Monitorare dimensione e consumo.
- La dashboard **non è ancora collegata** a /history: il Worker raccoglie dati indipendentemente, mentre la dashboard usa il proxy Pages e lo storico locale. Il collegamento si effettua dopo verifica del Worker e comunicazione del suo URL esatto.
- Non usare i dati per segnali operativi o ordini automatici.
