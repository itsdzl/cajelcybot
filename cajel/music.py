import os, asyncio, subprocess, json, shutil

def setup(bot, data):
    def download_youtube_audio(query):
        # Deteksi otomatis apakah yt-dlp terinstall di VPS Anda
        if not shutil.which("yt-dlp"): 
            return None, "yt-dlp belum diinstall di sistem VPS Anda."
            
        os.makedirs("downloads", exist_ok=True)
      
        # Bersihkan sisa file "song." lama agar tidak bentrok dengan pencarian baru
        for f in os.listdir("downloads"):
            if f.startswith("song."):
                try: os.remove(os.path.join("downloads", f))
                except: pass

        safe_title = "song"
        # Cek apakah sistem VPS Anda memiliki ffmpeg untuk konversi mp3
        has_ffmpeg = shutil.which("ffmpeg") is not None
        
        # Gunakan format output dinamis %(ext)s agar ekstensi diatur otomatis oleh yt-dlp
        output_template = f"downloads/{safe_title}.%(ext)s"
        
        cmd_dl = [
            "yt-dlp", 
            "-f", "bestaudio/best", 
            "--no-playlist", 
            "-o", output_template
        ]
        
        # Jika ada ffmpeg, paksa ekstrak menjadi format .mp3 murni
        if has_ffmpeg:
            cmd_dl.extend(["--extract-audio", "--audio-format", "mp3"])
            
        cmd_dl.append("ytsearch1:" + query)
        
        try:
            # Jalankan proses download
            result = subprocess.run(cmd_dl, capture_output=True, text=True)
            
            # Cari file hasil download secara dinamis di dalam folder
            downloaded_file = None
            for f in os.listdir("downloads"):
                if f.startswith(safe_title + "."):
                    downloaded_file = os.path.join("downloads", f)
                    break
            
            if downloaded_file and os.path.exists(downloaded_file): 
                return {
                    "path": downloaded_file, 
                    "title": query, 
                    "performer": "YouTube Download", 
                    "duration": 0
                }, None
                
            # Jika file tidak ada, kirim logs error stderr asli dari yt-dlp agar tahu masalahnya
            err_log = result.stderr.strip() if result.stderr else "File musik tidak ditemukan di server."
            return None, f"Gagal mengunduh. Detail: {err_log[:150]}"
            
        except Exception as e: 
            return None, str(e)
            
    def get_stats_db():
        return data.get("stats_db", {})

    @bot.message_handler(commands=['getmusic'])
    async def get_music(m):
        stats_db = get_stats_db()
        if stats_db and stats_db.get("is_banned") and stats_db["is_banned"](str(m.from_user.id)): 
            return
            
        # PERBAIKAN DI SINI: Memotong perintah menggunakan split berdasarkan spasi pertama
        # Contoh: "/getmusic@cajelcybot dumes" -> ["/getmusic@cajelcybot", "dumes"]
        # Contoh: "/getmusic@cajelcybot" -> ["/getmusic@cajelcybot"]
        parts = m.text.split(maxsplit=1)
        query = parts[1].strip() if len(parts) > 1 else ""
        
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
                await bot.send_audio(
                    chat_id=m.chat.id, 
                    audio=audio_file, 
                    title=music_data["title"], 
                    performer=music_data["performer"], 
                    duration=music_data["duration"], 
                    reply_to_message_id=m.message_id
                )
            
            # Hapus file lokal setelah sukses dikirim agar penyimpanan VPS Anda tidak penuh
            if os.path.exists(music_data["path"]): 
                os.remove(music_data["path"])
                
            await bot.delete_message(m.chat.id, status_msg.message_id)
            
        except Exception as e: 
            # Hapus file sisa jika terjadi error saat pengiriman
            if os.path.exists(music_data["path"]): 
                os.remove(music_data["path"])
            await bot.edit_message_text(f"❌ yahh cajel gagal ngirim audionya, error: {str(e)}", m.chat.id, status_msg.message_id)
