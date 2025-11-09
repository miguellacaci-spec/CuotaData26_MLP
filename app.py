from flask import Flask, render_template, request, redirect, session
from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash
# NOTA: Ya no importamos 'init_db' aquí porque Render lo ejecuta por separado.

app = Flask(__name__)
# ¡IMPORTANTE! Cambia esta clave secreta a algo largo y complejo antes de desplegar en producción.
app.secret_key = "clave_super_segura_y_larga_para_la_session" 

# --- Función auxiliar para la conexión a la base de datos ---
def get_db_connection():
    # Render usa el archivo data.db que fue creado en la fase de "Build"
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Home ---
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = get_db_connection()
    user = conn.execute("SELECT username FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()

    return render_template('home.html', username=user['username'] if user else 'Manager')

# --- Registro ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Seguridad: Hashing de la contraseña antes de guardarla
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            error = "❌ El nombre de usuario ya existe. Por favor, elige otro."
        finally:
            conn.close()
        
        if not error:
            return redirect('/login')
            
    return render_template('register.html', error=error)

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        
        # 1. Buscamos al usuario por el nombre de usuario y obtenemos su hash
        user = conn.execute("SELECT id, password FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        # 2. Verificamos si el usuario existe y si la contraseña coincide con el hash almacenado
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/')
        else:
            error = "❌ Usuario o contraseña incorrectos"
            
    return render_template('login.html', error=error)

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- Modo Carrera ---
@app.route('/modo_carrera', methods=['GET', 'POST'])
def modo_carrera():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    message = None 

    if request.method == 'POST':
        try:
            position = request.form['position']
            name = request.form['name']
            # Intentamos convertir a entero. Esto puede fallar si el usuario introduce texto.
            age = int(request.form['age'])
            nationality = request.form['nationality']
            grl = int(request.form['grl'])
            market_value = request.form['market_value']
            salary = request.form['salary']

            conn.execute('''
                INSERT INTO players (user_id, position, name, age, nationality, grl, market_value, salary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], position, name, age, nationality, grl, market_value, salary))
            conn.commit()
            message = "✅ Jugador añadido exitosamente."
        except ValueError:
            # Capturamos el error si 'age' o 'grl' no son números válidos
            message = "⚠️ Error: La Edad y el GRL deben ser números enteros válidos."
        except Exception as e:
            # Error genérico de base de datos u otro
            message = f"❌ Error al añadir jugador: {str(e)}"
            print(f"Error adding player: {e}")


    # Fetch players for the current user, ordered by GRL
    players = conn.execute('SELECT * FROM players WHERE user_id=? ORDER BY grl DESC, name ASC', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('modo_carrera.html', players=players, message=message)

# --- Partidos ---
@app.route('/partidos')
def partidos():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('partidos.html')

# --- Ejecución Local / Producción ---
if __name__ == '__main__':
    # Usado solo para desarrollo local, ignorado por Gunicorn en Render
    app.run(host='0.0.0.0', port=5000, debug=True)
