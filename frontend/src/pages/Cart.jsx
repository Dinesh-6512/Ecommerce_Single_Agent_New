import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchCart } from '../api';
import { useAuth } from '../context/AuthContext';

export default function Cart() {
  const [cartData, setCartData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const { isAuthenticated, token } = useAuth();

  const loadCart = async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const data = await fetchCart(token);
      setCartData(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch cart');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, [isAuthenticated, token]);

  // Unauthenticated State
  if (!isAuthenticated) {
    return (
      <div className="auth-wrapper" id="cart-screen">
        <div className="info-card" style={{ maxWidth: '480px' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>🛍️</div>
          <h2>Your Cart is Waiting</h2>
          <p>Please login to your account to view your shopping cart and saved items.</p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <Link to="/login" className="btn-primary" style={{ width: 'auto', textDecoration: 'none' }} id="cart-login-link">
              Login to View Cart
            </Link>
            <Link to="/" className="btn-primary" style={{ width: 'auto', textDecoration: 'none', backgroundColor: '#64748b' }}>
              Browse Products
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const totalQuantity = cartData.items.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <div id="cart-screen">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">My Shopping Cart</h1>
          <p className="page-subtitle">Real-time cart connected to Neon PostgreSQL</p>
        </div>
        <Link to="/" className="nav-link" style={{ fontWeight: 600, color: 'var(--primary)' }}>
          &larr; Continue Shopping
        </Link>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="info-card">
          <p style={{ color: 'var(--text-muted)' }}>⏳ Loading your cart from database...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="info-card">
          <p style={{ color: 'var(--danger)', fontWeight: 600 }}>⚠️ {error}</p>
          <button
            type="button"
            className="btn-primary"
            style={{ width: 'auto', padding: '0.6rem 1.25rem', marginTop: '1rem' }}
            onClick={loadCart}
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty Cart */}
      {!loading && !error && cartData.items.length === 0 && (
        <div className="info-card" id="empty-cart-state">
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🛒</div>
          <h2>Your cart is currently empty</h2>
          <p>You haven't added any items to your shopping cart yet.</p>
          <Link to="/" className="btn-primary" style={{ display: 'inline-block', width: 'auto', textDecoration: 'none', padding: '0.65rem 1.4rem' }}>
            Browse Products &rarr;
          </Link>
        </div>
      )}

      {/* Populated Cart Layout */}
      {!loading && !error && cartData.items.length > 0 && (
        <div className="cart-layout">
          {/* Cart Items List */}
          <div className="cart-items-list" id="cart-items-list">
            {cartData.items.map((item) => (
              <div key={item.id} className="cart-item-card" id={`cart-item-${item.id}`}>
                <img
                  src={item.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80'}
                  alt={item.title}
                  className="cart-item-img"
                  loading="lazy"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80';
                  }}
                />
                <div className="cart-item-details">
                  <h2 className="cart-item-title">{item.title}</h2>
                  <div className="cart-item-price">Unit Price: ${item.price.toFixed(2)}</div>
                  <div className="cart-item-qty">Quantity: {item.quantity}</div>
                </div>
                <div className="cart-item-subtotal">
                  ${item.subtotal.toFixed(2)}
                </div>
              </div>
            ))}

            <div style={{ marginTop: '0.5rem' }}>
              <Link to="/" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 600 }}>
                &larr; Add more products from catalog
              </Link>
            </div>
          </div>

          {/* Order Summary Sidebar */}
          <aside className="cart-summary-card" id="cart-summary-card">
            <h2 className="summary-title">Order Summary</h2>

            <div className="summary-row">
              <span>Items Total ({totalQuantity} units)</span>
              <span>${cartData.total.toFixed(2)}</span>
            </div>

            <div className="summary-row">
              <span>Shipping</span>
              <span style={{ color: 'var(--success)', fontWeight: 600 }}>FREE</span>
            </div>

            <div className="summary-total">
              <span>Total:</span>
              <span className="summary-total-val">${cartData.total.toFixed(2)}</span>
            </div>

            <div style={{ marginTop: '1.5rem' }}>
              <Link
                to="/"
                className="btn-primary"
                style={{
                  display: 'block',
                  textAlign: 'center',
                  textDecoration: 'none',
                  padding: '0.85rem'
                }}
              >
                Continue Shopping &rarr;
              </Link>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
