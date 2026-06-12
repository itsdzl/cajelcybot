# Skeleton rewritten bot for Python 3.10+
# Reads settings including GEMINI_API_KEY by key=value.
# Supports:
# - @bot mention replies
# - random "cajel" replies
# - startup greeting
# - Gemini via HTTP REST API (No Google-GenAI library required!)
# - Fitur "fuckoff" untuk mematikan bot & sesi Termux jarak jauh[span_0](start_span)[span_0](end_span)
#
# NOTE: Fill in further custom behaviour as needed.

import random, asyncio, aiohttp, json, os
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
    "apaci manggil manggil😠"
    "apa sayang... sjsiejdhdofj"
]

# Fungsi untuk memanggil API Gemini menggunakan HTTP POST secara Asynchronous (Mendukung API Key Format Baru AQ.)
async def ask_gemini(prompt):
    clean_key = API_KEY.strip() 
    
    # URL sekarang bersih, tidak perlu menempelkan ?key= di ujungnya
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    # PERBAIKAN: API Key format baru (AQ.) wajib dikirimkan lewat HEADER x-goog-api-key
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": clean_key
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Kamu adalah {NAME}, bot Telegram lucu. Jawab singkat bahasa Indonesia. {prompt}"}]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                if response.status == 200:
                    res_json = await response.json()
                    return res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    err_text = await response.text()
                    return f"Error API ({response.status}): {err_text[:150]}"
    except Exception as e:
        return f"Koneksi Error: {str(e)}"

@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt = m.text or ""
    low = txt.lower().strip()

    OWNER_ID = 8278748114 

    if low == "fuckoff":
        if m.from_user.id == OWNER_ID:
            await bot.reply_to(m, "ih jahat dimatiin 🥹")
            await asyncio.sleep(1)
            os._exit(0)
        else:
            await bot.reply_to(m, "kamu bukan paduka ijel, kamu gabisa matiin aku!")

    # =========================================================

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

        await bot.send_chat_action(m.chat.id, 'typing')
        jawaban = await ask_gemini(q)
        await bot.reply_to(m, jawaban)

async def startup():
    me = await bot.get_me()
    print(f"Bot Berhasil Online! Username: @{me.username}")
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
    
