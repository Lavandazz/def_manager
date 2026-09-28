# def_manager

Система управления документами и делами арбитражных управляющих на основе данных портала КадАрбитр.

Проект задуман как замена telegram-боту-помощнику юристов: расширяет возможности ведения дел, автоматизирует рутину и снимает с юриста механическую работу.


## Возможности

- **Парсинг КадАрбитра.** Playwright забирает движение документов, даты судебных заседаний и связанные материалы по каждому делу.
- **Ведение дел.** Единый реестр должников (физлица и юрлица), банков, счетов, адресов и судебных сессий с разграничением доступа по пользователям.
- **Автогенерация запросов.** На основе данных дела формируются документы Word для отправки в госорганы и банки.
- **Рассылка.** Отправка уведомлений через `fastapi_mail`.
- **Фоновые задачи.** Долгие операции (парсинг, генерация, рассылка) выполняются в Celery и не блокируют портал.

## Стек

| Слой | Технология |
|------|------------|
| Web / API | FastAPI, Jinja2, Bootstrap 5 |
| База данных | PostgreSQL, SQLAlchemy 2.x (async), Alembic |
| Парсинг | Playwright |
| Очереди | Celery, Redis |
| Аутентификация | JWT (access + refresh) |
| Почта | fastapi_mail |
| Валидация | Pydantic v2 |
| Контейнеризация | Docker / docker-compose |

## Быстрый старт

### 1. Клонирование

```bash
git clone https://github.com/<your-username>/def_manager.git
cd def_manager
```

### 2. Окружение

```bash
python -m venv .venv
source .venv/bin/activate           # Linux / macOS
# .venv\Scripts\activate            # Windows

pip install -r requirements.txt
playwright install chromium
```

### 3. Переменные окружения

Создайте два файла в корне проекта — `.env` и `.env_mail`. Оба не коммитятся в репозиторий.

#### `.env`

```dotenv
# --- PostgreSQL ---
POSTGRES_NAME=my_base_name
POSTGRES_USER=my_user
POSTGRES_PASSWORD=my_password
POSTGRES_HOST=my_host
POSTGRES_PORT=5432

# --- Redis ---
REDIS_HOST=my_host
REDIS_PORT=6380
REDIS_PASSWORD=my_password

# --- JWT ---
SECRET_KEY=mypassword
REFRESH_SECRET_KEY=mypasswordkey
ALGORITHM=HS256

# --- Прочее ---
DEFAULT_PASSWORD=qwerty
```

#### `.env_mail`

```dotenv
# Адрес, с которого идёт рассылка
MAIL_FROM=example@mail.ru

# Пароль приложения для входа в почтовый ящик из сторонних сервисов
EMAIL_PASSWORD=my_password
```

> Для `MAIL_FROM` на Mail.ru / Яндекс.Почте нужен именно пароль приложения, а не основной пароль от аккаунта. Включается в настройках безопасности почтового ящика.

### 4. Миграции

```bash
alembic upgrade head
```

### 5. Запуск

```bash
docker compose build
docker compose up
```

Приложение будет доступно по адресу [http://localhost:8000](http://localhost:8000).

## Структура проекта

```text
def_manager/
├── app/
    ├── routers/
    │   ├── html_debtor.py        # HTML-страницы по должникам
    │   ├── api_*.py              # JSON API
    │   └── ...
    ├── templates/                # Jinja2
    │   ├── layout.html
    │   ├── debtor_edit.html
    │   └── ...
    ├── app.py
    └── ...
├── celery_tasks/  # celery Задачи
├── config/
    ├──schemas/                  # Pydantic-схемы (валидация входа)
    ├── db/
    │   └── models.py         # SQLAlchemy-модели
    ├── settings_env.py           # Pydantic Settings, чтение .env
    └── ...
├── core/
    ├── repository/             # Слой доступа к БД
    │   ├── debtor.py
    │   ├── case.py
    │   ├── region.py
    │   └── ...
    ├── services/                 # Бизнес-логика
    │   ├── debtor.py
    │   ├── case.py
    │   └── ...
├── documents/               # Генерация документов Word
├── parser_app/                    # Парсер
│   ├── parser_plw.py
│   └── ...
├── alembic/
├── .env
├── .env_mail
├── requirements.txt
└── ...
```

## Слои

- **Repositories** — только SQLAlchemy: `select`, `joinedload`, `selectinload`.
- **Services** — сценарии: проверка прав, создание связанных сущностей, генерация документов.
- **Routers** — HTTP: принять форму, вызвать сервис, отрендерить шаблон или вернуть JSON.
- **Schemas** — валидация входных данных через Pydantic. ORM-модели в шаблон отдаются напрямую, без промежуточного слоя.


## Разработка

### Полезные команды

```bash
# Новая миграция
alembic revision --autogenerate -m "add table X"

# Применить миграции
alembic upgrade head

# Откатить одну
alembic downgrade -1

```
