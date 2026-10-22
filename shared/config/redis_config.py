import redis.asyncio as redis
from shared.config.settings_env import settings
from shared.core.services.redis_service import RedisService


redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT,
    db=0,
    password=settings.REDIS_PASSWORD,
    decode_responses=True  # указывает сохранять не в байтах данные
    )


redis_service = RedisService(redis_client)

