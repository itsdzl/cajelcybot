import json
import os

ROOMS_FILE = "anon_rooms.json"
QUEUE_FILE = "anon_queue.json"
MESSAGES_FILE = "anon_messages.json"


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def setup(bot, data):

    anon_data = data["anonymous_data"]

    rooms = load_json(ROOMS_FILE, {})
    queue = load_json(QUEUE_FILE, [])
    messages = load_json(MESSAGES_FILE, {})

    anon_data["rooms"] = rooms
    anon_data["queue"] = queue
    anon_data["messages"] = messages

    for gid in rooms:
        data["anonymous_active"][str(gid)] = True

    def save_all():
        save_json(ROOMS_FILE, rooms)
        save_json(QUEUE_FILE, queue)
        save_json(MESSAGES_FILE, messages)

    async def notify_disconnect(chat_id):
        try:
            await bot.send_message(
                chat_id,
                "partnernya pergi.\n\n"
                "cajel sempat mau ngejar...\n"
                "tapi cajel kan cuma bot 😔\n\n"
                "ketik /searchanon kalau mau cari temen baru."
            )
        except:
            pass

    @bot.message_handler(commands=["searchanon"])
    async def searchanon(m):

        if m.chat.type not in ["group", "supergroup"]:
            return

        chat_id = str(m.chat.id)

        if chat_id in rooms:
            await bot.reply_to(
                m,
                "eh masih ada partner kok.\n\n"
                "jangan cari yang lain dulu dong 😠\n\n"
                "/nextanon buat cari yang baru\n"
                "/stopanon buat udahan"
            )
            return

        if chat_id in queue:
            await bot.reply_to(
                m,
                "sabar yaa.\n\n"
                "cajel masih nyari partner buat grup ini."
            )
            return

        if len(queue) == 0:
            queue.append(chat_id)
            save_all()

            await bot.reply_to(
                m,
                "cajel lagi nyari grup lain...\n\n"
                "semoga ketemunya yang asik ya."
            )
            return

        partner = queue.pop(0)

        if str(partner) == str(chat_id):
            queue.append(chat_id)
            save_all()
            return

        rooms[chat_id] = partner
        rooms[partner] = chat_id

        data["anonymous_active"][chat_id] = True
        data["anonymous_active"][partner] = True

        msg1 = await bot.send_message(
            int(chat_id),
            "partner ketemu!\n\n"
            "balas pesan ini buat mulai ngobrol yaa."
        )

        msg2 = await bot.send_message(
            int(partner),
            "partner ketemu!\n\n"
            "balas pesan ini buat mulai ngobrol yaa."
        )

        messages[f"{chat_id}:{msg1.message_id}"] = True
        messages[f"{partner}:{msg2.message_id}"] = True

        save_all()
     
     @bot.message_handler(commands=["stopanon"])
    async def stopanon(m):

        if m.chat.type not in ["group", "supergroup"]:
            return

        chat_id = str(m.chat.id)

        if chat_id in queue:

            queue.remove(chat_id)
            save_all()

            await bot.reply_to(
                m,
                "okee.\n\ncajel batalin pencariannya."
            )
            return

        if chat_id not in rooms:

            await bot.reply_to(
                m,
                "lah emang lagi ga punya partner 😠"
            )
            return

        partner = rooms[chat_id]

        rooms.pop(chat_id, None)
        rooms.pop(partner, None)

        data["anonymous_active"].pop(chat_id, None)
        data["anonymous_active"].pop(partner, None)

        save_all()

        await bot.reply_to(
            m,
            "hubungan anonimnya udah cajel putusin 😔"
        )

        await notify_disconnect(int(partner))


    @bot.message_handler(commands=["nextanon"])
    async def nextanon(m):

        if m.chat.type not in ["group", "supergroup"]:
            return

        chat_id = str(m.chat.id)

        if chat_id not in rooms:

            await bot.reply_to(
                m,
                "belum ada partner nih.\n\n/searchanon dulu ya."
            )
            return

        partner = rooms[chat_id]

        rooms.pop(chat_id, None)
        rooms.pop(partner, None)

        data["anonymous_active"].pop(chat_id, None)
        data["anonymous_active"].pop(partner, None)

        queue.append(chat_id)

        save_all()

        try:
            await notify_disconnect(int(partner))
        except:
            pass

        await bot.reply_to(
            m,
            "cajel putusin dulu yang tadi.\n\nlagi nyari yang baru yaa..."
        )


    @bot.message_handler(commands=["anonstatus"])
    async def anonstatus(m):

        chat_id = str(m.chat.id)

        if chat_id in rooms:

            await bot.reply_to(
                m,
                "masih nyambung sama partner anon.\n\n"
                "/nextanon\n"
                "/stopanon"
            )

        elif chat_id in queue:

            await bot.reply_to(
                m,
                "lagi nunggu partner nih."
            )

        else:

            await bot.reply_to(
                m,
                "grup ini lagi jomblo.\n\n/searchanon dulu yuk."
            )


    @bot.message_handler(commands=["anonhelp"])
    async def anonhelp(m):

        await bot.reply_to(
            m,
            "cara pakai anonymous:\n\n"
            "1. /searchanon\n"
            "2. tunggu partner ketemu\n"
            "3. balas pesan starter dari cajel\n"
            "4. pesan bakal diterusin ke partner\n\n"
            "/nextanon\n"
            "/stopanon\n"
            "/anonstatus"
)

 @bot.message_handler(
        func=lambda m: (
            m.chat.type in ["group", "supergroup"]
            and not (m.text and m.text.startswith("/"))
        ),
        content_types=["text"]
    )
    async def anonymous_reply(m):

        if getattr(m.from_user, "is_bot", False):
            return

        chat_id = str(m.chat.id)

        if chat_id not in rooms:
            return

        if not m.reply_to_message:
            return

        replied_key = f"{chat_id}:{m.reply_to_message.message_id}"

        if replied_key not in messages:
            return

        partner = rooms.get(chat_id)

        if not partner:
            return

        try:

            sent = await bot.send_message(
                int(partner),
                "[ANON]\n\n"
                f"{m.text}\n\n"
                "balas pesan ini pakai reply yaa."
            )

            messages[f"{partner}:{sent.message_id}"] = True

            if len(messages) > 10000:

                newest = {}

                for k in list(messages.keys())[-3000:]:
                    newest[k] = True

                messages.clear()
                messages.update(newest)

            save_all()

        except Exception as e:
            print("[ANON ERROR]", e)

    print("✅ anonymous.py loaded")
