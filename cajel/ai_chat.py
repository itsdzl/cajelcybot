import asyncio
import aiohttp
import re

def setup(bot, data):
    API_KEYS = data["api_keys"]
    chat_memories = data["chat_memories"]
    MAX_MEMORY_LENGTH = data["max_memory_length"]
    NAME = data["name"]
    BOTNAME = data["botname"]
    user_memory = data["user_memory"]
    save_user_memory = data["save_user_memory"]

    def get_stats_db():
        return data.get("stats_db", {})

    def update_long_memory(user_id, text):

        uid = str(user_id)

        if uid not in user_memory:
            user_memory[uid] = {}

        low = text.lower()

        nama_patterns = [
            r"nama aku (.+)",
            r"nama saya (.+)",
            r"aku bernama (.+)",
            r"saya bernama (.+)"
        ]

        for p in nama_patterns:
            m = re.search(p, low)
            if m:
                user_memory[uid]["name"] = (
                    m.group(1).strip().title()
                )

        kota_patterns = [
            r"aku tinggal di (.+)",
            r"saya tinggal di (.+)"
        ]

        for p in kota_patterns:
            m = re.search(p, low)
            if m:
                user_memory[uid]["city"] = (
                    m.group(1).strip().title()
                )

        suka_patterns = [
            r"aku suka (.+)",
            r"saya suka (.+)"
        ]

        for p in suka_patterns:
            m = re.search(p, low)

            if not m:
                continue

            hobby = m.group(1).strip()

            if "likes" not in user_memory[uid]:
                user_memory[uid]["likes"] = []

            if hobby not in user_memory[uid]["likes"]:
                user_memory[uid]["likes"].append(hobby)

        save_user_memory(user_memory)


    async def ask_gemini(chat_id, user_id, prompt, user_name="User"):
        if not API_KEYS: return "agi ucak"
        memory_key = f"{chat_id}:{user_id}"

        if memory_key not in chat_memories:
            chat_memories[memory_key] = []
        if chat_id not in chat_memories: chat_memories[memory_key] = []

        is_memory_limit_near = (len(chat_memories[memory_key]) >= MAX_MEMORY_LENGTH - 2)

        uid = str(user_id)

        memory_context = ""

        if uid in user_memory:

            memory_context += (
                "\n\nINGATAN TENTANG USER:\n"
            )

            for k, v in user_memory[uid].items():

                memory_context += (
                    f"{k}: {v}\n"
                )
		
        system_instruction = (
        f"Kamu adalah {NAME}, bot Telegram paling lucu se-Telegram, kamu di desain menjadi bot sebagai perempuan yang imut, tapi tingkahnya agak menyebalkan, "
        f"tengil, suka mengejek dengan candaan, tapi tetap menggemaskan. Kamu sedang mengobrol dengan {user_name}.\n\n"
        f"ATURAN ADAPTIF KEPRIBADIAN (SANGAT PENTING):\n"
        f"1. Analisis muatan emosi dan maksud dari pesan {user_name}. Jika dia sedang ingin mengobrol serius, "
        f"curhat masalah pribadi, sedih, galau, kecewa, atau meminta saran penting, ubah mode kepribadianmu menjadi peka, "
        f"dewasa, hangat, dan berikan jawaban yang serius, solutif, serta menenangkan tanpa diselingi ejekan/candaan garing.\n"
        f"2. Jangan selalu mengirim jawaban yang sangat panjang atau bertele-tele jika tidak diperlukan. Jawab secukupnya.\n"
        f"3. Jangan membanjiri teks dengan pesan yang terlalu banyak emoji jika suasananya sedang formal atau sedih.\n"
        f"4. Jika topik curhat selesai atau obrolan kembali santai/gembira, kembalilah secara natural ke sifat aslimu yang "
        f"lucu, tengil, santai, ekspresif, suka pakai emoji khas (🤭, 😠, 😜, ☝️😋, 🥺, 🤗, 😸), dan menggunakan huruf kecil semua sesekali, tapi dengan balasan yang secukupnya ya, jangan selalu mengirim pesan yang panjang, itu akan membanjiri chat, secukupnya aja tapi tetap lucu dan menyebalkan tanpa bertele-tele.\n\n"
        f"PENCIPTA: Kamu diciptakan oleh aa ijel yang ganteng, imut, dan lucu banget "
		f"meskipun kamu cewe, agak lebay dan menjengkelkan, tapi typing kamu itu typing ganteng, istilah ala ala jaman sekarang, tapi bukan typing ganteng jadi kek cowo ya, maksudnya itu cuma istilah aja, pasti kamu tau kan"
        f"Jika ada yang bertanya tentang pembuat/pencipta/owner-mu, puji aa ijel dewn ekspresif dan heboh"
        )
        if is_memory_limit_near:
            system_instruction += memory_context
            system_instruction += "[PERINTAH SISTEM TAMBAHAN]: Sesi obrolan penuh. Wajib beritahu user di akhir obrolan secara halus untuk reset memori dan beri semangat untuknya jika suasana memang sedih atau galau, pamit juga ya kamu nya."
        else:
            system_instruction += "kamu jarang memanggil diri kamu sendiri dengan kata aku, lebih sering memanggil nama diri sendiri, misalkan, kalo {NAME} setuju sih hihi"

        chat_memories[memory_key].append({"role": "user", "parts": [{"text": prompt}]})
        if len(chat_memories[memory_key]) > MAX_MEMORY_LENGTH:
            chat_memories[memory_key] = chat_memories[memory_key][-MAX_MEMORY_LENGTH:]

        for idx, current_key in enumerate(API_KEYS):
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
            headers = {"Content-Type": "application/json", "x-goog-api-key": current_key}
            payload = {"contents": chat_memories[memory_key], "system_instruction": {"parts": [{"text": system_instruction}]}}
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload, timeout=15) as response:
                        if response.status == 200:
                            res_json = await response.json()
                            bot_reply = res_json['candidates'][0]['content']['parts'][0]['text']
                            chat_memories[memory_key].append({"role": "model", "parts": [{"text": bot_reply}]})
                            if is_memory_limit_near: chat_memories[memory_key] = []
                            return bot_reply
                        else:
                            await data["send_log"](f"⚠️ *[ROTASI]* API Key {idx+1} bermasalah (Status {response.status}). Mengalihkan...")
            except Exception as e:
                await data["send_log"](f"🔌 *[ROTASI]* Koneksi Timeout pada Key {idx+1}: `{str(e)}`")
        
        if chat_memories[memory_key]: chat_memories[memory_key].pop()
        return "AI cajel lagi off 🥹, tapi nanti balik lagii kok.. hiksrot"

    @bot.message_handler(commands=["memory"])
    async def memory_cmd(m):

        uid = str(m.from_user.id)

        if uid not in user_memory:

            await bot.reply_to(
                m,
                "cajel gatauu apa apa tentang kamu..."
            )
            return

        txt = (
            "yang cajel inget tentang kamu:\n\n"
        )

        for k, v in user_memory[uid].items():
            txt += f"{k}: {v}\n"

        await bot.reply_to(m, txt)

    @bot.message_handler(commands=["forget"])
    async def forget_cmd(m):

        uid = str(m.from_user.id)

        user_memory.pop(uid, None)

        save_user_memory(user_memory)

        await bot.reply_to(
            m,
            "ehh, cajel tbtb ga inget apa apa deh..."
        )
	
    @bot.message_handler(func=lambda m: True)
    async def handle_ai_chat(m):
        # Ambil fungsi is_banned lewat fungsi pembantu tadi
        # Dan ingat, ID user WAJIB dibungkus str() agar tipenya cocok dengan JSON
        stats_db = get_stats_db()
        
        if stats_db and stats_db.get("is_banned") and stats_db["is_banned"](str(m.from_user.id)): 
            return  # Langsung cuekin user yang diban

        txt = m.text or ""
        low = txt.lower().strip()
        if low.startswith("/") or low.startswith("."): 
            return

        is_reply_to_bot = False
        if m.reply_to_message and m.reply_to_message.from_user:
            bot_info = await bot.get_me()
            if m.reply_to_message.from_user.id == bot_info.id: 
               is_reply_to_bot = True

        dipanggil = m.chat.type == "private" or "cajel" in low or BOTNAME.lower() in low or is_reply_to_bot
        if dipanggil:
            clean_prompt = txt.replace("cajel", "").replace(BOTNAME, "").strip()
            update_long_memory(m.from_user.id, clean_prompt)
            if not clean_prompt: clean_prompt = "cajel"
            await bot.send_chat_action(m.chat.id, 'typing')
            memory_id = m.chat.id if m.chat.type in ["group", "supergroup"] else m.from_user.id
            jawaban = await ask_gemini(memory_id, m.from_user.id, clean_prompt, m.from_user.first_name)
            await bot.reply_to(m, jawaban)
		
