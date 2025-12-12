# ==============================================================================
# PROYECTO: AutoFix Server (Backend)
# MÓDULO:   Persistencia de Datos (PostgreSQL Ready)
# VERSIÓN:  4.0.0 (Data Saved)
# ==============================================================================

from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
import psycopg2
from psycopg2 import pool, sql
import random
import time
import math
import os
import sys

app = Flask(__name__)
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

# --- CONFIGURACIÓN DE BASE DE DATOS POSTGRES ---
# ¡IMPORTANTE! Reemplace esta URL con la que obtenga de ElephantSQL o Render Postgres
# Render buscará automáticamente una variable de entorno llamada DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@host:port/dbname") 

ADMIN_PASSWORD = "admin"

# Pool de conexiones (mejor rendimiento para un servidor)
conn_pool = None

# Inicializar DB
def init_db():
    global conn_pool
    if 'user' in DATABASE_URL:
        # En ambiente de Render o con URL completa
        conn_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)
    else:
        # Si la URL no está seteada, forzamos un error visible
        print("❌ ERROR: DATABASE_URL no está configurada. El servidor fallará.")
        sys.exit(1)
        
    try:
        conn = conn_pool.getconn()
        c = conn.cursor()
        
        # PostgreSQL syntax for creating table
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                password TEXT,
                plan TEXT DEFAULT 'FREE',
                status TEXT DEFAULT 'ACTIVE',
                notes TEXT
            );
        """)
        
        # Intentar crear usuario base si no existe
        c.execute("INSERT INTO users (email, password, plan, notes) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING", 
                  ("mecanico@test.com", "1234", "MASTER", "Usuario Beta"))
        
        conn.commit()
        conn_pool.putconn(conn)
        print("✅ BASE DE DATOS INICIALIZADA EN POSTGRES.")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO AL INICIAR POSTGRES: {e}")
        sys.exit(1)

def get_db_connection():
    return conn_pool.getconn()

# Ejecutar inicio DB
init_db() 

# --- DASHBOARD ADMIN ULTRA (HTML OMITIDO POR ESPACIO, ES EL MISMO ANTERIOR) ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoFix CONTROL TOWER v4.0</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        /* [ESTILOS OMITIDOS POR BREVEDAD - SON LOS MISMOS DE V3.1.0] */
        /* BASE */
        * { box-sizing: border-box; }
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Roboto', sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .navbar { width: 100%; background: #161b22; border-bottom: 1px solid #30363d; padding: 15px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
        .logo { font-size: 1.5rem; font-weight: bold; color: white; letter-spacing: 1px; }
        .logo span { color: #58a6ff; }
        .logout-btn { color: #f85149; text-decoration: none; font-weight: bold; border: 1px solid #f85149; padding: 5px 15px; border-radius: 6px; transition: 0.2s; }
        .logout-btn:hover { background: #f85149; color: white; }
        .container { width: 95%; max-width: 1200px; margin-top: 40px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; text-align: center; }
        .card h3 { margin: 0; font-size: 0.9rem; color: #8b949e; text-transform: uppercase; }
        .card .number { font-size: 2.5rem; font-weight: bold; color: white; margin: 10px 0 0 0; }
        .card.blue .number { color: #58a6ff; }
        .card.gold .number { color: #e3b341; }
        .card.green .number { color: #3fb950; }
        .panel { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 25px; margin-bottom: 30px; }
        .panel-header { font-size: 1.2rem; font-weight: bold; color: white; margin-bottom: 20px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        .form-row { display: flex; gap: 10px; flex-wrap: wrap; }
        input { flex: 1; padding: 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; outline: none; }
        input:focus { border-color: #58a6ff; }
        .btn-add { background: #238636; color: white; border: none; padding: 12px 25px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .btn-add:hover { background: #2ea043; }
        .table-responsive { overflow-x: auto; background: #161b22; border-radius: 10px; border: 1px solid #30363d; }
        table { width: 100%; border-collapse: collapse; min-width: 800px; }
        th { text-align: left; padding: 15px; background: #21262d; color: #8b949e; font-size: 0.85rem; text-transform: uppercase; }
        td { padding: 15px; border-top: 1px solid #30363d; color: #c9d1d9; vertical-align: middle; }
        tr:hover { background: #21262d; }
        .tag { padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; display: inline-block; }
        .tag-free { background: #30363d; color: #c9d1d9; border: 1px solid #8b949e; }
        .tag-pro { background: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid #58a6ff; }
        .tag-master { background: rgba(227, 179, 65, 0.15); color: #e3b341; border: 1px solid #e3b341; box-shadow: 0 0 8px rgba(227, 179, 65, 0.2); }
        .tag-banned { background: rgba(248, 81, 73, 0.15); color: #f85149; text-decoration: line-through; border: 1px solid #f85149; }
        .actions { display: flex; gap: 5px; }
        .act-btn { padding: 6px 12px; border: 1px solid #30363d; background: #21262d; color: #c9d1d9; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 500; transition: 0.2s; }
        .act-btn:hover { background: #30363d; color: white; }
        .act-btn.danger { color: #f85149; border-color: #f85149; }
        .act-btn.danger:hover { background: #f85149; color: white; }
        .login-wrap { display: flex; height: 100vh; width: 100%; align-items: center; justify-content: center; background: #010409; }
        .login-card { width: 400px; padding: 40px; background: #161b22; border: 1px solid #30363d; border-radius: 12px; text-align: center; }
        .login-btn { width: 100%; margin-top: 20px; padding: 12px; background: #58a6ff; border: none; border-radius: 6px; color: black; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>

    {% if not logged_in %}
    <div class="login-wrap">
        <div class="login-card">
            <h1 style="margin-bottom:30px">AutoFix <span style="color:#58a6ff">SECURE</span></h1>
            <form method="POST" action="/admin/login">
                <input type="password" name="password" placeholder="🔒 Ingrese Clave de Admin" required style="text-align:center; font-size:1.1rem;">
                <button type="submit" class="login-btn">ACCEDER AL SISTEMA</button>
            </form>
            {% if error %} <p style="color:#f85149; margin-top:15px">⛔ Acceso Denegado</p> {% endif %}
        </div>
    </div>
    {% else %}

    <div class="navbar">
        <div class="logo">AutoFix <span>TOWER v4.0</span></div>
        <a href="/admin/logout" class="logout-btn">Cerrar Sesión</a>
    </div>

    <div class="container">
        
        <div class="stats-grid">
            <div class="card"><div class="number">{{ stats.total }}</div><h3>Usuarios Totales</h3></div>
            <div class="card gold"><div class="number">{{ stats.masters }}</div><h3>Nivel Master</h3></div>
            <div class="card blue"><div class="number">{{ stats.pros }}</div><h3>Nivel Pro</h3></div>
            <div class="card green"><div class="number">{{ stats.active }}</div><h3>Activos</h3></div>
        </div>

        <div class="panel">
            <div class="panel-header">Registrar Nuevo Usuario Beta</div>
            <form action="/admin/add_user" method="POST" class="form-row">
                <input type="email" name="email" placeholder="Correo del Mecánico" required>
                <input type="text" name="notes" placeholder="Nota (Ej. Amigo Juan)">
                <button type="submit" class="btn-add">CREAR CUENTA</button>
            </form>
        </div>

        <div class="table-responsive">
            <table>
                <thead>
                    <tr>
                        <th>Usuario / Notas</th>
                        <th>Nivel de Acceso</th>
                        <th>Estado</th>
                        <th>Gestión de Licencia</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>
                            <strong style="color:white; font-size:1rem">{{ user.email }}</strong><br>
                            <span style="color:#8b949e; font-size:0.8rem">{{ user.notes }}</span>
                        </td>
                        <td>
                            <span class="tag 
                                {% if user.plan == 'MASTER' %}tag-master{% elif user.plan == 'PRO' %}tag-pro{% else %}tag-free{% endif %}">
                                {{ user.plan }}
                            </span>
                        </td>
                        <td>
                            <span style="color: {% if user.status == 'BANNED' %}#f85149{% else %}#3fb950{% endif %}">
                                {{ user.status }}
                            </span>
                        </td>
                        <td>
                            <form action="/admin/update" method="POST" class="actions">
                                <input type="hidden" name="email" value="{{ user.email }}">
                                <button name="action" value="set_free" class="act-btn" title="Nivel Básico">FREE</button>
                                <button name="action" value="set_pro" class="act-btn" title="Nivel Intermedio" style="color:#58a6ff">PRO</button>
                                <button name="action" value="set_master" class="act-btn" title="Nivel Dios" style="color:#e3b341">MASTER</button>
                                
                                {% if user.status == 'BANNED' %}
                                    <button name="action" value="unban" class="act-btn" style="color:#3fb950">UNLOCK</button>
                                {% else %}
                                    <button name="action" value="ban" class="act-btn danger">BLOCK</button>
                                {% endif %}
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div style="text-align:center; margin-top:40px; color:#8b949e; font-size:0.8rem;">
            AutoFix Server Backend • Running on Render Cloud
        </div>

    </div>
    {% endif %}

</body>
</html>
"""

