import random

def setup(bot, data):
    NAME = data["name"]
    OWNER_ID = data["owner_id"]
    BOTNAME = data["botname"]
    LOG_GROUP_ID = data.get("log_group_id")

    # 1. Definisikan fungsi send_log agar bisa dipanggil sebagai data["send_log"]
    async def send_log(msg):
        if LOG_GROUP_ID:
            try:
                await bot.send_message(LOG_GROUP_ID, msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Gagal kirim log ke grup: {e}")
    
    # Masukkan fungsi ke dalam dictionary data
    data["send_log"] = send_log

    @bot.message_handler(commands=['start'])
    async def send_welcome(m):
        user_name = m.from_user.first_name
        
        # 2. Panggil fungsi database untuk mencatat user baru
        data["stats_db"]["update_chat"](m.chat.id, m.chat.type, user_name)
        
        if m.chat.type == "private":
            # Kirim log ke grup
            await data["send_log"](f"👤 *[USER BARU]* Seseorang memulai bot di PC!\n• *Nama:* {user_name}\n• *ID:* `{m.from_user.id}`")
            
            welcome_message = (
                f"👋 *Halo {user_name}!* Selamat datang di markas rahasia! ✨\n\n"
                f"Kenalin, aku *{NAME}*, bot paling imut se telegram raya. 😜\n👑 Ciptaan mutlak *aa ijel yang ganteng dan imut tiada tara*.\n\n"
                f"Ketik /help untuk melihat daftar perintah."
            )
            await bot.reply_to(m, welcome_message, parse_mode="Markdown")
        else:
            await bot.reply_to(m, "Ngapain start-start di grup? PC sini kalau berani 😠")

    @bot.my_chat_member_handler()
    async def handle_bot_added(update):
        if update.new_chat_member.status == "member" and update.old_chat_member.status in ["left", "kicked"]:
            # 3. Panggil fungsi database untuk mencatat grup baru
            data["stats_db"]["update_chat"](update.chat.id, update.chat.type, update.chat.title)
            
            # Kirim log ke grup
            await data["send_log"](f"📥 *[BOT MASUK GRUP BARU]*\n• *Grup:* {update.chat.title}\n• *ID:* `{update.chat.id}`")
            
            welcome = f"🎉 *HALO SEMUANYA! CAJEL DATANG!!* 🤪🤙\n\nAku bot lucu imut dan menggemaskan se telegram raya! jadiin cajel admin dulu biar bisa pake semua fitur yaa...\npanggil aku ketik `cajel` untuk ngobrol atau /help untuk melihat fitur fitur cajel."
            await bot.send_message(update.chat.id, welcome, parse_mode="Markdown")
)

    @bot.message_handler(commands=['help'])
    async def help_menu(m):
        help_text = (
            f"✨ *PANDUAN PERINTAH BOT* ✨\n\n"
            f"• Panggil `cajel` atau reply chat-ku untuk mengobrol.\n"
            f"• /getmusic [judul] - Unduh musik MP3 dari YouTube.\n"
            f"• /mock [teks] - Mengubah teks format ejekan.\n"
            f"• /help - Untuk melihat cara memakai bot.\n"
            f"• /game - Untuk bermain games dan memilih mode permainan.\n"
            f"• /info - Cek informasi bot dan server.\n\n"
            f"🌟 *FITUR TAMBAHAN*\n"
            f"• *Whisper (Pesan Rahasia):* Kirim Pesan Rahasia di Grup!\n\n"
            f"Cara Penggunaan, Ketik:\n\n"
            f"`@{BOTNAME} [isi pesan] @username_target`\n"
            f"Lalu klik pop-up yang muncul. Pesan rahasiamu akan terkirim ke orangnyaa! 🤫"
        )
        if m.from_user.id == OWNER_ID:
            help_text += "\n\n👑 *MENU OWNER:* \n• `syuh` - matikan bot.\n• `.restart` - restart bot.\n• `.hu` - info user.\n• `.update` - update bot.\n• `.bc` - broadcast pc/grup.\n• `.eval [kode]` - python\n• `.exe [cmd]` - bash terminal"
        await bot.reply_to(m, help_text, parse_mode="Markdown")

    @bot.message_handler(commands=['info'])
    async def info_bot(m):
        await bot.reply_to(m, f"""🤖 *Bot Info*\n• Name: {NAME}\n• Your ID: `{m.from_user.id}`\n• Chat ID: `{m.chat.id}`\n• Status: Online""", parse_mode="Markdown")

    @bot.message_handler(commands=['mock'])
    async def mock_text(m):
        target_text = m.text.replace("/mock", "").strip()
        if not target_text and m.reply_to_message: target_text = m.reply_to_message.text or ""
        if target_text:
            mocked = "".join([c.upper() if random.choice([True, False]) else c.lower() for c in target_text])
            await bot.reply_to(m, f"{mocked} 🤪")
          
