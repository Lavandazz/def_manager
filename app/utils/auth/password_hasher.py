import bcrypt


ACCESS_TOKEN_EXPIRE_MINUTES = 60


class PasswordHasher:
    """
    Класс для хэширования паролей и проверки паролей.
    """

    @staticmethod
    def hash_password(password: str):
        """
        Хэширование пароля перед сохранением в БД
        :param password: пароль, который ввел пользователь
        :return: хэш пароля для сохранения в бд
        """
        user_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return user_pass.decode('utf-8')  # Преобразуем хеш в строку для хранения в бд

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        Проверка пароля с бд (хэш)
        :param plain_password: пароль, который ввел пользователь
        :param hashed_password: пароль, который хранится в бд (хэш)
        :return: True, если пароль верный, иначе False
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
