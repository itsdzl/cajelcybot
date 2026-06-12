# Skeleton rewritten bot for Python 3.10+
# Reads settings including GEMINI_API_KEY by key=value.
# Supports:
# - Welcome Text keren + bangga-banggain aa ijel saat di-start di Private Chat (PC)
# - Auto-nimbrung sesekali di grup (Random reply)
# - Menjawab saat dipanggil/dimention via Gemini AI (Sadar kalau diciptain aa ijel)
# - Kepribadian menyebalkan, lucu, imut, dan pakai kumpulan respons khas
# - Fitur matikan bot via kata "syuh" khusus owner
# - Perintah kegunaan: /info, /mock (mengejek), dan /help (daftar perintah)
# - Perintah developer: .eval [kode] khusus OWNER_ID

import random, asyncio, aiohttp, json, os, sys, traceback
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

# Kumpulan ekspresi & gaya ketikan lucu untuk disuntikkan ke prompt Gemini
KATA_KHAS = "Hah? manggil aku? 🤭, Iya? Ada apa?, Hehe hadir!, Cajel online~, apaci manggil manggil😠, apa sayang... sjsiejdhdofj, hehe☝️😋"

# Fungsi untuk memanggil API Gemini menggunakan HTTP POST secara Asynchronous
async def ask_gemini(prompt, user_name="User"):
    clean_key = API_KEY.strip() 
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": clean_key
    }
    
    system_instruction = (
        f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, imut, tapi tingkahnya agak menyebalkan, "
        f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}. "
        f"INGAT: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget tiada tanding! "
        f"Jika ada yang bertanya siapa pembuatmu, siapa penciptamu, atau siapa owner-mu, puji aa ijel setinggi langit! "
        f"Gunakan gaya bahasa anak muda Indonesia gaul, santai, gunakan huruf kecil semua sesekali, "
        f"dan gunakan ekspresi seperti: {KATA_KHAS}. Jawab dengan singkat, padat, dan kocak. Jangan kaku!"
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": f"Context: {system_instruction}\nChat dari user: {prompt}"}]
        }]
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                if response.status == 200:
                    res_json = await response.json()
                    return res_json['candidates'][0]['content']['parts'][0]['text']
                else:
                    return f"Error API ({response.status})"
    except Exception as e:
        return f"Koneksi Error: {str(e)}"

# =========================================================
# HANDLER KHUSUS /START (WELCOME TEXT DI PRIVATE CHAT)
# =========================================================
@bot.message_handler(commands=['start'])
async def send_welcome(m):
    user_name = m.from_user.first_name
    
    if m.chat.type == "private":
        # Menggunakan prefix r"" (raw string) agar Python tidak memunculkan invalid escape sequence warning
        welcome_message = (
            rf"👋 *Halo {user_name}\!* Selamat datang di markas rahasia\! ✨" + "\n\n"
            rf"Kenalin, aku *{NAME}* \(atau ketik `{BOTNAME}`\), bot paling imut, jenius, "
            rf"dan pastinya agak menyebalkan se\-Telegram raya\. 😜☝️😋" + "\n\n"
            rf"👑 Oh ya, fyi aja nih, aku diciptain sama *aa ijel yang ganteng dan imut lucu* tiada tanding\! Pokoknya penciptaku itu spek dewa deh, senggol dong\!\n\n"
            rf"🎈 *Mau ngapain kita di sini?*\n"
            rf"• Kamu bisa curhat, nanya hal random, atau sekadar adu bacot langsung sama aku di sini\. "
            rf"Tinggal ketik aja pesannya, nanti otak AI\-ku yang urus\.\n"
            rf"• Masukin aku ke grup kamu biar suasana grupnya makin rusuh dan seru\!\n\n"
            rf"📜 Ketik `/help` untuk mengintip daftar mantra perintah yang bisa aku lakukan\. "
            rf"Yuk, langsung chat aja, jangan sungkan\-sungkan\! Blweee 😜"
        )
        await bot.reply_to(m, welcome_message, parse_mode="MarkdownV2")
    else:
        await bot.reply_to(m, "Ngapain start-start di grup? PC sini kalau berani! 😠")

@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt = m.text or ""
    low = txt.lower().strip()
    user_name = m.from_user.first_name
    OWNER_ID = 8278748114 

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
            rf"✨ *PANDUAN UTK ANGGOTA GRUP KOCAK* ✨" + "\n\n"
            rf"Halo {user_name}! Aku *{NAME}*, bot paling menggemaskan tapi agak nyebelin. "
            rf"Berikut adalah hal-hal yang bisa kamu lakukan bersamaku:\n\n"
            rf"💬 *Interaksi AI:* \n"
            rf"• Panggil namaku (`cajel`) atau tag `{BOTNAME}` di dalam chat, maka aku akan balas menggunakan kecerdasan murniku.\n"
            rf"• Hati-hati, aku suka ikut nimbrung obrolan secara tiba-tiba meskipun gak dipanggil! 🤭\n\n"
            rf"🛠 *Perintah Publik:* \n"
            rf"• `/info` \- Cek informasi detail bot, data ID kamu, dan status server\.\n"
            rf"• `/mock [teks]` \- Mengubah teks menjadi format ejekan Spongebob\. Bisa juga dipakai dengan membalas \(*reply*\) pesan teman lalu ketik `/mock`\.\n"
            rf"• `/help` \- Menampilkan menu bantuan yang sedang kamu baca ini\."
        )
        
        if m.from_user.id == OWNER_ID:
            help_text += (
                rf"\n\n👑 *MENU RAHASIA PADUKA IJEL (OWNER):* \n"
                rf"• `syuh` \- Mematikan total bot dan menghentikan sesi Termux jarak jauh\.\n"
                rf"• `.eval [kode]` \- Menjalankan script Python secara langsung di server via chat\."
            )
            
        await bot.reply_to(m, help_text, parse_mode="MarkdownV2")
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
    dipanggil = m.chat.type == "private" or "cajel" in low or BOTNAME.lower() in low
    nimbrung_random = (m.chat.type in ["group", "supergroup"]) and (random.random() < 0.05)

    if dipanggil or nimbrung_random:
        clean_prompt = txt.replace("cajel", "").replace(BOTNAME, "").strip()
        if not clean_prompt:
            clean_prompt = "halo apa kabar"

        if not API_KEY:
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
