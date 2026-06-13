import hashlib, telebot, random

def setup(bot, data):
    whisper_data = data["whisper_data"]

    @bot.inline_handler(func=lambda query: len(query.query) > 0)
    async def query_text(inline_query):
        try:
            raw_text = inline_query.query
            parts = raw_text.split()
            if parts[-1].startswith('@') and len(parts) > 1: target_username, secret_message = parts[-1].replace('@', '').lower(), " ".join(parts[:-1])
            elif parts[0].startswith('@') and len(parts) > 1: target_username, secret_message = parts[0].replace('@', '').lower(), " ".join(parts[1:])
            else:
                hint = telebot.types.InlineQueryResultArticle(id='hint', title='Format Bisikan Salah! 😠', description='Ketik: [isi pesan] @username target', input_message_content=telebot.types.InputTextMessageContent(message_text='Cara pakai whisper: `@cajelcybot isi pesan @username` 😜', parse_mode='Markdown'))
                await bot.answer_inline_query(inline_query.id, [hint], cache_time=1)
                return
            unique_id = hashlib.md5(f"{inline_query.id}_{secret_message}".encode()).hexdigest()[:10]
            whisper_data[unique_id] = {"target": target_username, "message": secret_message}
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text="✉️ Buka Pesan Rahasia", callback_data=f"wh_{unique_id}"))
            result = telebot.types.InlineQueryResultArticle(id=unique_id, title=f"Kirim bisikan ke @{target_username}", description=f"Isi pesan: {secret_message[:30]}...", reply_markup=markup, input_message_content=telebot.types.InputTextMessageContent(message_text=f"🤫 *Sssttt...* Ada pesan rahasia nih khusus buat *@{target_username}*.\nOrang lain dilarang ngintip ya! 😠", parse_mode="Markdown"))
            await bot.answer_inline_query(inline_query.id, [result], cache_time=1)
        except Exception as e: print(f"Error Inline Whisper: {e}")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("wh_"))
    async def handle_whisper_click(call):
        user_username = (call.from_user.username or "").lower()
        unique_id = call.data.replace("wh_", "")
        if unique_id not in whisper_data:
            await bot.answer_callback_query(call.id, text="Yah, pesan rahasia ini udah kedaluwarsa atau bot habis di-restart! 🥺", show_alert=True)
            return
        target_user, secret_text = whisper_data[unique_id]["target"], whisper_data[unique_id]["message"]
        if user_username == target_user: 
            await bot.answer_callback_query(call.id, text=f"💬 Pesan Rahasia:\n\" {secret_text} \"", show_alert=True)
        else:
            kutipan = ["Heh kepo banget! Bukan buat kamu ya! 😠 BLEEE 😜", "Jangan ngintip! Nanti matanya bintitan loh! 🤭"]
            await bot.answer_callback_query(call.id, text=random.choice(kutipan), show_alert=True)
          
