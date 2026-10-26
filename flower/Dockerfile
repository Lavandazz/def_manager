FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Europe/Moscow

WORKDIR /app

COPY flower/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ /app/shared/
CMD ["celery", "-A", "shared.config.tasks_config", "flower", "--port=5555"]