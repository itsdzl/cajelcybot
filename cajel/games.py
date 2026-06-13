import json
import random
from telebot import types

game_sessions = {}

def load_kbbi_word(length=None):
    try:
        with open("dataKBBI.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            word_list = [k.lower() for k in data.keys() if k.strip().isalpha()]
            
            if length == 5:
                # Mode Wordle: HARUS 5 huruf
                filtered = [w for w in word_list if len(w) == 5]
            else:
                # Mode lain: Ambil kata apa saja
                filtered = word_list
            
            return random.choice(filtered) if filtered else "gajah"
    except: 
        return "gajah"

def get_wordle_hint(tebak, target):
    res = ["⬛"] * 5
    t_list = list(target)
    b_list = list(tebak)
    
    # 1. Hijau
    for i in range(5):
        if i < len(b_list) and b_list[i] == t_list[i]:
            res[i] = "🟩"; t_list[i] = None; b_list[i] = None
    # 2. Kuning
    for i in range(5):
        if i < len(b_list) and b_list[i] and b_list[i] in t_list:
            res[i] = "🟨"; t_list[t_list.index(b_list[i])] = None
    return "".join(res)

def setup(bot, data):
    add_rewards = data["games_db"]["add_rewards"]
    OWNER_ID = data.get("owner_id") 

    @bot.message_handler(commands=['game'])
    async def game_menu(m):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 Wordle (5 Huruf)", callback_data="game_start_wordle")
        )
        await bot.reply_to(m, "🎮 **Pusat Game**\nKetik .jawabanmu untuk menebak!", reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_start_"))
    async def start_game(call):
        mode = call.data.split("_")[2]
        chat_id = call.message.chat.id
        # Hanya kirim angka 5 jika mode-nya wordle
        word = load_kbbi_word(5 if mode == "wordle" else None)
        game_sessions[chat_id] = {"mode": mode, "jawaban": word}
        
        if mode == "wordle":
            await bot.edit_message_text("🟩 **Wordle Indonesia (5 Huruf)**\nKetik .jawabanmu", chat_id, call.message.message_id)
        elif mode == "susun":
            s = list(word.upper()); random.shuffle(s)
            await bot.edit_message_text(f"🧩 **Susun Kata**\n{' '.join(s)}", chat_id, call.message.message_id)
        elif mode == "lengkapi":
            hint = "".join([c if i % 2 == 0 else " _ " for i, c in enumerate(word)])
            await bot.edit_message_text(f"🔍 **Lengkapi Kata**\n{hint}", chat_id, call.message.message_id)

    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and (m.text.startswith('.') or (m.from_user.id == OWNER_ID and m.text.strip() == "*")))
    async def handle_reply(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        
        if m.from_user.id == OWNER_ID and m.text.strip() == "*":
            tebakan = s["jawaban"]
        elif m.text.startswith('.'):
            tebakan = m.text[1:].strip().lower()
        else:
            return

        if tebakan == s["jawaban"]:
            add_rewards(m.from_user.id, m.from_user.first_name, 50, 100)
            
            # Soal baru otomatis dengan filter yang sama
            s["jawaban"] = load_kbbi_word(5 if s["mode"] == "wordle" else None)
            
            msg = f"🎉 TEPAT! Soal baru siap."
            if s["mode"] == "susun":
                sc = list(s["jawaban"].upper()); random.shuffle(sc)
                msg += f"\n🧩 Baru: {' '.join(sc)}"
            elif s["mode"] == "lengkapi":
                h = "".join([c if i % 2 == 0 else " _ " for i, c in enumerate(s["jawaban"])])
                msg += f"\n🔍 Baru: {h}"
            
            await bot.reply_to(m, msg)
        else:
            if s["mode"] == "wordle":
                if len(tebakan) != 5:
                    await bot.reply_to(m, "⚠️ Harus 5 huruf!")
                else:
                    await bot.reply_to(m, get_wordle_hint(tebakan, s["jawaban"]))
            else:
                await bot.reply_to(m, "❌ Jawaban Salah!")
            
