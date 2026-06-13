# Skeleton rewritten bot for Python 3.10+
# Credit by @itsdzl
# Supports:
# - Welcome Text keren + bangga-banggain aa ijel saat di-start di Private Chat (PC)
# - Welcome Text otomatis saat bot dimasukkan ke dalam sebuah grup baru!
# - Menjawab saat dipanggil/dimention via Gemini AI (Sadar kalau diciptain aa ijel)
# - SISTEM REPLY & MEMORI PERCAKAPAN: Bot mengingat konteks chat sebelumnya agar nyambung!
# - NOTIFIKASI BATAS MEMORI: Memberi tahu dengan hangat jika sesi obrolan akan segera di-reset.
# - FITUR KEPRIBADIAN ADAPTIF: Bisa serius saat curhat, kembali imut/lucu saat santai.
# - SISTEM LIVE LOGS: Mengirimkan info startup, error API, user baru (PC), dan grup baru ke grup log utama.
# - ROTASI MULTI-API KEY: Otomatis ganti ke API Key cadangan jika API Key utama limit/error!
# - Fitur matikan bot via kata "syuh" khusus owner
# - Perintah kegunaan: /info, /mock (mengejek), dan /help (daftar perintah yang rapi)
# - Perintah developer: .eval [kode] & .exe [terminal command] khusus OWNER_ID
# - FITUR Whisper Secret Message EKSKLUSIF via Inline Mode (@botname)

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

# ID Grup Utama tempat penampungan Log Status Bot, Log User/Grup Baru, dan Error API Key
LOG_GROUP_ID = int(cfg.get("log_group_id", 0))

# Kamus database sementara di memori untuk menyimpan pesan rahasia whisper
whisper_data = {}

# Kamus memori percakapan sementara untuk menjaga konteks chat tetap nyambung
chat_memories = {}
MAX_MEMORY_LENGTH = 12  # Sesi obrolan maksimal sebelum sistem melakukan pembersihan

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

async def send_bot_log(text):
    """Fungsi pembantu untuk mengirimkan log real-time ke grup utama"""
    if LOG_GROUP_ID != 0:
        try:
            await bot.send_message(LOG_GROUP_ID, text, parse_mode="Markdown")
        except Exception as e:
            print(f"[LOG ERROR] Gagal mengirim log ke grup utama: {e}")

