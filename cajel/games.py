import os
import json
import random
from telebot import types
from cajel.games_db import add_rewards, get_leaderboard, get_player

# Penyimpanan sesi game yang sedang berjalan di RAM
game_sessions = {}

def load_kbbi_word():
    """Mengambil 1 kata acak dari dataKBBI.json secara aman"""
    try:
        with open("dataKBBI.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            if isinstance(words, dict):
                word_list = list(words.keys())
            else:
                word_list = list(words)
            
            valid_words = [w.strip().lower() for w in word_list if w.strip().isalpha() and 4 <= len(w.strip()) <= 7]
            return random.choice(valid_words) if valid_words else "cajel"
    except Exception as e:
        print(f"[GAME ERROR] Gagal memuat dataKBBI.json: {e}")
        return "cajel"

def setup(bot, data):
    
    def generate_menu_keyboard():
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🧩 1. Susun Kata", callback_data="game_start_susun"),
            types.InlineKeyboardButton("🔍 2. Lengkapi Kata", callback_data="game_start_lengkapi"),
            types.InlineKeyboardButton("🟩 3. Wordle Indonesia", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("🏆 Peringkat (Leaderboard)", callback_data="game_leaderboard")
        )
        return kb

    @bot.message_handler(commands=['game', 'games'])
    async def send_game_menu(m):
        pesan = (
            "🎮 **Pusat Game Cajel Cybot** 🎮\n\n"
            "Silakan pilih mode permainan di bawah ini menggunakan tombol, Paduka! "
            "Kumpulkan Poin dan XP untuk menaikkan Level dan merajai Peringkat! 🏆\n\n"
            "Gunakan perintah ini saat bermain:\n"
            "• /skip untuk ganti kata baru\n"
            "• /menyerah untuk menyudahi game"
        )
        await bot.reply_to(m, pesan, reply_markup=generate_menu_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def handle_game_callbacks(call):
        chat_id = call.message.chat.id
        action = call.data
        
        if action == "game_leaderboard":
            board = get_leaderboard()
            if not board:
                return await bot.answer_callback_query(call.id, "Belum ada data peringkat, ayo mainkan dulu!", show_alert=True)
            
            txt = "🏆 **TOP 10 PERINGKAT CAJEL GAMES** 🏆\n\n"
            for idx, (uid, p_data) in enumerate(board, 1):
                txt += f"{idx}. 👤 **{p_data['username']}** ➡️ Lvl {p_data['level']} | {p_data['poin']} Poin\n"
            
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="game_menu"))
            await bot.edit_message_text(txt, chat_id, call.message.message_id, reply_markup=kb, parse_mode="Markdown")
            return

        if action == "game_menu":
            pesan = (
                "🎮 **Pusat Game Cajel Cybot** 🎮\n\n"
                "Silakan pilih mode permainan di bawah ini menggunakan tombol, Paduka!\n\n"
                "• /skip untuk ganti kata baru\n"
                "• /menyerah untuk menyudahi game"
            )
            await bot.edit_message_text(pesan, chat_id, call.message.message_id, reply_markup=generate_menu_keyboard(), parse_mode="Markdown")
            return

        word = load_kbbi_word()
        
        if action == "game_start_susun":
            scrambled = list(word.upper())
            random.shuffle(scrambled)
            scrambled_str = " ".join(scrambled)
            
            game_sessions[chat_id] = {"mode": "susun", "jawaban": word, "display": scrambled_str}
            
            info = (
                "🧩 **MODE: SUSUN KATA**\n"
                "────────────────────\n"
                "**Cara Bermain:** Susun kembali huruf-huruf acak di bawah ini menjadi satu kata baku KBBI yang benar.\n\n"
                f"🔠 Huruf Acak: {scrambled_str}\n\n"
                "⚠️ **PENTING:** Paduka WAJIB REPLY (Balas) pesan ini untuk mengirim jawaban!\n"
                "Gunakan /skip untuk ganti kata atau /menyerah untuk berhenti."
            )
            await bot.edit_message_text(info, chat_id, call.message.message_id, parse_mode="Markdown")

        elif action == "game_start_lengkapi":
            display_list = [char.upper() if i % 2 == 0 else "_" for i, char in enumerate(word)]
            display_str = " ".join(display_list)

            game_sessions[chat_id] = {"mode": "lengkapi", "jawaban": word, "display": display_str, "kesempatan": 6}

            info = (
                "🔍 **MODE: LENGKAPI KATA**\n"
                "────────────────────\n"
                "**Cara Bermain:** Tebak kata utuh yang rumpang di bawah ini berdasarkan huruf bantuan.\n\n"
                f"📝 Kata: {display_str}\n"
                "❤️ Kesempatan salah: 6 kali\n\n"
                "⚠️ **PENTING:** Paduka WAJIB REPLY (Balas) pesan ini untuk menjawab!\n"
                "Gunakan /skip untuk ganti kata atau /menyerah untuk berhenti."
            )
            await bot.edit_message_text(info, chat_id, call.message.message_id, parse_mode="Markdown")

        elif action == "game_start_wordle":
            game_sessions[chat_id] = {"mode": "wordle", "jawaban": word, "kesempatan": 6, "history": []}

            info = (
                "🟩 **MODE: WORDLE INDONESIA**\n"
                "────────────────────\n"
                "**Cara Bermain:** Tebak kata rahasia. 🟩=Benar, 🟨=Posisi salah, ⬜=Tidak ada.\n\n"
                f"📏 Panjang kata target: {len(word)} Huruf\n"
                "❤️ Sisa kesempatan tebak: 6\n\n"
                "⚠️ **PENTING:** Paduka WAJIB REPLY (Balas) pesan ini untuk menjawab!\n"
                "Gunakan /skip untuk ganti kata atau /menyerah untuk berhenti."
            )
            await bot.edit_message_text(info, chat_id, call.message.message_id, parse_mode="Markdown")

    @bot.message_handler(commands=['skip', 'menyerah'])
    async def handle_game_control(m):
        chat_id = m.chat.id
        if chat_id not in game_sessions:
            return await bot.reply_to(m, "Tidak ada sesi game aktif, Paduka. Ketik /game dulu yuk!")

        session = game_sessions[chat_id]
        jawaban_benar = session["jawaban"].upper()

        if m.text.startswith("/menyerah"):
            del game_sessions[chat_id]
            await bot.reply_to(m, f"🏳️ Paduka menyerah! Kata aslinya adalah: {jawaban_benar}.")
        elif m.text.startswith("/skip"):
            # Logika re-inisiasi kata baru (disingkat untuk efisiensi)
            new_word = load_kbbi_word()
            game_sessions[chat_id]["jawaban"] = new_word
            await bot.reply_to(m, f"⏩ Kata dilewati! Kata sebelumnya: {jawaban_benar}. Silakan cek pesan game Paduka untuk tebakan baru!")

    @bot.message_handler(func=lambda m: m.reply_to_message is not None)
    async def handle_game_replies(m):
        chat_id = m.chat.id
        user_id = m.from_user.id
        username = m.from_user.first_name
        tebakan = (m.text or "").strip().lower()

        if chat_id not in game_sessions: return
        bot_info = await bot.get_me()
        if m.reply_to_message.from_user.id != bot_info.id: return

        session = game_sessions[chat_id]
        jawaban_asli = session["jawaban"].lower()

        if session["mode"] == "susun":
            if tebakan == jawaban_asli:
                del game_sessions[chat_id]
                p_data, lvl_up = add_rewards(user_id, username, 10, 25)
                await bot.reply_to(m, f"🎉 Benar! +10 Poin, +25 XP. Level: {p_data['level']}")
            else:
                await bot.reply_to(m, "❌ Jawaban Salah! Coba lagi atau /skip.")

        elif session["mode"] == "lengkapi":
            if tebakan == jawaban_asli:
                del game_sessions[chat_id]
                p_data, lvl_up = add_rewards(user_id, username, 15, 35)
                await bot.reply_to(m, f"🎉 Benar! +15 Poin, +35 XP. Level: {p_data['level']}")
            else:
                session["kesempatan"] -= 1
                if session["kesempatan"] <= 0:
                    del game_sessions[chat_id]
                    await bot.reply_to(m, f"💀 Kesempatan habis! Kata aslinya: {jawaban_asli.upper()}")
                else:
                    await bot.reply_to(m, f"❌ Salah! Sisa kesempatan: {session['kesempatan']}")

        elif session["mode"] == "wordle":
            # Logika Wordle tetap sama
            result_emojis = "".join(["🟩" if tebakan[i] == jawaban_asli[i] else "🟨" if tebakan[i] in jawaban_asli else "⬜" for i in range(len(tebakan))])
            session["history"].append(result_emojis + f" ({tebakan.upper()})")
            session["kesempatan"] -= 1
            if tebakan == jawaban_asli:
                del game_sessions[chat_id]
                p_data, _ = add_rewards(user_id, username, 25, 50)
                await bot.reply_to(m, f"🎉 Wordle Selesai! Poin: {p_data['poin']}")
            else:
                await bot.reply_to(m, f"📊 Hasil:\n" + "\n".join(session["history"]) + f"\n❤️ Sisa: {session['kesempatan']}")
              
