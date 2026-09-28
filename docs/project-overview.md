# QuickBite — Project Overview & Architecture

## 1. Problem Statement
During college break intervals and lunch periods, the campus canteen experiences extreme peak-time rushes. Students lose 15–25 minutes of their limited break standing in queues:
1. Waiting to view physical menu boards.
2. Waiting to place orders and pay.
3. Waiting for food preparation at the counter.

Simultaneously, canteen kitchen staff struggle with chaotic order tracking, unpredicted demand rushes, unrecorded inventory stockouts, and disjointed payment reconciliation.

## 2. Proposed Solution: QuickBite
QuickBite is an end-to-end smart college canteen pre-ordering, scheduled pickup, and live inventory management system. 

It enables:
* **Students**: Browse the live menu, see real-time stock availability, assemble a cart, select a pre-defined 15-minute pickup slot (e.g. 1:15 PM – 1:30 PM), place an atomic pre-order, and collect food directly from the express pickup counter using their digital token (`QB-XXXX`).
* **Canteen Staff**: Process incoming kitchen orders in real-time (`PLACED` $\to$ `PREPARING` $\to$ `READY` $\to$ `COMPLETED`), manage food availability, update stock thresholds, and view analytics.
* **Administrators**: Manage food categories, vendor suppliers, inventory intake records, and user permissions.

## 3. Technology Stack

```
Frontend:    React 18 + Vite + React Router v6 + Modern Custom CSS
Backend:     Python 3.14 + FastAPI + Pydantic v2 + SQLAlchemy 2.0
Database:    PostgreSQL 16 (Relational DB with Transactions, Views & Triggers)
Migrations:  Alembic (Version-controlled schema management)
Auth:        JWT (JSON Web Tokens) with PBKDF2-SHA256 password hashing
Testing:     Pytest + HTTPX test client
Dev Env:     Fedora Linux / Docker Compose
```

## 4. Key Architectural Principles
1. **Server-Authoritative Business Logic**: Totals, subtotals, item availability, and stock checks are never calculated or trusted from client-side state. The PostgreSQL database and FastAPI services are the sole sources of truth.
2. **ACID Transaction Isolation**: Order placement executes within an atomic transaction. Pessimistic row locking (`SELECT ... FOR UPDATE OF inventory`) guarantees that simultaneous checkouts cannot over-sell limited stock.
3. **Reactive RDBMS Integration**: PostgreSQL triggers (`trg_sync_food_availability`) automatically ensure relational consistency across dependent tables, while PostgreSQL views (`available_food_items`, `daily_sales_summary`) optimize operational queries and reports.
