import hashlib
import logging
import json
import redis
from typing import Optional, Dict, Any
import threading
from dotenv import load_dotenv
import os
load_dotenv()


logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL")




_global_cache_instance = None
_cache_lock = threading.Lock()

def get_global_cache(
    max_size: int = 100,
    ttl_seconds: int = 3600,
    enable_lru: bool = True
) -> 'CacheService':
    global _global_cache_instance
    with _cache_lock:
        if _global_cache_instance is None:
            _global_cache_instance = CacheService(
                max_size=max_size,
                ttl_seconds=ttl_seconds,
                enable_lru=enable_lru
            )
            logger.info("Cache global inicializado con Redis")
    return _global_cache_instance

class CacheService:
    """
    Cache Service migrado a Redis.
    Mantiene la misma interfaz pero delega la persistencia y LRU a Redis.
    """

    DEFAULT_MAX_SIZE = 100
    DEFAULT_TTL_SECONDS = 3600

    def __init__(
        self,
        max_size: int = None,
        ttl_seconds: int = None,
        enable_lru: bool = True
    ):
        # Configuración básica
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
        self.ttl_seconds = ttl_seconds or self.DEFAULT_TTL_SECONDS
        self.enable_lru = enable_lru
        
        # Conexión a Redis (asumiendo valores por defecto de tu instalación)
        # Uso de Connection Pool: Vital para Serverless
        
        pool = redis.ConnectionPool.from_url(
            REDIS_URL,
            db=0, 
            decode_responses=True,
            # Evita que una función serverless deje colgada una conexión
            socket_timeout=5,
            socket_keepalive=True ,
            ssl_cert_reqs=None
        )
        self.client = redis.Redis(connection_pool=pool)
        
        # Intentamos configurar Redis para que maneje el LRU automáticamente
     
        self._stats_lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def generate_hash(
        self,
        content: str,
        doc_type: str,
        extra_requirements: str = None
    ) -> str:
        hash_input = f"{content}|{doc_type}"
        if extra_requirements:
            hash_input += f"|{extra_requirements}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene valor de Redis. 
        Redis maneja el TTL y el LRU automáticamente al acceder.
        """
        result = self.client.get(cache_key)
        
        with self._stats_lock:
            if result is None:
                self._stats["misses"] += 1
                logger.debug(f"Redis cache miss: {cache_key[:16]}...")
                return None
            
            self._stats["hits"] += 1
            logger.debug(f"Redis cache hit: {cache_key[:16]}...")
            
        # Redis devuelve strings, hay que deserializar el JSON
        return json.loads(result)

    def set(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Guarda en Redis usando el TTL nativo de Redis.
        """
        # Convertimos el diccionario de Python a un string JSON para Redis
        serialized_result = json.dumps(result)
        
        # Usamos el comando SET con el parámetro 'ex' (expiry) para el TTL
        self.client.set(cache_key, serialized_result, ex=self.ttl_seconds)
        
        logger.debug(f"Redis cache set: {cache_key[:16]}...")

    def clear(self) -> None:
        """Limpia la base de datos actual de Redis."""
        self.client.flushdb()
        logger.info("Redis cache limpiado (FLUSHDB)")

    def get_stats(self) -> Dict[str, Any]:
        """Versión segura para nubes gestionadas."""
        try:
            info = self.client.info()
            # En nubes, db0 a veces no existe si está vacía
            db0_info = info.get('db0', {})
            current_keys = db0_info.get('keys', 0)
        except Exception:
            current_keys = "N/A"

        with self._stats_lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
            
            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate_percent": round(hit_rate, 2),
                "current_size": current_keys,
                "redis_version": info.get('redis_version', 'unknown')
            }