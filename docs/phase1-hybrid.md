# FUT Trader 27 — Fase 1 ibrida

Branch: `fut-trader-27-test` (non pubblicare su main senza autorizzazione).

## Implementato
- Web app installabile da Safari tramite Aggiungi alla schermata Home, manifest e icona.
- Capitale configurabile 0–100.000 crediti, con clamp anche sui dati salvati.
- Backup JSON ripristinabile fino a 100.000 crediti.
- Feed non verificato esplicitamente segnalato: nessun segnale BUY live.

## Test manuali su iPhone
1. Aprire la pagina del branch di test da hosting di anteprima HTTPS; verificare il manifest.
2. Impostare capitale a 80.000, ricaricare: deve restare 80.000.
3. Esportare backup, ripristinarlo e verificare capitale.
4. Aprire Dati e backup e controllare il feed: senza fonte verificata nessun segnale live.
5. Aggiungere una carta manuale e verificare tassa EA 5%.

## Limiti
GitHub Pages di produzione non deve cambiare; il solo commit sul branch di test non crea automaticamente una URL di anteprima. Manifest SVG può avere supporto variabile come icona iOS; per un'icona Home ottimale aggiungere PNG Apple touch. Nessuna raccolta automatica o notifica push è stata attivata.
