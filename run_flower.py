"""
Запуск flower: python run_flower.py
Остановка: pkill -f "celery.*flower"
или поиск процесса ps aux | grep flower
и kill 1234 - номер процесса
"""


import os
import subprocess
from config.settings_env import settings

broker_url = os.environ["CELERY_BROKER_URL"] = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

# Команда для выполнения в терминале
# command = ["celery", "-A", "tasks", "flower"]
command = ["celery", "-A", "app.utils.task_manager", "flower"]

# Запускаем процесс в фоне
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# Не ждём, продолжаем выполнение скрипта
print(f"Flower запущен в фоне, PID: {process.pid}")
print(f"Для завершения процесса нажать enter и ввести  kill {process.pid}")
input("Или Нажмите Enter для остановки Flower...\n")
input()

process.terminate()
process.wait()