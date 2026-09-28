# QuickBite — Database Design & Normalization Analysis

## 1. Relational Architecture & Normalization (3NF Justification)

The QuickBite database is designed in approximately **Third Normal Form (3NF)** to eliminate data redundancy, prevent insertion/update/deletion anomalies, and guarantee strict transactional integrity.

### A. First Normal Form (1NF)
* **Atomicity**: Every column contains atomic (indivisible) values. No repeating groups, arrays, or comma-separated lists are stored in any column.
* **Primary Keys**: Every relation has an explicitly declared primary key (`users.id`, `food_items.id`, `orders.id`, etc.).
* **Unique Rows**: Each tuple is uniquely identifiable.

### B. Second Normal Form (2NF)
* A relation is in 2NF if it is in 1NF and **every non-prime attribute is fully functionally dependent on the entire primary key** (no partial functional dependencies).
* In the associative table `supplier_items`, the composite primary key is `(supplier_id, food_id)`. Non-key attributes:
  * `supply_price` depends on both the supplier and the specific food item being supplied: $\text{(supplier\_id, food\_id)} \to \text{supply\_price}$.
  * `quantity_supplied` and `supply_date` likewise depend on the composite key.
  * Attributes dependent solely on `supplier_id` (like `supplier_name`, `contact`, `address`) are placed in the separate `suppliers` table.
  * Attributes dependent solely on `food_id` (like `food_name`, `price`, `category_id`) are placed in the separate `food_items` table.
  * Hence, no partial functional dependency exists in `supplier_items`.

### C. Third Normal Form (3NF)
* A relation is in 3NF if it is in 2NF and **no non-prime attribute is transitively dependent on the primary key** (i.e. $X \to Y$ and $Y \to Z$ where $Z$ is non-prime is disallowed).
* **Category Separation**: If `category_name` were stored directly inside `food_items`, we would have:
  $$\text{food\_id} \to \text{category\_id} \quad \text{and} \quad \text{category\_id} \to \text{category\_name}$$
  This would cause transitive dependency and repeating category names. By creating a separate `categories(id, name)` relation, `food_items` only holds the foreign key `category_id`.
* **Order & Order_Details Separation**: Storing line items in `orders` would create repeating groups or redundant customer headers. Separating `orders` ($1$) and `order_details` ($N$) ensures that order-level metadata (student ID, pickup slot, order status, total amount) is recorded exactly once.
* **Unit Price Snapshot in Order_Details**:
  `order_details.unit_price` stores the price of the food item at the exact moment of order creation. While `food_items.price` can fluctuate in the future, storing `unit_price` in `order_details` is not a normalization violation—it represents an **immutable historical business fact (audit trail)**, preventing past financial accounting from altering when future menu prices change.
* **1:1 Payment Separation**: Moving payment details (`transaction_reference`, `mode`, `status`) to a separate `payments` table ensures that payment lifecycle updates do not lock the `orders` relation.
* **1:1 Food-Item Level Inventory**: Inventory quantities (`stock_quantity`, `minimum_stock`) are isolated in `inventory(food_id PK/FK)` so high-frequency stock updates during concurrent checkouts only acquire row-level locks on `inventory` without interfering with read queries on menu descriptions in `food_items`.

---

## 2. Relational Entities & Relationships

| Entity | Primary Key | Foreign Keys | Relationship | Cardinality | Description |
|---|---|---|---|---|---|
| `users` | `id` | None | Student $\to$ Orders | $1 : N$ | Stores students, staff, and administrators with role-based access. |
| `categories` | `id` | None | Category $\to$ FoodItem | $1 : N$ | Classifies menu items (Snacks, Meals, Beverages, Desserts). |
| `food_items` | `id` | `category_id` $\to$ `categories.id` | FoodItem $\to$ Inventory | $1 : 1$ | Food items with name, description, unit price, and availability. |
| `inventory` | `id`, `food_id` (UK) | `food_id` $\to$ `food_items.id` | FoodItem $\to$ Inventory | $1 : 1$ | Tracks live physical stock and low-stock alert thresholds. |
| `orders` | `id` | `student_id` $\to$ `users.id`, `staff_id` $\to$ `users.id` | Order $\to$ OrderDetails | $1 : N$ | Canteen pre-orders with scheduled pickup slot and status. |
| `order_details` | `id` | `order_id` $\to$ `orders.id`, `food_id` $\to$ `food_items.id` | FoodItem $\to$ OrderDetails | $1 : N$ | Line items capturing food reference, quantity, unit price, and subtotal. |
| `payments` | `id`, `order_id` (UK) | `order_id` $\to$ `orders.id` | Order $\to$ Payment | $1 : 1$ | Payment records with mode, transaction reference, and status. |
| `suppliers` | `id` | None | Supplier $\to$ SupplierItem | $1 : N$ | Canteen raw material and wholesale food providers. |
| `supplier_items` | `(supplier_id, food_id)` | `supplier_id` $\to$ `suppliers.id`, `food_id` $\to$ `food_items.id` | Supplier $\leftrightarrow$ FoodItem | $M : N$ | Associative entity resolving supplier-to-food intake records. |

