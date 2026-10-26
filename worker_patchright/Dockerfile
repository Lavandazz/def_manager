# FROM python:3.13-slim

FROM ghcr.io/borski/patchright-docker

# Говорим Python не создавать временные файлы (.pyc) - чтобы не захламлять контейнер
ENV PYTHONDONTWRITEBYTECODE 1

# Говорим Python сразу показывать все сообщения в консоли (без задержек)
ENV PYTHONUNBUFFERED 1

ENV TZ=Europe/Moscow

WORKDIR /app

COPY worker_patchright/requirements.txt .

# Xvfb + xauth - для «визуального» режима внутри headless-сервера
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /app/shared/
COPY worker_patchright/ /app/

# Устанавливаем patchright
# RUN pip install --upgrade pip && \
#     pip install -r requirements.txt && \
#     pip install patchright && \
#     patchright install --with-deps chromium
