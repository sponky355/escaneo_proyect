import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from ai_hiper import get_llama_response, generate_query_language  # helpers de IA

# -------------------------
# Configuración básica
# -------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

SECRET_FILE = os.path.join(BASE_DIR, "secret.brokey")    
ADMIN_PASS_FILE = os.path.join(BASE_DIR, "admin_pass.txt")  

app = Flask(__name__)
app.secret_key = "clave_secreta_123"  # cámbiala si quieres

# -------------------------
# Inicializar DB
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
# Contraseña Admin
# -------------------------
def load_admin_password():
    if os.path.exists(SECRET_FILE):
        try:
            with open(SECRET_FILE, "r", encoding="utf-8") as f:
                pw = f.readline().strip()
                if pw:
                    print(f"[INFO] Contraseña admin cargada desde '{os.path.basename(SECRET_FILE)}'")
                    return pw
        except Exception as e:
            print(f"[WARN] Error leyendo {SECRET_FILE}: {e}")

    if os.path.exists(ADMIN_PASS_FILE):
        try:
            with open(ADMIN_PASS_FILE, "r", encoding="utf-8") as f:
                pw = f.readline().strip()
                if pw:
                    print(f"[INFO] Contraseña admin cargada desde '{os.path.basename(ADMIN_PASS_FILE)}'")
                    return pw
        except Exception as e:
            print(f"[WARN] Error leyendo {ADMIN_PASS_FILE}: {e}")

    # Crear admin_pass.txt con contraseña por defecto
    try:
        with open(ADMIN_PASS_FILE, "w", encoding="utf-8") as f:
            f.write("1234")
        print(f"[WARN] No se encontró ningún archivo de contraseña. Se creó '{os.path.basename(ADMIN_PASS_FILE)}' con contraseña por defecto '1234'.")
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
# Rutas principales
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

        # admin login
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

@app.route("/home")
def home():
    if "user" not in session:
        flash("Inicia sesión primero.", "warning")
        return redirect(url_for("login"))
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
# Ruta para IA
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return {"error": "No autenticado"}, 401
    
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return {"error": "Mensaje vacío"}, 400
    
    try:
        print(f"[CHAT] Usuario {session['user']} envió: {user_message}")
        
        # Llamar a los helpers de IA
        ai_response = get_llama_response(user_message)
        query_language = generate_query_language(user_message)
        
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
        }, 500  # Comentario correcto en Python

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    init_db()
    print(f"[INFO] ADMIN password loaded (priority: secret.brokey then admin_pass.txt).")
    app.run(host="0.0.0.0", port=5000)
