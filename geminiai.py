# Skeleton rewritten bot for Python 3.10+
# Credit by @itsdzl
# Supports:
# - Welcome Text keren + bangga-banggain aa ijel saat di-start di Private Chat (PC)
# - Auto-nimbrung sesekali di grup (Random reply)
# - Menjawab saat dipanggil/dimention via Gemini AI (Sadar kalau diciptain aa ijel)
# - SISTEM REPLY: Cukup balas pesan bot di grup, bot akan otomatis menjawab!
# - ROTASI MULTI-API KEY: Otomatis ganti ke API Key cadangan jika API Key utama limit/error!
# - Jauh Lebih Tangguh: Auto-Retry (Exponential Backoff) sebelum berganti key.
# - Kepribadian menyebalkan, lucu, imut, super random, dan menggemaskan
# - Fitur matikan bot via kata "syuh" khusus owner
# - Perintah kegunaan: /info, /mock (mengejek), dan /help (daftar perintah)
# - Perintah developer: .eval [kode] khusus OWNER_ID
# - FITUR PREMIUM: Whisper Secret Message via Command /whisper & Inline Mode (@botname)

import random, asyncio, aiohttp, json, os, sys, traceback, subprocess, shutil, hashlib
import telebot
from telebot.async_telebot import AsyncTeleBot

cfg={}
with open("set", "r", encoding="utf8") as f:
    for line in f:
        if "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

TOKEN = cfg["token"]
BOTNAME = cfg["botname"]
NAME = cfg.get("name", "cajel")
OWNER_ID = 8278748114 

# Kamus database sementara di memori untuk menyimpan pesan rahasia whisper
whisper_data = {}

# ---------------------------------------------------------
# SISTEM DETEKSI MULTI-API KEY (ROTASI)
# ---------------------------------------------------------
API_KEYS = []

if "GEMINI_API_KEY" in cfg:
    for key in cfg["GEMINI_API_KEY"].split(","):
        clean_key = key.strip()
        if clean_key:
            API_KEYS.append(clean_key)

for i in range(2, 6):
    key_name = f"GEMINI_API_KEY_{i}"
    if key_name in cfg:
        clean_key = cfg[key_name].strip()
        if clean_key and clean_key not in API_KEYS:
            API_KEYS.append(clean_key)

bot = AsyncTeleBot(TOKEN)

# ---------------------------------------------------------
# BAGIAN DETEKSI YTDLP HYBRID
# ---------------------------------------------------------
try:
    import yt_dlp
    YTDLP_IMPORT_AVAILABLE = True
except ImportError:
    YTDLP_IMPORT_AVAILABLE = False

YTDLP_CLI_AVAILABLE = shutil.which("yt-dlp") is not None
YTDLP_AVAILABLE = YTDLP_IMPORT_AVAILABLE or YTDLP_CLI_AVAILABLE

async def ask_gemini(prompt, user_name="User"):
    if not API_KEYS:
        return "agi ucak"

    system_instruction = (
        f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, imut, tapi tingkahnya agak menyebalkan, "
        f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}. "
        f"INGAT: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget tiada tanding! "
        f"Jika ada yang bertanya siapa pembuatmu, siapa penciptamu, atau siapa owner-mu, puji aa ijel setinggi langit dengan heboh! "
        f"Gunakan gaya bahasa anak muda Indonesia gaul, santai, gunakan huruf kecil semua sesekali, "
        f"dan gunakan ekspresi emoji lucu secara beragam dan bebas (seperti: 🤭, 😠, 😜, ☝️😋, 🥺, 🥰, 😜, 🙄) biar terasa hidup dan tidak monoton. "
        f"Jawab dengan singkat, padat, sangat dinamis, kocak, kreatif, dan tidak kaku!"
    )

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
                        
                        error_body = await response.text()
                        
                        if response.status in [503, 429, 500]:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(delay)
                                delay *= 2
                                continue
                            else:
                                print(f"[ROTASI] API Key {idx+1} Gagal (status {response.status}). Respon: {error_body}")
                                key_failed = True
                                break
                                
                        elif response.status in [401, 403, 400]:
                            print(f"[ROTASI] API Key {idx+1} Error {response.status} (Tidak Valid/Salah Format). Respon: {error_body}")
                            key_failed = True
                            break
                        else:
                            print(f"[ROTASI] Error API {response.status} pada Key {idx+1}. Respon: {error_body}")
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

    return "g mood, nanti aja y.."