async def ask_gemini(chat_id, prompt, user_name="User"):
    if not API_KEYS:
        return "agi ucak"

    if chat_id not in chat_memories:
        chat_memories[chat_id] = []

    # Deteksi jika memori sudah menyentuh batas kritis (sisa 1 slot pesan sebelum reset)
    is_memory_limit_near = (len(chat_memories[chat_id]) >= MAX_MEMORY_LENGTH - 2)

    system_instruction = (
        f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, imut, tapi tingkahnya agak menyebalkan, "
        f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}.\n\n"
        f"ATURAN ADAPTIF KEPRIBADIAN (SANGAT PENTING):\n"
        f"1. Analisis emosi pesan {user_name}. Jika dia sedang ingin mengobrol serius, "
        f"curhat masalah pribadi, sedih, galau, kecewa, atau meminta saran penting, ubah mode kepribadianmu menjadi peka, "
        f"dewasa, hangat, dan berikan jawaban yang serius, solutif, serta menenangkan tanpa diselingi ejekan/candaan garing.\n"
        f"2. Jangan selalu mengirim jawaban yang sangat panjang bertele-tele jika tidak diperlukan. Jawab secukupnya.\n"
        f"3. Jangan membanjiri teks dengan terlalu banyak emoji jika suasananya sedang formal atau sedih.\n"
        f"4. Jika topik curhat selesai atau obrolan kembali santai/gembira, kembalilah secara natural ke sifat aslimu yang "
        f"lucu, tengil, santai, ekspresif, suka pakai emoji khas (🤭, 😠, 😜, ☝️😋, 🥺, 🥰).\n\n"
    )

    if is_memory_limit_near:
        system_instruction += (
            f"[PERINTAH SISTEM TAMBAHAN]: Ini adalah pesan terakhir dalam sesi obrolan kali ini karena memori internal bot sudah penuh. "
            f"Di bagian akhir jawabanmu, wajib beritahu {user_name} secara halus dan sopan bahwa percakapan sesi ini harus berakhir demi "
            f"kesehatan ingatan bot. Berikan kata penutup yang penuh semangat, lalu yakinkan dia bahwa kamu ({NAME}) tetap "
            f"akan selalu ada di sini, setia menunggu, dan siap untuk mendengarkan semua keluh kesah atau curhatannya lagi nanti kapan saja! "
            f"Gunakan pembawaan yang hangat dan menyentuh hati."
        )
    else:
        system_instruction += (
            f"PENCIPTA: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget tiada tanding! "
            f"Jika ada yang bertanya tentang pembuat/pencipta/owner-mu, puji aa ijel setinggi langit dengan heboh!"
        )

    chat_memories[chat_id].append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    if len(chat_memories[chat_id]) > MAX_MEMORY_LENGTH:
        chat_memories[chat_id] = chat_memories[chat_id][-MAX_MEMORY_LENGTH:]

    for idx, current_key in enumerate(API_KEYS):
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": current_key}
        payload = {"contents": chat_memories[chat_id], "system_instruction": {"parts": [{"text": system_instruction}]}}
        
        max_retries = 2
        delay = 1
        key_failed = False
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                        if response.status == 200:
                            res_json = await response.json()
                            bot_reply = res_json['candidates'][0]['content']['parts'][0]['text']
                            
                            chat_memories[chat_id].append({"role": "model", "parts": [{"text": bot_reply}]})
                            
                            if is_memory_limit_near:
                                chat_memories[chat_id] = []
                                
                            return bot_reply
                        
                        error_body = await response.text()
                        if response.status in [503, 429, 500]:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(delay)
                                delay *= 2
                                continue
                            else:
                                log_msg = f"⚠️ *[ROTASI]* API Key {idx+1} Gagal (status {response.status}). Mengalihkan kunci...\nDetail: `{error_body[:200]}`"
                                print(log_msg)
                                await send_bot_log(log_msg)
                                key_failed = True
                                break
                        elif response.status in [401, 403, 400]:
                            log_msg = f"❌ *[ROTASI]* API Key {idx+1} Error {response.status} (Format Salah/Invalido). Mengalihkan...\nDetail: `{error_body[:200]}`"
                            print(log_msg)
                            await send_bot_log(log_msg)
                            key_failed = True
                            break
                        else:
                            log_msg = f"💥 *[ROTASI]* Masalah sistem {response.status} pada Key {idx+1}.\nDetail: `{error_body[:200]}`"
                            print(log_msg)
                            await send_bot_log(log_msg)
                            key_failed = True
                            break
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                else:
                    log_msg = f"🔌 *[ROTASI]* Koneksi Error/Timeout pada Key {idx+1}: `{str(e)}`"
                    print(log_msg)
                    await send_bot_log(log_msg)
                    key_failed = True
                    break
        
        if key_failed:
            continue

    if chat_memories[chat_id]:
        chat_memories[chat_id].pop()
    return "g mood, nanti aja y.."

# ---------------------------------------------------------
# FUNGSI UNDUH MUSIK HYBRID
# ---------------------------------------------------------
def download_youtube_audio(query):
    if not YTDLP_AVAILABLE: return None, "ytdlp belum diinstall"
    os.makedirs("downloads", exist_ok=True)
    if YTDLP_IMPORT_AVAILABLE:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'downloads/%(title)s.%(ext)s', 'quiet': True, 'no_warnings': True, 'default_search': 'ytsearch', 'max_entries': 1, 'noplaylist': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                video_info = info['entries'][0] if 'entries' in info and len(info['entries']) > 0 else info
                filename = ydl.prepare_filename(video_info)
                if not os.path.exists(filename):
                    base = os.path.splitext(filename)[0]
                    for f in os.listdir("downloads"):
                        if os.path.join("downloads", f).startswith(base):
                            filename = os.path.join("downloads", f)
                            break
                return {"path": filename, "title": video_info.get('title', 'Unknown Title'), "performer": video_info.get('uploader', 'Unknown Artist'), "duration": video_info.get('duration', 0)}, None
        except Exception: pass
    if YTDLP_CLI_AVAILABLE:
        try:
            cmd_meta = ["yt-dlp", "--skip-download", "--dump-json", "--no-playlist", "ytsearch1:" + query]
            proc_meta = subprocess.run(cmd_meta, capture_output=True, text=True)
            title, uploader, duration, ext = "Lagu Download", "YouTube", 0, "mp3"
            if proc_meta.returncode == 0 and proc_meta.stdout.strip():
                try:
                    meta = json.loads(proc_meta.stdout.split('\n')[0])
                    title, uploader, duration, ext = meta.get('title', title), meta.get('uploader', uploader), int(meta.get('duration', 0)), meta.get('ext', ext)
                except Exception: pass
            safe_title = "".join([c for c in title if c.isalnum() or c in " '()-_. "]).strip()
            if not safe_title: safe_title = "song"
            filename = f"downloads/{safe_title}.{ext}"
            cmd_dl = ["yt-dlp", "-f", "bestaudio/best", "--no-playlist", "-o", filename, "ytsearch1:" + query]
            proc_dl = subprocess.run(cmd_dl, capture_output=True, text=True)
            if os.path.exists(filename): return {"path": filename, "title": title, "performer": uploader, "duration": duration}, None
            for file in os.listdir("downloads"):
                if file.startswith(safe_title) or (safe_title in file): return {"path": os.path.join("downloads", file), "title": title, "performer": uploader, "duration": duration}, None
            return None, f"File tidak ditemukan. Detail log: {proc_dl.stderr[:150]}"
        except Exception as e: return None, f"Gagal mengunduh lewat sistem: {str(e)}"
    return None, "ytdlp belum diinstall"

