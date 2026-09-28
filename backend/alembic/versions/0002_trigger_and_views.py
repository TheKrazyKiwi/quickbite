"""Add daily sales summary view, inventory sync trigger, and constraint enhancements.

Revision ID: 0002
Revises: 0001
"""
from pathlib import Path
import sys
from alembic import op

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # 0. Add REFUNDED to paymentstatus enum if not present
    op.execute("ALTER TYPE paymentstatus ADD VALUE IF NOT EXISTS 'REFUNDED';")

    # 1. Create daily_sales_summary view
    op.execute("""
    CREATE OR REPLACE VIEW daily_sales_summary AS
    SELECT 
        DATE(p.created_at) AS sale_date,
        COUNT(DISTINCT o.id) AS total_orders,
        COALESCE(SUM(p.amount), 0) AS total_revenue,
        COUNT(DISTINCT o.student_id) AS unique_customers
    FROM orders o
    JOIN payments p ON p.order_id = o.id
    WHERE p.status = 'SUCCESS' AND o.status != 'CANCELLED'
    GROUP BY DATE(p.created_at);
    """)

    # 2. Create sync_food_availability trigger on inventory table
    op.execute("""
    CREATE OR REPLACE FUNCTION sync_food_availability()
    RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.stock_quantity <= 0 THEN
            UPDATE food_items SET available = FALSE WHERE id = NEW.food_id;
        ELSIF OLD.stock_quantity <= 0 AND NEW.stock_quantity > 0 THEN
            UPDATE food_items SET available = TRUE WHERE id = NEW.food_id AND active = TRUE;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_sync_food_availability ON inventory;
    CREATE TRIGGER trg_sync_food_availability
    AFTER UPDATE OF stock_quantity ON inventory
    FOR EACH ROW
    EXECUTE FUNCTION sync_food_availability();
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_sync_food_availability ON inventory;")
    op.execute("DROP FUNCTION IF EXISTS sync_food_availability();")
    op.execute("DROP VIEW IF EXISTS daily_sales_summary;")
