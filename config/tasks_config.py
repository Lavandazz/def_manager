"""
Запуск процесса таски
celery -A tasks worker --loglevel=info
или
# Для парсинга (только одна задача за раз)
Флаг Q говорит о наименовании очереди.
celery -A tasks worker -Q parsing --concurrency=1
# Для остальных задач (параллельно, конкурентно 4 процесса)
celery -A tasks worker -Q messages --concurrency=4

Эти запуски привязывают воркера к конкретной очереди.
Первый слушает только очередь parsing и обрабатывает одну задачу за раз (так как --concurrency=1) - берем 1 ворвера и выполняем по 1 задаче,
чтобы не получить бан от сайта КадАрбитр.

Так же один воркер может обрабатывать несколько очередей:
celery -A tasks worker -Q parsing,messages --concurrency=1

Запуск flower
celery -A tasks.app flower
"""

from celery import Celery
from .settings_env import settings


task_app = Celery(
    'tasks',
    broker=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"
)
