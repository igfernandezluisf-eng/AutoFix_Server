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
import sys

app = Flask(__name__)
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

# Configuración de DB
if os.name == 'nt':
    DB_NAME = "autofix_users.db"
else:
    DB_NAME = "/tmp/autofix_users.db"

ADMIN_PASSWORD = "admin"

# Inicializar DB
def init_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT, plan TEXT DEFAULT 'FREE', status TEXT DEFAULT 'ACTIVE', notes TEXT)''')
        # Usuario de prueba
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

# Ejecutar inicio DB
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
        /* ESTILO GENERAL TECH-NOIR */
        body { background-color: #0f1015; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; padding: 0; margin: 0; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        
        /* HEADER */
        .header { width: 100%; background: #141419; padding: 20px; border-bottom: 1px solid #333; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { margin: 0; color: #fff; letter-spacing: 2px; font-weight: 800; }
        h1 span { color: #00f3ff; }

        /* CONTENEDOR PRINCIPAL */
        .container { width: 90%; max-width: 1000px; margin-top: 30px; }

        /* ESTADISTICAS */
        .stats { display: flex; gap: 20px; justify-content: center; margin-bottom: 30px; flex-wrap: wrap; }
        .stat-card { background: #1a1b20; padding: 20px; border-radius: 12px; border: 1px solid #333; text-align: center; min-width: 150px; flex: 1; transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); border-color: #00f3ff; }
        .stat-num { font-size: 2.5rem; font-weight: bold; color: white; margin: 0; }
        .stat-label { color: #888; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }

        /* FORMULARIO AGREGAR */
        .add-box { background: #1a1b20; padding: 20px; border-radius: 12px; border: 1px solid #333; display: flex; gap: 10px; align-items: center; margin-bottom: 30px; flex-wrap: wrap; }
        .add-title { font-weight: bold; color: #00ff9d; margin-right: 15px; }
        input { flex: 1; padding: 12px; background: #0f1015; border: 1px solid #444; color: white; border-radius: 6px; outline: none; }
        input:focus { border-color: #00f3ff; }
        button { padding: 12px 20px; background: #00f3ff; color: #000; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; }
        button:hover { background: #00c2cc; transform: scale(1.05); }

        /* TABLA DE USUARIOS */
        .table-container { background: #1a1b20; border-radius: 12px; overflow: hidden; border: 1px solid #333; }
        table { width: 100%; border-collapse: collapse; }
        th { background-color: #222; color: #888; padding: 15px; text-align: left; font-size: 0.8rem; text-transform: uppercase; }
        td { padding: 15px; border-bottom: 1px solid #2a2a30; color: #ccc; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background-color: #25262c; }
        
        /* BADGES (ETIQUETAS) */
        .badge { padding: 5px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; display: inline-block; }
        .bg-free { background: #333; color: #aaa; border: 1px solid #555; }
        .bg-pro { background: rgba(0, 243, 255, 0.1); color: #00f3ff; border: 1px solid #00f3ff; }
        .bg-master { background: rgba(255, 170, 0, 0.1); color: #ffaa00; border: 1px solid #ffaa00; box-shadow: 0 0 10px rgba(255, 170, 0, 0.2); }
        .text-banned { color: #ff0055; font-weight: bold; text-decoration: line-through; }
        
        /* BOTONES DE ACCION */
        .action-form { display: inline-flex; gap: 5px; }
        .mini-btn { padding: 5px 10px; font-size: 0.7rem; border-radius: 4px; opacity: 0.7; }
        .mini-btn:hover { opacity: 1; transform: scale(1.1); }
        .btn-ban { background: #ff0055; color: white; }
        
        /* LOGIN BOX */
        .login-wrapper { display: flex; height: 100vh; width: 100%; align-items: center; justify-content: center; background: radial-gradient(circle at center, #1a1b20 0%, #0f1015 100%); }
        .login-box { width: 350px; padding: 40px; background: #141419; border: 1px solid #333; border-radius: 15px; text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        
        .footer-link { margin-top: 40px; margin-bottom: 20px; color: #666; text-decoration: none; font-size: 0.9rem; }
        .footer-link:hover { color: #fff; }

    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-wrapper">
        <div class="login-box">
            <h2 style="color:#fff; margin-bottom:30px">ACCESO <span style="color:#00f3ff">ADMIN</span></h2>
            <form method="POST" action="/admin/login">
                <input type="password" name="password" placeholder="Ingrese Clave Maestra" required style="text-align:center; font-size:1.2rem;">
                <button type="submit" style="width:100%; margin-top:20px;">INICIAR SESIÓN</button>
            </form>
            {% if error %}
                <p style="color:#ff0055; margin-top:15px">Clave incorrecta</p>
            {% endif %}
        </div>
    </div>
    {% else %}
    
    <div class="header">
        <h1>AutoFix <span style="color:#00f3ff">COMMAND CENTER</span></h1>
    </div>

    <div class="container">
        
        <div class="stats">
            <div class="stat-card"><p class="stat-num">{{ stats.total }}</p><p class="stat-label">Usuarios Totales</p></div>
            <div class="stat-card" style="border-color:#ffaa00"><p class="stat-num" style="color:#ffaa00">{{ stats.masters }}</p><p class="stat-label">Nivel MASTER</p></div>
            <div class="stat-card" style="border-color:#00ff9d"><p class="stat-num" style="color:#00ff9d">{{ stats.active }}</p><p class="stat-label">Activos</p></div>
        </div>

        <div class="add-box">
            <span class="add-title">+ NUEVO BETA TESTER</span>
            <form action="/admin/add_user" method="POST" style="display:flex; gap:10px; flex:1;">
                <input type="email" name="email" placeholder="Email del Mecánico" required>
                <input type="text" name="notes" placeholder="Notas (Ej. Taller Norte)">
                <button type="submit" style="background:#00ff9d; color:black;">REGISTRAR</button>
            </form>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Usuario / Email</th>
                        <th>Plan Actual</th>
                        <th>Estado</th>
                        <th>Acciones Rápidas</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>
                            <strong style="color:white; font-size:1rem;">{{ user.email }}</strong><br>
                            <small style="color:#666">{{ user.notes }}</small>
                        </td>
                        <td>
                            <span class="badge 
                                {% if user.plan == 'MASTER' %}bg-master{% elif user.plan == 'PRO' %}bg-pro{% else %}bg-free{% endif %}">
                                {{ user.plan }}
                            </span>
                        </td>
                        <td>
                            {% if user.status == 'BANNED' %}
                                <span class="text-banned">BLOQUEADO</span>
                            {% else %}
                                <span style="color:#00ff9d">ACTIVO</span>
                            {% endif %}
                        </td>
                        <td>
                            <form action="/admin/update" method="POST" class="action-form">
                                <input type="hidden" name="email" value="{{ user.email }}">
                                <button name="action" value="set_free" class="mini-btn bg-free" title="Bajar a Gratis">FREE</button>
                                <button name="action" value="set_pro" class="mini-btn bg-pro" title="Subir a PRO">PRO</button>
                                <button name="action" value="set_master" class="mini-btn bg-master" title="DAR MODO DIOS">MASTER</button>
                                {% if user.status == 'BANNED' %}
                                    <button name="action" value="unban" class="mini-btn" style="background:#00ff9d; color:black">UNLOCK</button>
                                {% else %}
                                    <button name="action" value="ban" class="mini-btn btn-ban">BAN</button>
                                {% endif %}
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div style="text-align:center;">
            <a href="/admin/logout" class="footer-link">🔒 Cerrar Sesión Segura</a>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

# --- RUTAS DE LOGIN Y ADMIN ---
@app.route('/admin', methods=['GET'])
def admin_panel():
    if not session.get('logged_in'):
        return render_template_string(DASHBOARD_HTML, logged_in=False)
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users ORDER BY rowid DESC').fetchall()
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
    else:
        return render_template_string(DASHBOARD_HTML, logged_in=False, error=True)

@app.route('/admin/logout')
def admin_logout():
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
def update_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email')
    action = request.form.get('action')
    conn = get_db_connection()
    if action == 'set_free': conn.execute("UPDATE users SET plan='FREE' WHERE email=?", (email,))
    elif action == 'set_pro': conn.execute("UPDATE users SET plan='PRO' WHERE email=?", (email,))
    elif action == 'set_master': conn.execute("UPDATE users SET plan='MASTER' WHERE email=?", (email,))
    elif action == 'ban': conn.execute("UPDATE users SET status='BANNED' WHERE email=?", (email,))
    elif action == 'unban': conn.execute("UPDATE users SET status='ACTIVE' WHERE email=?", (email,))
    conn.commit(); conn.close()
    return redirect('/admin')

# --- API Y SIMULADOR (SIN CAMBIOS) ---
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
