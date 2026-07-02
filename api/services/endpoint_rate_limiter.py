import time
import logging
import redis
import os
import math
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL")


class EndpointRateLimiter:
    """
    Redis-based Rate Limiter for HTTP endpoints using the Token Bucket algorithm.
    Optimized for Serverless environments (state resides entirely in Redis).
    """

    def __init__(
        self,
        limit: int,
        window: int,
        key_prefix: str = "elimit",
        redis_client: redis.Redis = None,
    ):
        """
        :param limit: Maximum requests allowed within the window.
        :param window: Time window in seconds.
        :param key_prefix: Prefix for keys in Redis to avoid conflicts.
        :param redis_client: Optional pre-existing Redis client instance.
        """
        self.limit = limit
        self.window = window
        self.key_prefix = key_prefix
        self.refill_rate = float(limit) / float(window)  # Tokens refilled per second
        self.capacity = limit

        if redis_client:
            self.redis = redis_client
        else:
            try:
                if not REDIS_URL:
                    logger.error(
                        "REDIS_URL is not set. EndpointRateLimiter will operate in fail-open mode."
                    )
                    self.redis = None
                else:
                    pool = redis.ConnectionPool.from_url(
                        REDIS_URL,
                        db=0,
                        decode_responses=True,
                        socket_timeout=5,
                        socket_keepalive=True,
                    )
                    self.redis = redis.Redis(connection_pool=pool)
            except Exception as e:
                logger.error(
                    f"Failed to connect to Redis for EndpointRateLimiter [{key_prefix}]: {e}"
                )
                self.redis = None

        # Lua script to perform atomic token bucket check
        # It handles HMGET, calculations, conditional deduct, and EXPIRE in a single atomic roundtrip.
        self.lua_script = """
        local key = KEYS[1]
        local rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local requested = 1

        local data = redis.call("HMGET", key, "tokens", "last_updated")
        local last_tokens = tonumber(data[1] or capacity)
        local last_updated = tonumber(data[2] or now)

        local elapsed = math.max(0, now - last_updated)
        local refilled = elapsed * rate
        local current_tokens = math.min(capacity, last_tokens + refilled)

        local allowed = 0
        local remaining = current_tokens
        local retry_after = 0

        if current_tokens >= requested then
            allowed = 1
            remaining = current_tokens - requested
            redis.call("HMSET", key, "tokens", remaining, "last_updated", now)
            redis.call("EXPIRE", key, 3600)  -- 1 hour TTL on inactivity
        else
            allowed = 0
            local needed = requested - current_tokens
            retry_after = math.ceil(needed / rate)
        end

        return {allowed, tostring(math.floor(remaining)), tostring(retry_after)}
        """
        self._script = None
        if self.redis:
            try:
                self._script = self.redis.register_script(self.lua_script)
            except Exception as e:
                logger.error(
                    f"Failed to register Lua script in Redis for EndpointRateLimiter [{key_prefix}]: {e}"
                )

    def check(self, key_id: str) -> dict:
        """
        Checks if a request is allowed for a specific key (e.g. IP address or 'global').

        Returns a dictionary containing:
            - allowed (bool): True if request is allowed, False otherwise.
            - limit (int): The total capacity.
            - remaining (int): The number of tokens remaining.
            - retry_after (int): The number of seconds to wait before retrying (0 if allowed).
        """
        if not self.redis or not self._script:
            # Fail-open if Redis is down to prevent downtime on cache/infrastructure issues
            logger.warning(
                f"Redis unavailable. Fail-open mode active for EndpointRateLimiter [{self.key_prefix}]. Key: {key_id}"
            )
            return {
                "allowed": True,
                "limit": self.limit,
                "remaining": self.limit,
                "retry_after": 0,
            }

        key = f"{self.key_prefix}:{key_id}"
        now = time.time()
        try:
            result = self._script(keys=[key], args=[self.refill_rate, self.capacity, now])
            allowed = int(result[0]) == 1
            remaining = int(result[1])
            retry_after = int(result[2])

            return {
                "allowed": allowed,
                "limit": self.limit,
                "remaining": remaining,
                "retry_after": retry_after,
            }
        except Exception as e:
            logger.error(
                f"Error executing rate limit in Redis for [{key}]: {e}. Falling back to fail-open."
            )
            return {
                "allowed": True,
                "limit": self.limit,
                "remaining": self.limit,
                "retry_after": 0,
            }
