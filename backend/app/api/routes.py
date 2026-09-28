from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_token, current_user, require_roles
from app.models.models import (
    Role, OrderStatus, PaymentMode, PaymentStatus,
    User, Category, FoodItem, Inventory, Order, OrderDetail, Payment,
    Supplier, SupplierItem
)
from app.schemas.schemas import (
    Register, Login, FoodCreate, FoodUpdate, OrderCreate, StatusUpdate,
    InventoryUpdate, CategoryCreate, CategoryUpdate,
    SupplierCreate, SupplierUpdate, SupplierItemCreate,
    UserRoleUpdate, UserStatusUpdate
)
from app.services.orders import create_order

router = APIRouter(prefix="/api")


def user_out(u: User):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role.value if isinstance(u.role, Role) else str(u.role),
        "phone": u.phone,
        "department": u.department,
        "active": u.active,
        "created_at": u.created_at.isoformat() if u.created_at else None
    }


def food_out(f: FoodItem):
    is_available = f.available and f.active and bool(f.inventory and f.inventory.stock_quantity > 0)
    return {
        "id": f.id,
        "name": f.name,
        "description": f.description,
        "price": float(f.price),
        "available": is_available,
        "active": f.active,
        "category": {
            "id": f.category.id,
            "name": f.category.name
        } if f.category else None,
        "inventory": {
            "stock_quantity": f.inventory.stock_quantity,
            "minimum_stock": f.inventory.minimum_stock
        } if f.inventory else None
    }


def order_out(o: Order):
    return {
        "id": o.id,
        "token": f"QB-{o.id:04d}",
        "pickup_slot": o.pickup_slot,
        "status": o.status.value if isinstance(o.status, OrderStatus) else str(o.status),
        "total_amount": float(o.total_amount),
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "student": {
            "id": o.student.id,
            "name": o.student.name,
            "email": o.student.email
        } if o.student else None,
        "staff": {
            "id": o.staff.id,
            "name": o.staff.name
        } if o.staff else None,
        "items": [
            {
                "id": d.id,
                "food_id": d.food_id,
                "name": d.food.name if d.food else f"Item #{d.food_id}",
                "quantity": d.quantity,
                "unit_price": float(d.unit_price),
                "subtotal": float(d.subtotal)
            }
            for d in o.details
        ],
        "payment": {
            "status": o.payment.status.value if isinstance(o.payment.status, PaymentStatus) else str(o.payment.status),
            "mode": o.payment.mode.value if isinstance(o.payment.mode, PaymentMode) else str(o.payment.mode),
            "reference": o.payment.transaction_reference,
            "amount": float(o.payment.amount)
        } if o.payment else None
    }


# ==========================================
# AUTHENTICATION
# ==========================================

