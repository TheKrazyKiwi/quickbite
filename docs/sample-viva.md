# QuickBite — DBMS Viva Preparation & Oral Defense Guide

This guide provides technical, examiner-ready answers to the 18 most critical questions asked during college RDBMS mini-project evaluations.

---

### Q1: Why did you choose PostgreSQL over a NoSQL database like MongoDB?
**Answer:**
QuickBite is an ordering and financial transaction system where **ACID properties and strict data integrity are non-negotiable**. PostgreSQL provides:
1. Native relational integrity with foreign key cascading and domain check constraints (`ck_stock_nonnegative`, `ck_food_price_nonnegative`).
2. Strong concurrency control through row-level pessimistic locking (`SELECT ... FOR UPDATE`), preventing double-spending and overselling.
3. Powerful analytical query support including multi-table joins, subqueries, group aggregates, views, and PL/pgSQL triggers that are essential for inventory and sales reporting.

---

### Q2: What are the primary entities in your database?
**Answer:**
There are 9 core relational tables and 1 associative entity:
1. `users` (Students, Staff, Admins)
2. `categories` (Food categories)
3. `food_items` (Menu items)
4. `inventory` (Live physical stock levels)
5. `orders` (Order header & pickup slot)
6. `order_details` (Line items)
7. `payments` (Financial transaction record)
8. `suppliers` (Vendor information)
9. `supplier_items` (Associative $M:N$ bridge between Suppliers and Food Items)

---

### Q3: What is the primary key of each table?
**Answer:**
* `users` $\to$ `id` (Integer surrogate PK)
* `categories` $\to$ `id`
* `food_items` $\to$ `id`
* `inventory` $\to$ `id` (and `food_id` as unique candidate key)
* `orders` $\to$ `id`
* `order_details` $\to$ `id`
* `payments` $\to$ `id`
* `suppliers` $\to$ `id`
* `supplier_items` $\to$ Composite Primary Key: `(supplier_id, food_id)`

---

### Q4: What are the foreign keys and how do they enforce referential integrity?
**Answer:**
* `food_items.category_id` references `categories.id`
* `inventory.food_id` references `food_items.id`
* `orders.student_id` references `users.id`
* `orders.staff_id` references `users.id` (nullable, assigned upon order processing)
* `order_details.order_id` references `orders.id` (cascades on delete)
* `order_details.food_id` references `food_items.id`
* `payments.order_id` references `orders.id`
* `supplier_items.supplier_id` references `suppliers.id`
* `supplier_items.food_id` references `food_items.id`

---

### Q5: Why are `orders` and `order_details` split into two separate tables?
**Answer:**
This is required by **First Normal Form (1NF) and Second Normal Form (2NF)**. An order contains a variable number of food items with distinct quantities and prices. 
Storing items inside `orders` would require repeating groups or non-atomic comma-separated values (violating 1NF). Storing one row per food item in `orders` would cause customer and pickup details to repeat for every line item, introducing redundancy and partial dependencies.

---

### Q6: Why do you store `unit_price` in `order_details` when `price` already exists in `food_items`? Isn't that redundant?
**Answer:**
No, storing `unit_price` in `order_details` is **deliberate and essential for financial auditability (Receipt Immutability)**. 
`food_items.price` represents the **current selling price**, which can change over time. If we joined on `food_items.price` for historical orders, altering the price of a sandwich from ₹50 to ₹60 today would retroactively falsify historical sales receipts and accounting reports. `order_details.unit_price` captures an immutable historical snapshot.

---

### Q7: Why is `supplier_items` needed?
**Answer:**
The real-world relationship between `suppliers` and `food_items` is **Many-to-Many ($M:N$)**: one supplier supplies multiple food items, and one food item can be sourced from multiple vendors. 
In relational database design, an $M:N$ relationship cannot be modeled with foreign keys directly on either table without introducing multi-valued attributes or repeating columns. `supplier_items` is an **associative entity** that breaks the $M:N$ into two $1:N$ relationships, with composite primary key `(supplier_id, food_id)` and additional intersection attributes (`supply_price`, `quantity_supplied`, `supply_date`).

---

### Q8: What level of Normalization does your database achieve?
**Answer:**
The schema is normalized to **Third Normal Form (3NF)**:
1. **1NF**: Atomic attributes, explicit primary keys, no repeating groups.
2. **2NF**: In the composite table `supplier_items`, all non-prime attributes (`supply_price`, `quantity_supplied`) depend on the full composite key `(supplier_id, food_id)`.
3. **3NF**: No transitive dependencies. For example, `category_name` is factored out into `categories` so `food_items` only holds `category_id`, eliminating transitive dependency $\text{food\_id} \to \text{category\_id} \to \text{category\_name}$.

---

