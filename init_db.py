import sqlite3

def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Eliminar tablas si existen (para empezar limpio)
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS players")

    # Tabla de Usuarios (users)
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Tabla de Jugadores (players)
    cursor.execute("""
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            nationality TEXT NOT NULL,
            grl INTEGER NOT NULL,
            market_value TEXT,
            salary TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()
    print("Base de datos 'data.db' y tablas 'users' y 'players' inicializadas correctamente.")

# Ejecutar la función si el script se corre directamente
if __name__ == '__main__':
    init_db()
