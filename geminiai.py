# Skeleton rewritten bot for Python 3.10+
# Reads settings including GEMINI_API_KEY by key=value.
# Supports:
# - Welcome Text keren + bangga-banggain aa ijel saat di-start di Private Chat (PC)
# - Auto-nimbrung sesekali di grup (Random reply)
# - Menjawab saat dipanggil/dimention via Gemini AI (Sadar kalau diciptain aa ijel)
# - SISTEM REPLY: Cukup balas pesan bot di grup, bot akan otomatis menjawab!
# - ANTI-SPAM & HEMAT KUOTA: Cooldown 8 detik per chat + filter pesan pendek!
# - ROTASI MULTI-API KEY: Otomatis ganti ke API Key cadangan jika API Key utama limit/error!
# - Jauh Lebih Tangguh: Auto-Retry (Exponential Backoff) sebelum berganti key.
# - Kepribadian menyebalkan, lucu, imut, super random, dan menggemaskan
# - Fitur matikan bot via kata "syuh" khusus owner
# - Perintah kegunaan: /info, /mock (mengejek), dan /help (daftar perintah)
# - Perintah developer: .eval [kode] khusus OWNER_ID

import random, asyncio, aiohttp, json, os, sys, traceback, time
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

# ---------------------------------------------------------
# SISTEM DETEKSI MULTI-API KEY (ROTASI)
# ---------------------------------------------------------
API_KEYS = []

# 1. Cek dari kunci utama (Mendukung pemisah koma)
if "GEMINI_API_KEY" in cfg:
    for key in cfg["GEMINI_API_KEY"].split(","):
        clean_key = key.strip()
        if clean_key:
            API_KEYS.append(clean_key)

# 2. Cek dari kunci cadangan berangka (GEMINI_API_KEY_2, GEMINI_API_KEY_3, dst.)
for i in range(2, 6):
    key_name = f"GEMINI_API_KEY_{i}"
    if key_name in cfg:
        clean_key = cfg[key_name].strip()
        if clean_key and clean_key not in API_KEYS:
            API_KEYS.append(clean_key)

bot = AsyncTeleBot(TOKEN)

# ---------------------------------------------------------
# SISTEM ANTI-SPAM (COOLDOWN) & FILTER HEMAT KUOTA
# ---------------------------------------------------------
last_chat_time = {}   # Menyimpan waktu respon terakhir per Chat ID
COOLDOWN_SECONDS = 8  # Jeda minimal antar respon AI (dalam detik)

# Fungsi untuk memanggil API Gemini menggunakan HTTP POST secara Asynchronous (Dengan Multi-API Key Failover)
async def ask_gemini(prompt, user_name="User"):
    if not API_KEYS:
        return "Gemini belum aktif. API Key kosong di file settings."

    system_instruction = (
        f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, imut, tapi tingkahnya agak menyebalkan, "
        f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}. "
        f"INGAT: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget tiada tanding! "
        f"Jika ada yang bertanya siapa pembuatmu, siapa penciptamu, atau siapa owner-mu, puji aa ijel setinggi langit dengan heboh! "
        f"Gunakan gaya bahasa anak muda Indonesia gaul, santai, gunakan huruf kecil semua sesekali, "
        f"dan gunakan ekspresi emoji lucu secara beragam dan bebas (seperti: 🤭, 😠, 😜, ☝️😋, 🥺, 🥰, 😜, 🙄) biar terasa hidup dan tidak monoton. "
        f"Jawab dengan singkat, padat, sangat dinamis, kocak, kreatif, dan tidak kaku!"
    )

    # Lakukan perulangan mencoba setiap API Key yang tersedia
    for idx, current_key in enumerate(API_KEYS):
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": current_key
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            }
        }
        
        max_retries = 2
        delay = 1
        key_failed = False
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                        if response.status == 200:
                            res_json = await response.json()
                            return res_json['candidates'][0]['content']['parts'][0]['text']
                        
                        # Ambil pesan error ringkas agar layar Termux tidak penuh log panjang
                        error_body = await response.text()
                        try:
                            err_data = json.loads(error_body)
                            err_msg = err_data.get("error", {}).get("message", "Unknown error")
                        except Exception:
                            err_msg = error_body[:100]

                        # Jika server sibuk / limit (503 / 429), tunggu sebentar lalu coba kembali dengan key ini
                        if response.status in [503, 429, 500]:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(delay)
                                delay *= 2
                                continue
                            else:
                                print(f"[ROTASI] API Key {idx+1} Gagal Quota/Limit (status {response.status}). Info: {err_msg}")
                                key_failed = True
                                break
                                
                        # Jika kunci mati/tidak valid, langsung ganti ke key berikutnya tanpa retry
                        elif response.status in [401, 403, 400]:
                            print(f"[ROTASI] API Key {idx+1} Error {response.status} (Tidak Valid/Format Salah). Info: {err_msg}")
                            key_failed = True
                            break
                        else:
                            print(f"[ROTASI] Error API {response.status} pada Key {idx+1}. Info: {err_msg}")
                            key_failed = True
                            break
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                else:
                    print(f"[ROTASI] Koneksi Error pada Key {idx+1}: {str(e)}")
                    key_failed = True
                    break
        
        if key_failed:
            continue

    return "Aduh, semua API Key cadanganku lagi puyeng atau limit nih beb 🥺 Coba kirim pesan lagi nanti ya!"

