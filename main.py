import json
import random
from telebot import types

# Penyimpanan sesi game di RAM
game_sessions = {}

def load_kbbi_word(length=None):
    """Mengambil 1 kata acak dari dataKBBI.json dengan filter panjang huruf"""
    try:
        with open("dataKBBI.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            word_list = list(words.keys()) if isinstance(words, dict) else list(words)
            if length:
                valid_words = [w.strip().lower() for w in word_list if w.strip().isalpha() and len(w.strip()) == length]
            else:
                valid_words = [w.strip().lower() for w in word_list if w.strip().isalpha() and 4 <= len(w.strip()) <= 7]
            return random.choice(valid_words) if valid_words else "cajel"
    except: return "cajel"

def setup(bot, data):
    # Mengambil fungsi database dari main.py (via shared data)
    db_func = data["games_db"]
    add_rewards = db_func["add_rewards"]
    get_leaderboard = db_func["get_leaderboard"]

    def generate_menu_keyboard():
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 1. Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 2. Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 3. Wordle (5 Huruf)", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("🏆 Peringkat", callback_data="game_leaderboard")
        )
        return kb

    @bot.message_handler(commands=['game', 'games'])
    async def send_game_menu(m):
        pesan = (
            "🎮 **Pusat Game Cajel Cybot** 🎮\n\n"
            "Pilih mode permainan, Paduka! Cukup ketik jawabanmu langsung di chat tanpa perlu reply!\n\n"
            "• /skip untuk ganti kata\n"
            "• /menyerah untuk berhenti"
        )
        await bot.reply_to(m, pesan, reply_markup=generate_menu_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def handle_game_callbacks(call):
        chat_id = call.message.chat.id
        action = call.data
        
        if action == "game_leaderboard":
            board = get_leaderboard()
            txt = "🏆 **TOP 10 PERINGKAT** 🏆\n\n" + "\n".join([f"{i}. {p[1]['username']} (Lvl {p[1]['level']})" for i, p in enumerate(board, 1)])
            await bot.edit_message_text(txt, chat_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Kembali", callback_data="game_menu")), parse_mode="Markdown")
            return

        if action == "game_menu":
            await bot.edit_message_text("🎮 **Pilih mode permainan:**", chat_id, call.message.message_id, reply_markup=generate_menu_keyboard())
            return
        
        if action == "game_start_wordle":
            word = load_kbbi_word(length=5)
            game_sessions[chat_id] = {"mode": "wordle", "jawaban": word, "kesempatan": 6, "history": []}
            await bot.edit_message_text(f"🟩 **WORDLE INDONESIA**\n\nTarget: 5 huruf. Ketik tebakanmu langsung!\n/skip /menyerah", chat_id, call.message.message_id, parse_mode="Markdown")
        
        else:
            word = load_kbbi_word()
            if action == "game_start_susun":
                s = list(word.upper()); random.shuffle(s); s_str = " ".join(s)
                game_sessions[chat_id] = {"mode": "susun", "jawaban": word}
                await bot.edit_message_text(f"🧩 **SUSUN KATA**\n\nHuruf: {s_str}\n\nKetik jawabanmu langsung!\n/skip /menyerah", chat_id, call.message.message_id, parse_mode="Markdown")
            
            elif action == "game_start_lengkapi":
                d = " ".join([c.upper() if i%2==0 else "•" for i, c in enumerate(word)])
                game_sessions[chat_id] = {"mode": "lengkapi", "jawaban": word, "kesempatan": 6}
                await bot.edit_message_text(f"🔍 **LENGKAPI KATA**\n\nKata: {d}\n\nKetik jawabanmu langsung!\n/skip /menyerah", chat_id, call.message.message_id, parse_mode="Markdown")

    @bot.message_handler(commands=['skip', 'menyerah'])
    async def handle_game_control(m):
        if m.chat.id in game_sessions:
            ans = game_sessions[m.chat.id]["jawaban"].upper()
            del game_sessions[m.chat.id]
            await bot.reply_to(m, f"🏳️ Sesi dihentikan. Kata aslinya adalah: {ans}")

    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and not m.text.startswith('/'))
    async def handle_game_replies(m):
        chat_id = m.chat.id; s = game_sessions[chat_id]; tebakan = m.text.lower()
        if tebakan == s["jawaban"].lower():
            p_data, _ = add_rewards(m.from_user.id, m.from_user.first_name, 20, 40)
            del game_sessions[chat_id]
            await bot.reply_to(m, f"🎉 Benar! Poin: {p_data['poin']} | Level: {p_data['level']}")
        else:
            await bot.reply_to(m, "❌ Salah! Coba lagi atau gunakan /skip.")
                         
