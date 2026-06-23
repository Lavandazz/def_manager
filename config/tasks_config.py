"""
Запуск процесса таски
celery -A tasks worker --loglevel=info
или
# Для парсинга (только одна задача за раз)
Флаг Q говорит о наименовании очереди.
--hostname (или -n) говорит об именя ворвкера
celery -A celery_app.task_manager worker -Q parsing --concurrency=1 --hostname=worker-parsing@%h

# Для остальных задач (параллельно, конкурентно 2, 4 процесса)

celery -A celery_app.task_manager worker -Q messages --concurrency=2 -n=worker-messages@%h

Эти запуски привязывают воркера к конкретной очереди.
Первый слушает только очередь parsing и обрабатывает одну задачу за раз (так как --concurrency=1) - берем 1 ворвера и выполняем по 1 задаче,
чтобы не получить бан от сайта КадАрбитр.

Так же один воркер может обрабатывать несколько очередей:
celery -A tasks worker -Q parsing,messages --concurrency=2

Запуск celery beat для выполнения периодических задач
celery -A config.tasks_config beat --loglevel=info

Запуск flower
celery -A tasks.app flower
"""

from celery import Celery
from .settings_env import settings


app = Celery(
    'tasks',
    broker=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"
)

# Автоматически находим задачи в модулях внутри пакета celery_app
app.autodiscover_tasks(['celery_app'])

app.conf.beat_schedule = {
    'add-every-10-seconds': {
        # 'task': 'tasks.add',  # запуск задачи парсинга
        'task': 'celery_app.task_manager.send_message',
        'schedule': 30.0,
        'args': ("hello",),
        'options': {'queue': 'messages'}, 
    },
}