# =========================================================
# HANDLER KHUSUS /START (WELCOME TEXT DI PRIVATE CHAT)
# =========================================================
@bot.message_handler(commands=['start'])
async def send_welcome(m):
    user_name = m.from_user.first_name
    
    if m.chat.type == "private":
        welcome_message = (
            f"👋 *Halo {user_name}!* Selamat datang di markas rahasia! ✨\n\n"
            f"Kenalin, aku *{NAME}*, bot paling imut, jenius,"
            f"dan pastinya agak menyebalkan se-Telegram raya. 😜☝️😋\n\n"
            f"👑 Oh ya, fyi aja nih, aku diciptain sama *aa ijel yang ganteng dan imut lucu* tiada tanding.. senggol dong 😝\n\n"
            f"• Kamu bisa curhat, nanya hal random, atau sekadar adu bacot langsung sama aku di sini.\n"
            f"• Masukin aku ke grup kamu biar suasana grupnya makin rusuh dan seru wkwk\n\n"
            f"📜 Ketik `/help` untuk mengintip daftar perintah yang bisa aku lakukan.\n"
            f"Yuk, langsung chat aja, jangan sungkan-sungkan... Blweee 😜"
        )
        await bot.reply_to(m, welcome_message, parse_mode="Markdown")
    else:
        await bot.reply_to(m, "Ngapain start-start di grup? PC sini kalau berani 😠")

