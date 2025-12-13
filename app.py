# ==============================================================================
# PROYECTO: AutoFix Server (Backend)
# MÓDULO:   Servidor de Interfaz Seguro (v5.3.0)
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
# Usamos una clave secreta fija para mantener sesiones activas tras reinicios
app.secret_key = "AUTOFIX_SUPER_SECRET_KEY_2025"
CORS(app) 

# --- CONFIGURACIÓN DE BASE DE DATOS (NEON.TECH) ---
# Se extrae de la variable de entorno que usted ya configuró en Render
DATABASE_URL = os.environ.get("DATABASE_URL") 

ADMIN_PASSWORD = "admin"
conn_pool = None

def init_db():
    global conn_pool
    if DATABASE_URL:
        try:
            # Creamos un pool de conexiones para que el servidor sea rápido
            conn_pool = pool.SimpleConnectionPool(1, 20, DATABASE_URL)
            conn = conn_pool.getconn()
            c = conn.cursor()
            # Creamos la tabla de usuarios si no existe en Neon
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password TEXT,
                    plan TEXT DEFAULT 'FREE',
                    status TEXT DEFAULT 'ACTIVE',
                    notes TEXT
                );
            """)
            # Usuario maestro por defecto
            c.execute("INSERT INTO users (email, password, plan, notes) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING", 
                      ("mecanico@test.com", "1234", "MASTER", "Usuario Beta Maestro"))
            conn.commit()
            conn_pool.putconn(conn)
            print("✅ BASE DE DATOS POSTGRES CONECTADA EXITOSAMENTE.")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO DE BASE DE DATOS: {e}")
    else:
        print("❌ ERROR: DATABASE_URL no encontrada en las variables de entorno.")

# Inicializar al arrancar
init_db()

def get_db_connection():
    return conn_pool.getconn()

# ==============================================================================
# RUTA MAESTRA: SERVIDOR DE INTERFAZ (FRONTEND)
# ==============================================================================
@app.route('/')
def serve_frontend():
    """
    Esta ruta entrega el archivo index.html que está dentro de /templates/.
    Al cargarse desde https://autofix-server-7w12.onrender.com, 
    Android habilitará el acceso al Bluetooth.
    """
    return render_template('index.html')

# ==============================================================================
# PANEL DE ADMINISTRACIÓN (DASHBOARD HTML)
# ==============================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoFix CONTROL TOWER v5.3</title>
    <style>
        body { background: #0d1117; color: #c9d1d9; font-family: sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        .card { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        input { padding: 10px; background: #0d1117; border: 1px solid #30363d; color: white; border-radius: 5px; width: 80%; margin-bottom: 10px; }
        button { padding: 10px 20px; background: #238636; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button.ban { background: #da3633; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #161b22; }
        th, td { border: 1px solid #30363d; padding: 12px; text-align: left; }
        th { background: #21262d; color: #58a6ff; }
    </style>
</head>
<body>
    <div class="container">
    {% if not logged_in %}
        <div class="card">
            <h1>🔒 ACCESO ADMIN</h1>
            <form method="POST" action="/admin/login">
                <input type="password" name="password" placeholder="Clave Maestra de Seguridad" required>
                <button type="submit">ACCEDER AL PANEL</button>
            </form>
        </div>
    {% else %}
        <h1>AutoFix TOWER v5.3</h1>
        <div style="text-align: right; margin-bottom: 10px;">
            <a href="/admin/logout" style="color:#f85149; text-decoration: none; font-weight: bold;">[ CERRAR SESIÓN ]</a>
        </div>
        
        <div class="card">
            <h3>+ Registrar Nuevo Mecánico (Beta)</h3>
            <form action="/admin/add_user" method="POST">
                <input type="email" name="email" placeholder="Correo Electrónico" required>
                <input type="text" name="notes" placeholder="Notas o Nombre del Taller">
                <button type="submit">CREAR CUENTA PERMANENTE</button>
            </form>
        </div>

        <h3>Usuarios en Base de Datos (Neon)</h3>
        <table>
            <tr><th>Email</th><th>Plan</th><th>Estado</th><th>Gestión</th></tr>
            {% for user in users %}
            <tr>
                <td>{{ user[0] }}</td>
                <td><strong>{{ user[2] }}</strong></td>
                <td>{{ user[3] }}</td>
                <td>
                    <form action="/admin/update" method="POST" style="display:inline;">
                        <input type="hidden" name="email" value="{{ user[0] }}">
                        <button name="action" value="set_master">HACER MASTER</button>
                        <button name="action" value="ban" class="ban">BLOQUEAR</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    {% endif %}
    </div>
</body>
</html>
"""

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return render_template_string(DASHBOARD_HTML, logged_in=False)
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT email, password, plan, status, notes FROM users ORDER BY email ASC')
    users = c.fetchall()
    conn_pool.putconn(conn)
    return render_template_string(DASHBOARD_HTML, logged_in=True, users=users)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    if request.form.get('password') == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect('/admin')
    return "<h1>Error: Clave incorrecta</h1><a href='/admin'>Volver</a>"

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect('/admin')

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email')
    notes = request.form.get('notes')
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (email, plan, notes) VALUES (%s, 'FREE', %s) ON CONFLICT (email) DO NOTHING", 
                  (email, notes))
        conn.commit()
        conn_pool.putconn(conn)
    except: pass
    return redirect('/admin')

@app.route('/admin/update', methods=['POST'])
def update_user():
    if not session.get('logged_in'): return redirect('/admin')
    email = request.form.get('email')
    action = request.form.get('action')
    conn = get_db_connection()
    c = conn.cursor()
    if action == 'set_master':
        c.execute("UPDATE users SET plan='MASTER' WHERE email=%s", (email,))
    elif action == 'ban':
        c.execute("UPDATE users SET status='BANNED' WHERE email=%s", (email,))
    conn.commit()
    conn_pool.putconn(conn)
    return redirect('/admin')

# ==============================================================================
# API DE DATOS Y SIMULACIÓN
# ==============================================================================
@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        d = request.json
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT email, plan, status FROM users WHERE email=%s', (d.get('email'),))
        u = c.fetchone()
        conn_pool.putconn(conn)
        if u and u[2] == 'ACTIVE':
            return jsonify({"status":"success", "plan":u[1]})
        return jsonify({"status":"error", "message":"Usuario bloqueado o no existe."})
    except:
        return jsonify({"status":"error", "message":"Error de conexión a DB."})

@app.route('/live')
def live_data():
    """ Simulación de datos para las agujas """
    return jsonify({
        "connected": True,
        "vin": "1G1JC5444W720589",
        "rpm": int(800 + (math.sin(time.time()) * 40)), 
        "coolant_temp": 85 
    })

if __name__ == '__main__':
    # No habilitar debug en producción
    app.run()
