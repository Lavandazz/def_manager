FROM python:3.13-slim
LABEL authors="Марина"


# Говорим Python не создавать временные файлы (.pyc) - чтобы не захламлять контейнер
ENV PYTHONDONTWRITEBYTECODE 1

# Говорим Python сразу показывать все сообщения в консоли (без задержек)
ENV PYTHONUNBUFFERED 1

ENV TZ=Europe/Moscow

WORKDIR /app

COPY worker-playwright/requirements.txt .

# Устанавливаем playwright
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install playwright && \
    playwright install --with-deps chromium

COPY . .

