"""Initial QuickBite schema.

Revision ID: 0001
Revises:
"""
from pathlib import Path
import sys
from alembic import op

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
from app.core.database import Base
from app.models import models
revision='0001'; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    Base.metadata.create_all(bind=op.get_bind())
    op.execute("""CREATE VIEW available_food_items AS
        SELECT f.id, f.name, f.price, i.stock_quantity
        FROM food_items f JOIN inventory i ON i.food_id = f.id
        WHERE f.active AND f.available AND i.stock_quantity > 0""")
def downgrade():
    op.execute("DROP VIEW IF EXISTS available_food_items")
    Base.metadata.drop_all(bind=op.get_bind())