# ---------------------------------------------------------
# FUNGSI UNDUH MUSIK HYBRID
# ---------------------------------------------------------
def download_youtube_audio(query):
    if not YTDLP_AVAILABLE:
        return None, "ytdlp belum diinstall"
    
    os.makedirs("downloads", exist_ok=True)
    
    # Metode 1: Mencoba menggunakan Python Import
    if YTDLP_IMPORT_AVAILABLE:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'max_entries': 1,
            'noplaylist': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                if 'entries' in info and len(info['entries']) > 0:
                    video_info = info['entries'][0]
                else:
                    video_info = info
                    
                filename = ydl.prepare_filename(video_info)
                
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    for f in os.listdir("downloads"):
                        if os.path.join("downloads", f).startswith(base):
                            filename = os.path.join("downloads", f)
                            break

                title = video_info.get('title', 'Unknown Title')
                uploader = video_info.get('uploader', 'Unknown Artist')
                duration = video_info.get('duration', 0)
                
                return {
                    "path": filename,
                    "title": title,
                    "performer": uploader,
                    "duration": duration
                }, None
        except Exception:
            pass

    # Metode 2: Mencoba menggunakan Subprocess CLI
    if YTDLP_CLI_AVAILABLE:
        try:
            cmd_meta = [
                "yt-dlp",
                "--skip-download",
                "--dump-json",
                "--no-playlist",
                "ytsearch1:" + query
            ]
            proc_meta = subprocess.run(cmd_meta, capture_output=True, text=True)
            
            title = "Lagu Download"
            uploader = "YouTube"
            duration = 0
            ext = "mp3"
            
            if proc_meta.returncode == 0 and proc_meta.stdout.strip():
                try:
                    meta = json.loads(proc_meta.stdout.split('\n')[0])
                    title = meta.get('title', title)
                    uploader = meta.get('uploader', uploader)
                    duration = int(meta.get('duration', 0))
                    ext = meta.get('ext', ext)
                except Exception:
                    pass
                
            safe_title = "".join([c for c in title if c.isalnum() or c in " '()-_. "]).strip()
            if not safe_title:
                safe_title = "song"
            filename = f"downloads/{safe_title}.{ext}"
            
            cmd_dl = [
                "yt-dlp",
                "-f", "bestaudio/best",
                "--no-playlist",
                "-o", filename,
                "ytsearch1:" + query
            ]
            proc_dl = subprocess.run(cmd_dl, capture_output=True, text=True)
            
            if os.path.exists(filename):
                return {
                    "path": filename,
                    "title": title,
                    "performer": uploader,
                    "duration": duration
                }, None
                
            for file in os.listdir("downloads"):
                if file.startswith(safe_title) or (safe_title in file):
                    return {
                        "path": os.path.join("downloads", file),
                        "title": title,
                        "performer": uploader,
                        "duration": duration
                    }, None
                    
            return None, f"File tidak ditemukan. Detail log: {proc_dl.stderr[:150]}"
        except Exception as e:
            return None, f"Gagal mengunduh lewat sistem: {str(e)}"

    return None, "ytdlp belum diinstall"

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

