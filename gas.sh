#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

while true; do
    echo "🚀 Memulai bot..."
    python3.13 main.py 2> error.log
    echo "❌ Bot berhenti! Berikut adalah pesan error terakhir:"
    cat error.log
    echo "----------------------------------------------------"
    echo "💤 Menunggu 30 detik sebelum restart otomatis..."
    sleep 30
done
