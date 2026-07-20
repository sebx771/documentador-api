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

    def __init__(
        self,
        req_per_min: int = 10,
        tokens_per_min: int = 6000,
        burst_factor: float = 1.0,
        key_prefix: str = "ratelimit",
    ):
        """
        :param req_per_min: Solicitudes permitidas por minuto (RPM).
        :param tokens_per_min: Tokens permitidos por minuto (TPM). Si es 0, solo usa RPM.
        :param burst_factor: Multiplicador para permitir ráfagas (ej. 1.5 permite 50% extra de margen).
        :param key_prefix: Prefijo para las llaves en Redis.
        """
        self.req_per_min = req_per_min
        self.tokens_per_min = tokens_per_min

        # Calcula límites
        self.max_capacity = int(self.req_per_min * burst_factor)
        self.max_token_capacity = (
            int(self.tokens_per_min * burst_factor)
            if self.tokens_per_min > 0
            else self.max_capacity
        )
        self.refill_rate = self.req_per_min / 60.0  # peticiones por segundo
        self.refill_token_rate = (
            self.tokens_per_min / 60.0 if self.tokens_per_min > 0 else self.refill_rate
        )

        self.timeout = 30  # tiempo máximo de espera en segundos
        self.key_prefix = key_prefix

        logger.info(
            f"Ratelimiter [{key_prefix}] -> RPM: {self.refill_rate:.2f}/s, TPM: {self.refill_token_rate:.2f}/s, Capacidad: {self.max_capacity}"
        )

        try:
            pool = redis.ConnectionPool.from_url(
                REDIS_URL, db=0, decode_responses=True, socket_timeout=5
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
        Usa algoritmo Token Bucket con límites separados para RPM y TPM.

        IMPORTANTE: Si Redis no está disponible, RECHAZA la request (fallar cerrado)
        para proteger contra rate limits de APIs externas.
        """
        req_tokens_key = f"{self.key_prefix}:req"
        tok_tokens_key = f"{self.key_prefix}:tok"

        now = time.time()
        try:
            # Validar que Redis está conectado
            if not self.redis:
                logger.critical(
                    f"Redis no disponible en {self.key_prefix}. Rechazando request."
                )
                return False

            # Ejecutar script Lua para verificar RPM (requests per minute)
            result_req = self._script(
                keys=[req_tokens_key + ":tokens", req_tokens_key + ":timestamp"],
                args=[self.refill_rate, self.max_capacity, now, 1],
            )

            # Validar formato de respuesta
            if not isinstance(result_req, (list, tuple)) or len(result_req) < 2:
                logger.error(
                    f"Respuesta Lua inválida para RPM: {result_req}. Rechazando."
                )
                return False

            # Ejecutar script Lua para verificar TPM (tokens per minute)
            result_tok = self._script(
                keys=[tok_tokens_key + ":tokens", tok_tokens_key + ":timestamp"],
                args=[
                    self.refill_token_rate,
                    self.max_token_capacity,
                    now,
                    tokens_requested,
                ],
            )

            # Validar formato de respuesta
            if not isinstance(result_tok, (list, tuple)) or len(result_tok) < 2:
                logger.error(
                    f"Respuesta Lua inválida para TPM: {result_tok}. Rechazando."
                )
                return False

            # Ambos límites deben aprobar (ambos retornan 1)
            rpm_allowed = int(result_req[0]) == 1
            tpm_allowed = int(result_tok[0]) == 1

            if rpm_allowed and tpm_allowed:
                logger.debug(
                    f"Request permitida en {self.key_prefix} ({tokens_requested} tokens)"
                )
                return True
            else:
                remaining_req = float(result_req[1]) if result_req[1] else 0
                remaining_tok = float(result_tok[1]) if result_tok[1] else 0
                logger.warning(
                    f"Rate limit excedido en {self.key_prefix}: "
                    f"RPM={'✓' if rpm_allowed else '✗'} ({remaining_req:.0f} reqs), "
                    f"TPM={'✓' if tpm_allowed else '✗'} ({remaining_tok:.0f} tokens)"
                )
                return False

        except redis.ConnectionError as e:
            logger.critical(
                f"Redis DESCONECTADO en {self.key_prefix}. "
                f"Rate limiting desactivado. Error: {e}"
            )
            return False

        except Exception as e:
            logger.critical(
                f"Error CRÍTICO en RateLimiter ({self.key_prefix}): {type(e).__name__}: {e}. "
                f"Rechazando request por seguridad."
            )
            return False