# =========================================================
# HANDLER KHUSUS /START (WELCOME TEXT DI PRIVATE CHAT)
# =========================================================
@bot.message_handler(commands=['start'])
async def send_welcome(m):
    user_name = m.from_user.first_name
    user_id = m.from_user.id
    username_handle = f"@{m.from_user.username}" if m.from_user.username else "Tidak ada username"
    
    if m.chat.type == "private":
        log_text = (
            f"👤 *[USER BARU]* Seseorang telah memulai bot di Private Chat!\n"
            f"• *Nama:* {user_name}\n"
            f"• *User ID:* `{user_id}`\n"
            f"• *Username:* {username_handle}"
        )
        await send_bot_log(log_text)

        welcome_message = (
            f"👋 *Halo {user_name}!* Selamat datang di markas rahasia! ✨\n\n"
            f"Kenalin, aku *{NAME}*, bot paling imut, jenius,"
            f"dan pastinya agak menyebalkan se-Telegram raya. 😜☝️😋\n\n"
            f"👑 Oh ya, fyi aja nih, aku diciptain sama *aa ijel yang ganteng dan imut lucu* tiada tanding.. senggol dong 😝\n\n"
            f"• Kamu bisa curhat panjang lebar di sini (aku bakal dengerin & ingat obrolan kita biar selalu nyambung!).\n"
            f"• Masukin aku ke grup kamu biar suasana grupnya makin rusuh dan seru wkwk\n\n"
            f"📜 Ketik `/help` untuk mengintip daftar perintah yang bisa aku lakukan.\n"
            f"Yuk, langsung chat aja, jangan sungkan-sungkan... Blweee 😜"
        )
        await bot.reply_to(m, welcome_message, parse_mode="Markdown")
    else:
        await bot.reply_to(m, "Ngapain start-start di grup? PC sini kalau berani 😠")

