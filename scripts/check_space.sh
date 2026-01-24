#!/bin/bash

PARENT=${1:-/home}
if [ -z "$PARENT" ]; then
  echo "Usage: $0 <folder>"
  exit 1
fi

# Gestione path per df
if [[ "$PARENT" == /*/* ]]; then
    BASE=${PARENT%/*}
else
    BASE=$PARENT
fi

# Intestazione Disco (df -h)
DISK_INFO=$(df -h "$PARENT" | awk 'NR==2 {print $2, $3, $4, $5}')
TOTAL=$(echo "$DISK_INFO" | awk '{print $1}')
USED=$(echo "$DISK_INFO"  | awk '{print $2}')
FREE=$(echo "$DISK_INFO"  | awk '{print $3}')
PERC=$(echo "$DISK_INFO"  | awk '{print $4}')

echo "📊 Analisi: $PARENT"
echo "💾 Disco: $USED usati / $TOTAL ($PERC full)"
echo "-------------------------------------"
echo "🟢 <1GB | 🟡 1-5GB | 🔴 >5GB"
echo "-------------------------------------"

# Loop sulle cartelle
# Usiamo un array temporaneo o pipe per il sort
for FOLDER in "$PARENT"/*; do
  if [ -d "$FOLDER" ]; then
    # du -sk = dimensione in KB
    SIZE_KB=$(du -sk "$FOLDER" 2>/dev/null | awk '{print $1}')
    
    # Fix per cartelle illeggibili (imposta a 0)
    if [ -z "$SIZE_KB" ]; then SIZE_KB=0; fi
    
    # Stampa RAW: dimensione_kb nome_completo
    echo "$SIZE_KB $FOLDER"
  fi
done | sort -nr | head -n 20 | while read SIZE_KB FOLDER; do
    # Ciclo di lettura post-sort (Top 20)
    
    if [ "$SIZE_KB" -gt 0 ]; then
        # Calcolo dimensione umana (GB/MB)
        SIZE_HR=$(du -sh "$FOLDER" 2>/dev/null | awk '{print $1}')
        NAME=$(basename "$FOLDER")
        
        # Logica Icone
        # > 5GB (5242880 KB) -> Rosso
        if [ "$SIZE_KB" -gt 5242880 ]; then
            ICON="🔴"
        # > 1GB (1048576 KB) -> Giallo
        elif [ "$SIZE_KB" -gt 1048576 ]; then
            ICON="🟡"
        else
            ICON="🟢"
        fi
        
        # Stampa formattata: Icona - Spazio(allineato a 7 char) - Nome
        printf "%s %-7s %s\n" "$ICON" "$SIZE_HR" "$NAME"
    fi
done

echo "-------------------------------------"