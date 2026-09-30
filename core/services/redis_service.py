import secrets
import string

from utils.exceptions import VerificationCodeAlreadySent


class RedisService:
    """
    Сервис Redis. 
    Используется для управления данными в  Redis, а так же для верификации новых пользователей.
    """
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def set_value(self, key: str, value: str, expire: int = 600):
        await self.redis_client.set(key, value, ex=expire)

    async def get_value(self, key: str) -> str | None:
        return await self.redis_client.get(key)

    async def generate_and_save_verification_code(self, email: str, user_data: dict, expire_seconds: int = 600, cooldown=60) -> str:
        """
        Генерирует код, сохраняет его в Redis вместе с данными пользователя для подтверждения. 
        Используется модуль secrets для предотвращения подбора чисел.
        Ключем является почта, а в значение кладем словарь с данными пользоватетеля: имя пользователя, хэш пароль, телега и тд, все, что передано в словаре (распечатанном_). 
        Ключ хэшируется и сохраняется в Redis. 
        Время жизни ключа - expire_seconds (15 минут)
        При сохранении ключа, сохраняется и cooldown:{email} для того (на 60 сек), чтобы проверять, отправлен ли код.
        Если код уже был отправлен, отправляем сообщение пользователю и выходим из функции.
        return: code - возвращаем строковый код, чтобы не терять возможные нули в начале
        """
        cooldown_key = f"cooldown:{email}"
        if await self.redis_client.exists(cooldown_key):
            # ttl возвращает
            # > 0 — сколько секунд осталось,
            # -1 — ключ есть, но без TTL,
            # -2 — ключа нет.
            ttl = await self.redis_client.ttl(cooldown_key)
            raise VerificationCodeAlreadySent(f"Код уже отправлен. Повторная отправка возможна через {ttl} сек.")
        
        # Формируем шестизначный код из рандомных чисел
        code = ''.join(secrets.choice(string.digits) for _ in range(6))
        key = f"verify:{email}"
        
        # Сохраняем код и данные пользователя в виде хеша
        await self.redis_client.hset(key, mapping={"code": code, **user_data}) # **user_data разворачиваем словарь чтобы избежать вложенности, иначе Redis не закодирует
        await self.redis_client.expire(key, expire_seconds)
        await self.redis_client.set(cooldown_key, value="1", ex=cooldown) # сохраняем cooldown_key чтобы не отправлять код повторно 
        
        return code

    async def get_verification_data(self, email: str) -> dict | None:
        """
        Возвращает данные из Redis по email.
        """
        key = f"verify:{email}"
        data = await self.redis_client.hgetall(key)
        if not data:
            return None
        return data

    async def delete_verification_code(self, email: str):
        """
        Удаляет код подтверждения из Redis.
        """
        await self.redis_client.delete(f"verify:{email}")