# --- RUTAS DE LOGIN Y ADMIN ---
@app.route('/admin', methods=['GET'])
def admin_panel():
    try:
        if not session.get('logged_in'):
            return render_template_string(DASHBOARD_HTML, logged_in=False)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Consultar usuarios
        c.execute('SELECT email, plan, status, notes FROM users ORDER BY email')
        users = c.fetchall()
        
        # Calcular estadísticas
        c.execute("SELECT plan, COUNT(email) FROM users GROUP BY plan")
        plan_counts = dict(c.fetchall())
        
        stats = {
            "total": len(users),
            "masters": plan_counts.get('MASTER', 0),
            "pros": plan_counts.get('PRO', 0),
            "active": len([u for u in users if u[2] == 'ACTIVE']) # status is the 3rd element
        }

        conn_pool.putconn(conn)
        return render_template_string(DASHBOARD_HTML, logged_in=True, users=users, stats=stats)
    except Exception as e:
        return f"Error Crítico Dashboard: {e}"

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
        c = conn.cursor()
        c.execute("INSERT INTO users (email, plan, notes) VALUES (%s, 'FREE', %s) ON CONFLICT (email) DO NOTHING", 
                     (request.form.get('email'), request.form.get('notes')))
        conn.commit()
        conn_pool.putconn(conn)
    except Exception as e: 
        print(f"Error al agregar usuario: {e}")
    return redirect('/admin')

@app.route('/admin/update', methods=['POST'])
def update_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email')
    action = request.form.get('action')
    conn = get_db_connection()
    c = conn.cursor()
    if action == 'set_free': c.execute("UPDATE users SET plan='FREE' WHERE email=%s", (email,))
    elif action == 'set_pro': c.execute("UPDATE users SET plan='PRO' WHERE email=%s", (email,))
    elif action == 'set_master': c.execute("UPDATE users SET plan='MASTER' WHERE email=%s", (email,))
    elif action == 'ban': c.execute("UPDATE users SET status='BANNED' WHERE email=%s", (email,))
    elif action == 'unban': c.execute("UPDATE users SET status='ACTIVE' WHERE email=%s", (email,))
    conn.commit()
    conn_pool.putconn(conn)
    return redirect('/admin')

# --- API Y SIMULADOR (SIN CAMBIOS) ---
@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        d = request.json
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT email, plan, status FROM users WHERE email=%s', (d.get('email'),))
        u = c.fetchone()
        conn_pool.putconn(conn)
        
        if u and u[2] == 'ACTIVE': # u[2] is status
            return jsonify({"status":"success", "plan":u[1]}) # u[1] is plan
        
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
