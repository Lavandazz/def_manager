"""
Запуск процесса таски
celery -A tasks worker --loglevel=info
или
# Для парсинга (только одна задача за раз)
Флаг Q говорит о наименовании очереди.
--hostname (или -n) говорит об именя ворвкера
celery -A celery_tasks.task_manager worker -Q parsing --concurrency=1 --hostname=worker-parsing@%h

# Для остальных задач (параллельно, конкурентно 2, 4 процесса)

celery -A celery_tasks.task_manager worker -Q messages --concurrency=2 -n=worker-messages@%h

Эти запуски привязывают воркера к конкретной очереди.
Первый слушает только очередь parsing и обрабатывает одну задачу за раз (так как --concurrency=1) - берем 1 ворвера и выполняем по 1 задаче,
чтобы не получить бан от сайта КадАрбитр.

Так же один воркер может обрабатывать несколько очередей:
celery -A tasks worker -Q parsing,messages --concurrency=2

Запуск celery beat для выполнения периодических задач
celery -A config.tasks_config beat --loglevel=info

Запуск flower
celery -A tasks.app flower

beat_schedule	Периодические задачи (cron, каждые N секунд)
task_routes	Куда класть задачу (в какую очередь)
queue= в @app.task	Дефолтная очередь для этой таски (перебивается task_routes)
apply_async(queue=...)	Очередь для одного конкретного вызова
"""
import sys
import os
from typing import Any
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from celery.schedules import crontab
from .settings_env import settings

CASES = []

app = Celery(
    'tasks',
    broker=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"
)

# Автоматически находим задачи в модулях внутри пакета celery_tasks
app.autodiscover_tasks(['celery_tasks'], related_name='task_manager')

app.conf.task_routes = {
    'celery_tasks.task_manager.send_verification_email': {'queue': 'messages'},
    'celery_tasks.task_manager.start_parsing':           {'queue': 'parsing'},
}

app.conf.beat_schedule = {
    'celery_tasks.task_manager.send_verification_email': {'queue': 'messages'},
}

beat_schedule: dict[str, Any] = {}

if CASES:
    beat_schedule['parsing-every-second-day'] = {
        'task': 'celery_tasks.task_manager.start_parsing',
        'schedule': crontab(hour=7, minute=30, day_of_week=[1, 4]),
        'args': CASES,
        'options': {'queue': 'parsing'},
    }
# Передаем словарь для шедулера парсинга по расписанию в beat_schedule
app.conf.beat_schedule = beat_schedule
