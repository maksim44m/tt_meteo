import os
from logging.config import fileConfig

from sqlalchemy import create_engine, engine_from_config
from sqlalchemy import pool
from alembic import context

from app.db.models import Base
from app.db.base import DATABASE_URL

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Создание синхронного URL для Alembic
SYNC_DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg', 'postgresql')

# Подключение к базе данных через переменную окружения
if os.environ.get('DATABASE_URL'):
    config.set_main_option("sqlalchemy.url", os.environ.get('DATABASE_URL'))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
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
    """
    # Используем синхронный URL для Alembic
    connectable = create_engine(SYNC_DATABASE_URL, poolclass=pool.NullPool)

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