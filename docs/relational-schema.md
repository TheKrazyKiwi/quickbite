# QuickBite — Relational Schema & Data Dictionary

This document details the PostgreSQL physical schema definitions, data types, nullability, constraints, and relationships for the QuickBite database.

---

### 1. `users`
Represents registered students, canteen kitchen staff, and system administrators.

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Unique surrogate identifier |
| `name` | `VARCHAR(100)` | `NOT NULL` | — | — | Full name of user |
| `email` | `VARCHAR(255)` | `NOT NULL` | — | `UNIQUE`, `INDEX` | User login email address |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | — | — | PBKDF2-SHA256 hashed password string |
| `role` | `enum('STUDENT','STAFF','ADMIN')` | `NOT NULL` | `'STUDENT'` | — | Role-based authorization level |
| `phone` | `VARCHAR(30)` | `NULL` | — | — | Contact telephone number |
| `department` | `VARCHAR(100)` | `NULL` | — | — | Academic or operational department |
| `active` | `BOOLEAN` | `NOT NULL` | `TRUE` | — | Account activation status flag |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Account registration timestamp |

---

### 2. `categories`
Classifies canteen food items into operational sections.

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Category identifier |
| `name` | `VARCHAR(80)` | `NOT NULL` | — | `UNIQUE` | Category name (e.g. Snacks, Meals) |

---

### 3. `food_items`
Master table of menu offerings available at the canteen.

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Unique food identifier |
| `category_id` | `INTEGER` | `NOT NULL` | — | `FOREIGN KEY` $\to$ `categories.id` | Category classification reference |
| `name` | `VARCHAR(120)` | `NOT NULL` | — | `UNIQUE` | Item title on the menu |
| `description` | `TEXT` | `NULL` | — | — | Brief culinary description |
| `price` | `NUMERIC(10,2)` | `NOT NULL` | — | `CHECK (price >= 0)` | Current retail price in INR (₹) |
| `available` | `BOOLEAN` | `NOT NULL` | `TRUE` | — | Operational availability flag |
| `active` | `BOOLEAN` | `NOT NULL` | `TRUE` | — | Soft-delete flag preserving history |
| `image_url` | `VARCHAR(500)` | `NULL` | — | — | Optional asset image URI |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Creation timestamp |

---

### 4. `inventory`
Tracks physical on-hand units for each food item ($1:1$ relationship with `food_items`).

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Inventory record ID |
| `food_id` | `INTEGER` | `NOT NULL` | — | `FOREIGN KEY` $\to$ `food_items.id`, `UNIQUE` | 1-to-1 food item reference |
| `stock_quantity` | `INTEGER` | `NOT NULL` | `0` | `CHECK (stock_quantity >= 0)` | Currently available physical units |
| `minimum_stock` | `INTEGER` | `NOT NULL` | `5` | `CHECK (minimum_stock >= 0)` | Threshold below which low-stock triggers |
| `last_updated` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Timestamp of last stock change |

*Note: Attached to Trigger `trg_sync_food_availability` which syncs `food_items.available`.*

---

### 5. `orders`
Master record for canteen pre-orders placed by students.

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Order ID (Token display: `QB-0001`) |
| `student_id` | `INTEGER` | `NOT NULL` | — | `FOREIGN KEY` $\to$ `users.id` | Ordering student reference |
| `staff_id` | `INTEGER` | `NULL` | — | `FOREIGN KEY` $\to$ `users.id` | Processing staff member reference |
| `order_date` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Date of order placement |
| `pickup_slot` | `VARCHAR(40)` | `NOT NULL` | — | — | Fixed collection break window |
| `status` | `enum('PLACED','PREPARING','READY','COMPLETED','CANCELLED')` | `NOT NULL` | `'PLACED'` | — | Order lifecycle state |
| `total_amount` | `NUMERIC(10,2)` | `NOT NULL` | — | `CHECK (total_amount >= 0)` | Total calculated order price |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Audit timestamp |

---

### 6. `order_details`
Bridge table capturing ordered items per pre-order ($1:N$).

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Line item identifier |
| `order_id` | `INTEGER` | `NOT NULL` | — | `FOREIGN KEY` $\to$ `orders.id` | Parent order reference |
| `food_id` | `INTEGER` | `NOT NULL` | — | `FOREIGN KEY` $\to$ `food_items.id` | Food item reference |
| `quantity` | `INTEGER` | `NOT NULL` | — | `CHECK (quantity > 0)` | Number of portions ordered |
| `unit_price` | `NUMERIC(10,2)` | `NOT NULL` | — | `CHECK (unit_price >= 0)` | Price snapshot at time of order |
| `subtotal` | `NUMERIC(10,2)` | `NOT NULL` | — | `CHECK (subtotal >= 0)` | `quantity * unit_price` |

*Table constraint:* `UNIQUE(order_id, food_id)` prevents duplicate item rows in a single order.

---

### 7. `payments`
Stores financial transaction lifecycle data ($1:1$ with `orders`).

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Payment identifier |
| `order_id` | `INTEGER` | `NOT NULL` | — | `FOREIGN KEY` $\to$ `orders.id`, `UNIQUE` | 1-to-1 order reference |
| `amount` | `NUMERIC(10,2)` | `NOT NULL` | — | `CHECK (amount >= 0)` | Charged amount |
| `mode` | `enum('MOCK_ONLINE','PAY_AT_PICKUP')` | `NOT NULL` | — | — | Method of payment |
| `status` | `enum('PENDING','SUCCESS','FAILED','REFUNDED')` | `NOT NULL` | — | — | Payment settlement state |
| `transaction_reference` | `VARCHAR(80)` | `NOT NULL` | — | `UNIQUE` | Mock gateway transaction code |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Payment timestamp |

---

### 8. `suppliers`
Wholesale food vendors and ingredient distributors.

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `id` | `INTEGER` | `NOT NULL` | `nextval(...)` | `PRIMARY KEY` | Supplier identifier |
| `name` | `VARCHAR(150)` | `NOT NULL` | — | `UNIQUE` | Company / Supplier name |
| `contact` | `VARCHAR(50)` | `NULL` | — | — | Phone number |
| `email` | `VARCHAR(255)` | `NULL` | — | — | Contact email address |
| `address` | `TEXT` | `NULL` | — | — | Physical dispatch address |

---

### 9. `supplier_items`
Associative entity resolving the Many-to-Many ($M:N$) relationship between `suppliers` and `food_items`.

| Column | Data Type | Nullable | Default | Constraints | Description |
|---|---|---|---|---|---|
| `supplier_id` | `INTEGER` | `NOT NULL` | — | `PRIMARY KEY`, `FOREIGN KEY` $\to$ `suppliers.id` | Supplying vendor |
| `food_id` | `INTEGER` | `NOT NULL` | — | `PRIMARY KEY`, `FOREIGN KEY` $\to$ `food_items.id` | Supplied food item |
| `supply_price` | `NUMERIC(10,2)` | `NOT NULL` | — | `CHECK (supply_price >= 0)` | Wholesale acquisition unit cost |
| `quantity_supplied` | `INTEGER` | `NOT NULL` | — | `CHECK (quantity_supplied > 0)` | Units delivered |
| `supply_date` | `TIMESTAMPTZ` | `NOT NULL` | `CURRENT_TIMESTAMP` | — | Delivery date & time |
