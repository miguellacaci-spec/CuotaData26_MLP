from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

# =========================================
# CONFIGURACIÓN BASE DE DATOS
# =========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jugadores.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================================
# MODELOS
# =========================================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False, unique=True)
    contraseña = db.Column(db.String(100), nullable=False)

class Jugador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    posicion = db.Column(db.String(50), nullable=False)
    media = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()

# =========================================
# RUTAS PRINCIPALES
# =========================================
@app.route('/')
def home():
    return render_template('home.html')

# =========================================
# LOGIN
# =========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        user = Usuario.query.filter_by(usuario=usuario).first()
        if user and user.contraseña == contraseña:
            session['usuario'] = usuario
            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for('modo_carrera'))
        else:
            flash("Usuario o contraseña incorrectos", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

# =========================================
# REGISTRO
# =========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        # Evitar duplicados
        existente = Usuario.query.filter_by(usuario=usuario).first()
        if existente:
            flash("El nombre de usuario ya existe. Prueba con otro.", "error")
            return redirect(url_for('register'))

        nuevo_usuario = Usuario(usuario=usuario, contraseña=contraseña)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro completado con éxito. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# =========================================
# CERRAR SESIÓN
# =========================================
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for('home'))

# =========================================
# MODO CARRERA - CRUD JUGADORES
# =========================================
@app.route('/modo_carrera')
def modo_carrera():
    if 'usuario' not in session:
        flash("Debes iniciar sesión para acceder al modo carrera", "error")
        return redirect(url_for('login'))

    jugadores = Jugador.query.all()
    return render_template('modo_carrera.html', jugadores=jugadores)

@app.route('/agregar_jugador', methods=['GET', 'POST'])
def agregar_jugador():
    if 'usuario' not in session:
        flash("Debes iniciar sesión", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        posicion = request.form['posicion']
        media = request.form['media']
        valor = request.form['valor']

        nuevo_jugador = Jugador(nombre=nombre, posicion=posicion, media=media, valor=valor)
        db.session.add(nuevo_jugador)
        db.session.commit()
        flash("Jugador agregado correctamente", "success")
        return redirect(url_for('modo_carrera'))

    return render_template('agregar_jugador.html')

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    jugador = Jugador.query.get(id)
    if jugador:
        db.session.delete(jugador)
        db.session.commit()
        flash("Jugador eliminado correctamente", "success")
    else:
        flash("Jugador no encontrado", "error")
    return redirect(url_for('modo_carrera'))

@app.route('/modificar/<int:id>', methods=['GET', 'POST'])
def modificar(id):
    jugador = Jugador.query.get(id)
    if not jugador:
        flash("Jugador no encontrado", "error")
        return redirect(url_for('modo_carrera'))

    if request.method == 'POST':
        jugador.nombre = request.form['nombre']
        jugador.posicion = request.form['posicion']
        jugador.media = request.form['media']
        jugador.valor = request.form['valor']
        db.session.commit()
        flash("Jugador modificado correctamente", "success")
        return redirect(url_for('modo_carrera'))

    return render_template('modificar_jugador.html', jugador=jugador)

# =========================================
# PARTIDOS
# =========================================
@app.route('/partidos')
def partidos():
    return render_template('partidos.html')

# =========================================
# EJECUCIÓN LOCAL
# =========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

