import sqlite3

# === CONNECT TO DATABASE ===
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# === CREATE USERS TABLE ===
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'user'
)
""")

# === CREATE JOURNAL ENTRIES TABLE ===
cursor.execute("""
CREATE TABLE IF NOT EXISTS journal_entries (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    entry TEXT NOT NULL,
    probability REAL,
    prediction TEXT,
    mood TEXT,
    help_status TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
""")

conn.commit()
conn.close()
print("✅ users.db created with tables: users & journal_entries")
