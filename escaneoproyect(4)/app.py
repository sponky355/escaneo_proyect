import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

## librerias de inteliegencia artificial 
import ollama
import requests
import json


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

# Archivos posibles donde puede estar la contraseña admin (orden de prioridad)
SECRET_FILE = os.path.join(BASE_DIR, "secret.brokey")    # TU archivo actual
ADMIN_PASS_FILE = os.path.join(BASE_DIR, "admin_pass.txt")  # fallback

app = Flask(__name__)
app.secret_key = "clave_secreta_123"  # cámbiala si quieres







# -------------------------
# Inicializar DB si hace falta
# -------------------------
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        print("[OK] Base de datos creada correctamente.")
    else:
        print("[OK] Base de datos ya existe.")

# -------------------------
# Leer contraseña admin (SECRET_FILE > ADMIN_PASS_FILE > crear admin_pass.txt)
# -------------------------
def load_admin_password():
    # 1) Si existe secret.brokey usarla
    if os.path.exists(SECRET_FILE):
        try:
            with open(SECRET_FILE, "r", encoding="utf-8") as f:
                pw = f.readline().strip()
                if pw:
                    print(f"[INFO] Contraseña admin cargada desde '{os.path.basename(SECRET_FILE)}'")
                    return pw
        except Exception as e:
            print(f"[WARN] Error leyendo {SECRET_FILE}: {e}")

    # 2) Si no, intentar admin_pass.txt
    if os.path.exists(ADMIN_PASS_FILE):
        try:
            with open(ADMIN_PASS_FILE, "r", encoding="utf-8") as f:
                pw = f.readline().strip()
                if pw:
                    print(f"[INFO] Contraseña admin cargada desde '{os.path.basename(ADMIN_PASS_FILE)}'")
                    return pw
        except Exception as e:
            print(f"[WARN] Error leyendo {ADMIN_PASS_FILE}: {e}")

    # 3) Si ninguno existe, crear admin_pass.txt con contraseña por defecto '1234'
    try:
        with open(ADMIN_PASS_FILE, "w", encoding="utf-8") as f:
            f.write("1234")
        print(f"[WARN] No se encontró {os.path.basename(SECRET_FILE)} ni {os.path.basename(ADMIN_PASS_FILE)}. Se creó '{os.path.basename(ADMIN_PASS_FILE)}' con contraseña por defecto '1234'.")
    except Exception as e:
        print(f"[ERROR] No se pudo crear {ADMIN_PASS_FILE}: {e}")
    return "1234"

ADMIN_PASS = load_admin_password()

# -------------------------
# DB helpers
# -------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# -------------------------
# Rutas
# -------------------------
@app.route("/")
def index():
    if "admin" in session:
        return redirect(url_for("admin_panel"))
    if "user" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("register"))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password, status, created_at) VALUES (?, ?, 'pending', ?)",
                (username, password, datetime.utcnow().isoformat())
            )
            conn.commit()
            flash("Cuenta creada. Espera aprobación del administrador.", "info")
            print(f"[INFO] Nuevo registro '{username}' -> pending")
        except sqlite3.IntegrityError:
            flash("Ese usuario ya existe.", "danger")
            print(f"[WARN] Intento registro duplicado: {username}")
        finally:
            conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # admin login (usuario 'admin' comparado con ADMIN_PASS)
        if username.lower() == "admin" and password == ADMIN_PASS:
            session.clear()
            session["admin"] = True
            flash("Sesión de administrador iniciada.", "success")
            print("[INFO] Admin inició sesión.")
            return redirect(url_for("admin_panel"))

        # usuario normal
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, status FROM users WHERE username=? AND password=?", (username, password))
        row = c.fetchone()
        conn.close()

        if row:
            uid, status = row
            if status == "approved":
                session.clear()
                session["user"] = username
                flash(f"Bienvenido, {username}.", "success")
                print(f"[INFO] Usuario '{username}' inició sesión (approved).")
                return redirect(url_for("home"))
            elif status == "pending":
                flash("Tu cuenta está pendiente de aprobación.", "warning")
                print(f"[INFO] Usuario '{username}' intentó login (pending).")
            else:
                flash("Tu cuenta fue rechazada.", "danger")
                print(f"[INFO] Usuario '{username}' intentó login (rejected).")
        else:
            flash("Credenciales incorrectas.", "danger")
            print(f"[WARN] Login fallido para usuario: {username}")

    return render_template("login.html")

#@app.route("/home")
# def home():
#    if "user" not in session:
#        flash("Inicia sesión primero.", "warning")
#        return redirect(url_for("login"))
#    return render_template("home.html", user=session.get("user"))

## refuerzo de enrutamniento hacia estatic 

@app.route("/home")
def home():
    if "user" not in session:
        flash("Inicia sesión primero.", "warning")
        return redirect(url_for("login"))
    
    # AGREGAR ESTA LÍNEA PARA DEBUG
    print(f"[DEBUG] Serving home for {session.get('user')}")
    
    return render_template("home.html", user=session.get("user"))




