import json
import random
from telebot import types

# Penyimpanan sesi game di RAM
game_sessions = {}

def load_kbbi_word(length=None):
    """Mengambil 1 kata acak dengan filter panjang huruf"""
    try:
        with open("dataKBBI.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            word_list = [w.strip().lower() for w in words.keys() if w.strip().isalpha()]
            
            if length:
                filtered = [w for w in word_list if len(w) == length]
                return random.choice(filtered) if filtered else "cajel"
            else:
                filtered = [w for w in word_list if 4 <= len(w) <= 7]
                return random.choice(filtered) if filtered else "cajel"
    except: return "cajel"

def get_wordle_hint(tebak, target):
    """Memberikan feedback hijau (🟩), kuning (🟨), hitam (⬛)"""
    res = ["⬛"] * 5
    target_list = list(target)
    tebak_list = list(tebak)
    
    # 1. Hijau (Tepat posisi)
    for i in range(5):
        if tebak_list[i] == target_list[i]:
            res[i] = "🟩"
            target_list[i] = None
            tebak_list[i] = None
            
    # 2. Kuning (Salah posisi)
    for i in range(5):
        if tebak_list[i] is not None and tebak_list[i] in target_list:
            res[i] = "🟨"
            target_list[target_list.index(tebak_list[i])] = None
            
    return "".join(res)

def setup(bot, data):
    add_rewards = data["games_db"]["add_rewards"]

    def generate_menu_keyboard():
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 Wordle (5 Huruf)", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("❌ Stop", callback_data="game_stop")
        )
        return kb

    @bot.message_handler(commands=['game'])
    async def send_game_menu(m):
        await bot.reply_to(m, "🎮 **Pusat Game**\nKetik .jawabanmu untuk menebak!", reply_markup=generate_menu_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def handle_game_callbacks(call):
        chat_id = call.message.chat.id
        
        if call.data == "game_stop":
            if chat_id in game_sessions: del game_sessions[chat_id]
            await bot.edit_message_text("🏳️ Game dihentikan.", chat_id, call.message.message_id)
            return

        if call.data == "game_start_wordle":
            word = load_kbbi_word(5)
            game_sessions[chat_id] = {"mode": "wordle", "jawaban": word, "kesempatan": 6}
            await bot.edit_message_text("🟩 **WORDLE**\nTarget: 5 huruf. Ketik .jawaban", chat_id, call.message.message_id, parse_mode="Markdown")
        
        elif call.data == "game_start_susun":
            word = load_kbbi_word()
            s = list(word.upper()); random.shuffle(s)
            game_sessions[chat_id] = {"mode": "susun", "jawaban": word}
            await bot.edit_message_text(f"🧩 **SUSUN KATA**\nHuruf: {' '.join(s)}", chat_id, call.message.message_id, parse_mode="Markdown")
            
        elif call.data == "game_start_lengkapi":
            word = load_kbbi_word()
            d = " ".join([c.upper() if i%2==0 else "•" for i, c in enumerate(word)])
            game_sessions[chat_id] = {"mode": "lengkapi", "jawaban": word}
            await bot.edit_message_text(f"🔍 **LENGKAPI**\nKata: {d}", chat_id, call.message.message_id, parse_mode="Markdown")

    # Handler Utama dengan filter titik (.)
    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and m.text.startswith('.'))
    async def handle_game_replies(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        tebakan = m.text[1:].strip().lower()
        
        if s["mode"] == "wordle":
            if len(tebakan) != 5: return await bot.reply_to(m, "⚠️ Harus 5 huruf!")
            if tebakan == s["jawaban"]:
                add_rewards(m.from_user.id, m.from_user.first_name, 50, 100)
                s["jawaban"] = load_kbbi_word(5)
                await bot.reply_to(m, "🎉 Tepat! Lanjut ke soal berikutnya!")
            else:
                s["kesempatan"] -= 1
                if s["kesempatan"] <= 0:
                    ans = s["jawaban"].upper(); s["jawaban"] = load_kbbi_word(5); s["kesempatan"] = 6
                    await bot.reply_to(m, f"💀 Habis! Jawabannya: {ans}. Soal baru dimulai!")
                else:
                    await bot.reply_to(m, f"{get_wordle_hint(tebakan, s['jawaban'])}\nSisa: {s['kesempatan']}")

        elif s["mode"] in ["susun", "lengkapi"]:
            if tebakan == s["jawaban"]:
                add_rewards(m.from_user.id, m.from_user.first_name, 20, 40)
                # Generate soal baru sesuai mode
                new_word = load_kbbi_word()
                s["jawaban"] = new_word
                if s["mode"] == "susun":
                    shuf = list(new_word.upper()); random.shuffle(shuf)
                    await bot.reply_to(m, f"🎉 Benar! Baru: {' '.join(shuf)}")
                else:
                    hint = " ".join([c.upper() if i%2==0 else "•" for i, c in enumerate(new_word)])
                    await bot.reply_to(m, f"🎉 Benar! Baru: {hint}")
            else:
                await bot.reply_to(m, "❌ Salah!")
                    
