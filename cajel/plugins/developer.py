import sys, os, asyncio, traceback, random, json, aiohttp

def setup(bot, data):
    OWNER_ID = data["owner_id"]

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
        local_vars = {"bot": bot, "m": m, "asyncio": asyncio, "os": os, "sys": sys, "random": random, "aiohttp": aiohttp, "json": json, "data": data}
        try:
            if cmd.startswith("await "):
                clean_cmd = cmd.replace("await ", "", 1)
                result = await eval(clean_cmd, globals(), local_vars)
            else: result = eval(cmd, globals(), local_vars)
            await bot.reply_to(m, f"💡 *Result:* \n`{result}`", parse_mode="Markdown")
        except Exception:
            err = "".join(traceback.format_exception(*sys.exc_info()))
            await bot.reply_to(m, "❌ Error: \n" + str(err[:1000]))

    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".exe"))
    async def execute_terminal(m):
        if m.from_user.id != OWNER_ID:
            await bot.reply_to(m, "Eits, jangan sembarangan acak-acak sistem ya! Perintah ini cuma punya Paduka Ijel tercinta! 😠 Blweee 😜")
            return
        shell_cmd = m.text.replace(".exe", "").strip()
        if not shell_cmd:
            await bot.reply_to(m, "Perintah terminalnya mana yang mau dieksekusi, Paduka? 🫨")
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
            await bot.reply_to(m, f"❌ <b>Gagal mengeksekusi:</b> {html_escape(str(e))}", parse_mode="HTML")
