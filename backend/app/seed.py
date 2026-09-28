"""Run from backend: python -m app.seed after `alembic upgrade head`."""
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select, delete
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import (
    Role, OrderStatus, PaymentMode, PaymentStatus,
    User, Category, FoodItem, Inventory, Order, OrderDetail, Payment,
    Supplier, SupplierItem
)

FOOD_DATA = [
    ('Snacks', 'Veg Sandwich', 'Fresh toasted bread with cucumber, tomato & mint chutney', 50.0, 25, 8),
    ('Snacks', 'Cheese Sandwich', 'Grilled sandwich with molten cheese and herb seasoning', 65.0, 18, 6),
    ('Snacks', 'Samosa', 'Crispy spiced potato pastry served with tamarind dip', 20.0, 0, 8),  # Out of stock
    ('Meals', 'Pizza', 'Personal pan pizza with capsicum, sweet corn & mozzarella', 80.0, 5, 6),    # Low stock
    ('Meals', 'Burger', 'Crispy vegetable patty with lettuce, mayo & sesame bun', 70.0, 15, 5),
    ('Meals', 'Maggi', 'Classic hot masala noodles with diced vegetables', 55.0, 20, 6),
    ('Meals', 'Veg Roll', 'Flaky paratha wrap stuffed with sauteed spiced veggies', 60.0, 12, 5),
    ('Beverages', 'Cold Coffee', 'Rich blended chilled coffee with chocolate drizzle', 40.0, 30, 8),
    ('Beverages', 'Tea', 'Aromatic Indian masala chai brewed with fresh ginger and cardamom', 15.0, 40, 10),
    ('Beverages', 'Fresh Lime', 'Chilled sweet and salted fresh lime soda', 30.0, 22, 6),
    ('Desserts', 'Brownie', 'Warm chocolate fudge brownie with dark chocolate chips', 45.0, 10, 4),
]


