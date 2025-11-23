from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from pymongo import MongoClient
import os
import pandas as pd
from werkzeug.utils import secure_filename
from bson import ObjectId
import json
from datetime import datetime

facturas_bp = Blueprint("facturas", __name__, url_prefix="/facturas")

# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["escaneo_db"]
facturas_col = db["facturas"]

# Configuración de uploads (solo temporal)
UPLOAD_FOLDER = "uploads_temp"
ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def excel_to_json(file):
    """
    Convertir archivo Excel a JSON directamente desde el file object
    """
    try:
        # Leer el Excel directamente desde el file object
        df = pd.read_excel(file)
        
        # Convertir a diccionario
        data = df.to_dict('records')
        
        # Limpiar valores NaN y normalizar nombres de columnas
        clean_data = []
        for record in data:
            clean_record = {}
            for key, value in record.items():
                # Normalizar nombres de columnas (sin espacios, minúsculas)
                clean_key = str(key).strip().lower().replace(' ', '_')
                # Limpiar valores
                if pd.isna(value) or value == '':
                    clean_record[clean_key] = None
                else:
                    clean_record[clean_key] = value
            clean_data.append(clean_record)
        
        print(f"[DEBUG] Procesados {len(clean_data)} registros")
        return clean_data
        
    except Exception as e:
        print(f"[ERROR] excel_to_json: {e}")
        return []

# ---------------------------
# LISTAR FACTURAS – /facturas/lista
# ---------------------------
@facturas_bp.route("/lista")
def facturas_lista():
    try:
        facturas = list(facturas_col.find().sort("fecha_subida", -1))
        return render_template("facturas.html", facturas=facturas)
    except Exception as e:
        print(f"[ERROR] facturas_lista: {e}")
        flash("Error cargando las facturas", "danger")
        return render_template("facturas.html", facturas=[])

# ---------------------------
# SUBIR ARCHIVO – /facturas/upload (SOLO CONTENIDO)
# ---------------------------
@facturas_bp.route("/upload", methods=["POST"])
def facturas_upload():
    if "file" not in request.files:
        flash("No se recibió archivo.", "danger")
        return redirect(url_for("facturas.facturas_lista"))

    file = request.files["file"]

    if file.filename == "":
        flash("Archivo inválido.", "danger")
        return redirect(url_for("facturas.facturas_lista"))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        try:
            # Procesar el Excel directamente desde el file object
            datos_excel = excel_to_json(file)
            
            # Verificar que hay datos
            if not datos_excel:
                flash("El archivo está vacío o no se pudieron leer los datos.", "danger")
                return redirect(url_for("facturas.facturas_lista"))
            
            # Obtener las columnas únicas de todos los registros
            todas_columnas = set()
            for registro in datos_excel:
                todas_columnas.update(registro.keys())
            
            # Guardar SOLO el contenido en MongoDB (sin archivo físico)
            factura_doc = {
                "nombre_archivo": filename,
                "fecha_subida": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_registros": len(datos_excel),
                "datos": datos_excel,
                "metadata": {
                    "columnas": list(todas_columnas),
                    "tamaño_original": f"{len(datos_excel)} registros"
                }
            }
            
            result = facturas_col.insert_one(factura_doc)
            
            flash(f"✅ Contenido subido con éxito. {len(datos_excel)} registros procesados.", "success")
            print(f"[SUCCESS] Archivo '{filename}' procesado. ID: {result.inserted_id}")
            
        except Exception as e:
            flash(f"❌ Error procesando el archivo: {str(e)}", "danger")
            print(f"[ERROR] facturas_upload: {e}")
        
    else:
        flash("Tipo de archivo no permitido. Use .xls o .xlsx", "danger")

    return redirect(url_for("facturas.facturas_lista"))

# ---------------------------
# DESCARGAR JSON – /facturas/download/<id>
# ---------------------------
@facturas_bp.route("/download/<id_mongo>")
def facturas_download(id_mongo):
    try:
        factura = facturas_col.find_one({"_id": ObjectId(id_mongo)})
        if factura:
            # Crear respuesta JSON descargable
            response_data = {
                "nombre_archivo": factura["nombre_archivo"],
                "fecha_subida": factura["fecha_subida"],
                "total_registros": factura["total_registros"],
                "metadata": factura.get("metadata", {}),
                "datos": factura["datos"]
            }
            
            response = jsonify(response_data)
            response.headers.set('Content-Disposition', 'attachment', filename=f'{factura["nombre_archivo"]}_contenido.json')
            response.headers.set('Content-Type', 'application/json')
            return response
        else:
            flash("Factura no encontrada.", "danger")
    except Exception as e:
        flash(f"Error descargando factura: {str(e)}", "danger")
    
    return redirect(url_for("facturas.facturas_lista"))

# ---------------------------
# ELIMINAR FACTURA – /facturas/delete/<id>
# ---------------------------
@facturas_bp.route("/delete/<id_mongo>", methods=["POST"])
def facturas_delete(id_mongo):
    try:
        # Eliminar solo de MongoDB (no hay archivo físico)
        result = facturas_col.delete_one({"_id": ObjectId(id_mongo)})
        if result.deleted_count > 0:
            flash("✅ Factura eliminada correctamente.", "success")
        else:
            flash("Factura no encontrada.", "danger")
    except Exception as e:
        flash(f"❌ Error eliminando factura: {str(e)}", "danger")
    
    return redirect(url_for("facturas.facturas_lista"))

# ---------------------------
# DEBUG DATOS – Para verificar qué hay en MongoDB
# ---------------------------
@facturas_bp.route("/debug/datos")
def debug_datos():
    """Endpoint para ver qué datos hay realmente en MongoDB"""
    try:
        facturas = list(facturas_col.find({}, {
            'nombre_archivo': 1, 
            'fecha_subida': 1, 
            'total_registros': 1,
            'metadata.columnas': 1,
            'datos': {'$slice': 2}  # Solo primeros 2 registros para preview
        }))
        
        # Convertir ObjectId a string para serialización
        for factura in facturas:
            if '_id' in factura:
                factura['_id'] = str(factura['_id'])
        
        return jsonify({
            "total_facturas": len(facturas),
            "facturas": facturas
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# LIMPIAR TEMPORALES - Opcional: limpiar carpeta temporal periódicamente
# ---------------------------
@facturas_bp.route("/admin/limpiar-temp")
def limpiar_temp():
    """Limpiar carpeta temporal (opcional)"""
    try:
        import shutil
        if os.path.exists(UPLOAD_FOLDER):
            shutil.rmtree(UPLOAD_FOLDER)
            os.makedirs(UPLOAD_FOLDER)
        return "Carpeta temporal limpiada"
    except Exception as e:
        return f"Error limpiando temporal: {str(e)}"

#   /\_____/\  
#   \ 9   9 /  
#    \>--< /   19  
#    (      )19  
#     n   n
