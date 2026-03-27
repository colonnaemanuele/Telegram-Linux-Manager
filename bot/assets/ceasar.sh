#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
GIF_PATH="${1:-$SCRIPT_DIR/ceasar.gif}"
OUT_DIR="${2:-$SCRIPT_DIR/ceasar}"
TMP_DIR="$OUT_DIR/tmp_frames"
WIDTH="${WIDTH:-60}"

if [[ ! -f "$GIF_PATH" ]]; then
    echo "Errore: GIF non trovata: $GIF_PATH" >&2
    exit 1
fi

if ! command -v jp2a >/dev/null 2>&1; then
    echo "Errore: jp2a non installato." >&2
    exit 1
fi

if command -v magick >/dev/null 2>&1; then
    IM_CMD=(magick)
elif command -v convert >/dev/null 2>&1; then
    IM_CMD=(convert)
else
    echo "Errore: ImageMagick non installato (magick/convert non trovato)." >&2
    exit 1
fi

# 1. Crea una cartella temporanea ed estrae i frame dalla GIF
mkdir -p "$TMP_DIR"

cleanup() {
    # 3. Pulisce i file immagine temporanei
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

# Usa ImageMagick per dividere la gif in file png (frame_00.png, frame_01.png, ecc.)
"${IM_CMD[@]}" "$GIF_PATH" -coalesce "$TMP_DIR/frame_%04d.png"

# 2. Converte ogni PNG in un file di testo ASCII
shopt -s nullglob
frames=("$TMP_DIR"/*.png)

if ((${#frames[@]} == 0)); then
    echo "Errore: nessun frame estratto dalla GIF." >&2
    exit 1
fi

for img in "${frames[@]}"; do
    # Estrae il nome del file senza estensione
    filename="$(basename -- "$img" .png)"

    # Usa jp2a per convertire l'immagine in ASCII art (larghezza 60 caratteri)
    # e salva il risultato in file .txt
    jp2a --width="$WIDTH" "$img" > "$OUT_DIR/${filename}.txt"
done

echo "Finito! Frame ASCII generati: ${#frames[@]}"