import json
import random
from telebot import types

# Penyimpanan sesi game di RAM
game_sessions = {}

def load_kbbi_word(length=5):
    """Mengambil 1 kata acak dari dataKBBI.json dengan filter panjang huruf yang ketat"""
    try:
        with open("dataKBBI.json", "r", encoding="utf-8") as f:
            words = json.load(f)
            # Filter hanya kata dengan panjang yang diminta
            word_list = [w.strip().lower() for w in words.keys() if w.strip().isalpha() and len(w.strip()) == length]
            return random.choice(word_list) if word_list else "cajel"
    except Exception as e:
        print(f"Error loading words: {e}")
        return "cajel"

def get_wordle_hint(tebak, target):
    """Memberikan feedback hijau (🟩), kuning (🟨), hitam (⬛)"""
    res = ["⬛"] * 5
    target_list = list(target)
    tebak_list = list(tebak)
    
    # 1. Cek Hijau (Tepat posisi)
    for i in range(5):
        if tebak_list[i] == target_list[i]:
            res[i] = "🟩"
            target_list[i] = None # Tandai agar tidak dihitung lagi
            tebak_list[i] = None
            
    # 2. Cek Kuning (Ada tapi salah posisi)
    for i in range(5):
        if tebak_list[i] is not None and tebak_list[i] in target_list:
            res[i] = "🟨"
            target_list[target_list.index(tebak_list[i])] = None # Tandai agar tidak dipakai lagi
            
    return "".join(res)

def setup(bot, data):
    add_rewards = data["games_db"]["add_rewards"]

    def generate_menu_keyboard():
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("🟩 Wordle Indonesia (5 Huruf)", callback_data="game_start_wordle"),
            types.InlineKeyboardButton("❌ Berhenti Main", callback_data="game_stop")
        )
        return kb

    @bot.message_handler(commands=['game'])
    async def send_game_menu(m):
        await bot.reply_to(m, "🎮 **Pilih Mode Game:**", reply_markup=generate_menu_keyboard(), parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("game_"))
    async def handle_game_callbacks(call):
        chat_id = call.message.chat.id
        
        if call.data == "game_start_wordle":
            word = load_kbbi_word(5)
            game_sessions[chat_id] = {"mode": "wordle", "jawaban": word, "kesempatan": 6}
            await bot.edit_message_text(
                "🟩 **WORDLE INDONESIA**\n\n"
                "Target: 5 huruf. Ketik **.jawabanmu** untuk menebak.\n"
                "Contoh: .kabel", 
                chat_id, call.message.message_id, parse_mode="Markdown"
            )
        
        elif call.data == "game_stop":
            if chat_id in game_sessions: del game_sessions[chat_id]
            await bot.edit_message_text("🏳️ Game dihentikan.", chat_id, call.message.message_id)

    # BOT HANYA MERESPON JIKA DIAWALI TITIK (.)
    @bot.message_handler(func=lambda m: m.chat.id in game_sessions and m.text.startswith('.'))
    async def handle_game_replies(m):
        chat_id = m.chat.id
        s = game_sessions[chat_id]
        tebakan = m.text[1:].strip().lower()

        if s["mode"] == "wordle":
            if len(tebakan) != 5:
                await bot.reply_to(m, "⚠️ Tebakan harus 5 huruf!")
                return
            
            if tebakan == s["jawaban"]:
                add_rewards(m.from_user.id, m.from_user.first_name, 50, 100)
                # Soal baru otomatis
                s["jawaban"] = load_kbbi_word(5)
                s["kesempatan"] = 6
                await bot.reply_to(m, f"🎉 TEPAT! Kata tadi adalah **{tebakan.upper()}**.\n\nLanjut ke soal berikutnya! Ketik lagi .tebakanmu")
            else:
                s["kesempatan"] -= 1
                hint = get_wordle_hint(tebakan, s["jawaban"])
                
                if s["kesempatan"] <= 0:
                    ans = s["jawaban"].upper()
                    s["jawaban"] = load_kbbi_word(5)
                    s["kesempatan"] = 6
                    await bot.reply_to(m, f"💀 Habis kesempatan! Jawabannya adalah **{ans}**.\n\nSoal baru dimulai!")
                else:
                    await bot.reply_to(m, f"{hint}\nSisa kesempatan: {s['kesempatan']}")
                    