# =========================================================
# HANDLER OTOMATIS: WELCOME TEXT + LOG SAAT BOT MASUK GRUP
# =========================================================
@bot.my_chat_member_handler()
async def handle_bot_added(update):
    if update.new_chat_member.status == "member" and update.old_chat_member.status in ["left", "kicked", "restricted"]:
        chat_id = update.chat.id
        chat_title = update.chat.title
        inviter_name = update.from_user.first_name
        
        group_log = (
            f"📥 *[BOT MASUK GRUP BARU]*\n"
            f"• *Nama Grup:* {chat_title}\n"
            f"• *Chat ID:* `{chat_id}`\n"
            f"• *Yang Memasukkan:* {inviter_name} (`{update.from_user.id}`)"
        )
        await send_bot_log(group_log)
        
        welcome_group_text = (
            f"🎉 *HALO SEMUANYA! KRETEK KRETEK... CAJEL DATANG!!* 🤪🤙\n\n"
            f"Kenalin semuanya, aku *{NAME}*, bot paling menggemaskan, imut, tapi kelakuannya "
            f"agak di luar nalar se-Telegram raya! Aku diundang ke sini oleh kak {inviter_name} nih. 😎\n\n"
            f"👑 Sekadar info penting buat warga grup, aku ini ciptaan mutlak dari *aa ijel yang ganteng dan imut sedunia*, "
            f"jadi mohon dijaga ya kesopanan kalian sama robot kesayangan aa ijel ini! 😝\n\n"
            f"💬 *Cara Ngobrol bareng aku:* \n"
            f"Cukup ketik namaku `cajel` di dalam obrolan kalian atau langsung **reply/balas chat dari aku**, "
            f"maka aku bakal otomatis ikutan ngobrol pake otak AI-ku yang super pinter ini! "
            f"Kalian juga bisa curhat panjang lebar loh, aku pinter dengerin keluhan hidup orang wkwk.\n\n"
            f"📜 Ketik `/help` untuk melihat daftar perintah seru lainnya. Yuk lanjut ghibah! Blee 😜"
        )
        await bot.send_message(chat_id, welcome_group_text, parse_mode="Markdown")

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
        file_path, title, performer, duration = music_data["path"], music_data["title"], music_data["performer"], music_data["duration"]
        with open(file_path, "rb") as audio_file:
            await bot.send_audio(chat_id=m.chat.id, audio=audio_file, title=title, performer=performer, duration=duration, reply_to_message_id=m.message_id)
        if os.path.exists(file_path): os.remove(file_path)
        await bot.delete_message(m.chat.id, status_msg.message_id)
    except Exception as e: await bot.edit_message_text(f"❌ yahh cajel gagal ngirim audionya, error: {str(e)}", m.chat.id, status_msg.message_id)

# =========================================================
# HANDLER INLINE QUERY (FITUR BISIKAN EKSKLUSIF @cajelcybot)
# =========================================================
@bot.inline_handler(func=lambda query: len(query.query) > 0)
async def query_text(inline_query):
    try:
        raw_text = inline_query.query
        parts = raw_text.split()
        target_username = ""
        if parts[-1].startswith('@') and len(parts) > 1: target_username, secret_message = parts[-1].replace('@', '').lower(), " ".join(parts[:-1])
        elif parts[0].startswith('@') and len(parts) > 1: target_username, secret_message = parts[0].replace('@', '').lower(), " ".join(parts[1:])
        else:
            hint = telebot.types.InlineQueryResultArticle(id='hint', title='Format Bisikan Salah! 😠', description='Ketik: [isi pesan] @username target', input_message_content=telebot.types.InputTextMessageContent(message_text='Cara pakai whisper: `@cajelcybot isi pesan @username` 😜', parse_mode='Markdown'))
            await bot.answer_inline_query(inline_query.id, [hint], cache_time=1)
            return
        unique_id = hashlib.md5(f"{inline_query.id}_{secret_message}".encode()).hexdigest()[:10]
        whisper_data[unique_id] = {"target": target_username, "message": secret_message}
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton(text="✉️ Buka Pesan Rahasia", callback_data=f"wh_{unique_id}")
        markup.add(btn)
        result = telebot.types.InlineQueryResultArticle(id=unique_id, title=f"Kirim bisikan ke @{target_username}", description=f"Isi pesan: {secret_message[:30]}...", reply_markup=markup, input_message_content=telebot.types.InputTextMessageContent(message_text=f"🤫 *Sssttt...* Ada pesan rahasia nih khusus buat *@ {target_username}*.\nOrang lain dilarang ngintip ya! 😠", parse_mode="Markdown"))
        await bot.answer_inline_query(inline_query.id, [result], cache_time=1)
    except Exception as e: print(f"Error Inline Whisper: {e}")

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
        target_user, secret_text = whisper_data[unique_id]["target"], whisper_data[unique_id]["message"]
    else:
        msg_id = call.message.message_id
        if msg_id not in whisper_data:
            await bot.answer_callback_query(call.id, text="Yah, pesan rahasia ini udah kedaluwarsa atau bot habis di-restart! 🥺", show_alert=True)
            return
        target_user, secret_text = whisper_data[msg_id]["target"], whisper_data[msg_id]["message"]
    if user_username == target_user: await bot.answer_callback_query(call.id, text=f"💬 Pesan Rahasia:\n\" {secret_text} \"", show_alert=True)
    else:
        kutipan_ejekan = ["Heh kepo banget! Bukan buat kamu ya! 😠 BLEEE 😜", "Idih, dibilang rahasia masih aja diklik. Hus sana! 🙄", "Jangan ngintip! Nanti matanya bintitan loh! 🤭", "Hayo mau nyolong informasi ya? Gak bisa! 😜☝️"]
        await bot.answer_callback_query(call.id, text=random.choice(kutipan_ejekan), show_alert=True)

