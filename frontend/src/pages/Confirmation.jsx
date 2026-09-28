import React from 'react';
import { useLocation, Link, Navigate } from 'react-router-dom';

export function Confirmation() {
  const { state } = useLocation();
  const order = state?.order;

  if (!order) {
    return <Navigate to="/orders" replace />;
  }

  return (
    <main className="panel confirm">
      <div className="confirm-card">
        <div className="check-icon">&#10003;</div>
        <p className="eyebrow">ORDER CONFIRMED &bull; TRANSACTION COMMITTED</p>
        <h1 className="token-display">{order.token}</h1>
        <p className="pickup-time-banner">
          Scheduled Pickup: <strong>{order.pickup_slot}</strong>
        </p>

        <div className="status-container">
          <span className="badge placed">{order.status}</span>
        </div>

        <div className="receipt-box">
          <h4>Order Summary</h4>
          <div className="receipt-items">
            {order.items?.map((item) => (
              <div className="receipt-line" key={item.id}>
                <span>
                  {item.quantity} &times; {item.name}
                </span>
                <span>₹{item.subtotal.toFixed(2)}</span>
              </div>
            ))}
          </div>

          <div className="receipt-total">
            <strong>Total Amount:</strong>
            <strong>₹{order.total_amount.toFixed(2)}</strong>
          </div>

          {order.payment && (
            <div className="payment-meta">
              <small>
                Payment: {order.payment.mode} ({order.payment.status}) &bull; Ref: {order.payment.reference}
              </small>
            </div>
          )}
        </div>

        <div className="confirm-actions">
          <Link className="primary link" to="/orders">
            Track Order Status &rarr;
          </Link>
          <Link className="secondary-link" to="/">
            Back to Menu
          </Link>
        </div>
      </div>
    </main>
  );
}
