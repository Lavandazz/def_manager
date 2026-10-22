# core/exceptions.py (или где угодно рядом с сервисом)
class VerificationCodeAlreadySent(Exception):
    """Код уже отправлен, повторная отправка пока недоступна."""
    pass

class AccessForbidden(Exception):
    """Доступ запрещён, возможно, сайт заблокировал доступ. 403"""
    pass