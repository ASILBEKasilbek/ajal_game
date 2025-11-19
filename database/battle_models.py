import sqlite3
import json
from config import DB_FILE


def get_cost(amount: int) -> int:
    prices = {
        1: 0,
        10: 10,
        50: 35,
        100: 70,
        500: 450,
        1000: 900,
        5000: 4200,
        10000: 7500
    }
    return prices.get(amount, 0)

def get_name(user_id: int) -> str:
    if user_id == "bot":
        return "🤖 Bot"

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT first_name, username FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    conn.close()

    if row is None:
        return "Noma'lum"

    first_name, username = row
    if first_name:
        return first_name
    if username:
        return f"@{username}"

    return "Noma'lum"

def get_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("SELECT olmos FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    conn.close()

    return row[0] if row else 0

def update_balance(user_id: int, new_balance: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("UPDATE users SET olmos=? WHERE user_id=?", (new_balance, user_id))

    conn.commit()
    conn.close()
    



def save_vote(battle_id: int, pair_id: int, user_id: int, amount: int, target_player: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT votes1, votes2 FROM battle_pairs WHERE id=?", (pair_id,))
    votes1, votes2 = c.fetchone()

    if target_player == c.execute("SELECT player1 FROM battle_pairs WHERE id=?", (pair_id,)).fetchone()[0]:
        votes1 += amount
    else:
        votes2 += amount

    # DBga update
    c.execute("UPDATE battle_pairs SET votes1=?, votes2=? WHERE id=?", (votes1, votes2, pair_id))
    conn.commit()
    conn.close()



def get_name_battle(user_id):
    # DB dan user_id bo'yicha ismini oladi
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT first_name FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "Noma'lum"
