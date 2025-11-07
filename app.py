import os
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# SQLite para empezar (persistencia ligera en el host)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///futbol.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

### MODELS
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(80))
    position = db.Column(db.String(20))
    grl = db.Column(db.Integer, default=0)  # minutos/juegos o rating
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    market_value = db.Column(db.Float, default=0.0)
    salary = db.Column(db.Float, default=0.0)
    team = db.Column(db.String(120))

class MatchNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    competition = db.Column(db.String(120))
    home = db.Column(db.String(120))
    away = db.Column(db.String(120))
    comment = db.Column(db.Text)
    created_by = db.Column(db.String(120))

db.create_all()

### HELPERS para APIs y AIs (PLUG: sustituir con tus keys)
def fetch_fixtures_from_provider(params):
    # TODO: conectar con API real (ej: football-data.org, API-Football)
    # return requests.get(...).json()
    return []

def fetch_odds_for_match(home, away, date):
    # TODO: conectar con proveedor de cuotas
    # ejemplo: return requests.get(...).json()
    # estructura esperada: {'home':x,'draw':y,'away':z}
    return {'home': 2.0, 'draw': 3.5, 'away': 3.1}

def ai_estimate_probability(home, away, context):
    # Función que llama a una IA (tu elección) y devuelve probabilidad para cada resultado
    # Placeholder: simple conversión desde odds -> probabilidades implícitas
    odds = fetch_odds_for_match(home, away, context.get('date'))
    # convertir odds a probabilidad implícita:
    inv = {k: 1/odds[k] for k in odds}
    s = sum(inv.values())
    probs = {k: (inv[k]/s)*100 for k in inv}
    # Si usas IA, puedes mejorar este cálculo con modelos ML/LLM
    return probs

### RUTAS
@app.route('/')
def index():
    players = Player.query.all()
    matches = MatchNote.query.order_by(MatchNote.id.desc()).limit(20).all()
    return render_template('index.html', players=players, matches=matches)

# CRUD players (ejemplo básico)
@app.route('/players', methods=['POST'])
def add_player():
    data = request.json
    p = Player(**data)
    db.session.add(p)
    db.session.commit()
    return jsonify({'ok': True, 'id': p.id})

@app.route('/mode-carrera')
def mode_carrera():
    players = Player.query.all()
    # render form + tabla
    return render_template('mode_carrera.html', players=players)

# Export Excel de la plantilla/temporada
@app.route('/export/plantilla.xlsx')
def export_plantilla():
    players = Player.query.all()
    df = pd.DataFrame([{
        'Name': p.name,
        'Age': p.age,
        'Nationality': p.nationality,
        'Position': p.position,
        'GRL': p.grl,
        'Goals': p.goals,
        'Assists': p.assists,
        'MarketValue': p.market_value,
        'Salary': p.salary,
        'Team': p.team
    } for p in players])
    # Añadir sumas al final (club totals)
    totals = {
        'Name': 'Totals',
        'Age': '',
        'Nationality': '',
        'Position': '',
        'GRL': df['GRL'].sum() if 'GRL' in df else 0,
        'Goals': df['Goals'].sum() if 'Goals' in df else 0,
        'Assists': df['Assists'].sum() if 'Assists' in df else 0,
        'MarketValue': df['MarketValue'].sum() if 'MarketValue' in df else 0,
        'Salary': df['Salary'].sum() if 'Salary' in df else 0,
        'Team': ''
    }
    df = df.append(totals, ignore_index=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla')
    output.seek(0)
    return send_file(output, attachment_filename='plantilla.xlsx', as_attachment=True)

# Página de partido real con análisis y comentarios
@app.route('/match/<int:match_id>')
def match_detail(match_id):
    m = MatchNote.query.get_or_404(match_id)
    # fetch últimos 5 resultados ejemplo -> TODO conectar con API real
    last5_home = [('R1','V'), ('R2','E'), ('R3','P'), ('R4','V'), ('R5','V')]
    last5_away = [('R1','P'), ('R2','P'), ('R3','E'), ('R4','V'), ('R5','V')]
    probs = ai_estimate_probability(m.home, m.away, {'date': m.date})
    odds = fetch_odds_for_match(m.home, m.away, m.date)
    return render_template('match.html', match=m, last5_home=last5_home, last5_away=last5_away, probs=probs, odds=odds)

# Guardar nota/ comentario
@app.route('/match', methods=['POST'])
def create_match_note():
    data = request.form
    m = MatchNote(
        date=data.get('date'),
        competition=data.get('competition'),
        home=data.get('home'),
        away=data.get('away'),
        comment=data.get('comment'),
        created_by=data.get('created_by')
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({'ok': True, 'id': m.id})

if __name__ == '__main__':
    app.run(debug=True)
