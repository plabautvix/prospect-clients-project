from alembic import context

from prospect_clients.src.configurations.database import DATABASE_URL, engine
from prospect_clients.src.models.tables.base import Base

# Importing the table modules registers them on Base.metadata, which is what
# `alembic revision --autogenerate` compares the database against.
from prospect_clients.src.models.tables import (  # noqa: F401
    leads,
    operations,
    user,
)

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite cannot ALTER most things in place, so batch mode recreates
            # the table instead. Harmless on other backends.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
