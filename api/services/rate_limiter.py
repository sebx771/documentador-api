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
    Permite limitar por RPM (Requests) y TPM (Tokens).
    """
    def __init__(self, req_per_min: int = 10, tokens_per_min: int = 6000, burst_factor: float = 1.0, key_prefix: str = "ratelimit"):
        """
        :param req_per_min: Solicitudes permitidas por minuto (RPM).
        :param tokens_per_min: Tokens permitidos por minuto (TPM). Si es 0, solo usa RPM.
        :param burst_factor: Multiplicador para permitir ráfagas (ej. 1.5 permite 50% extra de margen).
        :param key_prefix: Prefijo para las llaves en Redis.
        """
        self.req_per_min = req_per_min
        self.tokens_per_min = tokens_per_min
        
        # Si usamos TPM, el "bucket size" es el TPM. Si no, es el RPM.
        
        self.max_capacity = int(self.req_per_min * burst_factor)
        self.max_token_capacity= int(self.tokens_per_min * burst_factor)
        self.refill_rate = self.req_per_min / 60.0  # Tokens (o peticiones) por segundo
        self.refill_token_rate = self.tokens_per_min / 60.0
        
        self.timeout = 30  # Aumentamos el timeout para esperar a que se recarguen los tokens
        self.key_prefix = key_prefix
        
        logger.info(f"Ratelimiter [{key_prefix}] -> Limit: {self.refill_rate}/min, Refill: {self.refill_rate:.2f}/s, Burst: {self.max_capacity}")

        try:
            pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                db=0,
                decode_responses=True,
                socket_timeout=5
            )
            self.redis = redis.Redis(connection_pool=pool)
        except Exception as e:
            logger.error(f"Error conectando a Redis para RateLimiter: {e}")
            raise

        self.lua_script = """
        local tokens_key = KEYS[1]
        local timestamp_key = KEYS[2]
        local rate = tonumber(ARGV[1])
        local max_capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = tonumber(ARGV[4])

        local last_tokens = tonumber(redis.call("get", tokens_key) or max_capacity)
        local last_refill = tonumber(redis.call("get", timestamp_key) or now)

        local elapsed = math.max(0, now - last_refill)
        local tokens_to_add = elapsed * rate
        local current_tokens = math.min(max_capacity, last_tokens + tokens_to_add)

        if current_tokens >= requested then
            local new_tokens = current_tokens - requested
            redis.call("set", tokens_key, new_tokens)
            redis.call("set", timestamp_key, now)
            redis.call("expire", tokens_key, 600)
            redis.call("expire", timestamp_key, 600)
            return {1, tostring(new_tokens)}
        else
            return {0, tostring(current_tokens)}
        end
        """
        self._script = self.redis.register_script(self.lua_script)

    def allow_request(self, tokens_requested: int = 1) -> bool:
        """
        Verifica si se permiten los tokens solicitados.
        Si no hay suficientes, espera hasta que el timeout expire.
        Verifica tanto RPM como TPM simultáneamente.
        """
        start_time = time.time()
        
        req_tokens_key = f"{self.key_prefix}:req:tokens"
        req_ts_key = f"{self.key_prefix}:req:timestamp"
        
        tok_tokens_key = f"{self.key_prefix}:tok:tokens"
        tok_ts_key = f"{self.key_prefix}:tok:timestamp"

        while True:
            now = time.time()
            try:
                result_req = self._script(
                    keys=[req_tokens_key, req_ts_key],
                    args=[self.refill_rate, self.max_capacity, now, 1]
                )
                
                result_tok = self._script(
                    keys=[tok_tokens_key, tok_ts_key],
                    args=[self.refill_token_rate, self.max_token_capacity, now, tokens_requested]
                )
                
                if result_req[0] == 1 and result_tok[0] == 1:
                    return True
                
                if now - start_time > self.timeout:
                    current_req = result_req[1]
                    current_tok = result_tok[1]
                    logger.warning(
                        f"RateLimiter [{self.key_prefix}]: Timeout. "
                        f"Req: {current_req}, Tok: {current_tok}"
                    )
                    return False
                
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error en RateLimiter ({self.key_prefix}): {e}")
                return True