# =========================================================
# HANDLER PERINTAH /WHISPER (COMMAND GRUP VERSI MANUAL)
# =========================================================
@bot.message_handler(commands=['whisper'])
async def send_whisper_cmd(m):
    if m.chat.type == "private":
        await bot.reply_to(m, "Fitur ini cuma bisa dipake di grup, beb! Biar yang lain pada kepo 😜")
        return

    args = m.text.split(maxsplit=2)
    if len(args) < 3 or not args[1].startswith('@'):
        await bot.reply_to(m, "Cara pakenya salah! 😠\nContoh: `/whisper @username Aku suka kamu`", parse_mode="Markdown")
        return

    target_username = args[1].replace('@', '').lower()
    secret_message = args[2]
    sender_name = m.from_user.first_name

    try:
        await bot.delete_message(m.chat.id, m.message_id)
    except Exception:
        pass

    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton(
        text=f"✉️ liat pesan rahasia dari {sender_name}", 
        callback_data="open_whisper"
    )
    markup.add(btn)

    sent_msg = await bot.send_message(
        m.chat.id, 
        f"🤫 kiw, ada pesan rahasia nih buat *@ {target_username}*.\nsiapa nih yang kepo? 🤭", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

    whisper_data[sent_msg.message_id] = {
        "target": target_username,
        "message": secret_message
    }

# =========================================================
# HANDLER PERINTAH /GETMUSIC
# =========================================================
@bot.message_handler(commands=['getmusic'])
async def get_music(m):
    query = m.text.replace("/getmusic", "").strip()
    if not query:
        await bot.reply_to(m, "Masukin judul lagu atau penyanyinya juga dong Contoh: `/getmusic dumes` 😠", parse_mode="Markdown")
        return
        
    await bot.send_chat_action(m.chat.id, 'upload_voice')
    status_msg = await bot.reply_to(m, "sabar ya beb, cajel lagi cariin lagunya... 🎧")
    
    loop = asyncio.get_event_loop()
    music_data, err = await loop.run_in_executor(None, download_youtube_audio, query)
    
    if err:
        await bot.edit_message_text(f"❌ yah gagal download lagunya 😞, error: {err}", m.chat.id, status_msg.message_id)
        return
        
    try:
        await bot.edit_message_text("ketemuuu! tunggu bentar ya... dududu", m.chat.id, status_msg.message_id)
        
        file_path = music_data["path"]
        title = music_data["title"]
        performer = music_data["performer"]
        duration = music_data["duration"]
        
        with open(file_path, "rb") as audio_file:
            await bot.send_audio(
                chat_id=m.chat.id,
                audio=audio_file,
                title=title,
                performer=performer,
                duration=duration,
                reply_to_message_id=m.message_id
            )
            
        if os.path.exists(file_path):
            os.remove(file_path)
            
        await bot.delete_message(m.chat.id, status_msg.message_id)
        
    except Exception as e:
        await bot.edit_message_text(f"❌ yahh cajel gagal ngirim audionya, error: {str(e)}", m.chat.id, status_msg.message_id)

# =========================================================
# HANDLER INLINE QUERY (FITUR BISIKAN @cajelcybot)
# =========================================================
@bot.inline_handler(func=lambda query: len(query.query) > 0)
async def query_text(inline_query):
    try:
        raw_text = inline_query.query
        parts = raw_text.split()
        target_username = ""
        
        if parts[-1].startswith('@') and len(parts) > 1:
            target_username = parts[-1].replace('@', '').lower()
            secret_message = " ".join(parts[:-1])
        elif parts[0].startswith('@') and len(parts) > 1:
            target_username = parts[0].replace('@', '').lower()
            secret_message = " ".join(parts[1:])
        else:
            hint = telebot.types.InlineQueryResultArticle(
                id='hint',
                title='Format Bisikan Salah! 😠',
                description='Ketik: [isi pesan] @username target',
                input_message_content=telebot.types.InputTextMessageContent(
                    message_text='Cara pakai whisper: `@cajelcybot isi pesan @username` 😜',
                    parse_mode='Markdown'
                )
            )
            await bot.answer_inline_query(inline_query.id, [hint], cache_time=1)
            return

        unique_id = hashlib.md5(f"{inline_query.id}_{secret_message}".encode()).hexdigest()[:10]
        
        whisper_data[unique_id] = {
            "target": target_username,
            "message": secret_message
        }

        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton(
            text="✉️ Buka Pesan Rahasia", 
            callback_data=f"wh_{unique_id}"
        )
        markup.add(btn)

        result = telebot.types.InlineQueryResultArticle(
            id=unique_id,
            title=f"Kirim bisikan ke @{target_username}",
            description=f"Isi pesan: {secret_message[:30]}...",
            reply_markup=markup,
            input_message_content=telebot.types.InputTextMessageContent(
                message_text=f"🤫 *Sssttt...* Ada pesan rahasia nih khusus buat *@ {target_username}*.\nOrang lain dilarang ngintip ya! 😠",
                parse_mode="Markdown"
            )
        )
        
        await bot.answer_inline_query(inline_query.id, [result], cache_time=1)
        
    except Exception as e:
        print(f"Error Inline Whisper: {e}")

# =========================================================
# HANDLER UNTUK TOMBOL WHISPER (CALLBACK QUERY)
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == "open_whisper" or call.data.startswith("wh_"))
async def handle_whisper_click(call):
    user_username = (call.from_user.username or "").lower()
    
    if call.data.startswith("wh_"):
        unique_id = call.data.replace("wh_", "")
        if unique_id not in whisper_data:
            await bot.answer_callback_query(call.id, text="Yah, pesan rahasia ini udah kedaluwarsa atau bot habis di-restart! 🥺", show_alert=True)
            return
        
        target_user = whisper_data[unique_id]["target"]
        secret_text = whisper_data[unique_id]["message"]
        
    else:
        msg_id = call.message.message_id
        if msg_id not in whisper_data:
            await bot.answer_callback_query(call.id, text="Yah, pesan rahasia ini udah kedaluwarsa atau bot habis di-restart! 🥺", show_alert=True)
            return
            
        target_user = whisper_data[msg_id]["target"]
        secret_text = whisper_data[msg_id]["message"]

    if user_username == target_user:
        await bot.answer_callback_query(call.id, text=f"💬 Pesan Rahasia:\n\" {secret_text} \"", show_alert=True)
    else:
        kutipan_ejekan = [
            "Heh kepo banget! Bukan buat kamu ya! 😠 BLEEE 😜",
            "Idih, dibilang rahasia masih aja diklik. Hus sana! 🙄",
            "Jangan ngintip! Nanti matanya bintitan loh! 🤭",
            "Hayo mau nyolong informasi ya? Gak bisa! 😜☝️"
        ]
        await bot.answer_callback_query(call.id, text=random.choice(kutipan_ejekan), show_alert=True)

