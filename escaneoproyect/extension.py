# extension.py
# MongoDB para facturas (Excel -> JSON)

from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "escaneo_facturas"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
facturas = db["facturas"]


def guardar_factura_doc(usuario, nombre_archivo, ruta_archivo, data_json):
    """
    Guarda la factura procesada en Mongo.
    data_json: lista de dict (registros) resultantes de convertir Excel -> JSON
    """
    doc = {
        "usuario": usuario,
        "filename": nombre_archivo,
        "archivo_ruta": ruta_archivo,
        "data": data_json,
        "created_at": datetime.utcnow()
    }
    res = facturas.insert_one(doc)
    return str(res.inserted_id)


def obtener_facturas_usuario(usuario):
    rows = list(facturas.find({"usuario": usuario}).sort("created_at", -1))
    # convertir ObjectId a str para evitar problemas en templates
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


def borrar_factura(id_mongo):
    try:
        oid = ObjectId(id_mongo)
    except Exception:
        return False
    facturas.delete_one({"_id": oid})
    return True


def obtener_factura_por_id(id_mongo):
    try:
        oid = ObjectId(id_mongo)
    except Exception:
        return None
    doc = facturas.find_one({"_id": oid})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc
