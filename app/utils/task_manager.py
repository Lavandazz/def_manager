
"""
celery -A app.utils.task_manager worker -Q parsing --concurrency=1
python run_flower.py

"""

import asyncio
from config.tasks_config import task_app


@task_app.task(bind=True, max_retries=2, default_retry_delay=60, queue='parsing')
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
