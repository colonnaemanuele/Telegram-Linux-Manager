#!/bin/bash

# URL e file temporaneo per i cookie
LOGIN_URL="https://autentica.uniba.it:1003/login?"
COOKIE_FILE=$(mktemp)

# Headers comuni per entrambe le richieste
common_headers=(
    -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
    -H 'Accept-Language: it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
    -H 'Connection: keep-alive'
    -H 'User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'
    -H 'sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
    -H 'sec-ch-ua-mobile: ?1'
    -H 'sec-ch-ua-platform: "Android"'
)

echo "🔄 Ottengo il magic token..."

# 1️⃣ - Recupera la pagina di login per ottenere il "magic"
PAGE_CONTENT=$(curl -k -s -c "$COOKIE_FILE" "$LOGIN_URL" "${common_headers[@]}")

# 2️⃣ - Estrai il valore del "magic" dal codice HTML
MAGIC=$(echo "$PAGE_CONTENT" | grep -oP '(?<=name="magic" value=")[^"]+')

# Controlla se il MAGIC è stato trovato
if [[ -z "$MAGIC" ]]; then
    echo "❌ Errore: Magic non trovato!"
    rm "$COOKIE_FILE"
    exit 1
fi

echo "🔑 Magic Token estratto: $MAGIC"

# Richiedi credenziali in modo interattivo
echo -n "👤 Inserisci username: "
read username
echo -n "🔒 Inserisci password: "
read -s password
echo  # nuova linea dopo l'input della password

echo "🔄 Eseguo l'autenticazione..."

# Esegui l'autenticazione
auth_response=$(curl -k -s -b "$COOKIE_FILE" -c "$COOKIE_FILE" \
    'https://autentica.uniba.it:1003/' \
    "${common_headers[@]}" \
    -H 'Cache-Control: max-age=0' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -H 'Origin: https://autentica.uniba.it:1003' \
    -H "Referer: $LOGIN_URL" \
    -H 'Sec-Fetch-Dest: document' \
    -H 'Sec-Fetch-Mode: navigate' \
    -H 'Sec-Fetch-Site: same-origin' \
    -H 'Sec-Fetch-User: ?1' \
    -H 'Upgrade-Insecure-Requests: 1' \
    --data-urlencode "4Tredir=$LOGIN_URL" \
    --data-urlencode "magic=$MAGIC" \
    --data-urlencode "username=$username" \
    --data-urlencode "password=$password" \
    -i)

# Estrai lo status code dalla risposta
status_code=$(echo "$auth_response" | grep -i "HTTP/" | awk '{print $2}')

if [ "$status_code" -eq 200 ] || [ "$status_code" -eq 302 ]; then
    echo "✅ Autenticazione completata con successo (HTTP $status_code)"

    # Salva la risposta per debug (opzionale)
    echo "$auth_response" > /dev/null
    echo "📝 Risposta salvata in /dev/null"
else
    echo "❌ Autenticazione fallita (HTTP $status_code)"
fi

# Pulizia
rm "$COOKIE_FILE"
