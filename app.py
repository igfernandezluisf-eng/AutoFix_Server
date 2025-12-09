# ==============================================================================
# PROYECTO: AutoFix Server (Backend)
# MÓDULO:   Gestor de Licencias (Render Compatible)
# VERSIÓN:  2.0.2 (Tmp Path + Debug Mode)
# ==============================================================================

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import random
import time
import math
import os
import sys

app = Flask(__name__)
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

# --- CONFIGURACIÓN DE BASE DE DATOS INTELIGENTE ---
# Si estamos en Windows (Tu PC), usa la carpeta normal.
# Si estamos en Linux (Render), usa la carpeta temporal /tmp para evitar errores de permiso.
if os.name == 'nt':
    DB_NAME = "autofix_users.db"
else:
    DB_NAME = "/tmp/autofix_users.db"

ADMIN_PASSWORD = "admin"

# --- BASE DE DATOS (USUARIOS) ---
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, plan TEXT DEFAULT 'FREE', status TEXT DEFAULT 'ACTIVE', notes TEXT)''')
        # Intentar crear usuario base si no existe
        try:
            c.execute("INSERT INTO users (email, password, plan, notes) VALUES (?, ?, ?, ?)", ("mecanico@test.com", "1234", "MASTER", "Usuario Beta"))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Ya existe
        conn.close()
        print(f"✅ BASE DE DATOS INICIALIZADA EN: {DB_NAME}")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO AL INICIAR DB: {e}")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Ejecutamos la creación de la DB inmediatamente
init_db()

# --- DASHBOARD ADMIN HTML ---
DASHBOARD_HTML = """
<!DOCTYPE html><html><head><title>AutoFix ADMIN</title>
<style>
body{background:#111;color:#0f0;font-family:sans-serif;padding:20px}
table{width:100%;border:1px solid #333;margin-top:20px;border-collapse:collapse}
th,td{padding:10px;border:1px solid #333;text-align:left}
th{background:#222;color:#00f3ff}
button{cursor:pointer;padding:5px;font-weight:bold}
.btn-master{background:#ffaa00;border:none}
.btn-ban{background:#ff0055;color:white;border:none}
</style></head>
<body>
<h1>PANEL DE CONTROL <span style="font-size:0.5em;color:#888">DB: {{ db_path }}</span></h1>

{% if error %}
    <div style="color:red;border:1px solid red;padding:10px;margin:10px;">ERROR SISTEMA: {{ error }}</div>
{% endif %}

{% if logged_in %}
  <div style="margin-bottom:20px;padding:10px;background:#222">
    <b>+ Nuevo Usuario:</b>
    <form action="/admin/add_user" method="POST" style="display:inline">
        <input type="email" name="email" placeholder="Email" required>
        <input type="text" name="notes" placeholder="Notas">
        <button>Crear</button>
    </form>
  </div>

  <table>
  <tr><th>Email</th><th>Plan</th><th>Estado</th><th>Notas</th><th>Acciones</th></tr>
  {% for u in users %}
  <tr>
    <td>{{u.email}}</td>
    <td><b style="color:{% if u.plan=='MASTER' %}#ffaa00{% else %}white{% endif %}">{{u.plan}}</b></td>
    <td>{{u.status}}</td>
    <td><small>{{u.notes}}</small></td>
    <td>
        <form action="/admin/update" method="POST" style="display:inline">
            <input type="hidden" name="email" value="{{u.email}}">
            <button name="action" value="set_master" class="btn-master">Dar MASTER</button> 
            <button name="action" value="set_pro">Dar PRO</button> 
            <button name="action" value="ban" class="btn-ban">BAN</button>
        </form>
    </td>
  </tr>
  {% endfor %}
  </table>
  <br><a href="/admin/logout" style="color:#666">Cerrar Sesión</a>
{% else %}
  <form method="POST" action="/admin/login">
    <input type="password" name="password" placeholder="Clave de Admin">
    <button>ENTRAR AL SISTEMA</button>
  </form>
{% endif %}
</body></html>
"""

# --- RUTAS DE LOGIN Y ADMIN ---
@app.route('/admin', methods=['GET'])
def admin():
    try:
        if not session.get('logged_in'): 
            return render_template_string(DASHBOARD_HTML, logged_in=False, db_path=DB_NAME)
        
        conn = get_db_connection()
        users = conn.execute('SELECT * FROM users ORDER BY rowid DESC').fetchall()
        conn.close()
        return render_template_string(DASHBOARD_HTML, logged_in=True, users=users, db_path=DB_NAME)
    
    except Exception as e:
        # Si falla, muestra el error en pantalla en lugar de 500
        return render_template_string(DASHBOARD_HTML, logged_in=False, error=str(e), db_path=DB_NAME)

@app.route('/admin/login', methods=['POST'])
def login():
    if request.form.get('password') == ADMIN_PASSWORD: session['logged_in'] = True
    return redirect('/admin')

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/admin')

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'): return redirect('/admin')
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO users (email, plan, notes) VALUES (?, 'FREE', ?)", 
                     (request.form.get('email'), request.form.get('notes')))
        conn.commit()
        conn.close()
    except: pass
    return redirect('/admin')

@app.route('/admin/update', methods=['POST'])
def update():
    if not session.get('logged_in'): return redirect('/admin')
    e = request.form.get('email'); a = request.form.get('action')
    conn = get_db_connection()
    if a == 'set_master': conn.execute("UPDATE users SET plan='MASTER' WHERE email=?", (e,))
    if a == 'set_pro': conn.execute("UPDATE users SET plan='PRO' WHERE email=?", (e,))
    if a == 'ban': conn.execute("UPDATE users SET status='BANNED' WHERE email=?", (e,))
    conn.commit(); conn.close()
    return redirect('/admin')

# --- API PARA LA APP ---
@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        d = request.json
        conn = get_db_connection()
        u = conn.execute('SELECT * FROM users WHERE email=?', (d.get('email'),)).fetchone()
        conn.close()
        if u and u['status'] == 'ACTIVE': return jsonify({"status":"success", "plan":u['plan']})
        return jsonify({"status":"error", "message":"Usuario no encontrado o Bloqueado"})
    except Exception as e:
        return jsonify({"status":"error", "message":str(e)})

# --- SIMULADOR ---
@app.route('/live', methods=['GET'])
def live_data():
    return jsonify({
        "connected": True,
        "vin": "1G1JC5444W720589",
        "rpm": int(800 + (math.sin(time.time()) * 50) + (random.random() * 20)), 
        "coolant_temp": int(90 + (math.sin(time.time()/10) * 5)) 
    })

@app.route('/sensors/all', methods=['GET'])
def all_sensors():
    return jsonify({
        "intake_temp": 45, "maf": 3.5, "map": 35, "throttle_pos": 12,
        "vehicle_speed": 0, "battery_voltage": 13.8 + (random.random()*0.2),
        "o2_voltage": round(abs(math.sin(time.time())), 2), "fuel_level": 75, "oil_pressure": 40
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
