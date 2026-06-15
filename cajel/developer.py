import sys, os, asyncio, traceback, json

def setup(bot, data):
    OWNER_ID = data["owner_id"]
    
    # Fungsi pembantu untuk mengakses stats_db dari shared_data
    def get_stats_db():
        return data.get("stats_db", {})

    # 1. Shutdown & Restart
    @bot.message_handler(func=lambda m: m.text and m.text.lower() in ["syuh", ".restart"])
    async def power_control(m):
        if m.from_user.id != OWNER_ID: return
        if "syuh" in m.text:
            await bot.reply_to(m, "🛑 Mematikan bot...")
            await data["send_log"](f"🛑 *[OFFLINE]* Bot dimatikan oleh Owner.")
            os._exit(0)
        else:
            await bot.reply_to(m, "🔄 Restarting bot...")
            await data["send_log"](f"🔄 *[RESTART]* Bot sedang dimulai ulang.")
            os.execv(sys.executable, ['python'] + sys.argv)

    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".hu"))
    async def get_user_info(m):
        if m.from_user.id != OWNER_ID: return
        args = m.text.replace(".hu", "").strip()
        target_user = None
        
        try:
            if m.reply_to_message:
                target_user = m.reply_to_message.from_user
            elif args:
                # Jika user memasukkan @username, kita hapus tanda @ agar menjadi username murni
                clean_args = args.replace("@", "")
                
                # Jika input adalah ID (angka), ubah ke integer
                if clean_args.isdigit():
                    target_user = await bot.get_chat(int(clean_args))
                else:
                    # Mencoba mencari user berdasarkan username
                    target_user = await bot.get_chat(clean_args)
            else:
                await bot.reply_to(m, "⚠️ Format: Reply pesan user, `.hu @username`, atau `.hu <user_id>`")
                return
            
            # Format pesan (tanpa parse_mode untuk menghindari error Markdown)
            info = (f"👤 Detail Pengguna\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"Nama: {getattr(target_user, 'first_name', 'N/A')}\n"
                    f"User ID: {target_user.id}\n"
                    f"Username: @{getattr(target_user, 'username', 'Tidak ada')}")
            
            await bot.reply_to(m, info)
            
        except Exception as e:
            # Memberikan pesan error yang lebih jelas jika gagal
            await bot.reply_to(m, f"❌ Error: {str(e)}\nPastikan username benar atau bot memiliki akses.")

    # 3. Update Bot
    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".update"))
    async def update_bot(m):
        if m.from_user.id != OWNER_ID: return
        await bot.reply_to(m, "⏳ Sedang melakukan update dari Git...")
        process = await asyncio.create_subprocess_shell("git pull", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        await bot.reply_to(m, "✅ Update selesai. Restarting bot...")
        os.execv(sys.executable, ['python'] + sys.argv)

    # 4. Broadcast (Menggunakan stats.json via stats_db)
    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".bc"))
    async def broadcast_msg(m):
        if m.from_user.id != OWNER_ID: return
        msg = m.text.replace(".bc", "").strip()
        if not msg:
            await bot.reply_to(m, "⚠️ Masukkan pesan broadcast!")
            return
        
        try:
            stats = get_stats_db()
            users = stats["get_all_users"]()
            
            count = 0

            for chat_id in users.keys():
                try:
                    await bot.send_message(chat_id, f"📢 **Broadcast:**\n\n{msg}", parse_mode="Markdown")
                    count += 1
                    await asyncio.sleep(0.5)
                except: continue
            await bot.reply_to(m, f"✅ Berhasil broadcast ke {count} chat.")
        except Exception as e: await bot.reply_to(m, f"❌ Error: {e}")

    # 5. Statistik
    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".stats"))
    async def get_stats(m):
        if m.from_user.id != OWNER_ID: return
        sdb = get_stats_db()
        if not sdb:
            await bot.reply_to(m, "⚠️ Data statistik belum dimuat.")
            return
        
        stats = sdb["get_summary"]()
        await bot.reply_to(m, f"📊 **Statistik Bot**\n━━━━━━━━━━━━━━\n👥 Total: `{stats['total']}`\n👤 Private: `{stats['private']}`\n🏘️ Grup: `{stats['groups']}`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".ban "))
    async def ban_user_cmd(m):
        if m.from_user.id != OWNER_ID:
            return

        try:
            # Mengambil ID user dari argumen perintah (.ban 123456)
            user_id = int(m.text.split()[1])
            stats = get_stats_db()

            # Menjalankan fungsi ban_user dari database
            if stats and stats.get("ban_user") and stats["ban_user"](user_id):
                await bot.reply_to(m, f"✅ User `{user_id}` berhasil diban.")
            else:
                await bot.reply_to(m, "❌ Gagal memban. User tidak ditemukan di database.")
        except:
            await bot.reply_to(m, "⚠️ Format salah! Gunakan: `.ban <user_id>`")


    @bot.message_handler(func=lambda m: m.text and m.text.startswith(".unban "))
    async def unban_user_cmd(m):
        if m.from_user.id != OWNER_ID:
            return

        try:
            user_id = int(m.text.split()[1])
            stats = get_stats_db()

            # Menjalankan fungsi unban_user dari database
            if stats and stats.get("unban_user") and stats["unban_user"](user_id):
                await bot.reply_to(m, f"✅ User `{user_id}` berhasil di-unban.")
            else:
                await bot.reply_to(m, "❌ Gagal meng-unban. User tidak ditemukan di database.")
        except:
            await bot.reply_to(m, "⚠️ Format salah! Gunakan: `.unban <user_id>`")


    @bot.message_handler(func=lambda m: m.text == ".banlist")
    async def banlist_cmd(m):
        if m.from_user.id != OWNER_ID:
            return

        stats = get_stats_db()
        if not stats or not stats.get("get_banlist"):
            await bot.reply_to(m, "❌ Fitur database tidak tersedia.")
            return

        # Mengambil list user yang sedang diban
        banned_users = stats["get_banlist"]()

        if not banned_users:
            await bot.reply_to(m, "✅ Bersih! Tidak ada user yang sedang diban.")
            return

        text = "🚫 *Daftar User Diban:*\n\n"
        for uid, info in banned_users.items():
            name = info.get("name", "Unknown")
            text += f"👤 {name} \n└ ID: `{uid}`\n"

        await bot.reply_to(m, text, parse_mode="Markdown")

    
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
            
