import enum
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, ForeignKey,
    CheckConstraint, Enum, Text, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Role(str, enum.Enum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class OrderStatus(str, enum.Enum):
    PLACED = "PLACED"
    PREPARING = "PREPARING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentMode(str, enum.Enum):
    MOCK_ONLINE = "MOCK_ONLINE"
    PAY_AT_PICKUP = "PAY_AT_PICKUP"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.STUDENT)
    phone: Mapped[str | None] = mapped_column(String(30))
    department: Mapped[str | None] = mapped_column(String(100))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(
        back_populates="student",
        foreign_keys="Order.student_id"
    )
    processed_orders: Mapped[list["Order"]] = relationship(
        back_populates="staff",
        foreign_keys="Order.staff_id"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)

    foods: Mapped[list["FoodItem"]] = relationship(back_populates="category")


class FoodItem(Base):
    __tablename__ = "food_items"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_food_price_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    category: Mapped[Category] = relationship(back_populates="foods")
    inventory: Mapped["Inventory"] = relationship(back_populates="food", uselist=False, cascade="all, delete-orphan")
    supplier_records: Mapped[list["SupplierItem"]] = relationship(back_populates="food")


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("stock_quantity >= 0", name="ck_stock_nonnegative"),
        CheckConstraint("minimum_stock >= 0", name="ck_min_stock_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), unique=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    minimum_stock: Mapped[int] = mapped_column(Integer, default=5)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now()
    )

    food: Mapped[FoodItem] = relationship(back_populates="inventory")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_order_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    staff_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    pickup_slot: Mapped[str] = mapped_column(String(40))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PLACED)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    student: Mapped[User] = relationship(back_populates="orders", foreign_keys=[student_id])
    staff: Mapped[User | None] = relationship(back_populates="processed_orders", foreign_keys=[staff_id])
    details: Mapped[list["OrderDetail"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payment: Mapped["Payment"] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderDetail(Base):
    __tablename__ = "order_details"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_qty_positive"),
        UniqueConstraint("order_id", "food_id", name="uq_order_food"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    food_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2))

    order: Mapped[Order] = relationship(back_populates="details")
    food: Mapped[FoodItem] = relationship()


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payment_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus))
    transaction_reference: Mapped[str] = mapped_column(String(80), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="payment")


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    contact: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)

    supplied_items: Mapped[list["SupplierItem"]] = relationship(back_populates="supplier")


class SupplierItem(Base):
    __tablename__ = "supplier_items"
    __table_args__ = (
        CheckConstraint("supply_price >= 0", name="ck_supply_price_nonnegative"),
        CheckConstraint("quantity_supplied > 0", name="ck_supply_qty_positive"),
    )

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), primary_key=True)
    supply_price: Mapped[float] = mapped_column(Numeric(10, 2))
    quantity_supplied: Mapped[int] = mapped_column(Integer)
    supply_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    supplier: Mapped[Supplier] = relationship(back_populates="supplied_items")
    food: Mapped[FoodItem] = relationship(back_populates="supplier_records")
