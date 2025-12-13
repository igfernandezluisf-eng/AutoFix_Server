# ==============================================================================
# PROYECTO: AutoFix Server (Backend)
# MÓDULO:   Restauración Admin Total (v5.4.0)
# REGLA DE ORO: INTEGRIDAD TOTAL - PROHIBIDO SIMPLIFICAR
# ==============================================================================

from flask import Flask, request, jsonify, render_template, render_template_string, redirect, url_for, session
from flask_cors import CORS
import psycopg2
from psycopg2 import pool
import random
import time
import math
import os
import sys

app = Flask(__name__)
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

# --- CONFIGURACIÓN DE BASE DE DATOS NEON ---
DATABASE_URL = os.environ.get("DATABASE_URL") 
ADMIN_PASSWORD = "admin"
conn_pool = None

def init_db():
    global conn_pool
    if DATABASE_URL:
        try:
            conn_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)
            conn = conn_pool.getconn()
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password TEXT,
                    plan TEXT DEFAULT 'FREE',
                    status TEXT DEFAULT 'ACTIVE',
                    notes TEXT
                );
            """)
            conn.commit()
            conn_pool.putconn(conn)
            print("✅ BASE DE DATOS POSTGRES ACTIVA.")
        except Exception as e: print(f"❌ ERROR DB: {e}")

init_db()

def get_db_connection(): return conn_pool.getconn()

# --- RUTA FRONTEND (Para Bluetooth HTTPS) ---
@app.route('/')
def serve_frontend():
    return render_template('index.html')

# --- DASHBOARD ADMIN RESTAURADO AL 100% ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoFix CONTROL TOWER v5.4</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; }
        .navbar { width: 100%; background: #161b22; border-bottom: 1px solid #30363d; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; }
        .container { width: 95%; max-width: 1200px; margin-top: 40px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; text-align: center; }
        .card .number { font-size: 2.5rem; font-weight: bold; color: white; }
        .panel { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 25px; margin-bottom: 30px; }
        input { padding: 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; width: 250px; }
        .btn-add { background: #238636; color: white; border: none; padding: 12px 25px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; background: #161b22; border-radius: 10px; overflow: hidden; }
        th { text-align: left; padding: 15px; background: #21262d; color: #8b949e; }
        td { padding: 15px; border-top: 1px solid #30363d; }
        .tag { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
        .act-btn { padding: 6px 12px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; border-radius: 6px; cursor: pointer; margin-right: 5px; }
        .login-wrap { display: flex; height: 100vh; align-items: center; justify-content: center; width: 100%; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="login-wrap">
        <div class="card" style="width: 400px;">
            <h1>AutoFix Admin</h1>
            <form method="POST" action="/admin/login">
                <input type="password" name="password" placeholder="Clave Maestra" required><br><br>
                <button type="submit" class="btn-add" style="width: 100%">ENTRAR</button>
            </form>
        </div>
    </div>
    {% else %}
    <div class="navbar">
        <div style="font-size: 1.5rem; font-weight: bold;">AutoFix <span>TOWER v5.4</span></div>
        <a href="/admin/logout" style="color: #f85149; text-decoration: none; font-weight: bold;">Cerrar Sesión</a>
    </div>
    <div class="container">
        <div class="stats-grid">
            <div class="card"><div class="number">{{ stats.total }}</div><h3>Usuarios Totales</h3></div>
            <div class="card" style="color: #e3b341;"><div class="number">{{ stats.masters }}</div><h3>Nivel Master</h3></div>
            <div class="card" style="color: #58a6ff;"><div class="number">{{ stats.pros }}</div><h3>Nivel Pro</h3></div>
            <div class="card" style="color: #3fb950;"><div class="number">{{ stats.active }}</div><h3>Activos</h3></div>
        </div>
        <div class="panel">
            <h3>Registrar Nuevo Mecánico</h3>
            <form action="/admin/add_user" method="POST">
                <input type="email" name="email" placeholder="Correo" required>
                <input type="text" name="notes" placeholder="Notas">
                <button type="submit" class="btn-add">CREAR CUENTA</button>
            </form>
        </div>
        <table>
            <thead><tr><th>Usuario / Notas</th><th>Nivel</th><th>Estado</th><th>Gestión</th></tr></thead>
            <tbody>
                {% for user in users %}
                <tr>
                    <td><strong>{{ user[0] }}</strong><br><small>{{ user[4] }}</small></td>
                    <td><span class="tag">{{ user[2] }}</span></td>
                    <td><span style="color: {% if user[3] == 'BANNED' %}#f85149{% else %}#3fb950{% endif %}">{{ user[3] }}</span></td>
                    <td>
                        <form action="/admin/update" method="POST">
                            <input type="hidden" name="email" value="{{ user[0] }}">
                            <button name="action" value="set_free" class="act-btn">FREE</button>
                            <button name="action" value="set_pro" class="act-btn" style="color:#58a6ff">PRO</button>
                            <button name="action" value="set_master" class="act-btn" style="color:#e3b341">MASTER</button>
                            {% if user[3] == 'BANNED' %}
                                <button name="action" value="unban" class="act-btn" style="color:#3fb950">UNLOCK</button>
                            {% else %}
                                <button name="action" value="ban" class="act-btn" style="color:#f85149">BLOCK</button>
                            {% endif %}
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'): return render_template_string(DASHBOARD_HTML, logged_in=False)
    conn = get_db_connection(); c = conn.cursor()
    c.execute('SELECT email, password, plan, status, notes FROM users ORDER BY email')
    users = c.fetchall()
    c.execute("SELECT plan, COUNT(email) FROM users GROUP BY plan")
    plan_counts = dict(c.fetchall())
    stats = {"total": len(users), "masters": plan_counts.get('MASTER', 0), "pros": plan_counts.get('PRO', 0), "active": len([u for u in users if u[3] == 'ACTIVE'])}
    conn_pool.putconn(conn); return render_template_string(DASHBOARD_HTML, logged_in=True, users=users, stats=stats)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect('/admin')
    return redirect('/admin')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect('/admin')

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email'); notes = request.form.get('notes')
    conn = get_db_connection(); c = conn.cursor()
    c.execute("INSERT INTO users (email, plan, notes, status) VALUES (%s, 'FREE', %s, 'ACTIVE') ON CONFLICT (email) DO NOTHING", (email, notes))
    conn.commit(); conn_pool.putconn(conn); return redirect('/admin')

@app.route('/admin/update', methods=['POST'])
def update_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email'); action = request.form.get('action')
    conn = get_db_connection(); c = conn.cursor()
    if action == 'set_free': c.execute("UPDATE users SET plan='FREE' WHERE email=%s", (email,))
    elif action == 'set_pro': c.execute("UPDATE users SET plan='PRO' WHERE email=%s", (email,))
    elif action == 'set_master': c.execute("UPDATE users SET plan='MASTER' WHERE email=%s", (email,))
    elif action == 'ban': c.execute("UPDATE users SET status='BANNED' WHERE email=%s", (email,))
    elif action == 'unban': c.execute("UPDATE users SET status='ACTIVE' WHERE email=%s", (email,))
    conn.commit(); conn_pool.putconn(conn); return redirect('/admin')

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        d = request.json
        conn = get_db_connection(); c = conn.cursor()
        c.execute('SELECT email, plan, status FROM users WHERE email=%s', (d.get('email'),))
        u = c.fetchone(); conn_pool.putconn(conn)
        if u and u[2] == 'ACTIVE': return jsonify({"status":"success", "plan":u[1]})
        return jsonify({"status":"error", "message":"Usuario bloqueado o no existe."})
    except: return jsonify({"status":"error"})

@app.route('/live')
def live_data():
    return jsonify({"connected": True, "vin": "1G1JC5444W720589", "rpm": int(800 + (math.sin(time.time()) * 50)), "coolant_temp": 85})

if __name__ == '__main__':
    app.run()
