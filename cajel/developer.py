import sys, os, asyncio, traceback, random, json, aiohttp

def setup(bot, data):
    OWNER_ID = data["owner_id"]
    BOTNAME = data["botname"]
    NAME = data["name"]

    @bot.message_handler(func=lambda m: m.text and m.text.strip().lower() == "syuh")
    async def shutdown_bot(m):
        if m.from_user.id == OWNER_ID:
            await bot.reply_to(m, "ih jahat dimatiin 🥹...")
            await data["send_log"](f"🛑 *[OFFLINE]* Bot dinonaktifkan via perintah `syuh`.")
            await asyncio.sleep(1)
            os._exit(0)
        else:
            await bot.reply_to(m, "kamu bukan paduka ijel, kamu gabisa matiin aku! wleee 😜")

    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".eval"))
    async def eval_code(m):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "heh tanganmu kotor ya! gausa sosoan pakai fitur ini, kamu bukan aa ijel! 😠 BLEEE 😜")
            return
        cmd = m.text.replace(".eval", "").strip()
        if not cmd:
            await bot.reply_to(m, "kodenya mana yang mau di eval, paduka? 🙂‍↕️")
            return

        local_vars = {
            "bot": bot, 
            "m": m, 
            "asyncio": asyncio, 
            "os": os, 
            "sys": sys, 
            "random": random, 
            "json": json, 
            "aiohttp": aiohttp, 
            "data": data
        }
        
        await bot.send_chat_action(m.chat.id, 'typing')
        try:
            if cmd.startswith("await "):
                clean_cmd = cmd.replace("await ", "", 1)
                result = await eval(clean_cmd, globals(), local_vars)
            else:
                result = eval(cmd, globals(), local_vars)
                
            await bot.reply_to(m, f"<b>📥 Input:</b>\n<code>{cmd}</code>\n\n<b>📤 Output:</b>\n<code>{result}</code>", parse_mode="HTML")
        except Exception as e:
            error_trace = traceback.format_exc()
            await bot.reply_to(m, f"<b>📥 Input:</b>\n<code>{cmd}</code>\n\n<b>⚠️ Error:</b>\n<pre>{error_trace}</pre>", parse_mode="HTML")
            await data["send_log"](f"❌ *[EVAL ERROR]* Perintah: `{cmd}`\n`{str(e)}`")

    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".exe"))
    async def execute_shell(m):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "perintah ini bahaya! cuma aa ijel yang bisa pakai! 🤫")
            return
        shell_cmd = m.text.replace(".exe", "").strip()
        if not shell_cmd:
            await bot.reply_to(m, "perintah terminalnya mana, paduka? 🤔")
            return
            
        await bot.send_chat_action(m.chat.id, 'typing')
        try:
            process = await asyncio.create_subprocess_shell(
                shell_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='replace').strip()
            error_output = stderr.decode('utf-8', errors='replace').strip()
            
            def html_escape(text):
                return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            response_text = ""
            if output:
                safe_output = html_escape(output)
                if len(safe_output) > 3800: safe_output = safe_output[:3800] + "\n\n...[Output Terpotong]..."
                response_text += f"<b>📤 Output:</b>\n<pre>{safe_output}</pre>\n"
            if error_output:
                safe_error = html_escape(error_output)
                if len(safe_error) > 3800: safe_error = safe_error[:3800] + "\n\n...[Error Terpotong]..."
                response_text += f"<b>⚠️ Error Output:</b>\n<pre>{safe_error}</pre>\n"
            if not response_text:
                response_text = "<b>✅ Sukses:</b> Perintah berhasil dieksekusi tanpa ada output terminal."
                
            await bot.reply_to(m, response_text, parse_mode="HTML")
        except Exception as e:
            await bot.reply_to(m, f"❌ Gagal mengeksekusi shell: `{str(e)}`")
            await data["send_log"](f"❌ *[EXE ERROR]* Perintah: `{shell_cmd}`\n`{str(e)}`")
            
