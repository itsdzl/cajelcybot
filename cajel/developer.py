import sys, os, asyncio, traceback, random, json, aiohttp

def setup(bot, data):
    OWNER_ID = data["owner_id"]
    BOTNAME = data["botname"]
    NAME = data["name"]

    # 1. Shutdown & Restart
    @bot.message_handler(func=lambda m: m.text and m.text.lower() in ["syuh", ".restart"])
    async def power_control(m):
        if m.from_user.id != OWNER_ID: return
        if "syuh" in m.text:
            await bot.reply_to(m, "🛑 Mematikan bot...")
            await data["send_log"](f"🛑 *[OFFLINE]* Bot dimatikan oleh owner.")
            os._exit(0)
        else:
            await bot.reply_to(m, "🔄 Restarting bot...")
            await data["send_log"](f"🔄 *[RESTART]* Bot sedang dimulai ulang.")
            os.execv(sys.executable, ['python'] + sys.argv)

    # 2. Detail User (.hu) - Mendukung Reply, @username, dan ID
    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".hu"))
    async def get_user_info(m):
        if m.from_user.id != OWNER_ID: return
        args = m.text.replace(".hu", "").strip()
        target_user = None
        try:
            if m.reply_to_message: target_user = m.reply_to_message.from_user
            elif args.startswith("@") or args.isdigit():
                target_user = await bot.get_chat(args if args.startswith("@") else int(args))
            else:
                await bot.reply_to(m, "⚠️ Format: Reply pesan user, `.hu @username`, atau `.hu <user_id>`")
                return
            info = (f"👤 Detail Pengguna\n━━━━━━━━━━━━━━\nNama: {getattr(target_user, 'first_name', 'N/A')}\n"
                    f"User ID: `{target_user.id}`\nUsername: @{getattr(target_user, 'username', 'none')}")
            await bot.reply_to(m, info, parse_mode="Markdown")
        except Exception as e: await bot.reply_to(m, f"Error: {str(e)}")

    # 3. Update Bot (Git Pull + Restart)
    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".update"))
    async def update_bot(m):
        if m.from_user.id != OWNER_ID: return
        await bot.reply_to(m, "⏳ Sedang melakukan update dari Git...")
        process = await asyncio.create_subprocess_shell("git pull", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        await bot.reply_to(m, "✅ Update selesai. Restarting bot...")
        os.execv(sys.executable, ['python'] + sys.argv)

     # 4. Broadcast (PC/Grup berdasarkan users.json)
     @bot.message_handler(func=lambda m: m.text and m.text.startswith(".bc"))
     async def broadcast_msg(m):
        if m.from_user.id != OWNER_ID: return
        msg = m.text.replace(".bc", "").strip()
        if not msg:
            await bot.reply_to(m, "⚠️ Masukkan pesan broadcast!")
            return
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
            count = 0
            for chat_id in users.keys():
                try:
                    await bot.send_message(chat_id, f"📢 Broadcast:\n\n{msg}", parse_mode="Markdown")
                    count += 1
                    await asyncio.sleep(0.5)
                except: continue
            await bot.reply_to(m, f"✅ Berhasil broadcast ke {count} chat.")
        except Exception as e: await bot.reply_to(m, f"❌ Error: {e}")

     # 5. Statistik Bot
     @bot.message_handler(func=lambda m: m.text and m.text.startswith(".stats"))
     async def get_stats(m):
        if m.from_user.id != OWNER_ID: return
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
            total, private, groups = len(users), sum(1 for u in users.values() if u.get("type") == "private"), sum(1 for u in users.values() if u.get("type") in ["group", "supergroup"])
            await bot.reply_to(m, f"📊 Statistik\n━━━━━━━━━━━━━━\n👥 Total: `{total}`\n👤 Private: `{private}`\n🏘️ Grup: `{groups}`", parse_mode="Markdown")
        except: await bot.reply_to(m, "⚠️ Data `users.json` belum tersedia.")

     # 6. Eval
     @bot.message_handler(func=lambda m: m.text and m.text.startswith(".eval"))
     async def eval_code(m):
        if m.from_user.id != OWNER_ID: return
        cmd = m.text.replace(".eval", "").strip()
        local_vars = {"bot": bot, "m": m, "asyncio": asyncio, "os": os, "data": data}
        try:
            res = await eval(cmd, globals(), local_vars) if cmd.startswith("await ") else eval(cmd, globals(), local_vars)
            await bot.reply_to(m, f"📤 Output:\n<code>{res}</code>", parse_mode="HTML")
        except Exception as e: await bot.reply_to(m, f"⚠️ Error:\n<pre>{traceback.format_exc()}</pre>", parse_mode="HTML")

     # 7. Execute Shell
     @bot.message_handler(func=lambda m: m.text and m.text.startswith(".exe"))
     async def execute_shell(m):
        if m.from_user.id != OWNER_ID: return
        cmd = m.text.replace(".exe", "").strip()
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        out = stdout.decode().strip() or stderr.decode().strip()
        await bot.reply_to(m, f"📤 Output:\n<pre>{out[:3000]}</pre>", parse_mode="HTML")
        
