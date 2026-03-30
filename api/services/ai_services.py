import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()  # Carga las variables de entorno desde el archivo .env

api=os.getenv("API_KEY")  # Obtiene la clave API desde las variables de entorno
client = Groq(api_key=api)

def generar_documentacion(codigo_fuente):
    prompt = f"""
    Actúa como un Ingeniero de Software experto. 
    Analiza el siguiente código y genera una descripción técnica para un informe del SENA.
    Usa un lenguaje profesional y estructurado.
    
    Código:
    {codigo_fuente}
    
    Salida esperada:
    1. Propósito del módulo.
    2. Descripción de campos/atributos.
    3. Reglas de negocio detectadas.
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile", # El modelo más rápido y eficiente
    )

    response= chat_completion.choices[0].message.content

    return response
