# ai_hiper.py
# Helpers para integrar Llama3 con Ollama

import ollama

def get_llama_response(user_message, conversation_history=[]):
    """
    Obtener respuesta de Llama3 usando Ollama
    """
    try:
        messages = conversation_history + [{"role": "user", "content": user_message}]
        response = ollama.chat(
            model='llama3',  # usa el modelo instalado
            messages=messages
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERROR] get_llama_response: {e}")
        return "Lo siento, hubo un error procesando tu consulta con Llama3."

def generate_query_language(user_message):
    """
    Generar lenguaje de consulta estructurado basado en el mensaje del usuario
    """
    try:
        prompt = f"""
        Convierte la siguiente instrucción en una consulta estructurada (SQL, JSON o pseudocódigo).
        Responde SOLO con el código, sin explicación.

        Instrucción del usuario:
        "{user_message}"
        """
        response = ollama.chat(
            model='llama3',
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[ERROR] generate_query_language: {e}")
        return f"# Error generando consulta para: {user_message}"
