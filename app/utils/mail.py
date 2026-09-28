
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from config.settings_env import mail_settings


mail_conf = ConnectionConfig(
    MAIL_USERNAME = mail_settings.MAIL_FROM,
    MAIL_PASSWORD = mail_settings.EMAIL_PASSWORD,
    MAIL_FROM = mail_settings.MAIL_FROM,
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.mail.ru",
    MAIL_FROM_NAME="Security",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


async def send_verification_email_async(to_email: str, code: str) -> None:
    """
    Отправка письма.
    recipients передаём списком строк — FastMail сам их преобразует в NameEmail.
    """
    html = f"""
    <p>Здравствуйте!</p>
    <p>Ваш код подтверждения регистрации:</p>
    <h2 style="letter-spacing: 4px;">{code}</h2>
    <p>Код действителен 15 минут. Если вы не запрашивали регистрацию — просто проигнорируйте письмо.</p>
    """
    print("====== FastMail отправка письма ")
    message = MessageSchema(
        subject="Подтверждение регистрации",
        recipients=[to_email],          # список email-строк, MessageSchema email принимает как список
        body=html,
        subtype=MessageType.html,
    )

    fm = FastMail(mail_conf)
    await fm.send_message(message)
