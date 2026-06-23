
"""
celery -A celery_app.task_manager worker -Q parsing --concurrency=1 --hostname=worker-parsing@%h
celery -A celery_app.task_manager worker -Q messages --concurrency=2 -n=worker-messages@%h

celery -A config.tasks_config beat --loglevel=info

python run_flower.py

"""

import asyncio
from config.tasks_config import app

@app.task(bind=True, max_retries=2, default_retry_delay=60, queue="case_parsing")
def parsing_task(self, case_number: str):
    # bind=True - флаг для доступа к атрибутам задачи, таким как self.retry
    from parser_app.parser_plw import run_playwright_parsing
    try:
        # запуск асинхронной функции внутри синхронного контекста Celery
        print(f"Запуск задачи парсинга для дела {case_number}")
        asyncio.run(run_playwright_parsing(case_number))
        print(f"Задача парсинга для дела {case_number} успешно завершена")
        return True
    
    except Exception as exc:
        print(f"Ошибка при выполнении задачи парсинга для дела {case_number}: {exc}")
        self.retry(exc=exc)


@app.task(queue="messages")
def send_message(arg):
    print(arg)


@app.task(queue="parsing")
def start_parsing(self, case_numbers: list):
    pass