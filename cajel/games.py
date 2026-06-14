import random
import traceback
import os
import json
from telebot import types

game_sessions = {}

def get_words(data, length=5):
    kbbi_raw = data.get("kbbi_data", {})
    if isinstance(kbbi_raw, dict):
        word_list = [k.lower() for k in kbbi_raw.keys() if k.strip().isalpha()]
    elif isinstance(kbbi_raw, list):
        word_list = [w.lower() for w in kbbi_raw if isinstance(w, str) and w.strip().isalpha()]
    else: word_list = []
    
    filtered = [w for w in word_list if len(w) == 5]
    return random.choice(filtered) if filtered else "gajah"

def check_wordle_colors(tebakan, jawaban):
    result = ['⬛'] * 5
    t, j = list(tebakan), list(jawaban)
    for i in range(5):
        if t[i] == j[i]:
            result[i] = '🟩'
            j[i] = None
    for i in range(5):
        if result[i] == '⬛' and t[i] in j:
            result[i] = '🟨'
            j[j.index(t[i])] = None
    return "".join(result)

def get_soal_text(mode, word):
    # Pengingat selalu disematkan di sini
    info = "\n━━━━━━━━━━━━━━\nKetik Jawabanmu Diawali dengan Titik!\n\nOrang lemah pasti mencet ini /skip (Ganti kata) | /udahan (Berhenti)"
    if mode == "wordle":
        return f"🟩Wordle Indonesia⬛\n◼️◼️◼️◼️◼️{info}"
    elif mode == "susun":
        s = list(word.upper()); random.shuffle(s)
        return f"🧩 Susun Kata: {' '.join(s)}{info}"
    elif mode == "lengkapi":
        hint = "".join([c.upper() if i % 2 == 0 else " _ " for i, c in enumerate(word)])
        return f"🔍 Lengkapi Kata: {hint}{info}"
    return ""

def setup(bot, data):
    db = data["games_db"]
    OWNER_ID = data.get("owner_id") 

    @bot.message_handler(commands=['game'])
    async def game_menu(m):
        if m.chat.id in game_sessions:
            await bot.reply_to(m, "❌ ada game yang lagi berjalan, ketik /udahan dulu baru mulai lagi.")
            return
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 Wordle (5 Huruf)", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("🏆 Leaderboard Global", callback_data="game_leaderboard")
        )
        await bot.reply_to(m, "🎮 Pusat Game\nPilih mode permainan:", reply_markup=kb)

    @bot.message_handler(commands=['rank', 'resetrank', 'setpoin', 'setlevel'])
    async def admin_handler(m):
        if m.text.startswith('/rank'):
            p = db["get_player"](m.from_user.id, m.from_user.first_name)
            await bot.reply_to(m, f"👤 {p['username']} | Poin: {p['poin']}")
        
        elif m.from_user.id == OWNER_ID:
            args = m.text.split()
            if m.text.startswith('/resetrank'):
                with open("cajel_players.json", "r+", encoding="utf-8") as f:
                    all_p = json.load(f)
                    if len(args) > 1: 
                        target = args[1]
                        if target in all_p:
                            all_p[target] = {"username": all_p[target]["username"], "level": 1, "xp": 0, "poin": 0}
                            f.seek(0); json.dump(all_p, f, indent=4); f.truncate()
                            await bot.reply_to(m, f"✅ Rank user {target} di-reset.")
                        else: await bot.reply_to(m, "❌ User tidak ditemukan.")
                    else: 
                        json.dump({}, open("cajel_players.json", "w", encoding="utf-8"))
                        await bot.reply_to(m, "✅ Seluruh peringkat di-reset.")

            elif m.text.startswith('/setpoin'):
                if len(args) < 3:
                    await bot.reply_to(m, "⚠️ Format: `/setpoin <user_id> <jumlah>`")
                    return
                target, val = args[1], int(args[2])
                with open("cajel_players.json", "r+", encoding="utf-8") as f:
                    all_p = json.load(f)
                    if target in all_p:
                        all_p[target]["poin"] += val
                        f.seek(0); json.dump(all_p, f, indent=4); f.truncate()
                        await bot.reply_to(m, f"✅ Poin diubah. Total sekarang: {all_p[target]['poin']}")
                    else: await bot.reply_to(m, "❌ User tidak ditemukan.")

    @bot.message_handler(commands=['skip'])
    async def skip_game(m):
        if m.chat.id in game_sessions:
            s = game_sessions[m.chat.id]
            old = s["jawaban"]
            s["jawaban"] = get_words(data)
            await bot.reply_to(m, f"⏭️ Skip! Jawaban tadi adalah: **{old.upper()}**\n" + get_soal_text(s["mode"], s["jawaban"]))
        else: await bot.reply_to(m, "Tidak ada game.")

    @bot.message_handler(commands=['udahan'])
    async def stop_game(m):
        if m.chat.id in game_sessions:
            del game_sessions[m.chat.id]
            await bot.reply_to(m, "👋 Permainan dihentikan.")
        else: await bot.reply_to(m, "Tidak ada game.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def callback_handler(call):
        try:
            await bot.answer_callback_query(call.id)
            if call.data == "game_leaderboard":
                top = db["get_leaderboard"]()
                text = "🏆 Top 10 Global 🏆\n\n" + "\n".join(
                    [f"{i}. {p[1]['username']} | Poin: {p[1]['poin']}" for i, p in enumerate(top, 1)])
                await bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Kembali", callback_data="game_back")))

            elif call.data == "game_back":
                kb = types.InlineKeyboardMarkup(row_width=1)
                kb.add(types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"), types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"), types.InlineKeyboardButton("🟩 Wordle", callback_data="game_start_wordle"), types.InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard"))
                await bot.edit_message_text("🎮 Pusat Game", call.message.chat.id, call.message.message_id, reply_markup=kb)
            elif call.data.startswith("game_start_"):
                m_type = call.data.split("_")[2]
                w = get_words(data)
                game_sessions[call.message.chat.id] = {"mode": m_type, "jawaban": w}
                await bot.edit_message_text(get_soal_text(m_type, w), call.message.chat.id, call.message.message_id)
        except Exception as e: print(e)

    @bot.message_handler(func=lambda m: m.chat.id in game_sessions)
    async def handle_reply(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        
        # Perintah Owner: Menampilkan jawaban dan langsung berganti soal
        if m.from_user.id == OWNER_ID and m.text.strip() == "*":
            ans = s["jawaban"]
            s["jawaban"] = get_words(data)
            msg = f"✅ {ans.upper()} adalah jawabannya!\n\n" + get_soal_text(s["mode"], s["jawaban"])
            await bot.reply_to(m, msg)
            return

        tebakan = m.text.strip().lower()
        
        if len(tebakan) == 5:
            if tebakan == s["jawaban"]:
                _, up = db["add_rewards"](m.from_user.id, m.from_user.first_name, 10, 10)
                ans = s["jawaban"]
                s["jawaban"] = get_words(data)
                msg = f"✅ {ans.upper()} benar! (+10 Poin)\n\n" + get_soal_text(s["mode"], s["jawaban"])
                await bot.reply_to(m, msg)
            elif s["mode"] == "wordle":
                res = check_wordle_colors(tebakan, s["jawaban"])
                await bot.reply_to(m, res)
        
