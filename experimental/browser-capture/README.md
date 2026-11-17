# FUT Trader 27 — acquisizione locale desktop (prototipo)

1. Apri Chrome/Edge su computer e vai a chrome://extensions (oppure edge://extensions).
2. Attiva Modalità sviluppatore, poi **Carica estensione non pacchettizzata** scegliendo questa cartella scaricata dal branch di test.
3. Apri una pagina HTTPS con una quotazione visibile, seleziona il prezzo col mouse e premi l'icona dell'estensione > **Leggi selezione**.
4. Controlla e completa manualmente ID EA **della specifica versione**, nome, prezzo e riferimento storico; premi **Esporta osservazione JSON**.
5. Importa il JSON in experimental/trading-desk.html. La medesima pagina di importazione è utilizzabile su Safari iPhone tramite File, ma l'estensione Chrome non funziona su iPhone.

Nessun accesso a cookie, credenziali, richieste XHR o API private; nessun polling, acquisto o pubblicazione di dati. L'estensione legge solo testo selezionato dopo un clic. L'osservazione esportata è non verificata; un solo prezzo non costituisce storico sufficiente per un segnale. Il codice non è ancora stato testato in un browser reale.
