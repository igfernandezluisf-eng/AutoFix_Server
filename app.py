# ==============================================================================
# PROYECTO: AutoFix Server (Backend)
# MÓDULO:   Admin Dashboard Deluxe (UI/UX Upgrade)
# VERSIÓN:  3.0.0 (Secure & Beautiful)
# ==============================================================================

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
import sqlite3
import random
import time
import math
import os

app = Flask(__name__)
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

if os.name == 'nt':
    DB_NAME = "autofix_users.db"
else:
    DB_NAME = "/tmp/autofix_users.db"

ADMIN_PASSWORD = "admin"

def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, plan TEXT DEFAULT 'FREE', status TEXT DEFAULT 'ACTIVE', notes TEXT)''')
        try:
            c.execute("INSERT INTO users (email, password, plan, notes) VALUES (?, ?, ?, ?)", ("mecanico@test.com", "1234", "MASTER", "Usuario Beta"))
            conn.commit()
        except sqlite3.IntegrityError:
            pass 
        conn.close()
    except Exception as e:
        print(f"❌ ERROR DB: {e}")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

init_db() 

# --- DASHBOARD ADMIN DELUXE (HTML/CSS MODERNO) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoFix SUPER ADMIN</title>
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0f1015; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding: 20px; }
        h1 { color: #00f3ff; text-align: center; letter-spacing: 2px; }
        .container { max-width: 1000px; margin: 0 auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #1a1b20; border-radius: 8px; overflow: hidden; }
        th, td { padding: 15px; text-align: left; border-bottom: 1px solid #333; }
        th { background-color: #222; color: #00f3ff; }
        tr:hover { background-color: #25262c; }
        
        .badge { padding: 5px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: bold; }
        .bg-free { background: #555; color: white; }
        .bg-pro { background: #00f3ff; color: black; }
        .bg-master { background: #ffaa00; color: black; box-shadow: 0 0 10px #ffaa00; }
        .bg-banned { background: #ff0055; color: white; }
        
        .action-btn { padding: 5px 10px; cursor: pointer; border: none; border-radius: 4px; font-weight: bold; margin-right: 5px; }
        .btn-green { background: #00ff9d; color: black; }
        .btn-gold { background: #ffaa00; color: black; }
        .btn-red { background: #ff0055; color: white; }
        
        .login-box { width: 300px; margin: 100px auto; padding: 30px; background: #1a1b20; border: 1px solid #333; border-radius: 10px; text-align: center; }
        input { width: 90%; padding: 10px; margin: 10px 0; background: #0f1015; border: 1px solid #444; color: white; }
        button { width: 100%; padding: 10px; background: #00f3ff; border: none; font-weight: bold; cursor: pointer; }
        
        .stats { display: flex; gap: 20px; justify-content: center; margin-bottom: 30px; }
        .stat-card { background: #1a1b20; padding: 20px; border-radius: 10px; border: 1px solid #333; text-align: center; min-width: 150px; }
        .stat-num { font-size: 2rem; font-weight: bold; color: white; }
        .stat-label { color: #888; font-size: 0.9rem; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-box">
        <h2>ACCESO RESTRINGIDO</h2>
        <form method="POST" action="/admin/login">
            <input type="password" name="password" placeholder="Clave Maestra" required>
            <button type="submit">ENTRAR</button>
        </form>
    </div>
    {% else %}
    <div class="container">
        <h1>AutoFix <span style="color:white">COMMAND CENTER</span></h1>
        
        <div class="stats">
            <div class="stat-card"><div class="stat-num">{{ stats.total }}</div><div class="stat-label">Usuarios Totales</div></div>
            <div class="stat-card" style="border-color:#ffaa00"><div class="stat-num" style="color:#ffaa00">{{ stats.masters }}</div><div class="stat-label">MODO DIOS</div></div>
            <div class="stat-card" style="border-color:#00ff9d"><div class="stat-num" style="color:#00ff9d">{{ stats.active }}</div><div class="stat-label">Activos Hoy</div></div>
        </div>

        <div style="background:#222; padding:15px; border-radius:8px; display:flex; gap:10px; align-items:center;">
            <span style="font-weight:bold;">+ Nuevo Beta Tester:</span>
            <form action="/admin/add_user" method="POST" style="display:flex; gap:10px; flex:1;">
                <input type="email" name="email" placeholder="Email del Mecánico" required style="margin:0;">
                <input type="text" name="notes" placeholder="Notas (Ej. Taller Pepe)" style="margin:0;">
                <button type="submit" class="btn-green" style="width:auto;">REGISTRAR</button>
            </form>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Usuario / Email</th>
                    <th>Plan Actual</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td>
                        <strong style="color:white; font-size:1.1rem;">{{ user.email }}</strong><br>
                        <small style="color:#888">{{ user.notes }}</small>
                    </td>
                    <td>
                        <span class="badge 
                            {% if user.plan == 'MASTER' %}bg-master{% elif user.plan == 'PRO' %}bg-pro{% else %}bg-free{% endif %}">
                            {{ user.plan }}
                        </span>
                    </td>
                    <td>
                        <span style="color: {% if user.status == 'BANNED' %}#ff0055{% else %}#00ff9d{% endif %}">
                            {{ user.status }}
                        </span>
                    </td>
                    <td>
                        <form action="/admin/update" method="POST" style="display:inline;">
                            <input type="hidden" name="email" value="{{ user.email }}">
                            <button name="action" value="set_free" class="action-btn bg-free" title="Bajar a Gratis">🥉</button>
                            <button name="action" value="set_pro" class="action-btn bg-pro" title="Subir a PRO">🥈</button>
                            <button name="action" value="set_master" class="action-btn bg-master" title="DAR MODO DIOS">🥇</button>
                            {% if user.status == 'BANNED' %}
                                <button name="action" value="unban" class="action-btn btn-green">DESBLOQUEAR</button>
                            {% else %}
                                <button name="action" value="ban" class="action-btn btn-red">BLOQUEAR 🚫</button>
                            {% endif %}
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div style="text-align:center; margin-top:30px;">
            <a href="/admin/logout" style="color:#888; text-decoration:none;">Cerrar Sesión Segura</a>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

# --- RUTAS DE LOGIN ---
@app.route('/admin', methods=['GET'])
def admin_panel():
    if not session.get('logged_in'):
        return render_template_string(DASHBOARD_HTML, logged_in=False)
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY rowid DESC').fetchall()
    
    # Estadisticas simples
    stats = {
        "total": len(users),
        "masters": len([u for u in users if u['plan'] == 'MASTER']),
        "active": len([u for u in users if u['status'] == 'ACTIVE'])
    }
    conn.close()
    return render_template_string(DASHBOARD_HTML, logged_in=True, users=users, stats=stats)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect('/admin')

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email')
    notes = request.form.get('notes')
    
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (email, plan, notes) VALUES (?, 'FREE', ?)", (email, notes))
        conn.commit()
    except:
        pass # Ignorar duplicados por ahora
    conn.close()
    return redirect('/admin')

@app.route('/admin/update', methods=['POST'])
def update_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email')
    action = request.form.get('action')
    
    conn = get_db_connection()
    if action == 'set_free':
        conn.execute("UPDATE users SET plan = 'FREE' WHERE email = ?", (email,))
    elif action == 'set_pro':
        conn.execute("UPDATE users SET plan = 'PRO' WHERE email = ?", (email,))
    elif action == 'set_master':
        conn.execute("UPDATE users SET plan = 'MASTER' WHERE email = ?", (email,))
    elif action == 'ban':
        conn.execute("UPDATE users SET status = 'BANNED' WHERE email = ?", (email,))
    elif action == 'unban':
        conn.execute("UPDATE users SET status = 'ACTIVE' WHERE email = ?", (email,))
        
    conn.commit()
    conn.close()
    return redirect('/admin')

# --- API Y SIMULADOR (IGUAL QUE ANTES) ---
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

@app.route('/live', methods=['GET'])
def live_data():
    return jsonify({
        "connected": True, "vin": "1G1JC5444W720589",
        "rpm": int(800 + (math.sin(time.time()) * 50) + (random.random() * 20)), 
        "coolant_temp": int(90 + (math.sin(time.time()/10) * 5)) 
    })

@app.route('/sensors/all', methods=['GET'])
def all_sensors():
    return jsonify({
        "intake_temp": 45, "maf": 3.5, "map": 35, "throttle_pos": 12, "vehicle_speed": 0, "battery_voltage": 13.8 + (random.random()*0.2), "o2_voltage": round(abs(math.sin(time.time())), 2), "fuel_level": 75, "oil_pressure": 40
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
