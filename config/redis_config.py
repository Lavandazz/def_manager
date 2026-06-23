import redis
from config.settings_env import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT,
    db=0,
    password=settings.REDIS_PASSWORD,
                           )