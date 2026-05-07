import sqlite3

DB_NAME = "safenet.db"

def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        mfa_secret TEXT,
        mfa_enabled INTEGER DEFAULT 0,
        dob TEXT,
        last_password_change TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        query TEXT,
        label INTEGER,
        source_ip TEXT,
        country TEXT,
        organization TEXT
    )
    """)

    # Default admin
    cur.execute("""
    INSERT OR IGNORE INTO users
    (username, password, mfa_enabled, dob, last_password_change)
    VALUES (?, ?, ?, ?, ?)
    """, ("admin", "password", 0, "2002-05-14", "2024-11-10"))

    db.commit()
    db.close()
