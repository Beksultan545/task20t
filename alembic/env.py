import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

from models import Base  # ✅ Сенің Base (SQLAlchemy declarative_base)

config = context.config

# Alembic .ini файлынан sqlalchemy.url алады
fileConfig(config.config_file_name)

target_metadata = Base.metadata  # ✅ автогенерация үшін

def run_migrations_offline() -> None:
    """Offline режим (engine құрмай)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=None,
    )

    async with connectable.connect() as connection:
        def do_run_migrations(sync_connection):
            context.configure(
                connection=sync_connection,
                target_metadata=target_metadata,
                compare_type=True,
            )
            with context.begin_transaction():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