@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt = m.text or ""
    low = txt.lower().strip()
    user_name = m.from_user.first_name
    OWNER_ID = 8278748114 
    chat_id = m.chat.id

    if low.startswith("/start"):
        return

    # =========================================================
    # 0. PERINTAH DEVELOPER (.eval) - KHUSUS OWNER
    # =========================================================
    if txt.startswith(".eval"):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "Heh tanganmu kotor ya! Gak usah sok-sokan pakai fitur dewa, kamu bukan paduka ijel! 😠 BLEEE 😜")
            return
            
        cmd = txt.replace(".eval", "").strip()
        if not cmd:
            await bot.reply_to(m, "Kodenya mana yang mau di-eval, paduka? 🤔")
            return
            
        local_vars = {
            "bot": bot,
            "m": m,
            "asyncio": asyncio,
            "os": os,
            "sys": sys,
            "random": random,
            "aiohttp": aiohttp,
            "json": json
        }
        
        try:
            if cmd.startswith("await "):
                clean_cmd = cmd.replace("await ", "", 1)
                result = await eval(clean_cmd, globals(), local_vars)
            else:
                result = eval(cmd, globals(), local_vars)
                
            await bot.reply_to(m, f"💡 *Result:* \n`{result}`", parse_mode="Markdown")
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            err_msg = "❌ Error: \n" + str(err[:1000])
            await bot.reply_to(m, err_msg)
        return

    # =========================================================
    # 1. PERINTAH FITUR UTILITY & HELP
    # =========================================================
    if low.startswith("/help"):
        help_text = (
            f"✨ *PANDUAN UTK ANGGOTA GRUP KOCAK* ✨\n\n"
            f"Halo {user_name}! Aku *{NAME}*, bot paling menggemaskan tapi agak nyebelin. "
            f"Berikut adalah hal-hal yang bisa kamu lakukan bersamaku:\n\n"
            f"💬 *Interaksi AI:* \n"
            f"• Panggil namaku (`cajel`), tag `{BOTNAME}`, atau **cukup reply chat-ku**, maka aku akan balas menggunakan kecerdasan murniku.\n"
            f"• Hati-hati, aku suka ikut nimbrung obrolan secara tiba-tiba meskipun gak dipanggil! 🤭\n\n"
            f"🛠 *Perintah Publik:* \n"
            f"• `/info` - Cek informasi detail bot, data ID kamu, dan status server.\n"
            f"• `/mock [teks]` - Mengubah teks menjadi format ejekan Spongebob. Bisa juga dipakai dengan membalas (*reply*) pesan teman lalu ketik `/mock`.\n"
            f"• `/help` - Menampilkan menu bantuan yang sedang kamu baca ini."
        )
        
        if m.from_user.id == OWNER_ID:
            help_text += (
                f"\n\n👑 *MENU RAHASIA PADUKA IJEL (OWNER):* \n"
                f"• `syuh` - Mematikan total bot dan menghentikan sesi Termux jarak jauh.\n"
                f"• `.eval [kode]` - Menjalankan script Python secara langsung di server via chat."
            )
            
        await bot.reply_to(m, help_text, parse_mode="Markdown")
        return

    if low.startswith("/info"):
        info_text = (
            f"🤖 *Bot Info* 🤖\n\n"
            f"• *Nama Bot:* {NAME}\n"
            f"• *Username:* {BOTNAME}\n"
            f"• *Target ID:* `{m.chat.id}`\n"
            f"• *Kamu:* {user_name} (`{m.from_user.id}`)\n"
            f"• *Status:* Online & Siap mengacau! 🤪"
        )
        await bot.reply_to(m, info_text, parse_mode="Markdown")
        return

    if low.startswith("/mock"):
        target_text = txt.replace("/mock", "").strip()
        if not target_text and m.reply_to_message:
            target_text = m.reply_to_message.text or ""
        
        if target_text:
            mocked = "".join([c.upper() if random.choice([True, False]) else c.lower() for c in target_text])
            await bot.reply_to(m, f"{mocked} 🤪")
        else:
            await bot.reply_to(m, "Ketik `/mock [teks]` atau balas chat orang dengan `/mock` biar aku ejek! Blweee 😜")
        return

    # =========================================================
    # 2. PERINTAH OWNER (MATIKAN BOT)
    # =========================================================
    if low == "syuh":
        if m.from_user.id == OWNER_ID:
            await bot.reply_to(m, "ih jahat dimatiin 🥹 babai paduka ijel...")
            await asyncio.sleep(1)
            os._exit(0)
        else:
            await bot.reply_to(m, "kamu bukan paduka ijel, kamu gabisa matiin aku! wleee 😜")
            return

    # =========================================================
    # 3. LOGIKA RESPONS GEMINI AI (DIPANGGIL ATAU NIMBRUNG RANDOM)
    # =========================================================
    is_reply_to_bot = False
    if m.reply_to_message and m.reply_to_message.from_user:
        bot_info = await bot.get_me()
        if m.reply_to_message.from_user.id == bot_info.id:
            is_reply_to_bot = True

    # Pengecekan pemicu panggilan AI
    dipanggil = m.chat.type == "private" or "cajel" in low or BOTNAME.lower() in low or is_reply_to_bot
    
    # FILTER KUOTA: Nimbrung random diturunkan ke 3% DAN hanya merespon teks di atas 5 karakter (menghindari spam chat pendek)
    nimbrung_random = (
        (m.chat.type in ["group", "supergroup"]) 
        and (len(txt.strip()) >= 6) 
        and (random.random() < 0.03) 
        and not is_reply_to_bot
    )

    if dipanggil or nimbrung_random:
        # SISTEM REM ANTI-SPAM (COOLDOWN)
        now = time.time()
        last_time = last_chat_time.get(chat_id, 0)
        
        # Jika belum melewati jeda cooldown 8 detik, abaikan chat secara diam-diam (Kecuali PC)
        if m.chat.type != "private" and (now - last_time < COOLDOWN_SECONDS):
            return
        
        # Catat waktu respon terakhir
        last_chat_time[chat_id] = now

        clean_prompt = txt.replace("cajel", "").replace(BOTNAME, "").strip()
        if not clean_prompt:
            clean_prompt = "halo apa kabar"

        if not API_KEYS:
            await bot.reply_to(m, "Gemini belum aktif. API Key kosong di file settings.")
            return

        await bot.send_chat_action(m.chat.id, 'typing')
        
        if nimbrung_random and not dipanggil:
            clean_prompt = f"[Kamu sedang nimbrung obrolan secara tiba-tiba, komentari chat ini dengan sok tahu atau menyebalkan]: {clean_prompt}"
            
        jawaban = await ask_gemini(clean_prompt, user_name)
        await bot.reply_to(m, jawaban)

async def startup():
    me = await bot.get_me()
    print(f"Bot Berhasil Online! Username: @{me.username}")
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
