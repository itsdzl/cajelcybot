import json
import random
from telebot import types

OWNER_ID = 8278748114 

game_sessions = {}

def load_kbbi_word(length=None):
    try:
        with open("dataKBBI.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            # Ambil list kata saja
            word_list = [w.strip().lower() for w in words.keys() if w.strip().isalpha()]
            
            if length:
                filtered = [w for w in word_list if len(w) == length]
                return random.choice(filtered) if filtered else "cajel"
            else:
                filtered = [w for w in word_list if len(w) >= 3]
                return random.choice(filtered) if filtered else "cajel"
    except: return "cajel"

def get_wordle_hint(tebak, target):
    res = ["⬛"] * 5
    t_list, b_list = list(target), list(tebak)
    for i in range(5):
        if b_list[i] == t_list[i]:
            res[i] = "🟩"; t_list[i] = None; b_list[i] = None
    for i in range(5):
        if b_list[i] and b_list[i] in t_list:
            res[i] = "🟨"; t_list[t_list.index(b_list[i])] = None
    return "".join(res)

def setup(bot, data):
    add_rewards = data["games_db"]["add_rewards"]

    @bot.message_handler(commands=['game'])
    async def send_game_menu(m):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 Wordle (5 Huruf)", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("❌ Stop", callback_data="game_stop")
        )
        await bot.reply_to(m, "🎮 **Pusat Game**\nKetik .jawabanmu untuk menebak!", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def handle_game_callbacks(call):
        chat_id = call.message.chat.id
        if call.data == "game_stop":
            if chat_id in game_sessions: del game_sessions[chat_id]
            await bot.edit_message_text("🏳️ Game dihentikan.", chat_id, call.message.message_id)
        elif call.data.startswith("game_start_"):
            mode = call.data.split("_")[2]
            word = load_kbbi_word(5 if mode == "wordle" else None)
            game_sessions[chat_id] = {"mode": mode, "jawaban": word}
            txt = f"🟩 **WORDLE** (5 Huruf)" if mode == "wordle" else f"🎮 **MODE {mode.upper()}**"
            await bot.edit_message_text(f"{txt}\nKetik .jawabanmu", chat_id, call.message.message_id)

    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and m.text.startswith('.'))
    async def handle_game_replies(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        tebakan = m.text[1:].strip().lower()
        
        # Bypass Owner
        is_correct = (tebakan == s["jawaban"]) or (m.from_user.id == OWNER_ID and m.text.strip() == "*")
        
        if is_correct:
            add_rewards(m.from_user.id, m.from_user.first_name, 50, 100)
            # Otomatis Soal Baru
            s["jawaban"] = load_kbbi_word(5 if s["mode"] == "wordle" else None)
            
            if s["mode"] == "wordle":
                await bot.reply_to(m, "🎉 TEPAT! Soal baru: (5 huruf)")
            elif s["mode"] == "susun":
                shuf = list(s["jawaban"].upper()); random.shuffle(shuf)
                await bot.reply_to(m, f"🎉 TEPAT! Baru: {' '.join(shuf)}")
            else:
                hint = " ".join([c.upper() if i%2==0 else "•" for i, c in enumerate(s["jawaban"])])
                await bot.reply_to(m, f"🎉 TEPAT! Baru: {hint}")
        else:
            if s["mode"] == "wordle":
                if len(tebakan) != 5: await bot.reply_to(m, "⚠️ Harus 5 huruf!")
                else: await bot.reply_to(m, get_wordle_hint(tebakan, s["jawaban"]))
            else:
                await bot.reply_to(m, "❌ Salah!")
                
