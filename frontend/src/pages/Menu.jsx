import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { apiRequest } from '../api/client';

export function Menu() {
  const { cart, addToCart } = useApp();
  const [foods, setFoods] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState('');

  useEffect(() => {
    Promise.all([apiRequest('/foods'), apiRequest('/categories')])
      .then(([foodsData, categoriesData]) => {
        setFoods(foodsData);
        setCategories(categoriesData);
      })
      .catch((err) => {
        console.error('Failed to load menu:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleAdd = (food) => {
    addToCart(food);
    setNotification(`Added "${food.name}" to cart!`);
    setTimeout(() => setNotification(''), 2000);
  };

  const filteredFoods = selectedCategory === 'All'
    ? foods
    : foods.filter((f) => f.category?.name === selectedCategory);

  const totalCartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <main>
      <section className="hero">
        <p className="eyebrow">CAMPUS PRE-ORDERING</p>
        <h1>Your break is too short for queues.</h1>
        <p>Pick your favourites now, select your pickup slot, and collect fresh food right on time.</p>
        <Link className="primary link hero-cta" to="/cart">
          Review Cart {totalCartCount > 0 && `(${totalCartCount})`}
        </Link>
      </section>

      {notification && <div className="toast-notification">{notification}</div>}

      <section className="menu">
        <div className="menu-header">
          <h2>Today’s Canteen Menu</h2>
          <div className="category-tabs">
            <button
              className={`cat-btn ${selectedCategory === 'All' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('All')}
            >
              All Items
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                className={`cat-btn ${selectedCategory === c.name ? 'active' : ''}`}
                onClick={() => setSelectedCategory(c.name)}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <p className="loading-state">Loading fresh campus menu from PostgreSQL...</p>
        ) : (
          <div className="grid">
            {filteredFoods.map((f) => {
              const stock = f.inventory?.stock_quantity ?? 0;
              const isLowStock = f.available && stock <= (f.inventory?.minimum_stock ?? 5) && stock > 0;
              const inCart = cart.find((item) => item.food_id === f.id);

              return (
                <article className="card" key={f.id}>
                  <div className="food-icon">{f.name[0]}</div>
                  <div className="card-top">
                    <span className="category">{f.category?.name}</span>
                    {isLowStock && <span className="stock-tag low">Only {stock} left!</span>}
                  </div>
                  <h3>{f.name}</h3>
                  <p className="food-desc">{f.description}</p>
                  <div className="card-bottom">
                    <strong className="food-price">₹{f.price.toFixed(2)}</strong>
                    {f.available ? (
                      <button className="add-btn" onClick={() => handleAdd(f)}>
                        {inCart ? `Add (${inCart.quantity}) +` : 'Add +'}
                      </button>
                    ) : (
                      <span className="sold-badge">Out of Stock</span>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}