# =========================================================
# MAIN MESSAGE HANDLER TEXT (ALL MESSAGES)
# =========================================================
@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt = m.text or ""
    low = txt.lower().strip()
    user_name = m.from_user.first_name

    if low.startswith("/start") or low.startswith("/getmusic"): return

    # =========================================================
    # 0. PERINTAH DEVELOPER (.eval & .exe) - KHUSUS IJEL
    # =========================================================
    if txt.startswith(".eval"):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "heh tanganmu kotor ya! gausa sosoan pakai fitur ini, kamu bukan aa ijel! 😠 BLEEE 😜")
            return
        cmd = txt.replace(".eval", "").strip()
        if not cmd:
            await bot.reply_to(m, "kodenya mana yang mau di eval, paduka? 🙂‍↕️")
            return
        local_vars = {"bot": bot, "m": m, "asyncio": asyncio, "os": os, "sys": sys, "random": random, "aiohttp": aiohttp, "json": json}
        try:
            if cmd.startswith("await "):
                clean_cmd = cmd.replace("await ", "", 1)
                result = await eval(clean_cmd, globals(), local_vars)
            else: result = eval(cmd, globals(), local_vars)
            await bot.reply_to(m, f"💡 *Result:* \n`{result}`", parse_mode="Markdown")
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            err = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            await bot.reply_to(m, "❌ Error: \n" + str(err[:1000]))
        return

        if txt.startswith(".exe"):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "Eits, jangan sembarangan acak-acak sistem ya! Perintah ini cuma punya Paduka Ijel tercinta! 😠 Blweee 😜")
            return
        shell_cmd = txt.replace(".exe", "").strip()
        if not shell_cmd:
            await bot.reply_to(m, "Perintah terminalnya mana yang mau dieksekusi, Paduka? 🫨")
            return
        
        await bot.send_chat_action(m.chat.id, 'typing')
        try:
            # Mengeksekusi perintah terminal secara asynchronous
            process = await asyncio.create_subprocess_shell(
                shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode('utf-8', errors='replace').strip()
            error_output = stderr.decode('utf-8', errors='replace').strip()
            
            # Menggunakan pelarian HTML agar karakter <, >, & tidak merusak parse_mode
            def html_escape(text):
                return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            response_text = ""
            if output:
                response_text += f"<b>📤 Output:</b>\n<pre>{html_escape(output)}</pre>\n"
            if error_output:
                response_text += f"<b>⚠️ Error Output:</b>\n<pre>{html_escape(error_output)}</pre>\n"
            if not response_text:
                response_text = "<b>✅ Sukses:</b> Perintah berhasil dieksekusi tanpa ada output terminal."
                
            # Menggunakan parse_mode="HTML" karena jauh lebih aman untuk cetak kode/script
            await bot.reply_to(m, response_text[:4000], parse_mode="HTML")
        except Exception as e:
            await bot.reply_to(m, f"❌ <b>Gagal mengeksekusi:</b> {html_escape(str(e))}", parse_mode="HTML")
        return

    # =========================================================
    # 1. PERINTAH FITUR UTILITY & HELP
    # =========================================================
    if low.startswith("/help"):
        help_text = (
            f"✨ *PANDUAN UTK ANGGOTA GRUP* ✨\n\n"
            f"Halo {user_name}! Aku *{NAME}*, bot paling menggemaskan tapi peka. "
            f"Berikut adalah daftar perintah yang bisa kamu gunakan:\n\n"
            f"💬 *INTERAKSI AI MULTI-SESI*\n"
            f"• Panggil namaku (`cajel`) atau **cukup reply chat-ku**, maka aku akan membalas obrolanmu.\n"
            f"• Kamu bisa ajak aku curhat panjang lebar! Aku bakal ingat konteks obrolannya biar selalu nyambung. 🥰\n\n"
            f"🛠 *PERINTAH UTILITAS PUBLIK*\n"
            f"• /getmusic [judul] - Cari dan unduh musik MP3 langsung dari YouTube!\n"
            f"• /mock [teks] - Mengubah teks jadi format ejekan Spongebob (Bisa juga dengan me-reply chat teman lalu ketik `/mock`).\n"
            f"• /info - Cek informasi detail bot, data ID kamu, dan status server.\n"
            f"• /help - Menampilkan menu bantuan ini.\n\n"
            f"🌟 *FITUR TAMBAHAN*\n"
            f"• *Whisper Secret Message (Pesan Rahasia):*\n"
            f"Sekaruh fitur bisikan murni menggunakan Inline Mode! Di kolom ketik chat mana saja, silakan ketik:\n"
            f"`@{BOTNAME} [isi pesan] @username_target`\n"
            f"Lalu klik pop-up yang muncul. Pesan rahasiamu akan terkirim dalam bentuk tombol rahasia dan cuma bisa diintip oleh target tersebut! 🤫"
        )
        if m.from_user.id == OWNER_ID: 
            help_text += f"\n\n👑 *MENU RAHASIA PADUKA IJEL:* \n• `syuh` - Mematikan total bot.\n• `.eval [kode]` - Evaluasi Python.\n• `.exe [cmd]` - Eksekusi Terminal Bash."
        await bot.reply_to(m, help_text, parse_mode="Markdown")
        return

    if low.startswith("/info"):
        info_text = (
            f"🤖 *Bot Info* 🤖\n\n"
            f"• *Nama Bot:* {NAME}\n"
            f"• *Username:* {BOTNAME}\n"
            f"• *Chat ID:* `{m.chat.id}`\n"
            f"• *Kamu:* {user_name} (`{m.from_user.id}`)\n"
            f"• *Status Bot:* online & siap mengacau 🤪"
        )
        await bot.reply_to(m, info_text, parse_mode="Markdown")
        return

    if low.startswith("/mock"):
        target_text = txt.replace("/mock", "").strip()
        if not target_text and m.reply_to_message: target_text = m.reply_to_message.text or ""
        if target_text:
            mocked = "".join([c.upper() if random.choice([True, False]) else c.lower() for c in target_text])
            await bot.reply_to(m, f"{mocked} 🤪")
        else: await bot.reply_to(m, "Ketik `/mock [teks]` atau balas chat orang dengan `/mock` biar aku ejek! Blweee 😜")
        return

    # =========================================================
    # 2. PERINTAH OWNER (MATIKAN BOT)
    # =========================================================
    if low == "syuh":
        if m.from_user.id == OWNER_ID:
            await bot.reply_to(m, "ih jahat dimatiin 🥹...")
            await send_bot_log(f"🛑 *[OFFLINE]* Bot dinonaktifkan dari jarak jauh oleh Paduka Owner via perintah `syuh`.")
            await asyncio.sleep(1)
            os._exit(0)
        else:
            await bot.reply_to(m, "kamu bukan paduka ijel, kamu gabisa matiin aku! wleee 😜")
            return

    # =========================================================
    # 3. LOGIKA RESPONS GEMINI AI
    # =========================================================
    is_reply_to_bot = False
    if m.reply_to_message and m.reply_to_message.from_user:
        bot_info = await bot.get_me()
        if m.reply_to_message.from_user.id == bot_info.id: is_reply_to_bot = True

    dipanggil = m.chat.type == "private" or "cajel" in low or BOTNAME.lower() in low or is_reply_to_bot

    if dipanggil:
        clean_prompt = txt.replace("cajel", "").replace(BOTNAME, "").strip()
        if not clean_prompt: clean_prompt = "halo apa kabar"
        await bot.send_chat_action(m.chat.id, 'typing')
        memory_id = m.chat.id if m.chat.type in ["group", "supergroup"] else m.from_user.id
        jawaban = await ask_gemini(memory_id, clean_prompt, user_name)
        await bot.reply_to(m, jawaban)

async def startup():
    me = await bot.get_me()
    startup_msg = f"🚀 *[ONLINE]* Bot *{NAME}* (@{me.username}) berhasil aktif di server!\n• Sistem Rotasi: `{len(API_KEYS)}` API Key terdeteksi.\n• Fitur Memori, Log Komprehensif, Terminal Executor (.exe): *Aktif*."
    print(startup_msg)
    await send_bot_log(startup_msg)
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
      
