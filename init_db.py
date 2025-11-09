import sqlite3

conn = sqlite3.connect('data.db')
c = conn.cursor()

# Tabla de usuarios
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Tabla de jugadores
c.execute('''
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    position TEXT,
    name TEXT,
    age INTEGER,
    nationality TEXT,
    grl INTEGER,
    matches INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    market_value TEXT,
    salary TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()
print("✅ Base de datos creada correctamente.")
