import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';

export function Navbar() {
  const { user, cart, logout } = useApp();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const totalCartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <header>
      <div className="brand-group">
        <Link className="brand" to="/">
          Quick<span>Bite</span>
        </Link>
      </div>

      <nav>
        {user ? (
          <>
            <Link to="/">Menu</Link>
            {user.role === 'STUDENT' ? (
              <>
                <Link to="/orders">My Orders</Link>
                <Link to="/cart" className="cart-nav-link">
                  Cart {totalCartCount > 0 && <span className="cart-badge">{totalCartCount}</span>}
                </Link>
              </>
            ) : (
              <Link to="/staff" className="staff-link">
                Operations Hub
              </Link>
            )}
            <div className="user-profile">
              <span className="user-name">{user.name.split(' ')[0]}</span>
              <span className={`role-pill ${user.role.toLowerCase()}`}>{user.role}</span>
              <button className="signout-btn" onClick={handleLogout} title="Sign Out">
                Sign out
              </button>
            </div>
          </>
        ) : (
          <div className="auth-links">
            <Link to="/login">Log in</Link>
            <Link to="/register" className="primary link small">
              Register
            </Link>
          </div>
        )}
      </nav>
    </header>
  );
}
