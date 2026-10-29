FROM python:3.13-slim
LABEL authors="Марина"


# Говорим Python не создавать временные файлы (.pyc) - чтобы не захламлять контейнер
ENV PYTHONDONTWRITEBYTECODE 1

# Говорим Python сразу показывать все сообщения в консоли (без задержек)
ENV PYTHONUNBUFFERED 1

ENV TZ=Europe/Moscow

WORKDIR /app

COPY worker_playwright/requirements.txt .

# Устанавливаем playwright 
# Все зависимости возьмет из кэша, если есть, для ускорения сборки
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    # pip install playwright && \
    playwright install --with-deps chromium

COPY shared/ /app/shared/

COPY worker_playwright/ /app/worker_playwright

CMD ["celery", "-A", "tasks", "worker", "-Q", "playwright", "--loglevel=info"]