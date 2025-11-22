import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from ai_hiper import get_llama_response, generate_query_language
from extension import facturas_bp   # <--- tu blueprint OK


# -----------------------------------
# CREAR APP
# -----------------------------------
app = Flask(__name__)
app.secret_key = "clave_secreta_123"


# -----------------------------------
# REGISTRAR BLUEPRINT
# -----------------------------------
app.register_blueprint(facturas_bp)


# -----------------------------------
# CONFIG
# -----------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

SECRET_FILE = os.path.join(BASE_DIR, "secret.brokey")
ADMIN_PASS_FILE = os.path.join(BASE_DIR, "admin_pass.txt")


# -----------------------------------
# CREAR DB SQLite SI NO EXISTE
# -----------------------------------
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

        print("[OK] Base de datos creada.")
    else:
        print("[OK] Base de datos ya existe.")


# -----------------------------------
# CONTRASEÑA ADMIN
# -----------------------------------
def load_admin_password():
    if os.path.exists(SECRET_FILE):
        try:
            with open(SECRET_FILE, "r", encoding="utf-8") as f:
                return f.readline().strip()
        except:
            pass

    if os.path.exists(ADMIN_PASS_FILE):
        try:
            with open(ADMIN_PASS_FILE, "r", encoding="utf-8") as f:
                return f.readline().strip()
        except:
            pass

    # Si no existe ningún archivo, crearlo
    try:
        with open(ADMIN_PASS_FILE, "w", encoding="utf-8") as f:
            f.write("1234")
        print("[WARN] Se creó admin_pass.txt con contraseña 1234")
    except:
        pass

    return "1234"


ADMIN_PASS = load_admin_password()


# -----------------------------------
# CONEXIÓN DB (Thread-Safe)
# -----------------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH, check_same_thread=False)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# -----------------------------------
# RUTAS PRINCIPALES
# -----------------------------------
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

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password, status, created_at) VALUES (?, ?, 'pending', ?)",
                (username, password, datetime.utcnow().isoformat())
            )
            conn.commit()
            flash("Cuenta creada. Espera aprobación del admin.", "info")
        except sqlite3.IntegrityError:
            flash("Ese usuario ya existe.", "danger")

        return redirect(url_for("login"))

    return render_template("register.html")



#   /\_____/\  
#   \ 9   9 /  
#    \>--< /   19  
#    (      )19  
#     n   n

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # Login admin
        if username.lower() == "admin" and password == ADMIN_PASS:
            session.clear()
            session["admin"] = True
            flash("Sesión de administrador iniciada.", "success")
            return redirect(url_for("admin_panel"))

        # Login usuario normal
        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id, status FROM users WHERE username=? AND password=?", (username, password))
        row = c.fetchone()

        if row:
            uid, status = row
            if status == "approved":
                session.clear()
                session["user"] = username
                flash(f"Bienvenido, {username}.", "success")
                return redirect(url_for("home"))
            elif status == "pending":
                flash("Tu cuenta está pendiente.", "warning")
            else:
                flash("Tu cuenta fue rechazada.", "danger")
        else:
            flash("Credenciales incorrectas.", "danger")

    return render_template("login.html")


@app.route("/home")
def home():
    if "user" not in session:
        flash("Inicia sesión primero.", "warning")
        return redirect(url_for("login"))

    return render_template("home.html", user=session.get("user"))


@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "admin" not in session:
        flash("Acceso denegado.", "danger")
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        uid = request.form.get("id")
        action = request.form.get("action")

        if uid and action:
            if action == "approve":
                c.execute("UPDATE users SET status='approved' WHERE id=?", (uid,))
            elif action == "reject":
                c.execute("UPDATE users SET status='rejected' WHERE id=?", (uid,))
            conn.commit()

    c.execute("SELECT id, username, status, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()

    return render_template("admin.html", users=users)


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# -----------------------------------
# CHAT IA
# -----------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return {"error": "No autenticado"}, 401

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return {"error": "Mensaje vacío"}, 400

    try:
        ai_response = get_llama_response(user_message)
        query_language = generate_query_language(user_message)

        return {
            "ai_response": ai_response,
            "query_language": query_language,
            "success": True
        }

    except Exception as e:
        print(f"[ERROR] Chat falló: {e}")
        return {"error": "Error interno"}, 500


# -----------------------------------
# MAIN
# -----------------------------------
if __name__ == "__main__":
    init_db()
    print("[INFO] Contraseña admin cargada.")
    app.run(host="0.0.0.0", port=5000)
