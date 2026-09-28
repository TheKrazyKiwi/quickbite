# QuickBite — Smart College Canteen Pre-Order & Inventory Management System

> **Skip the Queue. Grab Your Bite.**  
> A college RDBMS mini-project engineered with PostgreSQL, FastAPI, and React.

---

## 📌 Problem & Motivation

During college break and lunch intervals, students spend 15–25 minutes waiting in crowded queues just to order and collect meals. Canteen staff face unpredicted demand surges, inventory stockouts, and disorganized order fulfillment.

**QuickBite** solves this problem by enabling students to browse live menu availability, reserve scheduled 15-minute pickup slots, and pre-order meals. Canteen staff receive live kitchen orders, manage food availability, adjust stock thresholds, and view database-driven analytics.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Database** | **PostgreSQL 16** (ACID Transactions, Check Constraints, PL/pgSQL Triggers, Views) |
| **Migrations** | **Alembic** (Version-controlled schema management) |
| **Backend API** | **Python 3.14 + FastAPI + SQLAlchemy 2.0 + Pydantic v2** |
| **Authentication** | **JWT (JSON Web Tokens) with PBKDF2-SHA256 password hashing** |
| **Frontend** | **React 18 + Vite + React Router v6 + Modern Custom CSS** |
| **Testing** | **Pytest + HTTPX** (Automated test suite) |

---

## 🚀 Quick Start Guide

### Prerequisites
- Docker & Docker Compose (or local PostgreSQL)
- Python 3.11+
- Node.js 18+ and npm

### 1. Start the PostgreSQL Database
```bash
docker compose up -d
```
Verify PostgreSQL is ready:
```bash
docker compose exec db pg_isready -U quickbite
```

### 2. Setup & Run the Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed initial categories, menu items, suppliers, and historical demo orders
python -m app.seed

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at `http://localhost:8000`  
Interactive OpenAPI/Swagger documentation: `http://localhost:8000/docs`

### 3. Setup & Run the Frontend
In another terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be running at `http://localhost:5173`

---

## 👤 Demo Accounts

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Student** | `student@quickbite.demo` | `Student@123` | Browse menu, cart, select pickup slot, mock checkout, track orders, self-cancel order |
| **Staff** | `staff@quickbite.demo` | `Staff@123` | Process orders (`PLACED → PREPARING → READY → COMPLETED`), adjust stock, toggle availability, view reports |
| **Admin** | `admin@quickbite.demo` | `Admin@123` | Full staff permissions + Category management, Supplier intake (M:N), and User role management |

*Tip: The login page includes one-click demo chips to auto-fill these credentials instantly!*

---

## 🧪 Running Automated Tests

Run the backend test suite:
```bash
cd backend
source .venv/bin/activate
pytest -v
```
Tests verify:
- User registration, duplicate checks, and JWT authentication
- Pessimistic row locking during order checkout transactions
- Out-of-stock and invalid pickup slot validation
- Staff order status progression state transitions
- Order cancellation and atomic inventory restoration
- PostgreSQL view queries and analytical reporting endpoints

---

## 🎓 RDBMS Concepts Demonstrated

This project is built to showcase foundational and advanced RDBMS concepts:

1. **3NF Normalization**: Explicit separation of `orders`, `order_details`, `food_items`, `categories`, `inventory`, and `payments`.
2. **Associative Entity ($M:N$)**: `supplier_items` resolves the many-to-many relationship between `suppliers` and `food_items`.
3. **Receipt Immutability**: Historical unit prices are stored at order time in `order_details.unit_price`, preserving accounting accuracy even if future menu prices change.
4. **Pessimistic Concurrency Locking**: `SELECT ... FOR UPDATE OF inventory` locks stock rows during checkout, eliminating race conditions.
5. **ACID Transactions**: Atomic checkout rolls back completely on any failure (inventory, detail, or payment).
6. **PL/pgSQL Trigger**: `trg_sync_food_availability` on `inventory` automatically toggles `food_items.available` when stock hits 0 or is replenished.
7. **PostgreSQL Views**:
   - `available_food_items`: Filters active foods with positive stock.
   - `daily_sales_summary`: Pre-aggregates daily order counts, revenue, and unique customer metrics.
8. **Check Constraints**: `ck_stock_nonnegative`, `ck_food_price_nonnegative`, `ck_order_qty_positive`.

### Run the SQL Demonstration Script
To run all demonstration queries through `psql`:
```bash
docker compose exec -T db psql -U quickbite -d quickbite < database/sample_queries.sql
```

---

## 📚 Project Documentation

- [Database Design & Normalization Proofs](docs/database-design.md)
- [Relational Schema & Data Dictionary](docs/relational-schema.md)
- [Project Overview & Architecture](docs/project-overview.md)
- [DBMS Viva Preparation (18 Q&As)](docs/sample-viva.md)
- [SQL Demo Script](database/sample_queries.sql)
