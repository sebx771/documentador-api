import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_groq_client():
    """
    Inicializa y retorna el cliente de Groq.
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        logger.error("API_KEY no encontrada en variables de entorno")
        raise ValueError("API_KEY no configurada. Configure la variable de entorno API_KEY")

    try:
        client = Groq(api_key=api_key)
        logger.info("Cliente Groq inicializado correctamente")
        return client
    except Exception as e:
        logger.error(f"Error al inicializar cliente Groq: {str(e)}")
        raise
