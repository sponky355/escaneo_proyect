# ai_hiper.py - VERSIÓN CORREGIDA
import ollama
from pymongo import MongoClient
import json

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["escaneo_db"]
facturas_col = db["facturas"]



def get_facturas_context():
    """
    Obtener todas las facturas de MongoDB para proporcionar contexto a la IA
    """
    try:
        # Obtener datos específicos
        facturas = list(facturas_col.find({}, {
            'nombre_archivo': 1, 
            'fecha_subida': 1, 
            'total_registros': 1,
            'datos': 1,
            'metadata.columnas': 1
        }))
        
        print(f"[DEBUG] Se encontraron {len(facturas)} facturas en la base de datos")
        
        # Si no hay facturas, retornar mensaje claro
        if not facturas:
            return "No hay facturas cargadas en el sistema. Por favor, sube archivos Excel para analizar."
        
        # Preparar datos para la IA
        context_info = f"Total de archivos cargados: {len(facturas)}\n\n"
        
        for i, factura in enumerate(facturas, 1):
            context_info += f"--- ARCHIVO {i}: {factura.get('nombre_archivo', 'Sin nombre')} ---\n"
            context_info += f"Registros: {factura.get('total_registros', 0)}\n"
            context_info += f"Columnas: {', '.join(factura.get('metadata', {}).get('columnas', []))}\n"
            
            # Mostrar primeros 3 registros como ejemplo
            datos = factura.get('datos', [])
            if datos:
                context_info += "Primeros registros:\n"
                for j, registro in enumerate(datos[:3], 1):
                    context_info += f"  {j}. {registro}\n"
            context_info += "\n"
        
        print(f"[DEBUG] Contexto preparado: {len(context_info)} caracteres")
        return context_info
        
    except Exception as e:
        print(f"[ERROR] get_facturas_context: {e}")
        return "Error al cargar los datos de facturas."





def get_llama_response(user_message, conversation_history=[]):
    """
    Obtener respuesta de Llama3 usando Ollama con contexto de MongoDB
    """
    try:
        # Obtener contexto actualizado de las facturas
        facturas_context = get_facturas_context()
        
        system_prompt = f"""
Eres un asistente especializado en análisis de facturas. 

INFORMACIÓN DE FACTURAS DISPONIBLE:
{facturas_context}

INSTRUCCIONES:
- Responde ÚNICAMENTE basándote en los datos proporcionados arriba
- Si no hay facturas, informa al usuario que debe subir archivos Excel
- Si hay datos, analízalos y responde de forma específica y concreta
- Para pedidos de "primeras líneas", muestra los primeros registros de los datos
- Usa solo la información real disponible en los datos

Pregunta del usuario: {user_message}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": user_message}
        ]
        
        response = ollama.chat(
            model='llama3',
            messages=messages
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"[ERROR] get_llama_response: {e}")
        return f"Error procesando tu consulta: {str(e)}"

def generate_query_language(user_message):
    """
    Generar lenguaje de consulta estructurado
    """
    try:
        facturas_context = get_facturas_context()
        
        prompt = f"""
Contexto de la base de datos:
{facturas_context}

Para la pregunta: "{user_message}"

Genera una consulta MongoDB específica que respondería esta pregunta.
Responde SOLO con la consulta MongoDB en formato válido.

Ejemplo:
db.facturas.find({{}})
o análisis específico basado en los datos disponibles.
"""
        
        response = ollama.chat(
            model='llama3',
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERROR] generate_query_language: {e}")
        return f"// Error generando consulta: {str(e)}"

#   /\_____/\
#   \ 9   9 /
#    \>--< /   19 
#    (      )19 
#     n   n