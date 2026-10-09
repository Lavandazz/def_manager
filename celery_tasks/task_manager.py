
"""
celery -A celery_tasks.task_manager worker -Q parsing --concurrency=1 --hostname=worker-parsing@%h
celery -A celery_tasks.task_manager worker -Q messages --concurrency=2 -n=worker-messages@%h

celery -A config.tasks_config beat --loglevel=info

python run_flower.py

"""
import asyncio

from app.utils.mail import send_verification_email_async
from config.tasks_config import app

@app.task(bind=True, max_retries=2, default_retry_delay=60, queue="parsing")
def parsing_task(self, case_number: str):
    # bind=True - флаг для доступа к атрибутам задачи, таким как self.retry
    from parser_app.kad_parser import run_playwright_parsing
    try:
        # запуск асинхронной функции внутри синхронного контекста Celery
        print(f"Запуск задачи парсинга для дела {case_number}")
        asyncio.run(run_playwright_parsing(case_number))
        print(f"Задача парсинга для дела {case_number} успешно завершена")
        return True
    
    except Exception as exc:
        print(f"Ошибка при выполнении задачи парсинга для дела {case_number}: {exc}")
        self.retry(exc=exc)


@app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, email: str, code: str):
    """
    Синхронная Celery-таска. Внутри запускает async-функцию через asyncio.run.
    Таска зарегистрированна в очереди task_routes в tasks_config.py
    """
    print(f"отправляю письмо с кодом", email, code)
    try:
        asyncio.run(send_verification_email_async(email, code))
        print(f"Письмо с кодом отправлено на {email}")
    except Exception as exc:
        print(f"Ошибка отправки письма на {email}: {exc}")
        self.retry(exc=exc)
        

@app.task(queue="parsing")
def start_parsing(self):
    pass
