import random
from telebot import types

game_sessions = {}

def get_words(data, length=None):
    kbbi_dict = data.get("kbbi_data", {})
    word_list = [k.lower() for k in kbbi_dict.keys() if k.strip().isalpha()]
    
    if length == 5:
        filtered = [w for w in word_list if len(w) == 5]
    else:
        filtered = word_list
    
    return random.choice(filtered) if filtered else "gajah"

def get_wordle_hint(tebak, target):
    res = ["⬛"] * 5
    t_list = list(target)
    b_list = list(tebak)
    
    for i in range(5):
        if i < len(b_list) and b_list[i] == t_list[i]:
            res[i] = "🟩"; t_list[i] = None; b_list[i] = None
    for i in range(5):
        if i < len(b_list) and b_list[i] and b_list[i] in t_list:
            res[i] = "🟨"; t_list[t_list.index(b_list[i])] = None
    return "".join(res)

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
        await bot.reply_to(m, "🎮 **Pusat Game**\nPilih mode permainan di bawah!\n\n(Skor & XP terakumulasi untuk semua mode)\n*Tekan /rank untuk melihat peringkat kamu!*", reply_markup=kb)

    @bot.message_handler(commands=['rank'])
    async def rank_cmd(m):
        player = db["get_player"](m.from_user.id, m.from_user.first_name)
        await bot.reply_to(m, f"👤 **Profil {player['username']}**\nLevel: {player['level']}\nXP: {player['xp']}\nPoin: {player['poin']}")

    @bot.callback_query_handler(func=lambda call: call.data == "game_leaderboard")
    async def show_leaderboard_inline(call):
        top_players = db["get_leaderboard"]()
        text = "🏆 **Top 10 Pemain Global** 🏆\n\n"
        for i, (uid, info) in enumerate(top_players, 1):
            text += f"{i}. {info['username']} | Lvl: {info['level']} | Poin: {info['poin']}\n"
        await bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Kembali", callback_data="back_to_menu")))

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_start_"))
    async def start_game(call):
        mode = call.data.split("_")[2]
        chat_id = call.message.chat.id
        word = get_words(data, 5 if mode == "wordle" else None)
        game_sessions[chat_id] = {"mode": mode, "jawaban": word}
        
        if mode == "wordle":
            txt = ("🟩 **Permainan Wordle Indonesia telah dimulai!**\n\n"
                   "◼️◼️◼️◼️◼️\n"
                   "Ketik .jawabanmu menggunakan titik di awal!\n"
                   "Jawaban harus 5 huruf!")
        elif mode == "susun":
            s = list(word.upper()); random.shuffle(s)
            txt = ("🧩 **Permainan Susun Kata telah dimulai!**\n\n"
                   f"Susun kata berikut:\n{' '.join(s)}\n\n"
                   "Jawab menggunakan titik di awal!")
        elif mode == "lengkapi":
            hint = "".join([c.upper() if i % 2 == 0 else " _ " for i, c in enumerate(word)])
            txt = ("🔍 **Permainan Lengkapi Kata telah dimulai!**\n\n"
                   f"Lengkapi kata berikut:\n{hint}\n\n"
                   "Jawab menggunakan titik di awal!")
        
        await bot.edit_message_text(txt, chat_id, call.message.message_id)

    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and (m.text.startswith('.') or (m.from_user.id == OWNER_ID and m.text.strip() == "*")))
    async def handle_reply(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        
        if m.from_user.id == OWNER_ID and m.text.strip() == "*":
            tebakan = s["jawaban"]
        elif m.text.startswith('.'):
            tebakan = m.text[1:].strip().lower()
        else: return

        if tebakan == s["jawaban"]:
            player, leveled_up = db["add_rewards"](m.from_user.id, m.from_user.first_name, 50, 100)
            s["jawaban"] = get_words(data, 5 if s["mode"] == "wordle" else None)
            
            msg = f"🎉 **TEPAT!** (+50 Poin | +100 XP)\n"
            if leveled_up: msg += f"✨ **SELAMAT!** Naik ke Level {player['level']}!"
            
            # Tambah info soal baru
            if s["mode"] == "susun":
                sc = list(s["jawaban"].upper()); random.shuffle(sc)
                msg += f"\n🧩 Baru: {' '.join(sc)}"
            elif s["mode"] == "lengkapi":
                h = "".join([c.upper() if i % 2 == 0 else " _ " for i, c in enumerate(s["jawaban"])])
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
                                       
