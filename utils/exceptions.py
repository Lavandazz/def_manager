# core/exceptions.py (или где угодно рядом с сервисом)
class VerificationCodeAlreadySent(Exception):
    """Код уже отправлен, повторная отправка пока недоступна."""
    pass