### Q9: How does the system handle concurrent checkouts for low-stock items? (Race Conditions)
**Answer:**
We use **Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE OF inventory`)**:
When a checkout request arrives:
1. A transaction begins.
2. The database acquires an exclusive lock on the specific `inventory` rows involved in the cart.
3. Stock is verified. If sufficient, `stock_quantity` is decremented.
4. If another student attempts to purchase the same item concurrently, their transaction blocks until the first transaction commits or rolls back, reading the updated stock accurately.
5. In addition, a database check constraint (`ck_stock_nonnegative`) guarantees at the database engine level that stock can never drop below 0.

---

### Q10: Why did you wrap order creation in a database transaction?
**Answer:**
Order creation touches **four tables**: `orders`, `order_details`, `inventory`, and `payments`. 
If any step fails (e.g., payment failure, unexpected system crash, or stockout on item #2), the entire operation must **roll back completely** so no orphaned order, incomplete receipt, or unbacked payment record remains in the database. This guarantees the **Atomicity and Consistency** of the system.

---

### Q11: What PostgreSQL Views did you implement and why?
**Answer:**
We implemented two views:
1. **`available_food_items`**: Filters active, available menu items with live stock $> 0$. It abstracts the join between `food_items` and `inventory` so consumer queries don't need to repeat join and availability filters.
2. **`daily_sales_summary`**: Aggregates successful payment revenue, total order count, and distinct customer count grouped by date. This serves the administrative reporting dashboard directly from PostgreSQL without burdening Python application memory.

---

### Q12: What Trigger did you implement and why?
**Answer:**
We created a PostgreSQL `AFTER UPDATE OF stock_quantity` trigger named `trg_sync_food_availability` on the `inventory` table.
* **Logic**: When an item's `stock_quantity` drops to 0 or below, the trigger automatically executes `UPDATE food_items SET available = FALSE WHERE id = NEW.food_id`. When stock is replenished above 0, it sets `available = TRUE`.
* **Benefit**: It guarantees relational consistency at the storage engine level regardless of whether stock was adjusted by an order, a staff dashboard update, or an external script.

---

### Q13: Where did you use SQL Joins? Give examples.
**Answer:**
* **2-Table Inner Join**: Joining `food_items` and `inventory` to display menu items with live stock quantities.
* **3-Table Inner Join**: Joining `orders`, `order_details`, and `food_items` to generate customer receipts and kitchen order slips.
* **Category Aggregate Join**: Joining `categories`, `food_items`, `order_details`, and `orders` to compute gross revenue broken down by category.

---

### Q14: Where did you use Aggregate Functions and the `HAVING` clause?
**Answer:**
* **Aggregate Functions**: `SUM(d.quantity)` for popular food calculations, `SUM(p.amount)` for revenue totals, `COUNT(o.id)` for order counts, and `COALESCE()` to replace null sums with 0.
* **`HAVING` clause**: In `sample_queries.sql` Query #6, finding repeat customers:
  ```sql
  SELECT u.name, COUNT(o.id)
  FROM users u JOIN orders o ON o.student_id = u.id
  WHERE o.status = 'COMPLETED'
  GROUP BY u.id, u.name
  HAVING COUNT(o.id) > 1;
  ```
  The `WHERE` clause filters completed orders *before* grouping, while the `HAVING` clause filters student groups *after* aggregation.

---

### Q15: Where did you use Subqueries?
**Answer:**
* **Uncorrelated Subquery (`NOT IN`)**: Finding food items that have never been ordered:
  ```sql
  SELECT id, name FROM food_items 
  WHERE id NOT IN (SELECT DISTINCT food_id FROM order_details);
  ```
* **Correlated Subquery (`EXISTS`)**: Finding suppliers who provide food items currently below minimum stock:
  ```sql
  SELECT s.name FROM suppliers s
  WHERE EXISTS (
      SELECT 1 FROM supplier_items si 
      JOIN inventory i ON i.food_id = si.food_id
      WHERE si.supplier_id = s.id AND i.stock_quantity <= i.minimum_stock
  );
  ```

---

### Q16: How is user authentication implemented?
**Answer:**
We implement **JWT (JSON Web Token) authentication with PBKDF2-SHA256 password hashing**:
1. Passwords are never stored in plaintext. They are salted with 16 cryptographically secure random bytes and hashed with 600,000 iterations of PBKDF2-HMAC-SHA256.
2. Upon login, the backend verifies the hash, generates an HS256-signed JWT token containing the user ID and role claim (`STUDENT`, `STAFF`, `ADMIN`), and returns it to the client.
3. Protected endpoints use FastAPI dependencies (`current_user`, `require_roles`) to decode the token and enforce role-based access control.

---

### Q17: What happens to inventory if an order is cancelled?
**Answer:**
When an order transitions to `CANCELLED` (either by the student while still `PLACED`, or by canteen staff), the backend iterates through the line items in `order_details` and **restores the exact quantities back into `inventory.stock_quantity`**. If payment was already completed, the payment status updates to `REFUNDED`.

---

### Q18: What are Check Constraints and which ones did you define?
**Answer:**
Check constraints validate that column values satisfy a boolean predicate before PostgreSQL allows an `INSERT` or `UPDATE`:
* `ck_food_price_nonnegative`: `price >= 0`
* `ck_stock_nonnegative`: `stock_quantity >= 0`
* `ck_min_stock_nonnegative`: `minimum_stock >= 0`
* `ck_order_total_nonnegative`: `total_amount >= 0`
* `ck_order_qty_positive`: `quantity > 0`
* `ck_supply_qty_positive`: `quantity_supplied > 0`
These protect the database against corrupted data, software bugs, or accidental negative entries.
