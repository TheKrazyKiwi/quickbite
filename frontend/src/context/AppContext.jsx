import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiRequest } from '../api/client';

const AppContext = createContext();

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Cart with localStorage persistence
  const [cart, setCart] = useState(() => {
    try {
      const saved = localStorage.getItem('quickbite_cart');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('quickbite_cart', JSON.stringify(cart));
    } catch {}
  }, [cart]);

  // Check auth status on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoadingUser(false);
      return;
    }

    apiRequest('/auth/me')
      .then((userData) => {
        setUser(userData);
      })
      .catch(() => {
        localStorage.removeItem('token');
        setUser(null);
      })
      .finally(() => {
        setLoadingUser(false);
      });
  }, []);

  const addToCart = (food) => {
    setCart((prevCart) => {
      const existing = prevCart.find((item) => item.food_id === food.id);
      if (existing) {
        return prevCart.map((item) =>
          item.food_id === food.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [
        ...prevCart,
        {
          food_id: food.id,
          name: food.name,
          price: food.price,
          quantity: 1,
        },
      ];
    });
  };

  const updateQuantity = (food_id, delta) => {
    setCart((prevCart) => {
      return prevCart
        .map((item) => {
          if (item.food_id === food_id) {
            const newQty = item.quantity + delta;
            return newQty > 0 ? { ...item, quantity: newQty } : null;
          }
          return item;
        })
        .filter(Boolean);
    });
  };

  const removeFromCart = (food_id) => {
    setCart((prevCart) => prevCart.filter((item) => item.food_id !== food_id));
  };

  const clearCart = () => {
    setCart([]);
    localStorage.removeItem('quickbite_cart');
  };

  const logout = () => {
    localStorage.removeItem('token');
    clearCart();
    setUser(null);
  };

  return (
    <AppContext.Provider
      value={{
        user,
        setUser,
        loadingUser,
        cart,
        addToCart,
        updateQuantity,
        removeFromCart,
        clearCart,
        logout,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export const useApp = () => useContext(AppContext);
