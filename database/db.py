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
            username TEXT UNIQUE,
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
            clan_group TEXT DEFAULT 'Nomalum',
            clan_channel TEXT DEFAULT 'Nomalum',
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
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS kanallar(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kanal_link TEXT NOT NULL,
            kanal_name TEXT NOT NULL
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS guruhlar(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            group_link TEXT NOT NULL
        );""")
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS battle_1vs1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheduled_time TEXT,
            status TEXT DEFAULT 'pending',      -- pending / started / finished
            players TEXT DEFAULT '[]',          -- JSON list -> [...user_id...]
            created_at TEXT DEFAULT (datetime('now'))
        );""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS battle_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id INTEGER,
            player1 INTEGER,
            player2 INTEGER,
            votes1 INTEGER DEFAULT 0,
            votes2 INTEGER DEFAULT 0,
            winner INTEGER DEFAULT NULL
        );""")
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            battle_id INTEGER,
            pair_id INTEGER,
            voter_id INTEGER,
            for_player INTEGER,
            amount INTEGER
        );""")
            
    

        
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


def get_all_guruhlar():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM guruhlar ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_guruh(group_name: str, group_link: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO guruhlar (group_name, group_link) VALUES (?, ?)", (group_name, group_link))
    conn.commit()
    conn.close()

def delete_guruh(group_name: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM guruhlar WHERE group_name=?", (group_name,))
    conn.commit()
    conn.close()

def get_all_tulov_kanallar():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM tulov_kanallar ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_tulov_kanal(kanal_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM tulov_kanallar WHERE kanal_id=?", (kanal_id,))
    if not c.fetchone():
        c.execute("INSERT INTO tulov_kanallar (kanal_id) VALUES (?)", (kanal_id,))
    conn.commit()
    conn.close()

def delete_tulov_kanal(kanal_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tulov_kanallar WHERE kanal_id=?", (kanal_id,))
    conn.commit()
    conn.close()

def update_user_field(user_id: int, field: str, value):
    # SQL Injection prevention
    allowed_fields = ['username', 'bio', 'channel', 'user_group', 'clan_name']
    if field not in allowed_fields:
        raise ValueError(f"Field '{field}' not allowed for update")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, user_id))
    conn.commit()
    conn.close()

def join_clan(user_id: int, clan_name: str) -> bool:
    clan = get_clan(clan_name)
    user = get_user(user_id)

    if not clan or not user:
        return False

    # TO‘G‘RI: Agar allaqachon shu klanda bo‘lsa — ruxsat berilmaydi
    if user['clan_name'] == clan_name:
        return False

    # OLDINGI KLANdan chiqish (agar bo‘lsa)
    old_clan_name = user['clan_name']
    if old_clan_name != 'Yo‘q':
        # Eski klandan a'zolar sonini kamaytirish
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE clans SET members_count = members_count - 1 WHERE clan_name = ?", (old_clan_name,))
        conn.commit()
        conn.close()

    # YANGI klanda qo‘shish
    user['clan_name'] = clan_name
    user['clan_role'] = 'Azo'
    save_user(user)

    # Yangi klanda a'zolar sonini oshirish
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE clans SET members_count = members_count + 1 WHERE clan_name = ?", (clan_name,))
    conn.commit()
    conn.close()

    return True

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
def create_clan(clan_name, creator_id, clan_description, clan_group, clan_channel):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Klan nomi mavjudligini tekshirish
    c.execute("SELECT clan_name FROM clans WHERE clan_name = ?", (clan_name,))
    if c.fetchone():
        conn.close()
        return False

    # Yangi klan yaratish
    c.execute('''
    INSERT INTO clans 
    (clan_name, clan_description, creator_id, clan_group, clan_channel)
    VALUES (?, ?, ?, ?, ?)
    ''', (clan_name, clan_description, creator_id, clan_group, clan_channel))
    
    conn.commit()
    conn.close()
    return True

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
    user['clan_channel'] = clan['clan_channel']
    user['clan_group'] = clan['clan_group']
    save_user(user)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE clans SET members_count = members_count + 1 WHERE clan_name = ?", (clan_name,))
    conn.commit()
    conn.close()
    return True


def fetch_all(query: str, params: tuple = ()) -> list:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def execute_query(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()


def add_row(table: str, column_values: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    columns = ', '.join(column_values.keys())
    placeholders = ', '.join(['?'] * len(column_values))
    values = tuple(column_values.values())
    c.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()

def show_clan(clan_name: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM clans WHERE clan_name = ?", (clan_name,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

# def all_clans() -> list:
#     conn = sqlite3.connect(DB_FILE)
#     conn.row_factory = sqlite3.Row
#     c = conn.cursor()
#     c.execute("SELECT * FROM clans")
#     rows = c.fetchall()
#     conn.close()
#     return [dict(row) for row in rows]

def all_clans() -> list:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT * FROM clans
        ORDER BY clan_xp DESC
        LIMIT 10
    """)

    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# Yangi funksiyalar

def leave_clan(user_id: int) -> bool:
    user = get_user(user_id)
    if not user or user['clan_name'] == 'Yo‘q':
        return False

    clan_name = user['clan_name']
    user['clan_name'] = 'Yo‘q'
    user['clan_role'] = 'Azo'
    user['clan_channel'] = 'Nomalum'
    user['clan_group'] = 'Nomalum'
    save_user(user)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE clans SET members_count = members_count - 1 WHERE clan_name = ?", (clan_name,))
    conn.commit()
    conn.close()

    return True

def set_clan_join_type(clan_name: str, join_type: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE clans SET join_type = ? WHERE clan_name = ?", (join_type, clan_name))
    conn.commit()
    conn.close()

def get_clan_join_type(clan_name: str) -> str:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT join_type FROM clans WHERE clan_name = ?", (clan_name,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "open"

def add_join_request(clan_name: str, user_id: int, username: str, first_name: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO join_requests (clan_name, user_id, username, first_name) VALUES (?, ?, ?, ?)",
              (clan_name, user_id, username, first_name))
    conn.commit()
    conn.close()

def get_pending_requests(clan_name: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM join_requests WHERE clan_name = ? ORDER BY created_at", (clan_name,))
    rows = c.fetchall()
    conn.close()
    return [dict(zip([col[0] for col in c.description], row)) for row in rows]

def approve_request(clan_name: str, user_id: int):
    join_clan(user_id, clan_name)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM join_requests WHERE clan_name = ? AND user_id = ?", (clan_name, user_id))
    conn.commit()
    conn.close()

def reject_request(clan_name: str, user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM join_requests WHERE clan_name = ? AND user_id = ?", (clan_name, user_id))
    conn.commit()
    conn.close()

def transfer_leadership(clan_name: str, old_leader_id: int, new_leader_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE clans SET creator_id = ? WHERE clan_name = ?", (new_leader_id, clan_name))
    c.execute("UPDATE users SET clan_role = 'Azo' WHERE user_id = ? AND clan_name = ?", (old_leader_id, clan_name))
    c.execute("UPDATE users SET clan_role = 'Lider' WHERE user_id = ? AND clan_name = ?", (new_leader_id, clan_name))
    conn.commit()
    conn.close()

def update_user_clan_role(user_id: int, new_role: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET clan_role = ? WHERE user_id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

def kick_member(user_id: int):
    leave_clan(user_id)

def get_clan_members(clan_name: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE clan_name = ?", (clan_name,))
    rows = c.fetchall()
    conn.close()
    return [dict(zip([col[0] for col in c.description], row)) for row in rows]