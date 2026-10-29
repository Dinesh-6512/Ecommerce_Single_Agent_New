import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { fetchProducts, addToCart } from '../api';
import { useAuth } from '../context/AuthContext';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [addingId, setAddingId] = useState(null);

  const { isAuthenticated, token } = useAuth();

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await fetchProducts();
      setProducts(data);
    } catch (err) {
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleAddToCart = async (product) => {
    if (!isAuthenticated) {
      setToast({
        message: 'Please login to add items to your cart.',
        type: 'warning'
      });
      return;
    }

    setAddingId(product.id);
    try {
      const res = await addToCart(token, product.id, 1);
      setToast({
        message: `Added "${product.title}" to cart! (Current in cart: ${res.quantity})`,
        type: 'success'
      });
    } catch (err) {
      setToast({
        message: err.message || 'Could not add to cart',
        type: 'danger'
      });
    } finally {
      setAddingId(null);
    }
  };

  return (
    <div id="product-listing-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Available Products</h1>
          <p className="page-subtitle">Simple Store &mdash; Live Catalog from Neon PostgreSQL</p>
        </div>
        <Link to="/cart" className="nav-link nav-btn" style={{ textDecoration: 'none' }} id="top-cart-btn">
          🛒 View Cart
        </Link>
      </div>

      {/* Toast Notification */}
      {toast.message && (
        <div
          className="toast-notice"
          id="cart-toast-notice"
          style={{
            backgroundColor: toast.type === 'danger' ? '#fef2f2' : toast.type === 'warning' ? '#fffbeb' : '#ecfdf5',
            borderColor: toast.type === 'danger' ? '#fecaca' : toast.type === 'warning' ? '#fef3c7' : '#a7f3d0',
            color: toast.type === 'danger' ? '#b91c1c' : toast.type === 'warning' ? '#92400e' : '#065f46'
          }}
        >
          <span>{toast.message}</span>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            {!isAuthenticated ? (
              <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}>
                Login here &rarr;
              </Link>
            ) : (
              <Link to="/cart" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}>
                Go to Cart &rarr;
              </Link>
            )}
            <button
              type="button"
              onClick={() => setToast({ message: '', type: 'success' })}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontWeight: 'bold' }}
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="info-card" id="products-loading">
          <p style={{ color: 'var(--text-muted)' }}>⏳ Loading live products from backend...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="info-card" id="products-error">
          <p style={{ color: 'var(--danger)', fontWeight: 600 }}>⚠️ {error}</p>
          <button
            type="button"
            className="btn-primary"
            style={{ width: 'auto', padding: '0.6rem 1.25rem', marginTop: '1rem' }}
            onClick={loadProducts}
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty catalog */}
      {!loading && !error && products.length === 0 && (
        <div className="info-card" id="empty-catalog">
          <h2>No products available yet</h2>
          <p>The product catalog is currently empty. Admins can add products.</p>
        </div>
      )}

      {/* Real Products Grid */}
      {!loading && !error && products.length > 0 && (
        <div className="product-grid" id="product-grid">
          {products.map((product) => (
            <div key={product.id} className="product-card" id={`product-card-${product.id}`}>
              <div className="product-img-wrapper">
                <img
                  src={product.image_url || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80'}
                  alt={product.title}
                  className="product-image"
                  loading="lazy"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80';
                  }}
                />
              </div>
              <div className="product-body">
                <h2 className="product-title">{product.title}</h2>
                <p className="product-desc">{product.description || 'No description provided.'}</p>

                <div className="product-meta">
                  <span className="product-price">${product.price.toFixed(2)}</span>
                  <span className="stock-tag">Stock: {product.stock}</span>
                </div>

                <button
                  type="button"
                  className="btn-add-cart"
                  id={`add-to-cart-btn-${product.id}`}
                  disabled={addingId === product.id || product.stock <= 0}
                  onClick={() => handleAddToCart(product)}
                >
                  {addingId === product.id ? 'Adding...' : product.stock <= 0 ? 'Out of Stock' : '+ Add to Cart'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
