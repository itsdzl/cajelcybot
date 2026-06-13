import asyncio, aiohttp

def setup(bot, data):
    API_KEYS = data["api_keys"]
    chat_memories = data["chat_memories"]
    MAX_MEMORY_LENGTH = data["max_memory_length"]
    NAME = data["name"]
    BOTNAME = data["botname"]

    async def ask_gemini(chat_id, prompt, user_name="User"):
        if not API_KEYS: return "agi ucak"
        if chat_id not in chat_memories: chat_memories[chat_id] = []

        is_memory_limit_near = (len(chat_memories[chat_id]) >= MAX_MEMORY_LENGTH - 2)
        system_instruction = (
            f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, imut, tapi tingkahnya agak menyebalkan, "
            f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}.\n\n"
            f"ATURAN ADAPTIF KEPRIBADIAN (SANGAT PENTING):\n"
            f"1. Analisis emosi pesan {user_name}. Jika dia sedang ingin mengobrol serius, curhat, sedih, ubah kepribadianmu menjadi peka dan hangat.\n"
            f"2. Jika topik selesai kembali natural ke sifat aslimu yang lucu, tengil, santai, dan ekspresif.\n"
        )
        if is_memory_limit_near:
            system_instruction += "[PERINTAH SISTEM TAMBAHAN]: Sesi obrolan penuh. Wajib beritahu user di akhir obrolan secara halus untuk reset memori."
        else:
            system_instruction += "PENCIPTA: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget tiada tanding!"

        chat_memories[chat_id].append({"role": "user", "parts": [{"text": prompt}]})
        if len(chat_memories[chat_id]) > MAX_MEMORY_LENGTH:
            chat_memories[chat_id] = chat_memories[chat_id][-MAX_MEMORY_LENGTH:]

        for idx, current_key in enumerate(API_KEYS):
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {"Content-Type": "application/json", "x-goog-api-key": current_key}
            payload = {"contents": chat_memories[chat_id], "system_instruction": {"parts": [{"text": system_instruction}]}}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                        if response.status == 200:
                            res_json = await response.json()
                            bot_reply = res_json['candidates'][0]['content']['parts'][0]['text']
                            chat_memories[chat_id].append({"role": "model", "parts": [{"text": bot_reply}]})
                            if is_memory_limit_near: chat_memories[chat_id] = []
                            return bot_reply
                        else:
                            await data["send_log"](f"⚠️ *[ROTASI]* API Key {idx+1} bermasalah (Status {response.status}). Mengalihkan...")
            except Exception as e:
                await data["send_log"](f"🔌 *[ROTASI]* Koneksi Timeout pada Key {idx+1}: `{str(e)}`")
        
        if chat_memories[chat_id]: chat_memories[chat_id].pop()
        return "g mood, nanti aja y.."

    @bot.message_handler(func=lambda m: True)
    async def handle_ai_chat(m):
        txt = m.text or ""
        low = txt.lower().strip()
        if low.startswith("/") or low.startswith("."): return

        is_reply_to_bot = False
        if m.reply_to_message and m.reply_to_message.from_user:
            bot_info = await bot.get_me()
            if m.reply_to_message.from_user.id == bot_info.id: is_reply_to_bot = True

        dipanggil = m.chat.type == "private" or "cajel" in low or BOTNAME.lower() in low or is_reply_to_bot
        if dipanggil:
            clean_prompt = txt.replace("cajel", "").replace(BOTNAME, "").strip()
            if not clean_prompt: clean_prompt = "halo apa kabar"
            await bot.send_chat_action(m.chat.id, 'typing')
            memory_id = m.chat.id if m.chat.type in ["group", "supergroup"] else m.from_user.id
            jawaban = await ask_gemini(memory_id, clean_prompt, m.from_user.first_name)
            await bot.reply_to(m, jawaban)
              
