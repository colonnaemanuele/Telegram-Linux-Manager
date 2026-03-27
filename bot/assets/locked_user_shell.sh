#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
FRAMES_DIR="$SCRIPT_DIR/ceasar"
FRAME_DELAY="${FRAME_DELAY:-0.2}"

# Pulisce lo schermo totalmente all'inizio
printf '\033[2J\033[H'

# Carica i frame ASCII già generati in assets/ceasar/frame_*.txt
shopt -s nullglob
frames=("$FRAMES_DIR"/frame_*.txt)
shopt -u nullglob

if ((${#frames[@]} == 0)); then
    printf 'Errore: nessun frame trovato in %s\n' "$FRAMES_DIR" >&2
else
    for frame in "${frames[@]}"; do
        # Riporta il cursore in alto a sinistra senza cancellare tutto lo schermo
        # Questo riduce drasticamente lo sfarfallio (flickering) su SSH
        printf '\033[H'
        cat "$frame"

        printf '\n'
        printf '====================== CEASAAAAAR!!!! ======================\n'


        # Pausa tra un frame e l'altro
        sleep "$FRAME_DELAY"
    done
fi

printf '\n\n'

# Stampa il messaggio finale di ban
cat <<'EOF'
============================================================
                    YOU ARE BANNED
============================================================

Your access has been suspended for 2 minutes.
Come back later.
EOF

printf '\n'

# Lascia il messaggio a schermo per 2 secondi prima di chiudere la connessione
sleep 2

# Espelle l'utente
exit 1