
"""
celery -A celery_tasks.task_manager worker -Q parsing --concurrency=1 --hostname=worker-parsing@%h
celery -A celery_tasks.task_manager worker -Q messages --concurrency=2 -n=worker-messages@%h
"""
import asyncio
import time

from shared.config.tasks_config import celery_app
from shared.config.logger_config import task_logger
from shared.utils.exceptions import AccessForbidden



@celery_app.task(bind=True, max_retries=2, default_retry_delay=60, queue="parsing") # bind=True - флаг для доступа к атрибутам задачи, таким как self.retry
def parsing_task(self, case_number: str):
    """
    Запуск задачи для парсинга Картотеки арбитражныъ дел
    """
    from worker_playwright.utils.run_parsing import run_playwright_parsing
    try:
        # запуск асинхронной функции внутри синхронного контекста Celery
        task_logger.info(f"Запуск задачи парсинга для дела {case_number}")
        asyncio.run(run_playwright_parsing(case_number))
        task_logger.info(f"Задача парсинга для дела {case_number} успешно завершена")
        return True
    
    except Exception as exc:
        print(f"Ошибка при выполнении задачи парсинга для дела {case_number}: {exc}")
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, queue="messages")
def send_verification_email(self, email: str, code: str):
    """
    Запуск задачи для отправления сообщения на почту при регистрации.
    Синхронная Celery-таска. Внутри запускает async-функцию через asyncio.run.
    Таска зарегистрированна в очереди task_routes в tasks_config.py
    """
    from web_app.utils.mail import send_verification_email_async
    task_logger.debug(f"отправляю письмо с кодом на почту: {email}")
    try:
        asyncio.run(send_verification_email_async(email, code))
        task_logger.info(f"Письмо с кодом отправлено на {email}")
    except Exception as exc:
        task_logger.debug(f"Ошибка отправки письма на {email}: {exc}")
        self.retry(exc=exc)
        

@celery_app.task(bind=True, max_retries=1, default_retry_delay=80, queue="parsing_efrsb")
def start_efrsb_parsing(self, user_id: int, person_name: str):
    """ 
    Синхронная Celery-таска. для запуска асинхронной задачи парсинга ЕФРСБ
    """
    from worker_patchright.utils.run_parsing import run_efrsb_parsing
    try:
        # запуск асинхронной функции внутри синхронного контекста Celery
        task_logger.debug(f"Запуск задачи парсинга для дела {person_name}")
        result = asyncio.run(run_efrsb_parsing(user_id, person_name))
        task_logger.debug(f"Задача парсинга для дела {person_name} успешно завершена")
        return {"status": "success", "data": result}
        
    except AccessForbidden:
        # Важно: не перехватываем исключение, а пробрасываем дальше,
        # чтобы Celery зафиксировал FAILURE
        raise

    except Exception as exc:
        task_logger.error(f"Ошибка при выполнении задачи парсинга для дела {person_name}: {exc}")
        self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, queue="messages")
def send_admin_email(self, subject: str, body_html: str):
    """Celery-таска: отправка письма администратору."""
    from web_app.utils.mail import send_mail_to_admin
    from shared.config.settings_env import settings

    email = settings.ADMIN_EMAIL
    task_logger.debug(f"Отправляю письмо админу на {email}: {subject}")
    try:
        asyncio.run(send_mail_to_admin(email, subject, body_html))
        task_logger.info(f"Письмо админу отправлено на {email}")
    except Exception as exc:
        task_logger.error(f"Ошибка отправки письма админу на {email}: {exc}")
        raise self.retry(exc=exc)
    

@celery_app.task(queue="parsing")
def start_parsing_all_cases():
    """Запуск парсинга всех актуальных дел из БД. Оркестратор, который ставит задачи в очередь."""
    from shared.utils.schedull import get_number_cases
    task_logger.exception("Запуск таски для общего парсинга")
    # 1. Получаем список номеров
    try:
        case_numbers = asyncio.run(get_number_cases())
    except Exception as exc:
        task_logger.exception("Не удалось получить список дел из БД")
        # уведомляем — но не через asyncio.run, а через .delay()
        send_admin_email.delay(
            subject="[Парсинг] Ошибка получения списка дел",
            body_html=f"<p>Не смог получить список дел:</p><pre>{exc}</pre>",
        )
        raise

    # 2. Пустой список
    if not case_numbers:
        task_logger.info("Планировщик: нет актуальных дел для парсинга")
        send_admin_email.delay(
            subject="[Парсинг] Нет дел для парсинга",
            body_html="<p>Планировщик запустился, но список актуальных дел пуст.</p>",
        )
        return "Нет актуальных дел для парсинга."

    cases = len(case_numbers)
    task_logger.info(f"Планировщик: получено {cases} дел для парсинга")

    # 3. Уведомляем админа со списком
    items = "".join(f"<li>{n}</li>" for n in case_numbers)
    send_admin_email.delay(
        subject=f"[Парсинг] Запущено {cases} дел",
        body_html=f"<p>Запущен парсинг {cases} дел:</p><ul>{items}</ul>",
    )

    # 4. Ставим задачи в очередь
    for case_number in case_numbers:
        parsing_task.delay(case_number)
        time.sleep(7.3)  # Добавляем небольшую задержку между задачами

    return f"Запланировано {cases} задач парсинга."