import sqlite3

db = sqlite3.connect("safenet.db")
cur = db.cursor()

try:
    cur.execute("ALTER TABLE users ADD COLUMN mfa_secret TEXT")
    print("✔ mfa_secret column added")
except Exception as e:
    print("mfa_secret:", e)

try:
    cur.execute("ALTER TABLE users ADD COLUMN mfa_enabled INTEGER DEFAULT 0")
    print("✔ mfa_enabled column added")
except Exception as e:
    print("mfa_enabled:", e)

db.commit()
db.close()
