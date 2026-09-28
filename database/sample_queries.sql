-- ============================================================================
-- QUICKBITE: SMART COLLEGE CANTEEN PRE-ORDER & INVENTORY SYSTEM
-- RELATIONAL DATABASE MANAGEMENT SYSTEMS (RDBMS) DEMONSTRATION SCRIPT
-- ============================================================================
-- This script contains executable queries demonstrating core RDBMS concepts
-- for evaluation, viva defense, and project demonstration.
-- Run using:
--   docker compose exec -T db psql -U quickbite -d quickbite < database/sample_queries.sql
-- ============================================================================

\echo '--- [1] DDL & CONSTRAINTS: Table structures and check constraints ---'
\d food_items
\d orders
\d inventory

\echo '--- [2] BASIC SELECTION & FILTERING: Available food items sorted by price ---'
SELECT id, name, price, available 
FROM food_items 
WHERE active = TRUE AND available = TRUE 
ORDER BY price ASC;

\echo '--- [3] TWO-TABLE INNER JOIN: Active foods with their current live stock ---'
SELECT f.id, f.name, c.name AS category, f.price, i.stock_quantity, i.minimum_stock
FROM food_items f
JOIN categories c ON c.id = f.category_id
JOIN inventory i ON i.food_id = f.id
WHERE f.active = TRUE
ORDER BY c.name, f.name;

\echo '--- [4] THREE-TABLE INNER JOIN: Order details with student and food names ---'
SELECT 
    o.id AS order_id, 
    u.name AS student_name, 
    f.name AS food_item, 
    d.quantity, 
    d.unit_price, 
    d.subtotal, 
    o.pickup_slot, 
    o.status
FROM orders o
JOIN users u ON u.id = o.student_id
JOIN order_details d ON d.order_id = o.id
JOIN food_items f ON f.id = d.food_id
ORDER BY o.id DESC, d.id ASC;

\echo '--- [5] AGGREGATE FUNCTIONS & GROUP BY: Total sales revenue and order count by category ---'
SELECT 
    c.name AS category_name,
    COUNT(d.id) AS total_items_sold,
    SUM(d.quantity) AS total_quantity,
    COALESCE(SUM(d.subtotal), 0.00) AS gross_sales_amount
FROM categories c
JOIN food_items f ON f.category_id = c.id
JOIN order_details d ON d.food_id = f.id
JOIN orders o ON o.id = d.order_id
WHERE o.status != 'CANCELLED'
GROUP BY c.id, c.name
ORDER BY gross_sales_amount DESC;

\echo '--- [6] GROUP BY WITH HAVING CLAUSE: Students with more than 1 completed order ---'
SELECT 
    u.id AS student_id,
    u.name AS student_name,
    u.department,
    COUNT(o.id) AS completed_orders,
    SUM(o.total_amount) AS total_spent
FROM users u
JOIN orders o ON o.student_id = u.id
WHERE o.status = 'COMPLETED'
GROUP BY u.id, u.name, u.department
HAVING COUNT(o.id) >= 1
ORDER BY total_spent DESC;

\echo '--- [7] UNCORRELATED SUBQUERY (NOT IN): Food items that have NEVER been ordered ---'
SELECT id, name, price 
FROM food_items 
WHERE id NOT IN (
    SELECT DISTINCT food_id 
    FROM order_details
);

\echo '--- [8] CORRELATED SUBQUERY (EXISTS): Suppliers who supply low-stock foods ---'
SELECT s.id, s.name, s.contact, s.email
FROM suppliers s
WHERE EXISTS (
    SELECT 1 
    FROM supplier_items si
    JOIN inventory i ON i.food_id = si.food_id
    WHERE si.supplier_id = s.id 
      AND i.stock_quantity <= i.minimum_stock
);

\echo '--- [9] RDBMS VIEW #1: Querying `available_food_items` view ---'
SELECT * FROM available_food_items ORDER BY name;

\echo '--- [10] RDBMS VIEW #2: Querying `daily_sales_summary` view ---'
SELECT * FROM daily_sales_summary ORDER BY sale_date DESC;

\echo '--- [11] ASSOCIATIVE ENTITY (M:N): Supplier-to-Food Item supply intake records ---'
SELECT 
    s.name AS supplier_name,
    f.name AS food_supplied,
    si.supply_price,
    si.quantity_supplied,
    si.supply_date
FROM supplier_items si
JOIN suppliers s ON s.id = si.supplier_id
JOIN food_items f ON f.id = si.food_id
ORDER BY si.supply_date DESC;

\echo '--- [12] TRANSACTION CONTROL: Atomic block with SAVEPOINT and ROLLBACK ---'
BEGIN;
  -- Record temporary intake
  UPDATE inventory SET stock_quantity = stock_quantity + 50 WHERE food_id = 15;
  SAVEPOINT temp_intake;
  -- Simulate erroneous entry
  UPDATE inventory SET stock_quantity = stock_quantity + 9999 WHERE food_id = 15;
  -- Revert to savepoint
  ROLLBACK TO SAVEPOINT temp_intake;
-- Cancel entire test transaction
ROLLBACK;
\echo 'Transaction successfully rolled back; data integrity preserved.'

\echo '--- [13] TRIGGER DEMONSTRATION: `trg_sync_food_availability` in action ---'
-- Check Samosa stock (0) and availability (f)
SELECT f.name, f.available, i.stock_quantity
FROM food_items f
JOIN inventory i ON i.food_id = f.id
WHERE f.name = 'Samosa';

\echo 'Simulating new stock arrival for Samosa (+15 units)...'
UPDATE inventory 
SET stock_quantity = 15 
WHERE food_id = (SELECT id FROM food_items WHERE name = 'Samosa');

-- Verify trigger automatically flipped available to TRUE
SELECT f.name, f.available, i.stock_quantity
FROM food_items f
JOIN inventory i ON i.food_id = f.id
WHERE f.name = 'Samosa';

-- Revert stock back to 0 to demonstrate trigger flips available to FALSE
UPDATE inventory 
SET stock_quantity = 0 
WHERE food_id = (SELECT id FROM food_items WHERE name = 'Samosa');

SELECT f.name, f.available, i.stock_quantity
FROM food_items f
JOIN inventory i ON i.food_id = f.id
WHERE f.name = 'Samosa';

\echo '--- DEMONSTRATION COMPLETE ---'
