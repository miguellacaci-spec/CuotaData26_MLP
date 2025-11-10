from flask import Flask, render_template, request, redirect, url_for, flash, session from flask_sqlalchemy import SQLAlchemy from werkzeug.security import generate_password_hash, check_password_hash # Para contraseñas seguras import os
app = Flask(__name__)
# Usamos una clave secreta para la gestión de sesiones
app.secret_key = "clave_secreta_super_segura_2024_proyectoflask"
# =========================================
# CONFIGURACIÓN BASE DE DATOS
# =========================================
# La base de datos debe ser única por usuario/entorno
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///manager_career.db' app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False db = SQLAlchemy(app)
# =========================================
# MODELOS
# =========================================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False, unique=True)
    # Almacenamos el hash de la contraseña en lugar de la contraseña simple
    contraseña_hash = db.Column(db.String(128), nullable=False)
    # Relación con Jugadores (para gestión multiusuario)
    jugadores = db.relationship('Jugador', backref='manager', lazy=True)

    def set_password(self, password):
        """Genera el hash de la contraseña para almacenarla de forma segura."""
        self.contraseña_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña dada coincide con el hash almacenado."""
        return check_password_hash(self.contraseña_hash, password)

class Jugador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Clave foránea para vincular al jugador con el usuario logueado
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    posicion = db.Column(db.String(50), nullable=False)
    grl = db.Column(db.Integer, nullable=False) # media -> grl
    edad = db.Column(db.Integer, nullable=False) # nuevo campo
    market_value = db.Column(db.String(50), nullable=False) # valor -> market_value
    salary = db.Column(db.String(50), nullable=False) # nuevo campo

with app.app_context():
    db.create_all()

# =========================================
# LÓGICA DE ORDENACIÓN (PARA EL PUNTO 2)
# =========================================
POSICION_ORDEN = {
    "POR": 1,
    "CAI": 2,
    "LI": 3,
    "DFC": 4,
    "LD": 5,
    "CAD": 6,
    "MCD": 7,
    "MC": 8,
    "MCO": 9,
    "MI": 10,
    "MD": 11,
    "EI": 12,
    "DC": 13,
    "SD": 14,
    "ED": 15
}

def ordenar_jugadores(jugadores):
    """Ordena la lista de jugadores según la prioridad de posición definida."""
    # El valor 99 se usa si la posición no está en el diccionario, poniéndolo al final
    return sorted(jugadores, key=lambda p: POSICION_ORDEN.get(p.posicion, 99))

# =========================================
# RUTAS PRINCIPALES
# =========================================
@app.route('/')
def home():
    if 'user_id' not in session:
        # Si no hay sesión, redirige al login (Requisito 1: pedir registro o inicio de sesión)
        return redirect(url_for('login'))
    # Si hay sesión, muestra el home (el menú principal)
    username = session.get('usuario', 'Manager')
    return render_template('home.html', username=username)

# =========================================
# LOGIN
# =========================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario_req = request.form['usuario']
        contraseña_req = request.form['contraseña']

        user = Usuario.query.filter_by(usuario=usuario_req).first()
        # Usamos check_password para verificar el hash de forma segura
        if user and user.check_password(contraseña_req):
            session['user_id'] = user.id
            session['usuario'] = usuario_req
            flash("✅ Inicio de sesión exitoso", "success")
            # Redirige a home para que pueda elegir entre modo carrera o partidos
            return redirect(url_for('home'))
        else:
            flash("❌ Usuario o contraseña incorrectos", "error")
            return redirect(url_for('login'))
    return render_template('login.html')

# =========================================
# REGISTRO
# =========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario_req = request.form['usuario']
        contraseña_req = request.form['contraseña']

        # Evitar duplicados
        existente = Usuario.query.filter_by(usuario=usuario_req).first()
        if existente:
            flash("⚠️ El nombre de usuario ya existe. Prueba con otro.", "error")
            return redirect(url_for('register'))

        nuevo_usuario = Usuario(usuario=usuario_req)
        # Almacenamos el hash de la contraseña
        nuevo_usuario.set_password(contraseña_req)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("✅ Registro completado con éxito. Ahora puedes iniciar sesión.", "success")
        # Redirige al login, que a su vez llevará al home si el inicio de sesión es exitoso
        return redirect(url_for('login'))
    return render_template('register.html')

# =========================================
# CERRAR SESIÓN
# =========================================
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('usuario', None)
    flash("✅ Sesión cerrada correctamente", "success")
    return redirect(url_for('home'))

# =========================================
# MODO CARRERA - CRUD JUGADORES
# =========================================
@app.route('/modo_carrera', methods=['GET', 'POST'])
def modo_carrera():
    if 'user_id' not in session:
        flash("❌ Debes iniciar sesión para acceder al modo carrera", "error")
        return redirect(url_for('login'))

    user_id = session['user_id']
    message = None
    
    if request.method == 'POST':
        # Lógica para Añadir Jugador (POST)
        try:
            nombre = request.form['name'] # Nota: el form del HTML usa 'name'
            posicion = request.form['position']
            grl = request.form['grl'] # media -> grl
            edad = request.form['age'] # nuevo campo
            market_value = request.form['market_value'] # valor -> market_value
            salary = request.form['salary'] 
            # nuevo campo
            nuevo_jugador = Jugador(
                user_id=user_id,
                nombre=nombre, 
                posicion=posicion, 
                grl=int(grl), 
                edad=int(edad), 
                market_value=market_value,
                salary=salary
            )
            db.session.add(nuevo_jugador)
            db.session.commit()
            message = "✅ Jugador agregado correctamente."

        except Exception as e:
            db.session.rollback()
            # Muestra el error de forma más estética
            message = f"❌ Error: No se pudo agregar el jugador. Por favor, revisa los datos."
            
    # Lógica para Mostrar Jugadores (GET)
    # Solo carga jugadores del usuario logueado
    jugadores = Jugador.query.filter_by(user_id=user_id).all()
    # Aplicamos la ordenación personalizada ANTES de renderizar la plantilla
    jugadores_ordenados = ordenar_jugadores(jugadores)
    # Pasamos una lista de diccionarios para mayor compatibilidad con Jinja
    players_data = [{
        'id': p.id,
        'name': p.nombre,
        'position': p.posicion,
        'grl': p.grl,
        'age': p.edad,
        'market_value': 
        p.market_value,
        'salary': p.salary} for p in jugadores_ordenados]
        
    return render_template('modo_carrera.html', players=players_data, message=message, username=session.get('usuario', 'Manager'))

# ----------------------------------------------------
# NUEVAS RUTAS PARA MODIFICAR Y ELIMINAR (SOLUCIÓN 404)
# ----------------------------------------------------
# Corregida la sintaxis de la ruta para Flask: de '/int:player_id' a '/<int:player_id>'
@app.route('/eliminar_jugador/<int:player_id>', methods=['POST'])
def eliminar_jugador(player_id):
    if 'user_id' not in session:
        flash("❌ Debes iniciar sesión para realizar esta acción", "error")
        return redirect(url_for('login'))

    jugador = Jugador.query.filter_by(id=player_id, user_id=session['user_id']).first()
    if jugador:
        db.session.delete(jugador)
        db.session.commit()
        flash("✅ Jugador eliminado correctamente.", "success")
    else:
        flash("⚠️ Jugador no encontrado o no autorizado.", "error")
    return redirect(url_for('modo_carrera'))

# Corregida la sintaxis de la ruta para Flask: de '/int:player_id' a '/<int:player_id>'
@app.route('/actualizar_jugador/<int:player_id>', methods=['POST'])
def actualizar_jugador(player_id):
    if 'user_id' not in session:
        flash("❌ Debes iniciar sesión para realizar esta acción", "error")
        return redirect(url_for('login'))

    jugador = Jugador.query.filter_by(id=player_id, user_id=session['user_id']).first()
    if jugador and request.method == 'POST':
        try:
            # Los nombres de los campos vienen del modal JS en el HTML
            jugador.posicion = request.form['position']
            jugador.grl = int(request.form['grl'])
            jugador.edad = int(request.form['age'])
            jugador.market_value = request.form['market_value']
            jugador.salary = request.form['salary']
            
            db.session.commit()  
            flash(f"✅ Jugador {jugador.nombre} modificado correctamente.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al modificar el jugador: {e}. Revisa los datos.", "error")
    else:
        flash("⚠️ Jugador no encontrado o no autorizado para modificar.", "error")
    return redirect(url_for('modo_carrera'))

@app.route('/finalizar_plantilla', methods=['POST'])
def finalizar_plantilla():
    if 'user_id' not in session:
        flash("❌ Debes iniciar sesión para realizar esta acción", "error")
        return redirect(url_for('login'))

    # Lógica de servidor para registrar la plantilla como "Temporada 1"
    # Aquí podrías guardar una copia de la plantilla actual o cambiar un estado del usuario.
    flash("🎉 ¡Plantilla completada! Registrada como Temporada 1.", "success")
    return redirect(url_for('modo_carrera'))

# =========================================
# PARTIDOS (Mantener si existe)
# =========================================
@app.route('/partidos')
def partidos():
    return render_template('partidos.html')

# =========================================
# EJECUCIÓN LOCAL
# =========================================
if __name__ == '__main__': # Usamos un modo 'debug' en desarrollo
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
