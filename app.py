from flask import Flask, render_template, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import os

# --- APP & DB ---
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cuotadata_secret_key")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///modo_carrera.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- LOGIN MANAGER ---
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# --- CONSTANTS ---
POSITION_ORDER = ["POR", "LI", "CAI", "DFC", "LD", "CAD", "MCD", "MC", "MCO", "MI", "MD", "EI", "DC", "SD", "ED"]
POSITIONS = POSITION_ORDER[:]  # available options

# --- MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Season(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  # e.g., "2025/26"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # owner
    position = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    nationality = db.Column(db.String(50), nullable=False)
    grl = db.Column(db.Integer, nullable=False)  # 1-99
    market_value = db.Column(db.Float, default=0.0)  # in euros
    salary = db.Column(db.Float, default=0.0)  # in euros

class PlayerSeason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    season_id = db.Column(db.Integer, db.ForeignKey('season.id'), nullable=False)
    matches = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)

# Create DB
with app.app_context():
    db.create_all()

# --- LOGIN HELPERS ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- JINJA FILTERS ---
@app.template_filter('currency')
def format_currency(value):
    try:
        v = float(value)
    except Exception:
        return value
    # Format with thousands separator and euro symbol, no decimals if integer, else 3 decimals for thousands?
    if v >= 1_000_000:
        return f"{v:,.0f} €".replace(",", ".")
    else:
        # show with thousands and no decimals but show e.g., 875.000 €
        return f"{v:,.0f} €".replace(",", ".")

@app.context_processor
def utility_processor():
    def grl_class(value):
        try:
            x = int(value)
        except Exception:
            return "grl-default"
        if x <= 49:
            return "grl-low"
        if 50 <= x <= 69:
            return "grl-med"
        if 70 <= x <= 79:
            return "grl-orange"
        if 80 <= x <= 84:
            return "grl-green-light"
        return "grl-green-dark"
    return dict(POSITIONS=POSITIONS, grl_class=grl_class)

# --- ROUTES: AUTH ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash("Rellena usuario y contraseña", "danger")
            return redirect('/register')
        if User.query.filter_by(username=username).first():
            flash("Usuario ya existe", "danger")
            return redirect('/register')
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Cuenta creada ✅ Inicia sesión", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Sesión iniciada", "success")
            return redirect('/modo_carrera')
        flash("Usuario o contraseña incorrectos", "danger")
        return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect('/login')

# --- ROUTES: APP ---
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('/')
