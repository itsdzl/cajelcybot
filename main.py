import os, sys, asyncio, shutil, importlib, json, traceback
import logging
import telebot
from telebot.async_telebot import AsyncTeleBot
from cajel import stats_db  # Diubah agar mengambil dari folder cajel

# ==========================================
# SYSTEM LOGGING CONFIGURATION
# ==========================================
# Konfigurasi agar semua error internal bot otomatis tercetak di terminal
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CajelBot")

# Matikan spam "Received new updates" dengan menaikkan level ke WARNING
# Ini akan menyembunyikan log INFO biasa tetapi tetap menampilkan ERROR jika bot crash
telebot.logger.setLevel(logging.WARNING)

# 1. Membaca Konfigurasi Bot
cfg = {}
try:
    with open("set", "r", encoding="utf8") as f:
        for line in f:
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
except Exception as e:
    logger.critical(f"Gagal membaca file konfigurasi 'set': {e}")
    sys.exit(1)

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
        logger.info("✅ Data KBBI berhasil dimuat ke memori.")
except Exception as e:
    logger.error(f"❌ Gagal memuat dataKBBI.json: {e}")

# Inisialisasi bot asinkronus
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
        "get_summary": stats_db.get_summary,
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
    "max_memory_length": 12,
    "anonymous_active": {},
    "anonymous_data": {
        "rooms": {},
        "queue": [],
        "messages": {}
    }
}

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
            logger.error(f"[LOG ERROR] Gagal mengirim log ke grup: {e}")

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
                    logger.info(f"✅ Plugin [{filename}] berhasil dimuat.")
            except Exception as e:
                logger.error(f"❌ Gagal memuat plugin [{filename}]: {e}")
                traceback.print_exc()

async def startup():
    load_plugins()
    logger.info(f"🚀 Bot {shared_data['name']} aktif!")
    await bot.infinity_polling()

if __name__ == "__main__":
    try:
        asyncio.run(startup())
    except KeyboardInterrupt:
        logger.info("Bot dihentikan secara manual (KeyboardInterrupt).")
    except Exception as e:
        logger.critical(f"Bot crash tidak terduga: {e}")
        traceback.print_exc()
    
