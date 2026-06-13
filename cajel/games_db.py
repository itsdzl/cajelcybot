import os
import json

DB_FILE = "cajel_players.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

def get_or_create_player(user_id, username="Pemain"):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "username": username,
            "poin": 0,
            "xp": 0,
            "level": 1
        }
        save_db(db)
    return db[uid]

def add_rewards(user_id, username, poin_add, xp_add):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        get_or_create_player(user_id, username)
        db = load_db()
        
    db[uid]["username"] = username  # Update username terbaru
    db[uid]["poin"] += poin_add
    db[uid]["xp"] += xp_add
    
    # Rumus naik level simpel: Level * 100 XP
    current_level = db[uid]["level"]
    xp_needed = current_level * 100
    leveled_up = False
    
    while db[uid]["xp"] >= xp_needed:
        db[uid]["xp"] -= xp_needed
        db[uid]["level"] += 1
        current_level = db[uid]["level"]
        xp_needed = current_level * 100
        leveled_up = True
        
    save_db(db)
    return db[uid], leveled_up

def get_leaderboard():
    db = load_db()
    # Urutkan berdasarkan level terbanyak, lalu poin terbanyak
    sorted_players = sorted(db.items(), key=lambda x: (x[1]["level"], x[1]["poin"]), reverse=True)
    return sorted_players[:10] # Ambil top 10

def setup(bot, data):
    # Menyediakan fungsi database agar bisa diakses oleh main.py / plugin lain jika butuh
    data["games_db"] = {
        "add_rewards": add_rewards,
        "get_leaderboard": get_leaderboard,
        "get_player": get_or_create_player
    }
  
