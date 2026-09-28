from uuid import uuid4
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.models import (
    FoodItem, Inventory, Order, OrderDetail, Payment,
    PaymentMode, PaymentStatus, OrderStatus
)

VALID_SLOTS = {
    "12:30 PM – 12:45 PM",
    "12:45 PM – 1:00 PM",
    "1:00 PM – 1:15 PM",
    "1:15 PM – 1:30 PM",
    "1:30 PM – 1:45 PM"
}


def normalize_slot(slot: str) -> str:
    """Normalize hyphen styles to standard en-dash for consistency."""
    return slot.replace(" - ", " – ").replace("-", "–").strip()


def create_order(db: Session, user, payload):
    """
    RDBMS Transaction in Action:
    1. Validates input and pickup slot.
    2. Performs row-level pessimistic locking (SELECT ... FOR UPDATE) on the inventory records.
    3. Validates real-time availability and stock sufficiency.
    4. Calculates total amount on the server (authoritative).
    5. Deducts inventory stock.
    6. Creates Order, OrderDetail, and Payment records.
    7. Atomically commits the transaction or rolls back completely on any failure.
    """
    clean_slot = normalize_slot(payload.pickup_slot)
    if clean_slot not in VALID_SLOTS:
        raise HTTPException(422, f"Invalid pickup slot '{payload.pickup_slot}'. Choose an active canteen slot.")

    ids = [i.food_id for i in payload.items]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Each food item can occur at most once in an order. Use quantities instead.")

    # Pessimistic Row Lock: Lock only the Inventory rows directly.
    inventory_rows = db.execute(
        select(Inventory)
        .options(joinedload(Inventory.food))
        .where(Inventory.food_id.in_(ids))
        .with_for_update(of=Inventory)
    ).scalars().unique().all()

    found = {row.food_id: row.food for row in inventory_rows}
    if len(found) != len(ids):
        raise HTTPException(404, "One or more food items were not found")

    total = Decimal('0')
    order = Order(
        student_id=user.id,
        pickup_slot=clean_slot,
        status=OrderStatus.PLACED,
        total_amount=0
    )

    try:
        for line in payload.items:
            food = found[line.food_id]
            if not food.active or not food.available:
                raise HTTPException(409, f"'{food.name}' is currently unavailable or out of stock")

            if not food.inventory or food.inventory.stock_quantity < line.quantity:
                current_stock = food.inventory.stock_quantity if food.inventory else 0
                raise HTTPException(
                    409,
                    f"Insufficient stock for '{food.name}'. Only {current_stock} item(s) left."
                )

            unit = Decimal(str(food.price))
            subtotal = unit * line.quantity
            total += subtotal

            # Deduct stock
            food.inventory.stock_quantity -= line.quantity

            order.details.append(
                OrderDetail(
                    food_id=food.id,
                    quantity=line.quantity,
                    unit_price=unit,
                    subtotal=subtotal
                )
            )

        order.total_amount = total
        db.add(order)
        db.flush()

        mode = PaymentMode(payload.payment_mode)
        payment_status = PaymentStatus.SUCCESS if mode == PaymentMode.MOCK_ONLINE else PaymentStatus.PENDING
        tx_ref = f"MOCK-{uuid4().hex[:12].upper()}"

        db.add(
            Payment(
                order_id=order.id,
                amount=total,
                mode=mode,
                status=payment_status,
                transaction_reference=tx_ref
            )
        )

        db.commit()
        db.refresh(order)
        return order

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Order transaction failed: {str(exc)}")
