import json

from config.redis_config import redis_service



async def get_cases_from_cache(user_id) -> list | None:
    cache_key = f"cases:{user_id}_"
    cached_data = await redis_service.get_value(key=cache_key)
    if cached_data:
        try:
            cases = json.loads(cached_data) # type: ignore
            return cases
        
        except Exception as e:
            print("Ошибка с редисом", e)
            cases = None

async def save_cases_to_cache(user_id, cases) -> bool:       
    json_cases = json.dumps(cases)
    await redis_service.set_value(key=f"cases:{user_id}_", value=json_cases, expire=100)
    return True

