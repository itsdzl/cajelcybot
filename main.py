import os, sys, asyncio, shutil, importlib, json
import telebot
from telebot.async_telebot import AsyncTeleBot

# 1. Membaca Konfigurasi Bot
cfg = {}
with open("set", "r", encoding="utf8") as f:
    for line in f:
        if "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

TOKEN = cfg["token"]
BOTNAME = cfg["botname"]
NAME = cfg.get("name", "cajel")
OWNER_ID = int(cfg.get("OWNER_ID", 8278748114))
LOG_GROUP_ID = int(cfg.get("log_group_id", -1004362941881))

# 2. Mengumpulkan API Keys
API_KEYS = []
if "GEMINI_API_KEY" in cfg:
    for key in cfg["GEMINI_API_KEY"].split(","):
        clean_key = key.strip()
        if clean_key: API_KEYS.append(clean_key)

for i in range(2, 6):
    key_name = f"GEMINI_API_KEY_{i}"
    if key_name in cfg:
        clean_key = cfg[key_name].strip()
        if clean_key and clean_key not in API_KEYS: API_KEYS.append(clean_key)

# 3. Memuat Data KBBI
KBBI_DATA = {}
try:
    with open("dataKBBI.json", "r", encoding="utf-8") as f:
        KBBI_DATA = json.load(f)
        print("✅ Data KBBI berhasil dimuat.")
except Exception as e:
    print(f"❌ Gagal memuat dataKBBI.json: {e}")

bot = AsyncTeleBot(TOKEN)

# 4. Shared Data
shared_data = {
    "cfg": cfg, "botname": BOTNAME, "name": NAME, "owner_id": OWNER_ID,
    "log_group_id": LOG_GROUP_ID, "api_keys": API_KEYS, "kbbi_data": KBBI_DATA,
    "whisper_data": {}, "chat_memories": {}, "max_memory_length": 12
}

# Setup Yt-dlp
try:
    import yt_dlp
    shared_data["ytdlp_import"] = True
except ImportError:
    shared_data["ytdlp_import"] = False
shared_data["ytdlp_cli"] = shutil.which("yt-dlp") is not None
shared_data["ytdlp_available"] = shared_data["ytdlp_import"] or shared_data["ytdlp_cli"]

async def send_bot_log(text):
    if shared_data["log_group_id"] != 0:
        try:
            await bot.send_message(shared_data["log_group_id"], text, parse_mode="Markdown")
        except Exception as e:
            print(f"[LOG ERROR] Gagal mengirim log: {e}")

shared_data["send_log"] = send_bot_log

# 5. Plugin Loader
def load_plugins():
    plugin_folder = "cajel" 
    if not os.path.exists(plugin_folder): os.makedirs(plugin_folder)
    
    all_files = sorted(os.listdir(plugin_folder))
    for filename in all_files:
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"{plugin_folder}.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "setup"):
                    module.setup(bot, shared_data)
                    print(f"✅ Plugin [{filename}] dimuat.")
            except Exception as e:
                print(f"❌ Gagal memuat plugin [{filename}]: {e}")

# --- FUNGSI LOGGER OTOMATIS (Diletakkan di bawah agar tidak memblokir) ---
@bot.message_handler(func=lambda m: True)
async def track_users(m):
    try:
        json_path = "users.json"
        data = {}
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                try: data = json.load(f)
                except: data = {}
        
        if str(m.chat.id) not in data:
            data[str(m.chat.id)] = {"type": m.chat.type, "name": m.chat.title or m.chat.first_name}
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
    except Exception as e:
        print(f"DEBUG TRACK ERROR: {e}")

async def startup():
    load_plugins()
    print(f"🚀 Bot {shared_data['name']} aktif!")
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
    