---

## 3. RDBMS Integrity Constraints

1. **Domain & Type Constraints**:
   - `price NUMERIC(10,2)`: Avoids IEEE 754 floating-point inaccuracies for currency calculations.
   - `status Enum(OrderStatus)`: Enforces valid state machine values (`PLACED`, `PREPARING`, `READY`, `COMPLETED`, `CANCELLED`).
2. **Entity Integrity**:
   - Primary keys are non-null and uniquely indexed via B-Tree indexes.
3. **Referential Integrity**:
   - `ON DELETE RESTRICT` or `CASCADE` where appropriate (e.g. deleting an uncommitted order drops its details, but deleting a food item with historical orders is disallowed).
4. **Check Constraints**:
   - `ck_food_price_nonnegative`: `price >= 0`
   - `ck_stock_nonnegative`: `stock_quantity >= 0`
   - `ck_min_stock_nonnegative`: `minimum_stock >= 0`
   - `ck_order_total_nonnegative`: `total_amount >= 0`
   - `ck_order_qty_positive`: `quantity > 0`
   - `ck_payment_amount_nonnegative`: `amount >= 0`
   - `ck_supply_price_nonnegative`: `supply_price >= 0`
   - `ck_supply_qty_positive`: `quantity_supplied > 0`
5. **Unique Constraints**:
   - `users.email` UNIQUE
   - `categories.name` UNIQUE
   - `food_items.name` UNIQUE
   - `inventory.food_id` UNIQUE
   - `payments.order_id` UNIQUE
   - `payments.transaction_reference` UNIQUE

---

## 4. Advanced RDBMS Features Implemented

### A. Row-Level Pessimistic Locking & ACID Transactions
In `app/services/orders.py`, concurrent order checkouts run in an explicit transaction block:
```sql
SELECT * FROM inventory WHERE food_id IN (1, 2) FOR UPDATE OF inventory;
```
- **Atomicity**: The order, order details, inventory deduction, and mock payment are executed as one unit of work. Any failure triggers `db.rollback()`.
- **Consistency**: The `ck_stock_nonnegative` check constraint and row-level lock guarantee that two students checking out the last slice of pizza cannot cause negative stock (race condition).
- **Isolation**: Pessimistic row locking ensures strict isolation among concurrent checkouts.
- **Durability**: Committed transactions are written to PostgreSQL write-ahead logs (WAL).

### B. Active PostgreSQL Trigger: `trg_sync_food_availability`
- **Purpose**: Automatically synchronizes the boolean flag `food_items.available` whenever stock updates occur in the `inventory` table.
- **Trigger Definition**:
```sql
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

CREATE TRIGGER trg_sync_food_availability
AFTER UPDATE OF stock_quantity ON inventory
FOR EACH ROW
EXECUTE FUNCTION sync_food_availability();
```

### C. Active PostgreSQL Views
1. **`available_food_items`**:
   Combines `food_items` and `inventory` to present only active, saleable items with positive stock:
   ```sql
   CREATE VIEW available_food_items AS
   SELECT f.id, f.name, f.price, i.stock_quantity
   FROM food_items f JOIN inventory i ON i.food_id = f.id
   WHERE f.active AND f.available AND i.stock_quantity > 0;
   ```
2. **`daily_sales_summary`**:
   Pre-aggregates successful sales revenue and order counts by calendar date:
   ```sql
   CREATE VIEW daily_sales_summary AS
   SELECT 
       DATE(p.created_at) AS sale_date,
       COUNT(DISTINCT o.id) AS total_orders,
       COALESCE(SUM(p.amount), 0) AS total_revenue,
       COUNT(DISTINCT o.student_id) AS unique_customers
   FROM orders o
   JOIN payments p ON p.order_id = o.id
   WHERE p.status = 'SUCCESS' AND o.status != 'CANCELLED'
   GROUP BY DATE(p.created_at);
   ```
