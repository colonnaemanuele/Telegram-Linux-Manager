# Script Bot

Small Python utility to run the project's main process and helpers.

## Requirements
- Python 3.8+
- (Optional) project dependencies — install with:
    ```
    uv add -r requirements.txt
    ```

## Setup
1. Copy environment file:
     ```
     cp .env.sample .env
     ```
2. Edit `.env` to set required environment variables.

## Run
- Start normally:
    ```
    uv run main.py
    ```
or make it like a service in your system.


## Commands
1. ```/start```: Invia un messaggio di benvenuto e mostra la lista dei comandi disponibili.

2. ```/status```: Esegue il controllo dei processi attivi tramite la logica interna e restituisce il risultato formattato in Markdown.
<!-- - Accesso: Limitato al valore configurato in ALLOWED_CHAT_ID. -->

3. ```/scripts```: Elenca i file presenti nella cartella configurata da SCRIPTS_DIR.
<!-- - Comportamento: Verifica l'esistenza della cartella, segnala se vuota e mostra i nomi dei file.
- Accesso: Limitato al valore configurato in ALLOWED_CHAT_ID.
- Errori: Restituisce messaggi di errore in caso di eccezioni di I/O. -->

4. ```/run <script> [args...]```
Description: Esegue uno script presente in SCRIPTS_DIR con argomenti opzionali.
<!-- - Sicurezza: Blocca tentativi di traversal (.., /, \) e verifica che il file esista nella cartella degli script.
- Esecuzione: Avvia il comando con TERM=dumb, timeout di 60 secondi, cattura stdout/stderr, e rimuove i codici ANSI dall'output.
- Output: Restituisce l'output pulito (se vuoto riporta un messaggio di successo), tronca oltre 4000 caratteri e include eventuali errori stderr.
- Errori gestiti: TimeoutExpired, PermissionError (suggerimento: chmod +x), eccezioni generiche.
- Accesso: Limitato al valore configurato in ALLOWED_CHAT_ID. -->

## Files
- `.env`, `.env.sample` — environment variables.
- `main.py` — entry point.
- `command.py` — command definitions / CLI logic.
- `config.py` — configuration loader.
- `utils.py` — helper utilities.
- `check_nohup.py` — helper to verify background/nohup run.

## Notes
- Use a virtual environment for isolation.
- Adjust logging/output redirection as needed.
