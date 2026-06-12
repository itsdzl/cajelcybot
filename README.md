# 🤖 CAJEL CYBOT — Gemini AI Telegram Bot
<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" alt="Python Version">
<img src="https://img.shields.io/badge/Telegram-Bot%20API-blue?style=for-the-badge&logo=telegram" alt="Telegram Bot API">
<img src="https://img.shields.io/badge/AI-Google%20Gemini-orange?style=for-the-badge&logo=google-gemini" alt="Google Gemini">
<img src="https://img.shields.io/badge/Creator-aa%20ijel-red?style=for-the-badge" alt="t.me/niskalaaksa">
</p>

Selamat datang di repositori resmi **Cajel Cybot**!
Sebuah bot Telegram berbasis AI asinkron (AsyncTeleBot) yang ditenagai oleh model **Google Gemini 2.5-Flash.**

Bot ini dirancang dengan kepribadian yang imut, lucu, sangat random, menggemaskan, sekaligus sedikit menyebalkan dan tengil!

Bot ini diciptakan khusus oleh **AA IJEL YANG GANTENG, IMUT, DAN LUCU BANGET TIADA TANDING! 😎✨**

## ✨ Fitur Unggulan
 * **🧠 Gemini AI Integration**
   Otak pintar Gemini 2.5-Flash dengan kepribadian super random, dinamis, ekspresif menggunakan emoji, dan suka mengobrol gaul.
   
 * **🔄 Multi-API Key Rotation (Failover)**
   Fitur pertahanan ganda! Otomatis gonta-ganti API Key (maksimal hingga 5 kunci cadangan) jika salah satu key terkena limit kuota (*Error 429*), gangguan server (*Error 503*), atau tidak valid (*Error 401*).
   
 * **💬 Sistem Chat Natural (Reply Mode)**
   Cukup balas (*reply*) pesan si Cajel di grup, dan dia akan otomatis membalas obrolan tanpa perlu mengetik pemicu/tag namanya lagi.
   
 * **🎲 Auto-Nimbrung Random**
   Bot memiliki peluang acak sebesar 10% untuk ikut menyahut atau sok tahu mengomentari obrolan grup secara tiba-tiba biar suasana grup makin ramai! (Dioptimalkan agar hemat kuota).
   
 * **📜 Dynamic Help Command**
   Menu /help yang mendeteksi peran pengguna secara langsung. Menampilkan perintah rahasia developer hanya jika diakses oleh sang Owner (aa ijel).
   
 * **🛠️ Utilitas Publik & Hiburan**
   * /start — Sambutan hangat di Private Chat sekalian pamer ketampanan aa ijel.
   * /info — Informasi sistem, data Telegram ID Anda, dan status server.
   * /mock [teks] — Mengubah pesan menjadi format mOkInG tExT ejekan ala meme Spongebob (bisa digunakan via reply chat).
     
 * **👑 Fitur Dewa (Owner Only)**
   * syuh — Perintah instan untuk mematikan sesi bot secara aman dari jarak jauh via chat.
   * .eval [kode_python] — Menjalankan script Python secara langsung di server secara asinkron dari dalam ruang obrolan Telegram.
   
## 🚀 Panduan Instalasi (Termux / VPS)
Ikuti langkah-langkah mudah di bawah ini untuk menjalankan Cajel Cybot di perangkat Anda:

### 1. Persiapan Awal & Clone Repo
Pastikan Python 3.10+ sudah terpasang. Di Termux/VPS, jalankan perintah berikut:

```bash
pkg update && pkg upgrade -y
pkg install python git -y

```
### 2. Install Library yang Dibutuhkan
Bot ini berjalan sepenuhnya secara asinkron menggunakan pustaka pyTelegramBotAPI versi terbaru dan aiohttp untuk penanganan HTTP request berkecepatan tinggi:

```bash
pip install pyTelegramBotAPI aiohttp

```
### 3. Konfigurasi File settings
Buat sebuah file bernama settings di dalam direktori bot Anda dengan struktur key = value. Anda bisa memasukkan hingga 5 kunci API Gemini cadangan:
**Format Berangka (Sangat Direkomendasikan):**

```text
token = ISI_TOKEN_BOT_TELEGRAM_ANDA
botname = @UsernameBotAnda
name = cajel
GEMINI_API_KEY = KUNCI_GEMINI_UTAMA_ANDA
GEMINI_API_KEY_2 = KUNCI_GEMINI_CADANGAN_KEDUA
GEMINI_API_KEY_3 = KUNCI_GEMINI_CADANGAN_KETIGA

```

**Atau Format Satu Baris (Dipisah Koma):**

```text
token = ISI_TOKEN_BOT_TELEGRAM_ANDA
botname = @UsernameBotAnda
name = cajel
GEMINI_API_KEY = KUNCI_UTAMA, KUNCI_CADANGAN_2, KUNCI_CADANGAN_3

```

> 💡 *Dapatkan API Key Gemini secara gratis di Google AI Studio.*
> 
### 4. Jalankan Bot!
Jalankan bot dengan perintah sederhana berikut:
```bash
python geminiai_sip.py

```
Jika berhasil, Anda akan melihat pesan log di terminal:
```text
Bot Berhasil Online! Username: @UsernameBotAnda

```
## 🛡️ Logika Rotasi API Key (Cara Kerjanya)
Ketika bot mendeteksi adanya error pengiriman pesan ke Google AI Studio, bot akan memproses kegagalan tersebut secara cerdas:
 1. Jika respon server berupa **503 (Overloaded)**, **429 (Rate Limit)**, atau **500 (Server Error)**, bot akan mencoba mengulang kembali (*Auto-Retry*) sebanyak 2 kali menggunakan jeda waktu melipat (*Exponential Backoff*).
 2. Jika setelah diulang tetap gagal, atau jika respon server berupa **401/403 (Kunci Mati)**, bot akan mencetak log peringatan di Termux:
   [ROTASI] API Key 1 Gagal Quota/Limit (status 429). Info: Quota exceeded...
 3. Bot akan **otomatis beralih menggunakan API Key cadangan berikutnya** (Key 2, Key 3, dst.) tanpa menghentikan sesi atau mengganggu kenyamanan pengguna di grup Telegram.
## 🤝 Kontribusi & Hak Cipta
 * Pencipta & Pengembang Utama: **Aa Ijel Yang Ganteng, Imut, Dan Lucu**.
 * Menggunakan Model AI: **Google Gemini-2.5-Flash API**.
*Dibuat dengan cinta (dan sedikit ketengilan) oleh AA IJEL untuk Kalian Entah SIAPAA.* 🤍
