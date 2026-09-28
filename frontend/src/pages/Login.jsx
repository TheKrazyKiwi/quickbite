import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { apiRequest } from '../api/client';

export function Login() {
  const { setUser } = useApp();
  const navigate = useNavigate();

  const [email, setEmail] = useState('student@quickbite.demo');
  const [password, setPassword] = useState('Student@123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fillDemo = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      localStorage.setItem('token', data.access_token);
      setUser(data.user);

      if (data.user.role === 'STUDENT') {
        navigate('/');
      } else {
        navigate('/staff');
      }
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth">
      <p className="eyebrow">SKIP THE QUEUE. GRAB YOUR BITE.</p>
      <h1>Welcome back.</h1>
      <p className="subtext">Pre-order your canteen meal and pickup with zero wait time.</p>

      <form onSubmit={handleSubmit}>
        <label>
          Email address
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@quickbite.demo"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </label>

        {error && <p className="error-banner">{error}</p>}

        <button className="primary" type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Log in'}
        </button>

        <div className="demo-accounts-box">
          <p className="demo-title">Quick Demo Login:</p>
          <div className="demo-chips">
            <button
              type="button"
              className="chip student-chip"
              onClick={() => fillDemo('student@quickbite.demo', 'Student@123')}
            >
              Student
            </button>
            <button
              type="button"
              className="chip staff-chip"
              onClick={() => fillDemo('staff@quickbite.demo', 'Staff@123')}
            >
              Staff
            </button>
            <button
              type="button"
              className="chip admin-chip"
              onClick={() => fillDemo('admin@quickbite.demo', 'Admin@123')}
            >
              Admin
            </button>
          </div>
        </div>

        <p className="auth-footer">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
      </form>
    </main>
  );
}
