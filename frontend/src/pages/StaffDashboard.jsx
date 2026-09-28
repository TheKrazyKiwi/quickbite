import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { apiRequest } from '../api/client';
import { Modal } from '../components/Modal';

export function StaffDashboard() {
  const { user } = useApp();
  const isAdmin = user?.role === 'ADMIN';

  const [activeTab, setActiveTab] = useState('orders');
  const [orders, setOrders] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [foods, setFoods] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [reports, setReports] = useState({
    today: { orders: 0, revenue: 0 },
    popular: [],
    low: [],
    slots: [],
    sales: [],
  });

  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Modals state
  const [stockModal, setStockModal] = useState({ open: false, item: null, stock: '', minStock: '' });
  const [foodModal, setFoodModal] = useState({
    open: false,
    categoryId: '',
    name: '',
    description: '',
    price: '',
    stock: '20',
    minStock: '5',
  });
  const [categoryModal, setCategoryModal] = useState({ open: false, name: '' });
  const [supplierModal, setSupplierModal] = useState({ open: false, name: '', contact: '', email: '', address: '' });
  const [intakeModal, setIntakeModal] = useState({ open: false, supplierId: '', foodId: '', supplyPrice: '', quantity: '20' });

  const showNotice = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 3000);
  };

  const loadData = async () => {
    setLoading(true);
    setError('');
    try {
      const calls = [
        apiRequest('/orders'),
        apiRequest('/inventory'),
        apiRequest('/foods'),
        apiRequest('/categories'),
        apiRequest('/reports/today'),
        apiRequest('/reports/popular-food'),
        apiRequest('/reports/low-stock'),
        apiRequest('/reports/pickup-slots'),
        apiRequest('/reports/sales'),
      ];

      if (isAdmin) {
        calls.push(apiRequest('/suppliers'));
        calls.push(apiRequest('/users'));
      }

      const results = await Promise.all(calls);
      setOrders(results[0]);
      setInventory(results[1]);
      setFoods(results[2]);
      setCategories(results[3]);
      setReports({
        today: results[4],
        popular: results[5],
        low: results[6],
        slots: results[7],
        sales: results[8],
      });

      if (isAdmin) {
        setSuppliers(results[9]);
        setUsersList(results[10]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load operational data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll orders and inventory every 15 seconds
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [isAdmin]);

  // Order status transitions
  const handleStatusChange = async (orderId, targetStatus) => {
    try {
      await apiRequest(`/orders/${orderId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: targetStatus }),
      });
      showNotice(`Order #${orderId} transitioned to ${targetStatus}`);
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to update order status');
    }
  };

  // Stock update modal submission
  const handleSaveStock = async (e) => {
    e.preventDefault();
    if (!stockModal.item) return;

    try {
      await apiRequest(`/inventory/${stockModal.item.food_id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          stock_quantity: parseInt(stockModal.stock, 10),
          minimum_stock: parseInt(stockModal.minStock, 10),
        }),
      });
      setStockModal({ open: false, item: null, stock: '', minStock: '' });
      showNotice(`Stock updated for ${stockModal.item.food_name}`);
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to update stock');
    }
  };

  // Toggle food availability
  const handleToggleFood = async (food) => {
    try {
      await apiRequest(`/foods/${food.id}`, {
        method: 'PUT',
        body: JSON.stringify({ available: !food.available }),
      });
      showNotice(`Availability updated for ${food.name}`);
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to update food availability');
    }
  };

  // Deactivate food item
  const handleDeactivateFood = async (food) => {
    if (!window.confirm(`Deactivate "${food.name}"? It will no longer appear on the student menu.`)) {
      return;
    }
    try {
      await apiRequest(`/foods/${food.id}`, { method: 'DELETE' });
      showNotice(`"${food.name}" has been deactivated.`);
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to deactivate food');
    }
  };

  // Create new Food Item
  const handleCreateFood = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/foods', {
        method: 'POST',
        body: JSON.stringify({
          category_id: parseInt(foodModal.categoryId, 10),
          name: foodModal.name.trim(),
          description: foodModal.description.trim(),
          price: parseFloat(foodModal.price),
          stock_quantity: parseInt(foodModal.stock, 10),
          minimum_stock: parseInt(foodModal.minStock, 10),
          available: true,
        }),
      });
      setFoodModal({ open: false, categoryId: '', name: '', description: '', price: '', stock: '20', minStock: '5' });
      showNotice('New food item added to canteen menu!');
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to create food item');
    }
  };

  // Create Category
  const handleCreateCategory = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/categories', {
        method: 'POST',
        body: JSON.stringify({ name: categoryModal.name.trim() }),
      });
      setCategoryModal({ open: false, name: '' });
      showNotice('Category added successfully!');
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to create category');
    }
  };

  // Create Supplier
  const handleCreateSupplier = async (e) => {
    e.preventDefault();
    try {
      await apiRequest('/suppliers', {
        method: 'POST',
        body: JSON.stringify({
          name: supplierModal.name.trim(),
          contact: supplierModal.contact.trim() || null,
          email: supplierModal.email.trim() || null,
          address: supplierModal.address.trim() || null,
        }),
      });
      setSupplierModal({ open: false, name: '', contact: '', email: '', address: '' });
      showNotice('Supplier registered successfully!');
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to create supplier');
    }
  };

  // Record Supplier Intake (M:N)
  const handleRecordIntake = async (e) => {
    e.preventDefault();
    try {
      await apiRequest(`/suppliers/${intakeModal.supplierId}/items`, {
        method: 'POST',
        body: JSON.stringify({
          food_id: parseInt(intakeModal.foodId, 10),
          supply_price: parseFloat(intakeModal.supplyPrice),
          quantity_supplied: parseInt(intakeModal.quantity, 10),
        }),
      });
      setIntakeModal({ open: false, supplierId: '', foodId: '', supplyPrice: '', quantity: '20' });
      showNotice('Supply intake recorded; inventory stock increased!');
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to record supply intake');
    }
  };

  // Update user role
  const handleUserRoleChange = async (userId, newRole) => {
    try {
      await apiRequest(`/users/${userId}/role`, {
        method: 'PATCH',
        body: JSON.stringify({ role: newRole }),
      });
      showNotice(`Role updated to ${newRole}`);
      loadData();
    } catch (err) {
      setError(err.message || 'Failed to update user role');
    }
  };

  return (
    <main className="panel staff-panel">
      <div className="staff-header-row">
        <div>
          <p className="eyebrow">{user?.role} OPERATIONS HUB</p>
          <h1>Canteen Management</h1>
        </div>
        <button className="refresh-btn" onClick={loadData} disabled={loading}>
          {loading ? 'Syncing...' : '↻ Sync Data'}
        </button>
      </div>

      {notice && <div className="notice-banner">{notice}</div>}
      {error && <div className="error-banner">{error}</div>}

      <div className="tabs staff-tabs">
        <button
          className={`tab-btn ${activeTab === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveTab('orders')}
        >
          Active Orders ({orders.filter((o) => o.status !== 'COMPLETED' && o.status !== 'CANCELLED').length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'inventory' ? 'active' : ''}`}
          onClick={() => setActiveTab('inventory')}
        >
          Inventory
        </button>
        <button
          className={`tab-btn ${activeTab === 'foods' ? 'active' : ''}`}
          onClick={() => setActiveTab('foods')}
        >
          Food Items
        </button>
        <button
          className={`tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          Reports & Views
        </button>
        {isAdmin && (
          <button
            className={`tab-btn ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => setActiveTab('admin')}
          >
            Admin Panel
          </button>
        )}
      </div>

      {/* ============================================================== */}
      {/* TAB 1: ORDERS */}
      {/* ============================================================== */}
      {activeTab === 'orders' && (
        <section className="tab-section">
          <h2>Incoming & Processing Pre-Orders</h2>
          {!orders.length ? (
            <p className="empty-state">No pre-orders recorded yet.</p>
          ) : (
            <div className="staff-orders-grid">
              {orders.map((o) => (
                <article className={`staff-order-card status-${o.status.toLowerCase()}`} key={o.id}>
                  <div className="order-top">
                    <div>
                      <span className="order-token">{o.token}</span>
                      <strong className="student-name">&bull; {o.student?.name}</strong>
                    </div>
                    <span className={`badge status-${o.status.toLowerCase()}`}>{o.status}</span>
                  </div>

                  <p className="slot-badge">&#9200; Pickup: {o.pickup_slot}</p>

                  <div className="items-box">
                    {o.items.map((i) => (
                      <div className="item-row" key={i.id}>
                        <span>
                          {i.quantity} &times; {i.name}
                        </span>
                        <span className="unit-price">₹{i.subtotal.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="order-footer">
                    <div className="price-tag">
                      <small>Total:</small>
                      <strong>₹{o.total_amount.toFixed(2)}</strong>
                    </div>

                    <div className="action-buttons">
                      {o.status === 'PLACED' && (
                        <button
                          className="action-btn prep-btn"
                          onClick={() => handleStatusChange(o.id, 'PREPARING')}
                        >
                          Start Prep &rarr;
                        </button>
                      )}
                      {o.status === 'PREPARING' && (
                        <button
                          className="action-btn ready-btn"
                          onClick={() => handleStatusChange(o.id, 'READY')}
                        >
                          Mark Ready &rarr;
                        </button>
                      )}
                      {o.status === 'READY' && (
                        <button
                          className="action-btn complete-btn"
                          onClick={() => handleStatusChange(o.id, 'COMPLETED')}
                        >
                          Complete &rarr;
                        </button>
                      )}
                      {o.status !== 'COMPLETED' && o.status !== 'CANCELLED' && (
                        <button
                          className="action-btn cancel-sm-btn"
                          onClick={() => handleStatusChange(o.id, 'CANCELLED')}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ============================================================== */}
      {/* TAB 2: INVENTORY */}
      {/* ============================================================== */}
      {activeTab === 'inventory' && (
        <section className="tab-section">
          <h2>Food Inventory Stock Levels</h2>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Food Item</th>
                  <th>Current Stock</th>
                  <th>Minimum Alert Stock</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {inventory.map((item) => (
                  <tr key={item.food_id}>
                    <td>
                      <strong>{item.food_name}</strong>
                    </td>
                    <td>
                      <span className="stock-count">{item.stock_quantity} units</span>
                    </td>
                    <td>{item.minimum_stock} units</td>
                    <td>
                      <span className={`pill state-${item.state.toLowerCase().replace(/ /g, '-')}`}>
                        {item.state}
                      </span>
                    </td>
                    <td>
                      <button
                        className="small-btn primary"
                        onClick={() =>
                          setStockModal({
                            open: true,
                            item,
                            stock: String(item.stock_quantity),
                            minStock: String(item.minimum_stock),
                          })
                        }
                      >
                        Adjust Stock
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ============================================================== */}
      {/* TAB 3: FOOD MANAGEMENT */}
      {/* ============================================================== */}
      {activeTab === 'foods' && (
        <section className="tab-section">
          <div className="section-title-row">
            <h2>Food Menu & Availability</h2>
            <button
              className="primary"
              onClick={() =>
                setFoodModal({
                  open: true,
                  categoryId: categories[0]?.id ? String(categories[0].id) : '',
                  name: '',
                  description: '',
                  price: '',
                  stock: '20',
                  minStock: '5',
                })
              }
            >
              + Add New Food Item
            </button>
          </div>

          <div className="foods-management-list">
            {foods.map((f) => (
              <div className="food-manage-row" key={f.id}>
                <div className="food-info">
                  <strong>{f.name}</strong>
                  <small>
                    {f.category?.name} &bull; ₹{f.price.toFixed(2)} &bull; Stock: {f.inventory?.stock_quantity ?? 0}
                  </small>
                </div>
                <div className="food-controls">
                  <span className={`badge ${f.available ? 'ready' : 'cancelled'}`}>
                    {f.available ? 'AVAILABLE' : 'UNAVAILABLE'}
                  </span>
                  <button className="small-btn" onClick={() => handleToggleFood(f)}>
                    {f.available ? 'Set Unavailable' : 'Set Available'}
                  </button>
                  <button className="small-btn danger" onClick={() => handleDeactivateFood(f)}>
                    Deactivate
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ============================================================== */}
      {/* TAB 4: REPORTS & DBMS VIEWS */}
      {/* ============================================================== */}
      {activeTab === 'reports' && (
        <section className="tab-section">
          <h2>Database Analytics & PostgreSQL Views</h2>

          <div className="kpi-grid">
            <div className="kpi-card">
              <span className="kpi-title">Today's Total Orders</span>
              <strong className="kpi-value">{reports.today?.orders || 0}</strong>
            </div>
            <div className="kpi-card">
              <span className="kpi-title">Today's Revenue</span>
              <strong className="kpi-value">₹{(reports.today?.revenue || 0).toFixed(2)}</strong>
            </div>
          </div>

          <div className="reports-columns">
            <div className="report-box">
              <h3>Popular Food (GROUP BY & SUM)</h3>
              <ul className="ranked-list">
                {reports.popular?.length ? (
                  reports.popular.map((item, index) => (
                    <li key={item.name}>
                      <span>
                        #{index + 1} {item.name}
                      </span>
                      <strong>{item.quantity} units sold</strong>
                    </li>
                  ))
                ) : (
                  <p>No sales records yet.</p>
                )}
              </ul>
            </div>

            <div className="report-box">
              <h3>Orders by Pickup Slot</h3>
              <ul className="slot-list">
                {reports.slots?.map((s) => (
                  <li key={s.slot}>
                    <span>{s.slot}</span>
                    <span className="count-pill">{s.orders} orders</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* PostgreSQL View: daily_sales_summary */}
          <div className="view-report-box">
            <div className="view-header">
              <h3>PostgreSQL View: daily_sales_summary</h3>
              <span className="sql-tag">SELECT * FROM daily_sales_summary</span>
            </div>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Orders</th>
                    <th>Gross Revenue</th>
                    <th>Unique Customers</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.sales?.map((day) => (
                    <tr key={day.date}>
                      <td>{day.date}</td>
                      <td>{day.orders}</td>
                      <td>
                        <strong>₹{day.revenue.toFixed(2)}</strong>
                      </td>
                      <td>{day.customers ?? 1}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ============================================================== */}
      {/* TAB 5: ADMIN MANAGEMENT */}
      {/* ============================================================== */}
      {activeTab === 'admin' && isAdmin && (
        <section className="tab-section">
          <h2>System Administration</h2>

          <div className="admin-grid-layout">
            {/* Categories */}
            <div className="admin-card">
              <div className="card-header">
                <h3>Categories ({categories.length})</h3>
                <button
                  className="small-btn primary"
                  onClick={() => setCategoryModal({ open: true, name: '' })}
                >
                  + Add
                </button>
              </div>
              <ul className="simple-list">
                {categories.map((c) => (
                  <li key={c.id}>
                    <span>{c.name}</span>
                    <small>ID: {c.id}</small>
                  </li>
                ))}
              </ul>
            </div>

            {/* Suppliers */}
            <div className="admin-card">
              <div className="card-header">
                <h3>Suppliers ({suppliers.length})</h3>
                <button
                  className="small-btn primary"
                  onClick={() => setSupplierModal({ open: true, name: '', contact: '', email: '', address: '' })}
                >
                  + Add
                </button>
              </div>
              <ul className="simple-list">
                {suppliers.map((s) => (
                  <li key={s.id}>
                    <div>
                      <strong>{s.name}</strong>
                      <small>{s.contact || s.email || 'No contact'}</small>
                    </div>
                    <button
                      className="small-btn"
                      onClick={() =>
                        setIntakeModal({
                          open: true,
                          supplierId: String(s.id),
                          foodId: foods[0]?.id ? String(foods[0].id) : '',
                          supplyPrice: '30',
                          quantity: '20',
                        })
                      }
                    >
                      Record Intake
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* User Management */}
          <div className="admin-card full-width">
            <h3>User & Staff Roles</h3>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Department</th>
                    <th>Current Role</th>
                    <th>Change Role</th>
                  </tr>
                </thead>
                <tbody>
                  {usersList.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <strong>{u.name}</strong>
                      </td>
                      <td>{u.email}</td>
                      <td>{u.department || '—'}</td>
                      <td>
                        <span className={`role-pill ${u.role.toLowerCase()}`}>{u.role}</span>
                      </td>
                      <td>
                        <select
                          value={u.role}
                          onChange={(e) => handleUserRoleChange(u.id, e.target.value)}
                        >
                          <option value="STUDENT">STUDENT</option>
                          <option value="STAFF">STAFF</option>
                          <option value="ADMIN">ADMIN</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ============================================================== */}
      {/* MODALS */}
      {/* ============================================================== */}

      {/* Adjust Stock Modal */}
      <Modal
        isOpen={stockModal.open}
        title={`Adjust Stock: ${stockModal.item?.food_name}`}
        onClose={() => setStockModal({ open: false, item: null, stock: '', minStock: '' })}
      >
        <form onSubmit={handleSaveStock}>
          <label>
            Current Stock Quantity (Units)
            <input
              type="number"
              required
              min="0"
              value={stockModal.stock}
              onChange={(e) => setStockModal((prev) => ({ ...prev, stock: e.target.value }))}
            />
          </label>
          <label>
            Minimum Alert Threshold
            <input
              type="number"
              required
              min="0"
              value={stockModal.minStock}
              onChange={(e) => setStockModal((prev) => ({ ...prev, minStock: e.target.value }))}
            />
          </label>
          <button className="primary" type="submit">
            Save Stock to Database
          </button>
        </form>
      </Modal>

      {/* Add Food Modal */}
      <Modal
        isOpen={foodModal.open}
        title="Add New Food Item to Menu"
        onClose={() => setFoodModal((prev) => ({ ...prev, open: false }))}
      >
        <form onSubmit={handleCreateFood}>
          <label>
            Category
            <select
              value={foodModal.categoryId}
              onChange={(e) => setFoodModal((prev) => ({ ...prev, categoryId: e.target.value }))}
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Food Name
            <input
              type="text"
              required
              placeholder="e.g. Paneer Tikka Sandwich"
              value={foodModal.name}
              onChange={(e) => setFoodModal((prev) => ({ ...prev, name: e.target.value }))}
            />
          </label>
          <label>
            Description
            <input
              type="text"
              placeholder="Short description of ingredients"
              value={foodModal.description}
              onChange={(e) => setFoodModal((prev) => ({ ...prev, description: e.target.value }))}
            />
          </label>
          <div className="grid-two">
            <label>
              Price (₹)
              <input
                type="number"
                step="0.5"
                min="0"
                required
                value={foodModal.price}
                onChange={(e) => setFoodModal((prev) => ({ ...prev, price: e.target.value }))}
              />
            </label>
            <label>
              Initial Stock
              <input
                type="number"
                min="0"
                required
                value={foodModal.stock}
                onChange={(e) => setFoodModal((prev) => ({ ...prev, stock: e.target.value }))}
              />
            </label>
          </div>
          <button className="primary" type="submit">
            Create Food Item & Inventory Row
          </button>
        </form>
      </Modal>

      {/* Add Category Modal */}
      <Modal
        isOpen={categoryModal.open}
        title="Create New Category"
        onClose={() => setCategoryModal((prev) => ({ ...prev, open: false }))}
      >
        <form onSubmit={handleCreateCategory}>
          <label>
            Category Name
            <input
              type="text"
              required
              placeholder="e.g. Healthy Bowls"
              value={categoryModal.name}
              onChange={(e) => setCategoryModal((prev) => ({ ...prev, name: e.target.value }))}
            />
          </label>
          <button className="primary" type="submit">
            Add Category
          </button>
        </form>
      </Modal>

      {/* Add Supplier Modal */}
      <Modal
        isOpen={supplierModal.open}
        title="Register New Supplier"
        onClose={() => setSupplierModal((prev) => ({ ...prev, open: false }))}
      >
        <form onSubmit={handleCreateSupplier}>
          <label>
            Supplier Name
            <input
              type="text"
              required
              placeholder="e.g. Apex Dairy Supplies"
              value={supplierModal.name}
              onChange={(e) => setSupplierModal((prev) => ({ ...prev, name: e.target.value }))}
            />
          </label>
          <label>
            Contact Phone
            <input
              type="text"
              placeholder="9876543210"
              value={supplierModal.contact}
              onChange={(e) => setSupplierModal((prev) => ({ ...prev, contact: e.target.value }))}
            />
          </label>
          <label>
            Email
            <input
              type="email"
              placeholder="orders@supplier.com"
              value={supplierModal.email}
              onChange={(e) => setSupplierModal((prev) => ({ ...prev, email: e.target.value }))}
            />
          </label>
          <label>
            Address
            <input
              type="text"
              placeholder="Market Area, Sector 5"
              value={supplierModal.address}
              onChange={(e) => setSupplierModal((prev) => ({ ...prev, address: e.target.value }))}
            />
          </label>
          <button className="primary" type="submit">
            Save Supplier
          </button>
        </form>
      </Modal>

      {/* Record Intake Modal */}
      <Modal
        isOpen={intakeModal.open}
        title="Record Supplier Intake (M:N Associative Entity)"
        onClose={() => setIntakeModal((prev) => ({ ...prev, open: false }))}
      >
        <form onSubmit={handleRecordIntake}>
          <label>
            Select Food Item
            <select
              value={intakeModal.foodId}
              onChange={(e) => setIntakeModal((prev) => ({ ...prev, foodId: e.target.value }))}
            >
              {foods.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name} (Current Stock: {f.inventory?.stock_quantity ?? 0})
                </option>
              ))}
            </select>
          </label>
          <div className="grid-two">
            <label>
              Supply Unit Cost (₹)
              <input
                type="number"
                step="0.5"
                min="0"
                required
                value={intakeModal.supplyPrice}
                onChange={(e) => setIntakeModal((prev) => ({ ...prev, supplyPrice: e.target.value }))}
              />
            </label>
            <label>
              Quantity Delivered
              <input
                type="number"
                min="1"
                required
                value={intakeModal.quantity}
                onChange={(e) => setIntakeModal((prev) => ({ ...prev, quantity: e.target.value }))}
              />
            </label>
          </div>
          <button className="primary" type="submit">
            Record in supplier_items & Increment Inventory
          </button>
        </form>
      </Modal>
    </main>
  );
}
