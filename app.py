from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "lucia_secreto_seguro"

# -------------------- BASE DE DATOS --------------------
def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        # Usuarios
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')

        # Jugadores
        c.execute('''CREATE TABLE IF NOT EXISTS players (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        posicion TEXT,
                        nombre TEXT,
                        edad INTEGER,
                        nacionalidad TEXT,
                        grl INTEGER,
                        partidos INTEGER DEFAULT 0,
                        goles INTEGER DEFAULT 0,
                        asistencias INTEGER DEFAULT 0,
                        valor_mercado TEXT DEFAULT '0 €',
                        sueldo TEXT DEFAULT '0 €',
                        FOREIGN KEY (user_id) REFERENCES users(id))''')
        conn.commit()


def get_user_id():
    if "user" in session:
        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username = ?", (session["user"],))
            user = c.fetchone()
            return user[0] if user else None
    return None


def ordenar_posiciones(jugadores):
    orden = ["POR", "LI", "CAI", "DFC", "LD", "CAD", "MCD", "MC", "MCO", "MI", "MD", "EI", "DC", "SD", "ED"]
    return sorted(jugadores, key=lambda x: orden.index(x[1]) if x[1] in orden else 99)


@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for("modo_carrera"))
    return redirect(url_for("login"))


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                flash("Cuenta creada con éxito. Inicia sesión.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Ese nombre de usuario ya existe.", "error")
    return render_template("register.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = c.fetchone()
            if user:
                session["user"] = username
                return redirect(url_for("modo_carrera"))
            else:
                flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route('/modo_carrera', methods=["GET", "POST"])
def modo_carrera():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("login"))

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        jugadores = c.fetchall()

    jugadores = ordenar_posiciones(jugadores)
    return render_template("modo_carrera.html", jugadores=jugadores)


@app.route('/add_player', methods=["POST"])
def add_player():
    user_id = get_user_id()
    if not user_id:
        return redirect(url_for("login"))

    posicion = request.form["posicion"]
    nombre = request.form["nombre"]
    edad = request.form["edad"]
    nacionalidad = request.form["nacionalidad"]
    grl = int(request.form["grl"])

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO players (user_id, posicion, nombre, edad, nacionalidad, grl) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, posicion, nombre, edad, nacionalidad, grl))
        conn.commit()

    return redirect(url_for("modo_carrera"))


@app.route('/update_stats', methods=["POST"])
def update_stats():
    player_id = request.form["player_id"]
    partidos = int(request.form["partidos"])
    goles = int(request.form["goles"])
    asistencias = int(request.form["asistencias"])

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("SELECT partidos, goles, asistencias FROM players WHERE id = ?", (player_id,))
        old = c.fetchone()
        nuevos = (old[0] + partidos, old[1] + goles, old[2] + asistencias)
        c.execute("UPDATE players SET partidos=?, goles=?, asistencias=? WHERE id=?",
                  (nuevos[0], nuevos[1], nuevos[2], player_id))
        conn.commit()

    return redirect(url_for("modo_carrera"))


@app.route('/update_finanzas', methods=["POST"])
def update_finanzas():
    player_id = request.form["player_id"]
    valor = request.form["valor_mercado"]
    sueldo = request.form["sueldo"]

    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("UPDATE players SET valor_mercado=?, sueldo=? WHERE id=?",
                  (valor, sueldo, player_id))
        conn.commit()

    return redirect(url_for("modo_carrera"))


@app.route('/delete_player/<int:id>')
def delete_player(id):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("DELETE FROM players WHERE id=?", (id,))
        conn.commit()
    return redirect(url_for("modo_carrera"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

