import sqlite3
from config import DB_FILE

def search_users(query: str) -> list:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT user_id, username, first_name, last_name, rank, level 
        FROM users
        WHERE 
            username LIKE ? 
            OR first_name LIKE ?
            OR last_name LIKE ?
        LIMIT 10
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))

    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
