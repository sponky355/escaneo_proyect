from flask import Blueprint, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename

# Blueprint
facturas_bp = Blueprint("facturas", __name__, url_prefix="/facturas")

# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["escaneo_db"]
facturas_col = db["facturas"]


# ---------------------------
# LISTAR FACTURAS – /facturas/lista
# ---------------------------
@facturas_bp.route("/lista")
def facturas_lista():
    facturas = list(facturas_col.find())
    return render_template("facturas.html", facturas=facturas)


# ---------------------------
# SUBIR ARCHIVO – /facturas/upload
# ---------------------------
@facturas_bp.route("/upload", methods=["POST"])
def facturas_upload():

    if "file" not in request.files:
        flash("No se recibió archivo.")
        return redirect(url_for("facturas.facturas_lista"))

    file = request.files["file"]

    if file.filename == "":
        flash("Archivo inválido.")
        return redirect(url_for("facturas.facturas_lista"))

    filename = secure_filename(file.filename)
    save_path = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(save_path)

    facturas_col.insert_one({
        "nombre_archivo": filename,
        "fecha_subida": "hoy",
        "path": save_path
    })

    flash("Factura subida con éxito.")
    return redirect(url_for("facturas.facturas_lista"))


# ---------------------------
# DESCARGAR JSON – /facturas/download/<id>
# ---------------------------
@facturas_bp.route("/download/<id_mongo>")
def facturas_download(id_mongo):
    flash("Aquí iría la lógica de descarga JSON.")
    return redirect(url_for("facturas.facturas_lista"))


# ---------------------------
# ELIMINAR FACTURA – /facturas/delete/<id>
# ---------------------------
@facturas_bp.route("/delete/<id_mongo>", methods=["POST"])
def facturas_delete(id_mongo):
    facturas_col.delete_one({"_id": id_mongo})  # ajusta si usas ObjectId
    flash("Factura eliminada correctamente.")
    return redirect(url_for("facturas.facturas_lista"))

#   /\_____/\  
#   \ 9   9 /  
#    \>--< /   19  
#    (      )19  
#     n   n
