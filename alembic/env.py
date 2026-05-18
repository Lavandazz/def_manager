"""
После подключения инициируется база - создается базовая миграция без изменений : alembic revision -m "init_existing_db" 
Сгенерированный файл (в папке versions/) должен содержать пустые функции upgrade() и downgrade().
Применяется пустая миграция : alembic upgrade head. Изменений в базе не будет. 
В бд создастся таблица с миграциями alembic_version

Далее можно менять структуру бд и создавать и применять миграции : 
1) alembic revision --autogenerate -m "add_auth_fields" 
2) alembic upgrade head --sql - покажет sql запросы
или alembic upgrade head 

* --autogenerate нельзя использовать с непустой базой, иначе будет создана заново пустая база
* alembic downgrade -1 - понижение миграции на одну
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from config.settings_env import settings
from config.db.models import Base
from alembic import context


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Устанавливаем конфиг к базе
config.set_main_option("sqlalchemy.url", settings.get_sync_db_url())

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Base.metadata - содержит все таблицы наследники Base.
# Alembic использует эту метаинформацию, чтобы сравнить текущую структуру базы данных с моделями и сгенерировать миграции 
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
