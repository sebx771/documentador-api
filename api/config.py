"""Módulo central para la obtención de variables de entorno.

Centraliza la lectura de variables de entorno del proyecto para evitar
que se haga de forma descentralizada a lo largo del código (os.getenv,
load_dotenv, etc. en cada módulo).

Todas las variables de entorno configuradas en `.env` / `.env.example`
deben exponerse aquí dentro de la clase `Config`.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Exposición centralizada de las variables de entorno del proyecto."""

    @property
    def redis_url(self) -> str | None:
        """Retorna la URL de conexión a Redis (REDIS_URL)."""
        return os.getenv("REDIS_URL")

    @property
    def groq_api_key(self) -> str | None:
        """Retorna la API Key de Groq (GROQ_API_KEY), con fallback a API_KEY."""
        return os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")


config = Config()
