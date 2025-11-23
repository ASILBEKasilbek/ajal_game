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