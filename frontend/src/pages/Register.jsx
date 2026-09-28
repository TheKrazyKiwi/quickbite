import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { apiRequest } from '../api/client';

export function Register() {
  const { setUser } = useApp();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    phone: '',
    department: 'Computer Science',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(formData),
      });

      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth">
      <p className="eyebrow">NEW STUDENT REGISTRATION</p>
      <h1>Create an account</h1>
      <p className="subtext">Join QuickBite to pre-order food and skip canteen queues.</p>

      <form onSubmit={handleSubmit}>
        <label>
          Full Name
          <input
            type="text"
            required
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="e.g. Maya Patel"
          />
        </label>

        <label>
          College Email
          <input
            type="email"
            required
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="e.g. maya@college.edu"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            required
            minLength={6}
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="At least 6 characters"
          />
        </label>

        <div className="grid-two">
          <label>
            Department
            <input
              type="text"
              name="department"
              value={formData.department}
              onChange={handleChange}
              placeholder="e.g. Computer Science"
            />
          </label>
          <label>
            Phone Number
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              placeholder="9876543210"
            />
          </label>
        </div>

        {error && <p className="error-banner">{error}</p>}

        <button className="primary" type="submit" disabled={loading}>
          {loading ? 'Creating Account...' : 'Register'}
        </button>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Log in here</Link>
        </p>
      </form>
    </main>
  );
}
