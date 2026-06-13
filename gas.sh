#!/bin/bash

cd ~/cajel

while true
do
    echo "Menjalankan Cajel Bot Modular System..."
    python main.py
    
    echo "💤 Bot terhenti atau crash. Menunggu 30 detik sebelum restart otomatis..."
    sleep 30
done