@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "admin" not in session:
        flash("Acceso denegado. Solo admin.", "danger")
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        uid = request.form.get("id")
        action = request.form.get("action")
        if uid and action:
            if action == "approve":
                c.execute("UPDATE users SET status='approved' WHERE id=?", (uid,))
                conn.commit()
                flash("Usuario aprobado.", "success")
                print(f"[ADMIN] Aprobado id={uid}")
            elif action == "reject":
                c.execute("UPDATE users SET status='rejected' WHERE id=?", (uid,))
                conn.commit()
                flash("Usuario rechazado.", "info")
                print(f"[ADMIN] Rechazado id={uid}")

    c.execute("SELECT id, username, status, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users)

@app.route("/logout")
def logout():
    who = "admin" if "admin" in session else session.get("user")
    session.clear()
    flash("Sesión cerrada.", "info")
    print(f"[INFO] Sesión cerrada: {who}")
    return redirect(url_for("login"))

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    init_db()
    print(f"[INFO] ADMIN password loaded (priority: secret.brokey then admin_pass.txt).")
    app.run(host="127.0.0.1", port=5000, debug=True)


## este es un testeo 
#
#
#app.route("/test-css")
#ef test_css():
#   return """
#   <html>
#       <head>
#           <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
#       </head>
#       <body>
#           <h1>Test CSS</h1>
#           <p>Si esto tiene estilo, el problema está en home.html</p>
#       </body>
#   </html>
#   """


#
#
#app.route("/debug-static")
#ef debug_static():
#   static_folder = app.static_folder
#   exists = os.path.exists(os.path.join(static_folder, "styles.css"))
#   return f"Static folder: {static_folder}<br>CSS exists: {exists}"





# AGREGAR ESTAS FUNCIONES DESPUÉS DE LAS IMPORTACIONES

def get_llama_response(user_message, conversation_history=[]):
    """
    Obtener respuesta de Llama usando ollama
    """
    try:
        # Preparar el historial de conversación
        messages = conversation_history + [{"role": "user", "content": user_message}]
        
        # Llamar a Llama
        response = ollama.chat(
            model='llama2',  # o 'llama3', 'mistral', etc.
            messages=messages
        )
        
        return response['message']['content']
    
    except Exception as e:
        print(f"Error con Llama: {e}")
        return "Lo siento, hubo un error procesando tu consulta."

def generate_query_language(user_message):
    """
    Generar lenguaje de consulta basado en el mensaje del usuario
    """
    try:
        prompt = f"""
        El usuario dijo: "{user_message}"
        
        Genera un lenguaje de consulta estructurado (como SQL, JSON, o pseudocódigo) 
        basado en esta solicitud. Responde SOLO con el código, sin explicaciones.
        """
        
        response = ollama.chat(
            model='llama2',
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response['message']['content']
    
    except Exception as e:
        print(f"Error generando query: {e}")
        return f"# Error generando lenguaje de consulta\n# Mensaje: {user_message}"

# AGREGAR ESTA RUTA NUEVA EN app.py (después de la ruta /home)
#@app.route("/chat", methods=["POST"])
#def chat():
#    if "user" not in session:
#        return json.dumps({"error": "No autenticado"}), 401
#    
#    user_message = request.json.get("message", "").strip()
#    if not user_message:
#        return json.dumps({"error": "Mensaje vacío"}), 400
#    
#    try:
#        # Obtener respuesta de Llama
#        ai_response = get_llama_response(user_message)
#        
#        # Generar lenguaje de consulta
#        query_language = generate_query_language(user_message)
#        
#        return json.dumps({
#            "ai_response": ai_response,
#
#             "success": True
#        })
#    
#    except Exception as e:
#        print(f"Error en chat: {e}")
#        return json.dumps({
#            "error": "Error interno del servidor",
#            "success": False
#        }), 500

# este es un codigo en fase de desarrollo solo es una referencia para el desarrollo 

@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return {"error": "No autenticado"}, 401
    
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return {"error": "Mensaje vacío"}, 400
    
    try:
        print(f"[CHAT] Usuario {session['user']} envió: {user_message}")
        
        # Obtener respuesta de Ollama
        response = ollama.chat(
            model='llama2',
            messages=[{"role": "user", "content": user_message}]
        )
        ai_response = response['message']['content']
        
        # Generar lenguaje de consulta (versión simple)
        query_response = ollama.chat(
            model='llama2',
            messages=[{
                "role": "user", 
                "content": f"Convierte esta consulta en un lenguaje estructurado como SQL o JSON: '{user_message}'. Responde solo con el código."
            }]
        )
        query_language = query_response['message']['content']
        
        print(f"[CHAT] Respuesta generada exitosamente")
        
        return {
            "ai_response": ai_response,
            "query_language": query_language,
            "success": True
        }
    
    except Exception as e:
        print(f"[ERROR] Error en chat: {e}")
        return {
            "error": "Error interno del servidor",
            "success": False
        }, 500