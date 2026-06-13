import os
import json

DB_FILE = "cajel_players.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def get_or_create_player(user_id, username="Pemain"):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"username": username, "poin": 0, "xp": 0, "level": 1}
        save_db(db)
    return db[uid]

def add_rewards(user_id, username, poin_add, xp_add):
    db = load_db()
    uid = str(user_id)
    if uid not in db: get_or_create_player(user_id, username); db = load_db()
    
    db[uid].update({"username": username, "poin": db[uid]["poin"] + poin_add, "xp": db[uid]["xp"] + xp_add})
    
    # Logic level up
    xp_needed = db[uid]["level"] * 100
    leveled_up = False
    while db[uid]["xp"] >= xp_needed:
        db[uid]["xp"] -= xp_needed
        db[uid]["level"] += 1
        xp_needed = db[uid]["level"] * 100
        leveled_up = True
    save_db(db)
    return db[uid], leveled_up

def get_leaderboard():
    db = load_db()
    return sorted(db.items(), key=lambda x: (x[1]["level"], x[1]["poin"]), reverse=True)[:10]

def setup(bot, data):
    # Didaftarkan ke shared_data agar bisa diakses file lain TANPA import
    data["games_db"] = {
        "add_rewards": add_rewards,
        "get_leaderboard": get_leaderboard,
        "get_player": get_or_create_player
    }
    
