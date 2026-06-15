import os, sys, asyncio, shutil, importlib, json
import telebot
from telebot.async_telebot import AsyncTeleBot
from cajel import stats_db  # Diubah agar mengambil dari folder cajel

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
LOG_GROUP_ID = int(cfg.get("LOG_GROUP_ID", -1004362941881))

# 2. Mengumpulkan API Keys
API_KEYS = []
if "GEMINI_API_KEY" in cfg:
    for key in cfg["GEMINI_API_KEY"].split(","):
        clean_key = key.strip()
        if clean_key: API_KEYS.append(clean_key)

# 3. Memuat Data KBBI ke Memori
KBBI_DATA = {}
try:
    with open("dataKBBI.json", "r", encoding="utf-8") as f:
        KBBI_DATA = json.load(f)
        print("✅ Data KBBI berhasil dimuat ke memori.")
except Exception as e:
    print(f"❌ Gagal memuat dataKBBI.json: {e}")

bot = AsyncTeleBot(TOKEN)

# 4. Shared Data
shared_data = {
    "cfg": cfg,
    "botname": BOTNAME,
    "name": NAME,
    "owner_id": OWNER_ID,
    "log_group_id": LOG_GROUP_ID,
    "stats_db": {
        "update_chat": stats_db.update_chat_data,
        "get_summary": stats_db.get_summary
        "get_all_users": stats_db.get_all_users,
        "ban_user": stats_db.ban_user,
        "unban_user": stats_db.unban_user,
        "is_banned": stats_db.is_banned,
        "get_banlist": stats_db.get_banlist,
    },
    "api_keys": API_KEYS,
    "kbbi_data": KBBI_DATA,
    "whisper_data": {},
    "chat_memories": {},
    "max_memory_length": 12
}

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
    prioritas_db = ["games_db.py", "stats_db.py"]
    for db_file in prioritas_db:
        if db_file in all_files:
            all_files.remove(db_file)
            all_files.insert(0, db_file)

        if "ai_chat.py" in all_files:
            all_files.remove("ai_chat.py")
            all_files.append("ai_chat.py")

    for filename in all_files:
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"{plugin_folder}.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "setup"):
                    module.setup(bot, shared_data)
                    print(f"✅ Plugin [{filename}] berhasil dimuat.")
            except Exception as e:
                print(f"❌ Gagal memuat plugin [{filename}]: {e}")
async def startup():
    load_plugins()
    print(f"🚀 Bot {shared_data['name']} aktif!")
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
    
