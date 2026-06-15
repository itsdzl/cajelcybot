import os, asyncio, subprocess, json

def setup(bot, data):
    def download_youtube_audio(query):
        if not data["ytdlp_available"]: return None, "ytdlp belum diinstall"
        os.makedirs("downloads", exist_ok=True)
      
        try:
            safe_title = "song"
            filename = f"downloads/{safe_title}.mp3"
            cmd_dl = ["yt-dlp", "-f", "bestaudio/best", "--no-playlist", "-o", filename, "ytsearch1:" + query]
            subprocess.run(cmd_dl, capture_output=True, text=True)
            if os.path.exists(filename): 
                return {"path": filename, "title": query, "performer": "YouTube Download", "duration": 0}, None
            return None, "File musik tidak ditemukan."
        except Exception as e: 
            return None, str(e)
            
    def get_stats_db():
        return data.get("stats_db", {})

    @bot.message_handler(commands=['getmusic'])
    async def get_music(m):
        stats_db = get_stats_db()
        if stats_db and stats_db.get("is_banned") and stats_db["is_banned"](str(m.from_user.id)): 
            return
        query = m.text.replace("/getmusic", "").strip()
        if not query:
            await bot.reply_to(m, "Masukin judul lagu atau penyanyinya juga dong Contoh: `/getmusic dumes` 😠")
            return
        await bot.send_chat_action(m.chat.id, 'upload_voice')
        status_msg = await bot.reply_to(m, "sabar ya beb, cajel lagi cariin lagunya... 🎧")
        loop = asyncio.get_event_loop()
        music_data, err = await loop.run_in_executor(None, download_youtube_audio, query)
        if err:
            await bot.edit_message_text(f"❌ yah gagal download lagunya 😞, error: {err}", m.chat.id, status_msg.message_id)
            return
        try:
            with open(music_data["path"], "rb") as audio_file:
                await bot.send_audio(chat_id=m.chat.id, audio=audio_file, title=music_data["title"], performer=music_data["performer"], duration=music_data["duration"], reply_to_message_id=m.message_id)
            if os.path.exists(music_data["path"]): os.remove(music_data["path"])
            await bot.delete_message(m.chat.id, status_msg.message_id)
        except Exception as e: 
            await bot.edit_message_text(f"❌ yahh cajel gagal ngirim audionya, error: {str(e)}", m.chat.id, status_msg.message_id)