def seed_database():
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.scalar(select(User).limit(1)):
            print('Database already contains records. Clearing and reseeding demo data...')
            # Clear existing data in correct FK order
            db.execute(delete(SupplierItem))
            db.execute(delete(Payment))
            db.execute(delete(OrderDetail))
            db.execute(delete(Order))
            db.execute(delete(Inventory))
            db.execute(delete(FoodItem))
            db.execute(delete(Category))
            db.execute(delete(Supplier))
            db.execute(delete(User))
            db.commit()

        # 1. Users
        student1 = User(
            name='Aarav Sharma',
            email='student@quickbite.demo',
            password_hash=hash_password('Student@123'),
            role=Role.STUDENT,
            phone='9876501234',
            department='Computer Science',
            active=True
        )
        student2 = User(
            name='Priya Patel',
            email='priya@quickbite.demo',
            password_hash=hash_password('Student@123'),
            role=Role.STUDENT,
            phone='9876505678',
            department='Electronics',
            active=True
        )
        student3 = User(
            name='Rohan Verma',
            email='rohan@quickbite.demo',
            password_hash=hash_password('Student@123'),
            role=Role.STUDENT,
            phone='9876509999',
            department='Mechanical',
            active=True
        )
        staff1 = User(
            name='Maya Staff',
            email='staff@quickbite.demo',
            password_hash=hash_password('Staff@123'),
            role=Role.STAFF,
            phone='9876512345',
            department='Canteen Operations',
            active=True
        )
        admin1 = User(
            name='Admin QuickBite',
            email='admin@quickbite.demo',
            password_hash=hash_password('Admin@123'),
            role=Role.ADMIN,
            phone='9876598765',
            department='Administration',
            active=True
        )
        db.add_all([student1, student2, student3, staff1, admin1])
        db.flush()

        # 2. Categories
        cat_map = {}
        for cat_name in ['Snacks', 'Meals', 'Beverages', 'Desserts']:
            c = Category(name=cat_name)
            db.add(c)
            db.flush()
            cat_map[cat_name] = c

        # 3. Food Items & Inventory
        food_map = {}
        for category, name, desc, price, stock, minimum in FOOD_DATA:
            is_available = stock > 0
            f = FoodItem(
                category_id=cat_map[category].id,
                name=name,
                description=desc,
                price=Decimal(str(price)),
                available=is_available,
                active=True
            )
            f.inventory = Inventory(
                stock_quantity=stock,
                minimum_stock=minimum
            )
            db.add(f)
            db.flush()
            food_map[name] = f

        # 4. Suppliers (Associative M:N Table Demo)
        sup1 = Supplier(
            name='Campus Fresh Bakery',
            contact='9811223344',
            email='orders@campusfresh.demo',
            address='Industrial Estate, Block B, City'
        )
        sup2 = Supplier(
            name='Sunrise Dairy & Beverages',
            contact='9822334455',
            email='contact@sunrisedairy.demo',
            address='Dairy Road, Sector 4, City'
        )
        db.add_all([sup1, sup2])
        db.flush()

        # 5. Supplier Items (Associative M:N instances)
        now = datetime.now(timezone.utc)
        db.add_all([
            SupplierItem(
                supplier_id=sup1.id,
                food_id=food_map['Veg Sandwich'].id,
                supply_price=Decimal('28.00'),
                quantity_supplied=50,
                supply_date=now - timedelta(days=2)
            ),
            SupplierItem(
                supplier_id=sup1.id,
                food_id=food_map['Burger'].id,
                supply_price=Decimal('42.00'),
                quantity_supplied=40,
                supply_date=now - timedelta(days=2)
            ),
            SupplierItem(
                supplier_id=sup2.id,
                food_id=food_map['Cold Coffee'].id,
                supply_price=Decimal('22.00'),
                quantity_supplied=60,
                supply_date=now - timedelta(days=1)
            ),
            SupplierItem(
                supplier_id=sup2.id,
                food_id=food_map['Brownie'].id,
                supply_price=Decimal('25.00'),
                quantity_supplied=30,
                supply_date=now - timedelta(days=1)
            )
        ])
        db.flush()

        # 6. Sample Historical Orders & Payments
        # Order 1: Completed earlier today
        o1 = Order(
            student_id=student1.id,
            staff_id=staff1.id,
            pickup_slot='12:30 PM – 12:45 PM',
            status=OrderStatus.COMPLETED,
            total_amount=Decimal('140.00'),
            created_at=now - timedelta(hours=3),
            order_date=now - timedelta(hours=3)
        )
        o1.details.append(OrderDetail(food_id=food_map['Veg Sandwich'].id, quantity=2, unit_price=Decimal('50.00'), subtotal=Decimal('100.00')))
        o1.details.append(OrderDetail(food_id=food_map['Cold Coffee'].id, quantity=1, unit_price=Decimal('40.00'), subtotal=Decimal('40.00')))
        db.add(o1)
        db.flush()
        db.add(Payment(
            order_id=o1.id,
            amount=Decimal('140.00'),
            mode=PaymentMode.MOCK_ONLINE,
            status=PaymentStatus.SUCCESS,
            transaction_reference=f"MOCK-{uuid4().hex[:12].upper()}",
            created_at=now - timedelta(hours=3)
        ))

        # Order 2: Ready for pickup today
        o2 = Order(
            student_id=student2.id,
            staff_id=staff1.id,
            pickup_slot='1:00 PM – 1:15 PM',
            status=OrderStatus.READY,
            total_amount=Decimal('115.00'),
            created_at=now - timedelta(hours=1),
            order_date=now - timedelta(hours=1)
        )
        o2.details.append(OrderDetail(food_id=food_map['Pizza'].id, quantity=1, unit_price=Decimal('80.00'), subtotal=Decimal('80.00')))
        o2.details.append(OrderDetail(food_id=food_map['Fresh Lime'].id, quantity=1, unit_price=Decimal('30.00'), subtotal=Decimal('30.00')))
        db.add(o2)
        db.flush()
        db.add(Payment(
            order_id=o2.id,
            amount=Decimal('115.00'),
            mode=PaymentMode.MOCK_ONLINE,
            status=PaymentStatus.SUCCESS,
            transaction_reference=f"MOCK-{uuid4().hex[:12].upper()}",
            created_at=now - timedelta(hours=1)
        ))

        # Order 3: Preparing in kitchen right now
        o3 = Order(
            student_id=student3.id,
            staff_id=staff1.id,
            pickup_slot='1:15 PM – 1:30 PM',
            status=OrderStatus.PREPARING,
            total_amount=Decimal('125.00'),
            created_at=now - timedelta(minutes=25),
            order_date=now - timedelta(minutes=25)
        )
        o3.details.append(OrderDetail(food_id=food_map['Burger'].id, quantity=1, unit_price=Decimal('70.00'), subtotal=Decimal('70.00')))
        o3.details.append(OrderDetail(food_id=food_map['Maggi'].id, quantity=1, unit_price=Decimal('55.00'), subtotal=Decimal('55.00')))
        db.add(o3)
        db.flush()
        db.add(Payment(
            order_id=o3.id,
            amount=Decimal('125.00'),
            mode=PaymentMode.PAY_AT_PICKUP,
            status=PaymentStatus.PENDING,
            transaction_reference=f"MOCK-{uuid4().hex[:12].upper()}",
            created_at=now - timedelta(minutes=25)
        ))

        # Order 4: Yesterday order 1
        yesterday = now - timedelta(days=1)
        o4 = Order(
            student_id=student1.id,
            staff_id=staff1.id,
            pickup_slot='1:00 PM – 1:15 PM',
            status=OrderStatus.COMPLETED,
            total_amount=Decimal('175.00'),
            created_at=yesterday,
            order_date=yesterday
        )
        o4.details.append(OrderDetail(food_id=food_map['Cheese Sandwich'].id, quantity=2, unit_price=Decimal('65.00'), subtotal=Decimal('130.00')))
        o4.details.append(OrderDetail(food_id=food_map['Brownie'].id, quantity=1, unit_price=Decimal('45.00'), subtotal=Decimal('45.00')))
        db.add(o4)
        db.flush()
        db.add(Payment(
            order_id=o4.id,
            amount=Decimal('175.00'),
            mode=PaymentMode.MOCK_ONLINE,
            status=PaymentStatus.SUCCESS,
            transaction_reference=f"MOCK-{uuid4().hex[:12].upper()}",
            created_at=yesterday
        ))

        # Order 5: 2 days ago
        two_days_ago = now - timedelta(days=2)
        o5 = Order(
            student_id=student2.id,
            staff_id=staff1.id,
            pickup_slot='1:30 PM – 1:45 PM',
            status=OrderStatus.COMPLETED,
            total_amount=Decimal('195.00'),
            created_at=two_days_ago,
            order_date=two_days_ago
        )
        o5.details.append(OrderDetail(food_id=food_map['Pizza'].id, quantity=2, unit_price=Decimal('80.00'), subtotal=Decimal('160.00')))
        o5.details.append(OrderDetail(food_id=food_map['Fresh Lime'].id, quantity=1, unit_price=Decimal('30.00'), subtotal=Decimal('30.00')))
        db.add(o5)
        db.flush()
        db.add(Payment(
            order_id=o5.id,
            amount=Decimal('195.00'),
            mode=PaymentMode.MOCK_ONLINE,
            status=PaymentStatus.SUCCESS,
            transaction_reference=f"MOCK-{uuid4().hex[:12].upper()}",
            created_at=two_days_ago
        ))

        db.commit()
        print('========================================================')
        print('QuickBite Demo Database Seeded Successfully!')
        print('========================================================')
        print('Demo Accounts:')
        print('  Student: student@quickbite.demo / Student@123')
        print('  Staff:   staff@quickbite.demo   / Staff@123')
        print('  Admin:   admin@quickbite.demo   / Admin@123')
        print('========================================================')
    finally:
        db.close()


if __name__ == '__main__':
    seed_database()
