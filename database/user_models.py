# database.py
import sqlite3
import os
from datetime import datetime
from config import DB_FILE


def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        columns = [d[0] for d in c.description]
        user_dict = dict(zip(columns, row))
        conn.close()
        return user_dict
    conn.close()
    return None

def save_user(user: dict):
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
        user['user_id'],
        user.get('username'),
        user.get('first_name'),
        user.get('last_name'),
        user.get('language', 'uz'),
        user.get('channel', 'Nomalum'),
        user.get('user_group', 'Nomalum'),
        user.get('clan_name', 'Yo‘q'),
        user.get('clan_role', 'Azo'),
        user.get('clan_level', 0),
        user.get('clan_xp', 0),
        user.get('clan_xp_next', 800),
        user.get('clan_rank', 0),
        user.get('total_clans', 0),
        user.get('clan_channel', 'Nomalum'),
        user.get('clan_group', 'Nomalum'),
        user.get('level', 1),
        user.get('xp', 0),
        user.get('rank', 'D'),
        user.get('olmos', 0),
        user.get('balls', 0),
        user.get('popularity', 0),
        user.get('popularity_today', 0),
        user.get('wins', 0),
        user.get('total_games', 0),
        user.get('last_game_result', None),
        user.get('last_game_date', None),
        user.get('bio', 'Bio yozilmagan'),
        user.get('days_in_game', 0),
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))
    conn.commit()
    conn.close()

def save_user_language_only(user_id: int, language: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE users
        SET language = ?, last_active = ?
        WHERE user_id = ?
    ''', (language, datetime.now().strftime("%Y-%m-%d %H:%M"), user_id))
    conn.commit()
    conn.close()


def get_guruhlar():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT kanal_link FROM kanallar")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]