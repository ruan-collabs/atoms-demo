from alembic import context
from sqlalchemy import create_engine, pool
from app.config import settings
from app.db import Base
from app import models  # noqa: F401

config = context.config

def run_migrations_offline():
    context.configure(url=settings.db_url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    engine = create_engine(settings.db_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
