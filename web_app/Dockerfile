FROM python:3.13-slim
LABEL authors="Марина"


# Говорим Python не создавать временные файлы (.pyc) - чтобы не захламлять контейнер
ENV PYTHONDONTWRITEBYTECODE 1

# Говорим Python сразу показывать все сообщения в консоли (без задержек)
ENV PYTHONUNBUFFERED 1

ENV TZ=Europe/Moscow

WORKDIR /app

COPY web_app/requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируется общий код
COPY shared/ /app/shared/
COPY web_app/ /app/web_app/ 

#  Миграции
COPY alembic.ini /app/
COPY alembic/ /app/alembic/

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]