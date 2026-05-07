import sqlite3

db = sqlite3.connect("safenet.db")
cursor = db.cursor()

cursor.execute("""
SELECT time, source_ip, country, organization
FROM logs
ORDER BY id DESC
LIMIT 5
""")

rows = cursor.fetchall()
db.close()
    
for r in rows:
    print(r)
