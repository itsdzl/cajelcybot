
# Skeleton rewritten bot for Python 3.10+
# Reads settings including GEMINI_API_KEY by key=value.
# Supports:
# - @bot mention replies
# - random "cajel" replies
# - startup greeting
# - Gemini via google-genai
#
# NOTE: Fill in further custom behaviour as needed.

import random, asyncio
from telebot.async_telebot import AsyncTeleBot

cfg={}
with open("settings","r",encoding="utf8") as f:
    for line in f:
        if "=" in line:
            k,v=line.split("=",1)
            cfg[k.strip()]=v.strip()

TOKEN=cfg["token"]
BOTNAME=cfg["botname"]
NAME=cfg.get("name","cajel")
bot=AsyncTeleBot(TOKEN)

RANDOM_CAJEL=[
"Hah? manggil aku? 🤭",
"Iya? Ada apa?",
"Hehe hadir!",
"Cajel online~"
]

try:
    from google import genai
    client=genai.Client(api_key=cfg["GEMINI_API_KEY"])
except:
    client=None

@bot.message_handler(func=lambda m: True)
async def allmsg(m):
    txt=m.text or ""
    low=txt.lower()

    if low=="cajel":
        await bot.reply_to(m,random.choice(RANDOM_CAJEL))
        return

    if BOTNAME.lower() in low:
        q=txt.replace(BOTNAME,"").strip()
        if not q:
            q="halo"
        if client:
            try:
                r=client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"Kamu adalah {NAME}, bot Telegram lucu. Jawab singkat bahasa Indonesia. {q}"
                )
                await bot.reply_to(m,r.text)
                return
            except Exception as e:
                await bot.reply_to(m,"Gemini error: "+str(e))
                return
        await bot.reply_to(m,"Gemini belum aktif.")

async def startup():
    me=await bot.get_me()
    print(me.username)
    await bot.infinity_polling()

if __name__=="__main__":
    asyncio.run(startup())
