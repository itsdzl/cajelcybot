#!/bin/bash
# Mendapatkan lokasi folder tempat file gas.sh berada
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Menjalankan Cajel Bot Modular System di $DIR..."
cd "$DIR"

while true; do
    python3 main.py
    echo "💤 Bot terhenti atau crash. Menunggu 30 detik sebelum restart otomatis..."
    sleep 30
done
