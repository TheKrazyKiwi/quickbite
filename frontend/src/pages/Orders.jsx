import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../api/client';

export function Orders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState('');
  const [actionNotice, setActionNotice] = useState('');

  const loadOrders = () => {
    setLoading(true);
    apiRequest('/orders/my')
      .then((data) => {
        setOrders(data);
      })
      .catch((err) => {
        setActionError(err.message || 'Failed to load orders');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadOrders();
    // Auto refresh every 10 seconds for real-time status tracking
    const interval = setInterval(loadOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleCancel = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this pre-order? Your items will be returned to canteen inventory.')) {
      return;
    }

    setActionError('');
    setActionNotice('');

    try {
      await apiRequest(`/orders/${orderId}/cancel`, { method: 'POST' });
      setActionNotice('Order cancelled successfully. Inventory has been restored.');
      loadOrders();
    } catch (err) {
      setActionError(err.message || 'Failed to cancel order');
    }
  };

  return (
    <main className="panel">
      <div className="panel-header">
        <div>
          <h1>My Canteen Orders</h1>
          <p className="subtext">Track your pre-orders and status updates in real-time.</p>
        </div>
        <button className="refresh-btn" onClick={loadOrders} disabled={loading}>
          {loading ? 'Refreshing...' : '↻ Refresh Status'}
        </button>
      </div>

      {actionNotice && <div className="notice-banner">{actionNotice}</div>}
      {actionError && <div className="error-banner">{actionError}</div>}

      {!orders.length && !loading ? (
        <div className="empty-state">
          <p>You haven't placed any pre-orders yet.</p>
          <Link className="primary link" to="/">
            Explore the Menu
          </Link>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((o) => (
            <article className="order-card" key={o.id}>
              <div className="order-main-info">
                <div className="token-slot-row">
                  <span className="order-token">{o.token}</span>
                  <span className="order-slot">&#9200; {o.pickup_slot}</span>
                </div>

                <div className="order-items-summary">
                  {o.items.map((i) => (
                    <span className="order-item-tag" key={i.id}>
                      {i.quantity} &times; {i.name} (₹{i.subtotal.toFixed(2)})
                    </span>
                  ))}
                </div>

                {o.payment && (
                  <small className="payment-tag">
                    {o.payment.mode} &bull; {o.payment.status}
                  </small>
                )}
              </div>

              <div className="order-status-column">
                <span className={`badge status-${o.status.toLowerCase()}`}>
                  {o.status}
                </span>
                <strong className="order-total-price">₹{o.total_amount.toFixed(2)}</strong>

                {o.status === 'PLACED' && (
                  <button
                    className="cancel-btn"
                    onClick={() => handleCancel(o.id)}
                    title="Cancel order and restore inventory"
                  >
                    Cancel Order
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