# =========================================================
# MAIN MESSAGE HANDLER TEXT (ALL MESSAGES)
# =========================================================
@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt = m.text or ""
    low = txt.lower().strip()
    user_name = m.from_user.first_name

    if low.startswith("/start") or low.startswith("/getmusic") or low.startswith("/whisper"):
        return

    # =========================================================
    # 0. PERINTAH DEVELOPER (.eval) - KHUSUS IJEL
    # =========================================================
    if txt.startswith(".eval"):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "heh tanganmu kotor ya! gausa sosoan pakai fitur ini, kamu bukan aa ijel! 😠 BLEEE 😜")
            return
            
        cmd = txt.replace(".eval", "").strip()
        if not cmd:
            await bot.reply_to(m, "kodenya mana yang mau di eval, paduka? 🙂‍↕️")
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
            f"✨ *PANDUAN UTK ANGGOTA GRUP* ✨\n\n"
            f"Halo {user_name}! Aku *{NAME}*, bot paling menggemaskan tapi agak nyebelin. "
            f"Berikut adalah hal-hal yang bisa kamu lakukan bersamaku:\n\n"
            f"💬 *Interaksi AI:* \n"
            f"• Panggil namaku (`cajel`) atau **cukup reply chat-ku**, maka aku akan balas menggunakan kecerdasan murniku.\n"
            f"• Hati-hati, aku suka ikut nimbrung obrolan secara tiba-tiba meskipun gak dipanggil! 🤭\n\n"
            f"🛠 *Perintah Publik:* \n"
            f"• /getmusic [judul] - Cari dan unduh musik MP3 langsung dari YouTube!\n"
            f"• /whisper @username [pesan] - Kirim pesan bisikan rahasia (bisa juga via inline mode ketik `@{BOTNAME} [pesan] @username`).\n"
            f"• /info - Cek informasi detail bot, data ID kamu, dan status server.\n"
            f"• /mock [teks] - Mengubah teks menjadi format ejekan Spongebob. Bisa juga dipakai dengan membalas (*reply*) pesan teman lalu ketik `/mock`.\n"
            f"• /help - Menampilkan menu bantuan yang sedang kamu baca ini."
        )
        
        if m.from_user.id == OWNER_ID:
            help_text += (
                f"\n\n👑 *MENU RAHASIA PADUKA IJEL:* \n"
                f"• `syuh` - Mematikan total bot dan menghentikan sesi jarak jauh.\n"
                f"• `eval [kode]` - Menjalankan script Python secara langsung di server via chat."
            )
            
        await bot.reply_to(m, help_text, parse_mode="Markdown")
        return

    if low.startswith("/info"):
        info_text = (
            f"🤖 *Bot Info* 🤖\n\n"
            f"• *Nama Bot:* {NAME}\n"
            f"• *Username:* {BOTNAME}\n"
            f"• *Chat ID:* `{m.chat.id}`\n"
            f"• *Kamu:* {user_name} (`{m.from_user.id}`)\n"
            f"• *Status Bot:* online & siap mengacau! 🤪"
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
            await bot.reply_to(m, "ih jahat dimatiin 🥹...")
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

    dipanggil = m.chat.type == "private" or "cajel" in low or BOTNAME.lower() in low or is_reply_to_bot
    nimbrung_random = (m.chat.type in ["group", "supergroup"]) and (random.random() < 0.03) and not is_reply_to_bot

    if dipanggil or nimbrung_random:
        clean_prompt = txt.replace("cajel", "").replace(BOTNAME, "").strip()
        if not clean_prompt:
            clean_prompt = "halo apa kabar"

        if not API_KEYS:
            await bot.reply_to(m, "agi ucak.")
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
        
