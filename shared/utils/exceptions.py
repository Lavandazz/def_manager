# core/exceptions.py (или где угодно рядом с сервисом)
class VerificationCodeAlreadySent(Exception):
    """Код уже отправлен, повторная отправка пока недоступна."""
    pass

class AccessForbidden(Exception):
    """Доступ запрещён, возможно, сайт заблокировал доступ. 403"""
    pass

class UserNotFoundError(Exception):
    status_code = 401 
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Пользователь с id={user_id} не найден")