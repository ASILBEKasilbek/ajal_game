# database.py
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from config import DB_FILE

# ------------------- INIT DB -------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language TEXT DEFAULT 'uz',
            channel TEXT DEFAULT 'Nomalum',
            user_group TEXT DEFAULT 'Nomalum',
            clan_name TEXT DEFAULT 'Yo‘q',
            clan_role TEXT DEFAULT 'Azo',
            clan_level INTEGER DEFAULT 0,
            clan_xp INTEGER DEFAULT 0,
            clan_xp_next INTEGER DEFAULT 800,
            clan_rank INTEGER DEFAULT 0,
            total_clans INTEGER DEFAULT 0,
            clan_channel TEXT DEFAULT 'Nomalum',
            clan_group TEXT DEFAULT 'Nomalum',
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            rank TEXT DEFAULT 'D',
            olmos INTEGER DEFAULT 0,
            balls INTEGER DEFAULT 0,
            popularity INTEGER DEFAULT 0,
            popularity_today INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            total_games INTEGER DEFAULT 0,
            last_game_result TEXT,
            last_game_date TEXT,
            bio TEXT DEFAULT 'Bio yozilmagan',
            days_in_game INTEGER DEFAULT 0,
            last_active TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))

              
        )
    ''')

    # Games (JSON players)
    c.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE,
            status TEXT DEFAULT 'waiting',
            players TEXT,
            round_number INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    # Clans
    c.execute('''
        CREATE TABLE IF NOT EXISTS clans (
            clan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            clan_name TEXT UNIQUE,
            clan_description TEXT,
            creator_id INTEGER,
            members_count INTEGER DEFAULT 1,
            clan_level INTEGER DEFAULT 1,
            clan_xp INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tulov_kanallar(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              kanal_id INTEGER UNIQUE)
              ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS majburiy_kanallar(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              kanal_id INTEGER UNIQUE,
              kanal_link TEXT)
              ''')

    
    conn.commit()
    conn.close()

# ------------------- USER -------------------
def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_user(user: Dict[str, Any]):
    user['last_active'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO users
        (user_id, username, first_name, last_name, language,channel,user_group,
         clan_name, clan_role, clan_level, clan_xp, clan_xp_next, clan_rank, total_clans,
         clan_channel, clan_group,
         level, xp, rank, olmos, balls, popularity, popularity_today,
         wins, total_games, last_game_result, last_game_date, bio, days_in_game, last_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user['user_id'], user.get('username'), user.get('first_name'), user.get('last_name'),
        user.get('language', 'uz'), user.get('clan_name', 'Yo‘q'), user.get('clan_role', 'Azo'),
        user.get('clan_level', 0), user.get('clan_xp', 0), user.get('clan_xp_next', 800),
        user.get('clan_rank', 0), user.get('total_clans', 0), user.get('clan_channel', 'Nomalum'),
        user.get('clan_group', 'Nomalum'), user.get('channel', 'Nomalum'), user.get('user_group', 'Nomalum'),
        user.get('level', 1), user.get('xp', 0), user.get('rank', 'D'),
        user.get('olmos', 0), user.get('balls', 0), user.get('popularity', 0), user.get('popularity_today', 0),
        user.get('wins', 0), user.get('total_games', 0), user.get('last_game_result'),
        user.get('last_game_date'), user.get('bio', 'Bio yozilmagan'), user.get('days_in_game', 0),
        user['last_active']
    ))
    conn.commit()
    conn.close()

# ------------------- OLMOS / BALLS -------------------
def add_olmos(user_id: int, amount: int) -> bool:
    user = get_user(user_id)
    if not user: return False
    user['olmos'] = (user['olmos'] or 0) + amount
    save_user(user)
    return True

def remove_olmos(user_id: int, amount: int) -> bool:
    user = get_user(user_id)
    if not user or (user['olmos'] or 0) < amount: return False
    user['olmos'] -= amount
    save_user(user)
    return True

def add_balls(user_id: int, amount: int) -> bool:
    user = get_user(user_id)
    if not user: return False
    user['balls'] = (user['balls'] or 0) + amount
    save_user(user)
    return True

# ------------------- GAME STATE -------------------
def save_game_state(chat_id: int, players: Dict, round_number: int, status: str = "running"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    players_json = json.dumps(players, ensure_ascii=False)
    c.execute('INSERT OR REPLACE INTO games (chat_id, players, round_number, status) VALUES (?, ?, ?, ?)',
              (chat_id, players_json, round_number, status))
    conn.commit()
    conn.close()

def get_game_state(chat_id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM games WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row: return None
    game = dict(zip([d[0] for d in c.description], row))
    game['players'] = json.loads(game['players']) if game['players'] else {}
    return game

def delete_game_state(chat_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM games WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# ------------------- CLAN -------------------
def create_clan(clan_name: str, creator_id: int, description: str = "") -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO clans (clan_name, clan_description, creator_id) VALUES (?, ?, ?)',
                  (clan_name, description, creator_id))
        conn.commit()
        conn.close()
        user = get_user(creator_id)
        if user:
            user['clan_name'] = clan_name
            user['clan_role'] = 'Lider'
            save_user(user)
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_clan(clan_name: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE clan_name = ?", (clan_name,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def join_clan(user_id: int, clan_name: str) -> bool:
    clan = get_clan(clan_name)
    user = get_user(user_id)
    if not clan or not user or user['clan_name'] != 'Yo‘q':
        return False
    user['clan_name'] = clan_name
    user['clan_role'] = 'Azo'
    save_user(user)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE clans SET members_count = members_count + 1 WHERE clan_name = ?", (clan_name,))
    conn.commit()
    conn.close()
    return True