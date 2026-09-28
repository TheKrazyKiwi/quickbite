import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './context/AppContext';
import { Navbar } from './components/Navbar';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Menu } from './pages/Menu';
import { Cart } from './pages/Cart';
import { Checkout } from './pages/Checkout';
import { Confirmation } from './pages/Confirmation';
import { Orders } from './pages/Orders';
import { StaffDashboard } from './pages/StaffDashboard';

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loadingUser } = useApp();

  if (loadingUser) {
    return <div className="loading-screen">Authenticating QuickBite session...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === 'STUDENT' ? '/' : '/staff'} replace />;
  }

  return children;
}

function AppRoutes() {
  const { user, loadingUser } = useApp();

  if (loadingUser) {
    return <div className="loading-screen">Starting QuickBite...</div>;
  }

  return (
    <div className="app-container">
      <Navbar />
      <div className="main-content">
        <Routes>
          {/* Public / Auth */}
          <Route
            path="/login"
            element={!user ? <Login /> : <Navigate to={user.role === 'STUDENT' ? '/' : '/staff'} replace />}
          />
          <Route
            path="/register"
            element={!user ? <Register /> : <Navigate to="/" replace />}
          />

          {/* Student routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute allowedRoles={['STUDENT']}>
                <Menu />
              </ProtectedRoute>
            }
          />
          <Route
            path="/cart"
            element={
              <ProtectedRoute allowedRoles={['STUDENT']}>
                <Cart />
              </ProtectedRoute>
            }
          />
          <Route
            path="/checkout"
            element={
              <ProtectedRoute allowedRoles={['STUDENT']}>
                <Checkout />
              </ProtectedRoute>
            }
          />
          <Route
            path="/confirmation"
            element={
              <ProtectedRoute allowedRoles={['STUDENT']}>
                <Confirmation />
              </ProtectedRoute>
            }
          />
          <Route
            path="/orders"
            element={
              <ProtectedRoute allowedRoles={['STUDENT']}>
                <Orders />
              </ProtectedRoute>
            }
          />

          {/* Staff & Admin routes */}
          <Route
            path="/staff"
            element={
              <ProtectedRoute allowedRoles={['STAFF', 'ADMIN']}>
                <StaffDashboard />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </div>
  );
}

export function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
