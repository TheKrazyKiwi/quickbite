import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export function Cart() {
  const { cart, updateQuantity, removeFromCart, clearCart } = useApp();
  const navigate = useNavigate();

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <main className="panel">
      <div className="panel-header">
        <h1>Your Pre-Order Cart</h1>
        {cart.length > 0 && (
          <button className="text-btn danger" onClick={clearCart}>
            Clear Cart
          </button>
        )}
      </div>

      {!cart.length ? (
        <div className="empty-state">
          <p>Your cart is empty.</p>
          <Link className="primary link" to="/">
            Browse Today’s Menu
          </Link>
        </div>
      ) : (
        <div className="cart-wrapper">
          <div className="cart-items">
            {cart.map((item) => (
              <div className="line" key={item.food_id}>
                <div className="item-details">
                  <b>{item.name}</b>
                  <small>₹{item.price.toFixed(2)} each</small>
                </div>

                <div className="quantity-controls">
                  <button
                    className="qty-btn"
                    onClick={() => updateQuantity(item.food_id, -1)}
                    title="Decrease quantity"
                  >
                    −
                  </button>
                  <span className="qty-number">{item.quantity}</span>
                  <button
                    className="qty-btn"
                    onClick={() => updateQuantity(item.food_id, 1)}
                    title="Increase quantity"
                  >
                    +
                  </button>
                </div>

                <div className="line-price">
                  <b>₹{(item.price * item.quantity).toFixed(2)}</b>
                  <button
                    className="remove-btn"
                    onClick={() => removeFromCart(item.food_id)}
                    title="Remove item"
                  >
                    &times;
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <div className="total-row">
              <span>Estimated Order Total</span>
              <b className="total-amount">₹{total.toFixed(2)}</b>
            </div>

            <p className="summary-note">
              Prices are server-authoritative and will be locked with your reservation.
            </p>

            <button
              className="primary full-width"
              onClick={() => navigate('/checkout')}
            >
              Choose Pickup Slot & Checkout &rarr;
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