@router.post('/auth/register', status_code=201)
def register(p: Register, db: Session = Depends(get_db)):
    """Register a new student account."""
    if db.scalar(select(User).where(User.email == p.email)):
        raise HTTPException(409, "An account with this email already exists")
    u = User(
        name=p.name,
        email=p.email,
        password_hash=hash_password(p.password),
        phone=p.phone,
        department=p.department,
        role=Role.STUDENT,
        active=True
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    token = create_token(u.id, u.role.value)
    return {"access_token": token, "token_type": "bearer", "user": user_out(u)}


@router.post('/auth/login')
def login(p: Login, db: Session = Depends(get_db)):
    """Authenticate student, staff, or admin."""
    u = db.scalar(select(User).where(User.email == p.email))
    if not u or not verify_password(p.password, u.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if not u.active:
        raise HTTPException(403, "This account has been deactivated. Please contact an administrator.")
    token = create_token(u.id, u.role.value)
    return {"access_token": token, "token_type": "bearer", "user": user_out(u)}


@router.get('/auth/me')
def me(u: User = Depends(current_user)):
    return user_out(u)


# ==========================================
# CATEGORIES
# ==========================================

@router.get('/categories')
def list_categories(db: Session = Depends(get_db)):
    items = db.scalars(select(Category).order_by(Category.name)).all()
    return [{"id": x.id, "name": x.name} for x in items]


@router.post('/categories', status_code=201)
def add_category(p: CategoryCreate, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    if db.scalar(select(Category).where(Category.name.ilike(p.name))):
        raise HTTPException(409, "A category with this name already exists")
    c = Category(name=p.name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name}


@router.put('/categories/{category_id}')
def update_category(category_id: int, p: CategoryUpdate, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    c = db.get(Category, category_id)
    if not c:
        raise HTTPException(404, "Category not found")
    existing = db.scalar(select(Category).where(Category.name.ilike(p.name), Category.id != category_id))
    if existing:
        raise HTTPException(409, "Another category with this name already exists")
    c.name = p.name
    db.commit()
    return {"id": c.id, "name": c.name}


# ==========================================
# FOOD ITEMS
# ==========================================

@router.get('/foods')
def list_foods(db: Session = Depends(get_db)):
    items = db.scalars(
        select(FoodItem)
        .options(joinedload(FoodItem.category), joinedload(FoodItem.inventory))
        .where(FoodItem.active == True)
        .order_by(FoodItem.name)
    ).unique().all()
    return [food_out(x) for x in items]


@router.get('/foods/{food_id}')
def get_food(food_id: int, db: Session = Depends(get_db)):
    f = db.scalar(
        select(FoodItem)
        .options(joinedload(FoodItem.category), joinedload(FoodItem.inventory))
        .where(FoodItem.id == food_id)
    )
    if not f or not f.active:
        raise HTTPException(404, "Food item not found")
    return food_out(f)


@router.post('/foods', status_code=201)
def add_food(p: FoodCreate, db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    if not db.get(Category, p.category_id):
        raise HTTPException(404, "Category not found")
    if db.scalar(select(FoodItem).where(FoodItem.name.ilike(p.name))):
        raise HTTPException(409, "A food item with this name already exists")

    f = FoodItem(
        category_id=p.category_id,
        name=p.name,
        description=p.description,
        price=p.price,
        available=p.available and (p.stock_quantity > 0)
    )
    f.inventory = Inventory(stock_quantity=p.stock_quantity, minimum_stock=p.minimum_stock)
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"id": f.id, "name": f.name}


@router.put('/foods/{food_id}')
def update_food(food_id: int, p: FoodUpdate, db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    f = db.get(FoodItem, food_id)
    if not f:
        raise HTTPException(404, "Food item not found")

    if p.category_id is not None:
        if not db.get(Category, p.category_id):
            raise HTTPException(404, "Category not found")
        f.category_id = p.category_id

    if p.name is not None and p.name != f.name:
        existing = db.scalar(select(FoodItem).where(FoodItem.name.ilike(p.name), FoodItem.id != food_id))
        if existing:
            raise HTTPException(409, "Another food item with this name already exists")
        f.name = p.name

    if p.description is not None:
        f.description = p.description
    if p.price is not None:
        f.price = p.price
    if p.available is not None:
        f.available = p.available
    if p.active is not None:
        f.active = p.active

    db.commit()
    return {"message": "Food item updated"}


@router.delete('/foods/{food_id}')
def deactivate_food(food_id: int, db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    f = db.get(FoodItem, food_id)
    if not f:
        raise HTTPException(404, "Food item not found")
    # Soft delete preserves order history
    f.active = False
    f.available = False
    db.commit()
    return {"message": "Food item safely deactivated"}


# ==========================================
# ORDERS
# ==========================================

@router.post('/orders', status_code=201)
def place_order(p: OrderCreate, db: Session = Depends(get_db), u: User = Depends(require_roles('STUDENT'))):
    """Atomic order checkout transaction with pessimistic inventory locking."""
    o = create_order(db, u, p)
    # Refresh with full eager relations
    o = db.scalar(
        select(Order)
        .options(
            joinedload(Order.student),
            joinedload(Order.details).joinedload(OrderDetail.food),
            joinedload(Order.payment)
        )
        .where(Order.id == o.id)
    )
    return order_out(o)


@router.get('/orders/my')
def my_orders(db: Session = Depends(get_db), u: User = Depends(require_roles('STUDENT'))):
    """List current student's order history."""
    rows = db.scalars(
        select(Order)
        .options(
            joinedload(Order.student),
            joinedload(Order.details).joinedload(OrderDetail.food),
            joinedload(Order.payment)
        )
        .where(Order.student_id == u.id)
        .order_by(Order.created_at.desc())
    ).unique().all()
    return [order_out(o) for o in rows]


@router.get('/orders')
def all_orders(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    """List all canteen pre-orders for kitchen and staff display."""
    rows = db.scalars(
        select(Order)
        .options(
            joinedload(Order.student),
            joinedload(Order.details).joinedload(OrderDetail.food),
            joinedload(Order.payment)
        )
        .order_by(Order.created_at.desc())
    ).unique().all()
    return [order_out(o) for o in rows]


@router.get('/orders/{order_id}')
def get_order(order_id: int, db: Session = Depends(get_db), u: User = Depends(current_user)):
    o = db.scalar(
        select(Order)
        .options(
            joinedload(Order.student),
            joinedload(Order.details).joinedload(OrderDetail.food),
            joinedload(Order.payment)
        )
        .where(Order.id == order_id)
    )
    if not o:
        raise HTTPException(404, "Order not found")
    if u.role == Role.STUDENT and o.student_id != u.id:
        raise HTTPException(403, "You can only view your own orders")
    return order_out(o)


@router.patch('/orders/{order_id}/status')
def update_order_status(
    order_id: int,
    p: StatusUpdate,
    db: Session = Depends(get_db),
    u: User = Depends(require_roles('STAFF', 'ADMIN'))
):
    """
    Enforce valid order status state transitions.
    - If status -> COMPLETED: mark PAY_AT_PICKUP payment as SUCCESS.
    - If status -> CANCELLED: restore food inventory stock atomically!
    """
    o = db.scalar(
        select(Order)
        .options(
            joinedload(Order.details).joinedload(OrderDetail.food).joinedload(FoodItem.inventory),
            joinedload(Order.payment)
        )
        .where(Order.id == order_id)
    )
    if not o:
        raise HTTPException(404, "Order not found")

    allowed = {
        OrderStatus.PLACED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
        OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
        OrderStatus.READY: {OrderStatus.COMPLETED},
        OrderStatus.COMPLETED: set(),
        OrderStatus.CANCELLED: set()
    }
    target = OrderStatus(p.status)
    if target not in allowed[o.status]:
        raise HTTPException(409, f"Invalid state transition: Cannot change {o.status.value} to {target.value}")

    # Critical Business Logic: Restore inventory stock on cancellation
    if target == OrderStatus.CANCELLED:
        for detail in o.details:
            if detail.food and detail.food.inventory:
                detail.food.inventory.stock_quantity += detail.quantity
        if o.payment:
            o.payment.status = PaymentStatus.REFUNDED

    # Critical Business Logic: Record payment collected when Completed
    if target == OrderStatus.COMPLETED:
        if o.payment and o.payment.status == PaymentStatus.PENDING:
            o.payment.status = PaymentStatus.SUCCESS

    o.status = target
    o.staff_id = u.id
    db.commit()
    return {"message": "Status updated", "status": target.value}


@router.post('/orders/{order_id}/cancel')
def student_cancel_order(order_id: int, db: Session = Depends(get_db), u: User = Depends(require_roles('STUDENT'))):
    """Allow students to cancel their own order if it is still PLACED."""
    o = db.scalar(
        select(Order)
        .options(
            joinedload(Order.details).joinedload(OrderDetail.food).joinedload(FoodItem.inventory),
            joinedload(Order.payment)
        )
        .where(Order.id == order_id)
    )
    if not o:
        raise HTTPException(404, "Order not found")
    if o.student_id != u.id:
        raise HTTPException(403, "You can only cancel your own order")
    if o.status != OrderStatus.PLACED:
        raise HTTPException(409, f"Cannot cancel order in {o.status.value} state. Contact canteen staff.")

    for detail in o.details:
        if detail.food and detail.food.inventory:
            detail.food.inventory.stock_quantity += detail.quantity
    if o.payment:
        o.payment.status = PaymentStatus.REFUNDED

    o.status = OrderStatus.CANCELLED
    db.commit()
    return {"message": "Order cancelled successfully and stock restored", "status": "CANCELLED"}


# ==========================================
# INVENTORY
# ==========================================

@router.get('/inventory')
def get_inventory(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    rows = db.scalars(
        select(Inventory)
        .options(joinedload(Inventory.food))
        .join(FoodItem)
        .where(FoodItem.active == True)
        .order_by(Inventory.stock_quantity)
    ).all()
    return [
        {
            "food_id": i.food_id,
            "food_name": i.food.name,
            "stock_quantity": i.stock_quantity,
            "minimum_stock": i.minimum_stock,
            "state": (
                "OUT OF STOCK" if i.stock_quantity == 0
                else "LOW STOCK" if i.stock_quantity < i.minimum_stock
                else "NORMAL"
            )
        }
        for i in rows
    ]


@router.patch('/inventory/{food_id}')
def update_inventory(
    food_id: int,
    p: InventoryUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles('STAFF', 'ADMIN'))
):
    i = db.scalar(select(Inventory).where(Inventory.food_id == food_id))
    if not i:
        raise HTTPException(404, "Inventory record not found")
    i.stock_quantity = p.stock_quantity
    if p.minimum_stock is not None:
        i.minimum_stock = p.minimum_stock
    db.commit()
    return {"message": "Inventory updated", "food_id": food_id, "stock_quantity": i.stock_quantity}


# ==========================================
# SUPPLIERS & SUPPLIER ITEMS (M:N)
# ==========================================

@router.get('/suppliers')
def list_suppliers(db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    return [
        {"id": s.id, "name": s.name, "contact": s.contact, "email": s.email, "address": s.address}
        for s in db.scalars(select(Supplier).order_by(Supplier.name))
    ]


@router.post('/suppliers', status_code=201)
def add_supplier(p: SupplierCreate, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    if db.scalar(select(Supplier).where(Supplier.name.ilike(p.name))):
        raise HTTPException(409, "A supplier with this name already exists")
    s = Supplier(name=p.name, contact=p.contact, email=p.email, address=p.address)
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "name": s.name}


@router.put('/suppliers/{supplier_id}')
def update_supplier(supplier_id: int, p: SupplierUpdate, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    s = db.get(Supplier, supplier_id)
    if not s:
        raise HTTPException(404, "Supplier not found")
    if p.name and p.name != s.name:
        existing = db.scalar(select(Supplier).where(Supplier.name.ilike(p.name), Supplier.id != supplier_id))
        if existing:
            raise HTTPException(409, "Another supplier with this name already exists")
        s.name = p.name
    if p.contact is not None:
        s.contact = p.contact
    if p.email is not None:
        s.email = p.email
    if p.address is not None:
        s.address = p.address
    db.commit()
    return {"message": "Supplier updated"}


@router.get('/suppliers/{supplier_id}/items')
def get_supplier_items(supplier_id: int, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    """List food items supplied by this supplier (associative table SupplierItem)."""
    rows = db.scalars(
        select(SupplierItem)
        .options(joinedload(SupplierItem.food))
        .where(SupplierItem.supplier_id == supplier_id)
        .order_by(SupplierItem.supply_date.desc())
    ).all()
    return [
        {
            "food_id": item.food_id,
            "food_name": item.food.name,
            "supply_price": float(item.supply_price),
            "quantity_supplied": item.quantity_supplied,
            "supply_date": item.supply_date.isoformat() if item.supply_date else None
        }
        for item in rows
    ]


@router.post('/suppliers/{supplier_id}/items', status_code=201)
def record_supply(
    supplier_id: int,
    p: SupplierItemCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles('ADMIN'))
):
    """
    Record inventory intake from a supplier into supplier_items,
    and increment the food item's inventory stock!
    """
    if not db.get(Supplier, supplier_id):
        raise HTTPException(404, "Supplier not found")
    food = db.get(FoodItem, p.food_id)
    if not food:
        raise HTTPException(404, "Food item not found")

    # Add or update supplier item intake
    si = db.scalar(
        select(SupplierItem).where(
            SupplierItem.supplier_id == supplier_id,
            SupplierItem.food_id == p.food_id
        )
    )
    if si:
        si.supply_price = p.supply_price
        si.quantity_supplied += p.quantity_supplied
        si.supply_date = datetime.now(timezone.utc)
    else:
        si = SupplierItem(
            supplier_id=supplier_id,
            food_id=p.food_id,
            supply_price=p.supply_price,
            quantity_supplied=p.quantity_supplied
        )
        db.add(si)

    # Increment stock
    if food.inventory:
        food.inventory.stock_quantity += p.quantity_supplied

    db.commit()
    return {"message": "Supply intake recorded successfully", "new_stock": food.inventory.stock_quantity if food.inventory else None}


# ==========================================
# USER MANAGEMENT (ADMIN)
# ==========================================

@router.get('/users')
def list_users(db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    users = db.scalars(select(User).order_by(User.role, User.name)).all()
    return [user_out(u) for u in users]


@router.patch('/users/{user_id}/role')
def update_user_role(user_id: int, p: UserRoleUpdate, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.role = Role(p.role)
    db.commit()
    return {"message": f"User role updated to {u.role.value}"}


@router.patch('/users/{user_id}/status')
def update_user_status(user_id: int, p: UserStatusUpdate, db: Session = Depends(get_db), _=Depends(require_roles('ADMIN'))):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.active = p.active
    db.commit()
    return {"message": f"User {'activated' if u.active else 'deactivated'}"}


# ==========================================
# REPORTS & ANALYTICS (DBMS QUERIES & VIEWS)
# ==========================================

@router.get('/reports/today')
def report_today(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    """Returns today's order count and successful revenue."""
    today = date.today()
    orders = db.scalars(
        select(Order)
        .options(joinedload(Order.payment))
        .where(func.date(Order.created_at) == today)
    ).unique().all()

    revenue = sum(
        float(o.total_amount)
        for o in orders
        if o.payment and o.payment.status == PaymentStatus.SUCCESS and o.status != OrderStatus.CANCELLED
    )
    return {
        "date": today.isoformat(),
        "orders": len(orders),
        "revenue": round(revenue, 2)
    }


@router.get('/reports/popular-food')
def report_popular(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    """Aggregate query: Most popular food items by quantity sold."""
    rows = db.execute(
        select(FoodItem.name, func.sum(OrderDetail.quantity).label('quantity'))
        .join(OrderDetail, OrderDetail.food_id == FoodItem.id)
        .join(Order, Order.id == OrderDetail.order_id)
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(FoodItem.name)
        .order_by(func.sum(OrderDetail.quantity).desc())
    ).all()
    return [{"name": r.name, "quantity": int(r.quantity)} for r in rows]


@router.get('/reports/low-stock')
def report_low_stock(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    """Filter inventory items where stock is below minimum threshold."""
    rows = db.scalars(
        select(Inventory)
        .options(joinedload(Inventory.food))
        .join(FoodItem)
        .where(FoodItem.active == True, Inventory.stock_quantity < Inventory.minimum_stock)
        .order_by(Inventory.stock_quantity)
    ).all()
    return [
        {
            "food": i.food.name,
            "stock": i.stock_quantity,
            "minimum": i.minimum_stock
        }
        for i in rows
    ]


@router.get('/reports/pickup-slots')
def report_pickup_slots(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    """Distribution of active orders across scheduled pickup slots."""
    rows = db.execute(
        select(Order.pickup_slot, func.count(Order.id).label('orders'))
        .where(Order.status != OrderStatus.CANCELLED)
        .group_by(Order.pickup_slot)
        .order_by(Order.pickup_slot)
    ).all()
    return [{"slot": r.pickup_slot, "orders": int(r.orders)} for r in rows]


@router.get('/reports/sales')
def report_sales(db: Session = Depends(get_db), _=Depends(require_roles('STAFF', 'ADMIN'))):
    """
    RDBMS Concept in Action:
    Queries the PostgreSQL view `daily_sales_summary`.
    """
    try:
        rows = db.execute(
            text("SELECT sale_date, total_orders, total_revenue, unique_customers FROM daily_sales_summary ORDER BY sale_date DESC")
        ).fetchall()
        return [
            {
                "date": str(r[0]),
                "orders": int(r[1]),
                "revenue": float(r[2]),
                "customers": int(r[3])
            }
            for r in rows
        ]
    except Exception:
        # Fallback if view query fails
        rows = db.execute(
            select(
                func.date(Payment.created_at).label('date'),
                func.coalesce(func.sum(Payment.amount), 0).label('revenue'),
                func.count(Payment.id).label('orders')
            )
            .where(Payment.status == PaymentStatus.SUCCESS)
            .group_by(func.date(Payment.created_at))
            .order_by(func.date(Payment.created_at).desc())
        ).all()
        return [{"date": str(r.date), "revenue": float(r.revenue), "orders": int(r.orders)} for r in rows]
