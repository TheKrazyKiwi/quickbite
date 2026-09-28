from pathlib import Path
import sys

# Alembic loads this module from backend/alembic rather than the project root.
# Put backend/ on sys.path so `app.*` imports work for `alembic upgrade head`.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core.config import settings
from app.core.database import Base
from app.models import models
config=context.config
config.set_main_option('sqlalchemy.url',settings.database_url)
target_metadata=Base.metadata
def run_migrations_offline():
    context.configure(url=settings.database_url,target_metadata=target_metadata,literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
def run_migrations_online():
    connectable=engine_from_config(config.get_section(config.config_ini_section),prefix='sqlalchemy.',poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
