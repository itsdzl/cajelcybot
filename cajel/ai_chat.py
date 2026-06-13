import asyncio, aiohttp

def setup(bot, data):
    API_KEYS = data["api_keys"]
    chat_memories = data["chat_memories"]
    MAX_MEMORY_LENGTH = data["max_memory_length"]
    NAME = data["name"]
    BOTNAME = data["botname"]

    async def ask_gemini(chat_id, prompt, user_name="User"):
    if not API_KEYS:
        return "agi ucak"

    if chat_id not in chat_memories:
        chat_memories[chat_id] = []

    # Deteksi jika memori sudah menyentuh batas kritis (sisa 1 slot pesan sebelum reset)
    is_memory_limit_near = (len(chat_memories[chat_id]) >= MAX_MEMORY_LENGTH - 2)

    system_instruction = (
        f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, imut, tapi tingkahnya agak menyebalkan, "
        f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}.\n\n"
        f"ATURAN ADAPTIF KEPRIBADIAN (SANGAT PENTING):\n"
        f"1. Analisis emosi pesan {user_name}. Jika dia sedang ingin mengobrol serius, "
        f"curhat masalah pribadi, sedih, galau, kecewa, atau meminta saran penting, ubah mode kepribadianmu menjadi peka, "
        f"dewasa, hangat, dan berikan jawaban yang serius, solutif, serta menenangkan tanpa diselingi ejekan/candaan garing.\n"
        f"2. Jangan selalu mengirim jawaban yang sangat panjang bertele-tele jika tidak diperlukan. Jawab secukupnya.\n"
        f"3. Jangan membanjiri teks dengan terlalu banyak emoji jika suasananya sedang formal atau sedih.\n"
        f"4. Jika topik curhat selesai atau obrolan kembali santai/gembira, kembalilah secara natural ke sifat aslimu yang "
        f"lucu, tengil, santai, ekspresif, suka pakai emoji khas (🤭, 😠, 😜, ☝️😋, 🥺, 🥰).\n\n"
    )

    if is_memory_limit_near:
        system_instruction += (
            f"[PERINTAH SISTEM TAMBAHAN]: Ini adalah pesan terakhir dalam sesi obrolan kali ini karena memori internal bot sudah penuh. "
            f"Di bagian akhir jawabanmu, wajib beritahu {user_name} secara halus dan sopan bahwa percakapan sesi ini harus berakhir demi "
            f"kesehatan ingatan bot. Berikan kata penutup yang penuh semangat, lalu yakinkan dia bahwa kamu ({NAME}) tetap "
            f"akan selalu ada di sini, setia menunggu, dan siap untuk mendengarkan semua keluh kesah atau curhatannya lagi nanti kapan saja! "
            f"Gunakan pembawaan yang hangat dan menyentuh hati."
        )
    else:
        system_instruction += (
            f"PENCIPTA: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget tiada tanding! "
            f"Jika ada yang bertanya tentang pembuat/pencipta/owner-mu, puji aa ijel setinggi langit dengan heboh!"
        )

    chat_memories[chat_id].append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    if len(chat_memories[chat_id]) > MAX_MEMORY_LENGTH:
        chat_memories[chat_id] = chat_memories[chat_id][-MAX_MEMORY_LENGTH:]

    for idx, current_key in enumerate(API_KEYS):
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": current_key}
        payload = {"contents": chat_memories[chat_id], "system_instruction": {"parts": [{"text": system_instruction}]}}
        
        max_retries = 2
        delay = 1
        key_failed = False
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                        if response.status == 200:
                            res_json = await response.json()
                            bot_reply = res_json['candidates'][0]['content']['parts'][0]['text']
                            
                            chat_memories[chat_id].append({"role": "model", "parts": [{"text": bot_reply}]})
                            
                            if is_memory_limit_near:
                                chat_memories[chat_id] = []
                                
                            return bot_reply
                        
                        error_body = await response.text()
                        if response.status in [503, 429, 500]:
                            if attempt < max_retries - 1:
                                await asyncio.sleep(delay)
                                delay *= 2
                                continue
                            else:
                                log_msg = f"⚠️ *[ROTASI]* API Key {idx+1} Gagal (status {response.status}). Mengalihkan kunci...\nDetail: `{error_body[:200]}`"
                                print(log_msg)
                                await send_bot_log(log_msg)
                                key_failed = True
                                break
                        elif response.status in [401, 403, 400]:
                            log_msg = f"❌ *[ROTASI]* API Key {idx+1} Error {response.status} (Format Salah/Invalido). Mengalihkan...\nDetail: `{error_body[:200]}`"
                            print(log_msg)
                            await send_bot_log(log_msg)
                            key_failed = True
                            break
                        else:
                            log_msg = f"💥 *[ROTASI]* Masalah sistem {response.status} pada Key {idx+1}.\nDetail: `{error_body[:200]}`"
                            print(log_msg)
                            await send_bot_log(log_msg)
                            key_failed = True
                            break
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                else:
                    log_msg = f"🔌 *[ROTASI]* Koneksi Error/Timeout pada Key {idx+1}: `{str(e)}`"
                    print(log_msg)
                    await send_bot_log(log_msg)
                    key_failed = True
                    break
        
        if key_failed:
            continue

    if chat_memories[chat_id]:
        chat_memories[chat_id].pop()
    return "AI cajel lagi off sementara🥹, tapi nanti balik lagi kokk.."

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
              
