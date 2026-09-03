import json

from config.redis_config import redis_client
from config.schemas.user_schemas import CaseSchema

def get_cases_from_cache(user_id) -> list | None:
    cache_key = f"{user_id}_cases"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        try:
            cases = json.loads(cached_data) # type: ignore
            return cases
        
        except Exception as e:
            print("Ошибка с редисом", e)
            cases = None

def save_cases_to_cache(user_id, cases) -> bool:       
    json_cases = json.dumps(cases)
    redis_client.set(f"{user_id}_cases", json_cases, ex=100)
    return True
    