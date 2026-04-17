import time
import logging
import redis
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL")

class Ratelimiter:
    """
    Ratelimiter basado en Redis para soportar entornos Serverless.
    Usa el algoritmo Token Bucket con un script LUA para asegurar atomicidad.
    """
    def __init__(self, req_per_min: int, burst: int = 1, key_prefix: str = "ratelimit"):
        """
        :param req_per_min: Solicitudes permitidas por minuto.
        :param burst: Capacidad máxima del cubo (1 = sin ráfagas, 10 = permite 10 seguidas).
        :param key_prefix: Prefijo para las llaves en Redis.
        """
        logger.info(f"Configurando Ratelimiter: {req_per_min} RPM, Burst: {burst}")
        
        self.req_per_min = req_per_min
        self.max_tokens = burst  # El "tamaño del cubo" es ahora el burst
        self.refill_rate = req_per_min / 60.0  # Cuántos tokens se generan por segundo
        
        # Aumentamos el timeout a 20 segundos para ser aún más pacientes
        self.timeout = 20 
        self.key_prefix = key_prefix
        
        try:
            pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_keepalive=True,
                ssl_cert_reqs=None
            )
            self.redis = redis.Redis(connection_pool=pool)
        except Exception as e:
            logger.error(f"Error conectando a Redis para RateLimiter: {e}")
            raise

        # --- EXPLICACIÓN DEL SCRIPT LUA ---
        # 1. Recupera la cantidad de tokens y el tiempo de la última recarga.
        # 2. Calcula cuántos tokens nuevos se han generado por el paso del tiempo.
        # 3. Suma los nuevos al balance actual, sin pasarse del 'max_tokens' (burst).
        # 4. Si hay tokens suficientes (>= 1), resta 1, guarda y retorna 1 (éxito).
        # 5. Todo el proceso es ATÓMICO (nadie más puede leer/escribir mientras se ejecuta).
        self.lua_script = """
        local tokens_key = KEYS[1]
        local timestamp_key = KEYS[2]
        local rate = tonumber(ARGV[1])
        local max_tokens = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])

        -- Recuperar estado (si no existe, empezamos con el máximo permitido)
        local last_tokens = tonumber(redis.call("get", tokens_key) or max_tokens)
        local last_refill = tonumber(redis.call("get", timestamp_key) or now)

        -- Calcular recarga basada en tiempo transcurrido
        local elapsed = math.max(0, now - last_refill)
        local tokens_to_add = elapsed * rate
        local current_tokens = math.min(max_tokens, last_tokens + tokens_to_add)

        if current_tokens >= requested then
            -- Éxito: Consumir token y actualizar marcas de tiempo
            local new_tokens = current_tokens - requested
            redis.call("set", tokens_key, new_tokens)
            redis.call("set", timestamp_key, now)
            
            -- TTL de 10 minutos para mantenimiento automático
            redis.call("expire", tokens_key, 600)
            redis.call("expire", timestamp_key, 600)
            return {1, tostring(new_tokens)}
        else
            -- Fallo: Retornar 0 indicando que no hay tokens disponibles
            return {0, tostring(current_tokens)}
        end
        """
        self._script = self.redis.register_script(self.lua_script)

    def allow_request(self) -> bool:
        """
        Verifica si se permite la solicitud. 
        Si no hay tokens, espera y reintenta hasta que expire el timeout de 10s.
        """
        start_time = time.time()
        tokens_key = f"{self.key_prefix}:tokens"
        ts_key = f"{self.key_prefix}:timestamp"

        while True:
            now = time.time()
            
            try:
                result = self._script(
                    keys=[tokens_key, ts_key],
                    args=[self.refill_rate, self.max_tokens, now, 1]
                )
                
                allowed = result[0] == 1
                
                if allowed:
                    return True
                
                # Gestión de espera si el cubo está vacío
                if now - start_time > self.timeout:
                    logger.warning(f"RateLimiter: Timeout ({self.timeout}s) excedido")
                    return False
                
                # Pequeña pausa antes de volver a preguntar a Redis
                time.sleep(0.5) 
                
            except Exception as e:
                logger.error(f"Error en RateLimiter (Redis): {e}")
                return True # Fail open
