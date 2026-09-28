import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { apiRequest } from '../api/client';

const SLOTS = [
  '12:30 PM – 12:45 PM',
  '12:45 PM – 1:00 PM',
  '1:00 PM – 1:15 PM',
  '1:15 PM – 1:30 PM',
  '1:30 PM – 1:45 PM',
];

export function Checkout() {
  const { cart, clearCart } = useApp();
  const navigate = useNavigate();

  const [slot, setSlot] = useState(SLOTS[3]); // default 1:15 PM - 1:30 PM per demo spec
  const [paymentMode, setPaymentMode] = useState('MOCK_ONLINE');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!cart.length) {
    return (
      <main className="panel">
        <h1>Checkout</h1>
        <p>Your cart is empty.</p>
        <Link className="primary link" to="/">
          Return to Menu
        </Link>
      </main>
    );
  }

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const handlePlaceOrder = async () => {
    setError('');
    setLoading(true);

    try {
      const payload = {
        items: cart.map((i) => ({ food_id: i.food_id, quantity: i.quantity })),
        pickup_slot: slot,
        payment_mode: paymentMode,
      };

      const orderData = await apiRequest('/orders', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      // Clear in-memory and local cart
      clearCart();

      // Navigate to confirmation with rich order state
      navigate('/confirmation', { state: { order: orderData } });
    } catch (err) {
      setError(err.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="panel checkout-panel">
      <h1>Confirm Your Pre-Order</h1>
      <p className="subtext">
        Select your pickup slot and mock payment method to finalize your canteen token.
      </p>

      <div className="checkout-layout">
        <div className="checkout-form">
          <section className="form-section">
            <h3>1. Scheduled Pickup Slot</h3>
            <p className="section-hint">Select the break window when you will collect your food:</p>
            <label className="select-label">
              <select value={slot} onChange={(e) => setSlot(e.target.value)}>
                {SLOTS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <section className="form-section">
            <h3>2. Payment Method (Prototype)</h3>
            <div className="payment-options">
              <label className={`payment-card ${paymentMode === 'MOCK_ONLINE' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="payment"
                  checked={paymentMode === 'MOCK_ONLINE'}
                  onChange={() => setPaymentMode('MOCK_ONLINE')}
                />
                <div>
                  <strong>Mock Online Payment (Instant)</strong>
                  <small>Simulates instant payment gateway approval. Status: SUCCESS</small>
                </div>
              </label>

              <label className={`payment-card ${paymentMode === 'PAY_AT_PICKUP' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="payment"
                  checked={paymentMode === 'PAY_AT_PICKUP'}
                  onChange={() => setPaymentMode('PAY_AT_PICKUP')}
                />
                <div>
                  <strong>Pay at Pickup Counter</strong>
                  <small>Pay cash or UPI at the canteen counter. Status: PENDING</small>
                </div>
              </label>
            </div>
          </section>

          {error && <div className="error-banner">{error}</div>}

          <button
            className="primary place-order-btn"
            onClick={handlePlaceOrder}
            disabled={loading}
          >
            {loading ? 'Creating Transaction in PostgreSQL...' : `Confirm & Place Order (₹${total.toFixed(2)})`}
          </button>
        </div>

        <div className="order-summary-sidebar">
          <h3>Order Items</h3>
          <div className="sidebar-items">
            {cart.map((item) => (
              <div className="sidebar-line" key={item.food_id}>
                <span>
                  {item.quantity} &times; {item.name}
                </span>
                <b>₹{(item.price * item.quantity).toFixed(2)}</b>
              </div>
            ))}
          </div>
          <div className="sidebar-total">
            <span>Total to Pay:</span>
            <b>₹{total.toFixed(2)}</b>
          </div>
        </div>
      </div>
    </main>
  );
}
