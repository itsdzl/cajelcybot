import random
import traceback
import os
import json
from telebot import types

game_sessions = {}

def get_words(data, length=None):
    kbbi_raw = data.get("kbbi_data", {})
    if isinstance(kbbi_raw, dict):
        word_list = [k.lower() for k in kbbi_raw.keys() if k.strip().isalpha()]
    elif isinstance(kbbi_raw, list):
        word_list = [w.lower() for w in kbbi_raw if isinstance(w, str) and w.strip().isalpha()]
    else:
        word_list = []
    
    if length == 5:
        filtered = [w for w in word_list if len(w) == 5]
    else:
        filtered = word_list
    return random.choice(filtered) if filtered else "gajah"

def get_soal_text(mode, word):
    if mode == "wordle":
        return "Wordle Indonesia!\n\n◼️◼️◼️◼️◼️\nKetik .jawabanmu! (5 huruf)"
    elif mode == "susun":
        s = list(word.upper()); random.shuffle(s)
        return f"🧩 Susun Kata!\n\nSusun: {' '.join(s)}\n\nKetik .jawabanmu!"
    elif mode == "lengkapi":
        hint = "".join([c.upper() if i % 2 == 0 else " _ " for i, c in enumerate(word)])
        return f"🔍 Lengkapi Kata!\n\nLengkapi: {hint}\n\nKetik .jawabanmu!"
    return ""

def setup(bot, data):
    db = data["games_db"]
    OWNER_ID = data.get("owner_id") 

    @bot.message_handler(commands=['game'])
    async def game_menu(m):
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 Wordle (5 Huruf)", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("🏆 Leaderboard Global", callback_data="game_leaderboard")
        )
        await bot.reply_to(m, "🎮 Pusat Game\n(Skor & XP terus bertambah!)\nTekan /rank untuk melihat profil.", reply_markup=kb)

    @bot.message_handler(commands=['rank', 'resetrank', 'addpoin', 'setlevel'])
    async def admin_and_rank(m):
        if m.text.startswith('/rank'):
            player = db["get_player"](m.from_user.id, m.from_user.first_name)
            await bot.reply_to(m, f"👤 {player['username']}\nLevel: {player['level']} | XP: {player['xp']} | Poin: {player['poin']}")
        elif m.from_user.id == OWNER_ID:
            if m.text.startswith('/resetrank'):
                with open("cajel_players.json", "w", encoding="utf-8") as f: json.dump({}, f)
                await bot.reply_to(m, "✅ Peringkat di-reset.")
            elif m.text.startswith('/addpoin'):
                args = m.text.split()
                if len(args) >= 3:
                    db["add_rewards"](args[1], "Pemain", int(args[2]), 0)
                    await bot.reply_to(m, f"✅ Menambah {args[2]} poin ke {args[1]}.")
            elif m.text.startswith('/setlevel'):
                args = m.text.split()
                if len(args) >= 3:
                    with open("cajel_players.json", "r+", encoding="utf-8") as f:
                        all_p = json.load(f)
                        if args[1] in all_p:
                            all_p[args[1]]["level"] = int(args[2])
                            f.seek(0); json.dump(all_p, f, indent=4); f.truncate()
                            await bot.reply_to(m, "✅ Level diubah.")

    @bot.message_handler(commands=['skip'])
    async def skip_game(m):
        if m.chat.id in game_sessions:
            s = game_sessions[m.chat.id]
            old_ans = s["jawaban"]
            new_word = get_words(data, 5 if s["mode"] == "wordle" else None)
            game_sessions[m.chat.id]["jawaban"] = new_word
            await bot.reply_to(m, f"Skip! Jawaban sebelumnya: **{old_ans}**.\n\n" + get_soal_text(s["mode"], new_word))
        else: await bot.reply_to(m, "Tidak ada permainan.")

    @bot.message_handler(commands=['udahan'])
    async def stop_game(m):
        if m.chat.id in game_sessions:
            del game_sessions[m.chat.id]
            await bot.reply_to(m, "Permainan dihentikan. papaii 👋🏻")
        else: await bot.reply_to(m, "Tidak ada permainan.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def callback_handler(call):
        try:
            await bot.answer_callback_query(call.id)
            chat_id = call.message.chat.id
            if call.data == "game_leaderboard":
                top = db["get_leaderboard"]()
                text = "🏆 Top 10 Global\n\n" + "\n".join([f"{i}. {p[1]['username']} (Lvl: {p[1]['level']})" for i, p in enumerate(top, 1)])
                await bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Kembali", callback_data="game_back")))
            elif call.data == "game_back":
                kb = types.InlineKeyboardMarkup(row_width=1)
                kb.add(types.InlineKeyboardButton("🧩 Susun Kata", callback_data="game_start_susun"), types.InlineKeyboardButton("🔍 Lengkapi Kata", callback_data="game_start_lengkapi"), types.InlineKeyboardButton("🟩 Wordle (5 Huruf)", callback_data="game_start_wordle"), types.InlineKeyboardButton("🏆 Leaderboard", callback_data="game_leaderboard"))
                await bot.edit_message_text("🎮 Pusat Game", chat_id, call.message.message_id, reply_markup=kb)
            elif call.data.startswith("game_start_"):
                if chat_id in game_sessions: return
                mode = call.data.split("_")[2]
                word = get_words(data, 5 if mode == "wordle" else None)
                game_sessions[chat_id] = {"mode": mode, "jawaban": word}
                await bot.edit_message_text(get_soal_text(mode, word), chat_id, call.message.message_id)
        except Exception as e: print(e)

    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and (m.text.startswith('.') or (m.from_user.id == OWNER_ID and m.text.strip() == "*")))
    async def handle_reply(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        tebakan = s["jawaban"] if (m.from_user.id == OWNER_ID and m.text.strip() == "*") else m.text[1:].strip().lower()
        if tebakan == s["jawaban"]:
            player, leveled_up = db["add_rewards"](m.from_user.id, m.from_user.first_name, 10, 10)
            ans = s["jawaban"]
            new_word = get_words(data, 5 if s["mode"] == "wordle" else None)
            game_sessions[chat_id]["jawaban"] = new_word
            msg = f"{ans} benar! (+10 Poin & +10 XP) pinter deh 😋"
            if leveled_up: msg += f"\n✨ Naik ke Level {player['level']}!"
            msg += "\n\n" + get_soal_text(s["mode"], new_word)
            await bot.reply_to(m, msg)
        else: await bot.reply_to(m, "❌ Jawaban Salah!")
        
