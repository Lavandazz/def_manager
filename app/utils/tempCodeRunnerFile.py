def hash_password(password: str):
    """
    Хэш пароля перед сохранением в БД
    """
    user_pass = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return user_pass.decode('utf-8')  # Преобразуем хеш в строку для хранения в бд
