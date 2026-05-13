import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def get_groq_client()->Groq:
    """
    Inicializa y retorna el cliente de Groq.
    """
    # Busca GROQ_API_KEY primero (nombre estándar), luego API_KEY (legacy)
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY o API_KEY no encontrada en variables de entorno")
        raise ValueError("API key no configurada. Configure GROQ_API_KEY o API_KEY")

    try:
        client = Groq(api_key=api_key)
        logger.info("Cliente Groq inicializado correctamente")
        return client
    except Exception as e:
        logger.error(f"Error al inicializar cliente Groq: {str(e)}")
        raise
