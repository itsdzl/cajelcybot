# Skeleton rewritten bot for Python 3.10+
# Reads settings including GEMINI_API_KEY by key=value.
# Supports:
# - @bot mention replies
# - random "cajel" replies
# - startup greeting
# - Gemini via HTTP REST API (No Google-GenAI library required!)
#
# NOTE: Fill in further custom behaviour as needed.

import random, asyncio, aiohttp, json
from telebot.async_telebot import AsyncTeleBot

cfg={}
with open("settings", "r", encoding="utf8") as f:
    for line in f:
        if "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

TOKEN = cfg["token"]
BOTNAME = cfg["botname"]
NAME = cfg.get("name", "cajel")
API_KEY = cfg["GEMINI_API_KEY"]

bot = AsyncTeleBot(TOKEN)

RANDOM_CAJEL = [
    "Hah? manggil aku? 🤭",
    "Iya? Ada apa?",
    "Hehe hadir!",
    "Cajel online~"
]

# Fungsi untuk memanggil API Gemini menggunakan HTTP POST secara Asynchronous
async def ask_gemini(prompt):
    # Menggunakan model gemini-1.5-flash karena sangat stabil untuk endpoint REST API gratisan
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # Format payload instruksi sesuai dengan sistem kustomisasi karakter bot Anda
    payload = {
        "contents": [{
            "parts": [{"text": f"aku adalah {NAME}, bot tele paling imut, bagi duit donkkk 😸🫴🏻 {prompt}"}]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                if response.status_code == 200:
                    res_json = await response.json()
                    # Parsing struktur JSON balasan dari Google
                    return res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    err_text = await response.text()
                    return f"Error API ({response.status_code}): {err_text[:100]}"
    except Exception as e:
        return f"Koneksi Error: {str(e)}"

@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt = m.text or ""
    low = txt.lower()

    if low == "cajel":
        await bot.reply_to(m, random.choice(RANDOM_CAJEL))
        return

    if BOTNAME.lower() in low:
        q = txt.replace(BOTNAME, "").strip()
        if not q:
            q = "halo"
            
        if not API_KEY:
            await bot.reply_to(m, "Gemini belum aktif. API Key kosong di file settings.")
            return

        # Indikator bot sedang mengetik di Telegram biar terasa interaktif
        await bot.send_chat_action(m.chat.id, 'typing')
        
        # Memanggil fungsi Gemini HTTP alternatif kita
        jawaban = await ask_gemini(q)
        await bot.reply_to(m, jawaban)

async def startup():
    me = await bot.get_me()
    print(f"Bot Berhasil Online! Username: @{me.username}")
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
  
