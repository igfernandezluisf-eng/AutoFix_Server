# ==============================================================================
# PROYECTO: AutoFix Server (Backend)
# MÓDULO:   Gestor de Licencias + SIMULADOR DE MOTOR
# VERSIÓN:  2.0.0 (Engine Running)
# ==============================================================================

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import random
import time
import math

app = Flask(__name__)
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

DB_NAME = "autofix_users.db"
ADMIN_PASSWORD = "admin"

# --- BASE DE DATOS (USUARIOS) ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, plan TEXT DEFAULT 'FREE', status TEXT DEFAULT 'ACTIVE', notes TEXT)''')
    c.execute("INSERT OR IGNORE INTO users (email, password, plan, notes) VALUES (?, ?, ?, ?)", ("mecanico@test.com", "1234", "MASTER", "Usuario Beta"))
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- DASHBOARD ADMIN HTML (RESUMIDO) ---
DASHBOARD_HTML = """
<!DOCTYPE html><html><head><title>AutoFix ADMIN</title><style>body{background:#111;color:#0f0;font-family:sans-serif;padding:20px}table{width:100%;border:1px solid #333}th,td{padding:10px;border:1px solid #333}button{cursor:pointer}</style></head>
<body><h1>PANEL DE CONTROL</h1>
{% if logged_in %}
  <table><tr><th>Email</th><th>Plan</th><th>Acciones</th></tr>
  {% for u in users %}
  <tr><td>{{u.email}}</td><td>{{u.plan}}</td>
  <td><form action="/admin/update" method="POST"><input type="hidden" name="email" value="{{u.email}}"><button name="action" value="set_master">Hacer MASTER</button> <button name="action" value="ban">BANEAR</button></form></td></tr>
  {% endfor %}</table>
{% else %}
  <form method="POST" action="/admin/login"><input type="password" name="password"><button>ENTRAR</button></form>
{% endif %}
</body></html>
"""

# --- RUTAS DE LOGIN ---
@app.route('/admin', methods=['GET'])
def admin():
    if not session.get('logged_in'): return render_template_string(DASHBOARD_HTML, logged_in=False)
    conn = get_db_connection(); users = conn.execute('SELECT * FROM users').fetchall(); conn.close()
    return render_template_string(DASHBOARD_HTML, logged_in=True, users=users)

@app.route('/admin/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASSWORD: session['logged_in'] = True
    return redirect('/admin')

@app.route('/admin/update', methods=['POST'])
def update():
    if not session.get('logged_in'): return redirect('/admin')
    e = request.form.get('email'); a = request.form.get('action')
    conn = get_db_connection()
    if a == 'set_master': conn.execute("UPDATE users SET plan='MASTER' WHERE email=?", (e,))
    if a == 'ban': conn.execute("UPDATE users SET status='BANNED' WHERE email=?", (e,))
    conn.commit(); conn.close()
    return redirect('/admin')

@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json
    conn = get_db_connection(); u = conn.execute('SELECT * FROM users WHERE email=?', (d.get('email'),)).fetchone(); conn.close()
    if u and u['status'] == 'ACTIVE': return jsonify({"status":"success", "plan":u['plan']})
    return jsonify({"status":"error", "message":"No registrado o Baneado"})

# --- 🔧 MÓDULO NUEVO: SIMULADOR DE MOTOR (/live) ---
@app.route('/live', methods=['GET'])
def live_data():
    # Esta función simula que el carro está prendido
    return jsonify({
        "connected": True,
        "vin": "1G1JC5444W720589",
        "rpm": int(800 + (math.sin(time.time()) * 50) + (random.random() * 20)), # RPM oscilando en ralentí
        "coolant_temp": int(90 + (math.sin(time.time()/10) * 5)) # Temp oscilando
    })

# --- MÓDULO SENSORES EXTRA (/sensors/all) ---
@app.route('/sensors/all', methods=['GET'])
def all_sensors():
    return jsonify({
        "intake_temp": 45, "maf": 3.5, "map": 35, "throttle_pos": 12,
        "vehicle_speed": 0, "battery_voltage": 13.8 + (random.random()*0.2),
        "o2_voltage": round(random.random(), 2), "fuel_level": 75, "oil_pressure": 40
    })

if __name__ == '__main__':
    init_db()
    print("🚀 AutoFix SERVER + ENGINE SIMULATOR -> CORRIENDO EN PUERTO 5000")
    app.run(debug=True, port=5000)