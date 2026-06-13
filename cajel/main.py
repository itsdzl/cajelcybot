import os, sys, asyncio, shutil, importlib
import telebot
from telebot.async_telebot import AsyncTeleBot

cfg = {}
with open("set", "r", encoding="utf8") as f:
    for line in f:
        if "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

TOKEN = cfg["token"]
BOTNAME = cfg["botname"]
NAME = cfg.get("name", "cajel")
OWNER_ID = 8278748114
LOG_GROUP_ID = int(cfg.get("log_group_id", 0))

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

bot = AsyncTeleBot(TOKEN)

shared_data = {
    "cfg": cfg,
    "botname": BOTNAME,
    "name": NAME,
    "owner_id": OWNER_ID,
    "log_group_id": LOG_GROUP_ID,
    "api_keys": API_KEYS,
    "whisper_data": {},
    "chat_memories": {},
    "max_memory_length": 12
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
            print(f"[LOG ERROR] Gagal mengirim log: {e}")

shared_data["send_log"] = send_bot_log

def load_plugins():
    """Sistem Pemuat Otomatis disesuaikan ke folder cajel"""
    plugin_folder = "cajel"  
    if not os.path.exists(plugin_folder):
        os.makedirs(plugin_folder)
        
    init_path = os.path.join(plugin_folder, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f: pass

    for filename in os.listdir(plugin_folder):
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
    me = await bot.get_me()
    load_plugins()

    startup_msg = (
        f"🚀 *[ONLINE]* Bot *{shared_data['name']}* (@{me.username}) berhasil aktif!\n"
        f"• Sistem Rotasi: `{len(shared_data['api_keys'])}` API Key terdeteksi.\n"
        f"• Fitur: Modular Folder System (*Aktif*)."
    )
    print(startup_msg)
    await send_bot_log(startup_msg)
    await bot.infinity_polling()

if __name__ == "__main__":
    asyncio.run(startup())
        
