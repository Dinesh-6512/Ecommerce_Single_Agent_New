import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { createProduct } from '../api';
import { useAuth } from '../context/AuthContext';

export default function AddProduct() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [stock, setStock] = useState('10');
  const [imageUrl, setImageUrl] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, token } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const productData = {
        title: title.trim(),
        description: description.trim(),
        price: parseFloat(price) || 0,
        stock: parseInt(stock, 10) || 10,
        image_url: imageUrl.trim() || 'https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&q=80'
      };

      const created = await createProduct(token, productData);
      setSuccess(`Product "${created.title}" added to catalog successfully!`);
      setTimeout(() => {
        navigate('/');
      }, 1500);
    } catch (err) {
      setError(err.message || 'Failed to add product');
    } finally {
      setLoading(false);
    }
  };

  // Guard: User must be logged in as Admin
  if (!isAuthenticated || !isAdmin) {
    return (
      <div className="auth-wrapper" id="add-product-page">
        <div className="info-card" style={{ maxWidth: '480px' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🔒</div>
          <h2>Admin Privileges Required</h2>
          <p>
            {!isAuthenticated
              ? 'You must be logged in with an administrator account to add products to the catalog.'
              : 'Your current account does not have administrator privileges.'}
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <Link to="/login" className="btn-primary" style={{ width: 'auto', textDecoration: 'none' }}>
              Login as Admin
            </Link>
            <Link to="/" className="btn-primary" style={{ width: 'auto', textDecoration: 'none', backgroundColor: '#64748b' }}>
              Back to Catalog
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-wrapper" id="add-product-page">
      <div className="auth-card" style={{ maxWidth: '520px' }}>
        <div className="auth-header">
          <h1>Add New Product</h1>
          <p>Create and publish a new item into Neon PostgreSQL</p>
        </div>

        {error && (
          <div
            style={{
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#b91c1c',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              marginBottom: '1.25rem',
              fontSize: '0.9rem'
            }}
            id="add-product-error-msg"
          >
            ⚠️ {error}
          </div>
        )}

        {success && (
          <div
            style={{
              backgroundColor: '#ecfdf5',
              border: '1px solid #a7f3d0',
              color: '#065f46',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              marginBottom: '1.25rem',
              fontSize: '0.9rem'
            }}
            id="add-product-success-msg"
          >
            ✓ {success}
          </div>
        )}

        <form onSubmit={handleSubmit} id="add-product-form">
          {/* Product Name */}
          <div className="form-group">
            <label className="form-label" htmlFor="product-name">Product Name *</label>
            <input
              id="product-name"
              type="text"
              className="form-input"
              placeholder="e.g. Ergonomic Office Chair"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          {/* Price and Stock Row */}
          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="product-price">Price ($) *</label>
              <input
                id="product-price"
                type="number"
                step="0.01"
                min="0"
                className="form-input"
                placeholder="29.99"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="product-stock">Stock Quantity *</label>
              <input
                id="product-stock"
                type="number"
                min="1"
                className="form-input"
                placeholder="10"
                value={stock}
                onChange={(e) => setStock(e.target.value)}
                required
                disabled={loading}
              />
            </div>
          </div>

          {/* Image URL */}
          <div className="form-group">
            <label className="form-label" htmlFor="product-image-url">Image URL</label>
            <input
              id="product-image-url"
              type="url"
              className="form-input"
              placeholder="https://images.unsplash.com/..."
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              disabled={loading}
            />
          </div>

          {/* Description */}
          <div className="form-group">
            <label className="form-label" htmlFor="product-description">Description *</label>
            <textarea
              id="product-description"
              className="form-textarea"
              placeholder="Enter product details..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            id="save-product-submit-btn"
            disabled={loading}
          >
            {loading ? 'Saving Product...' : '💾 Save Product'}
          </button>
        </form>

        <div className="auth-footer">
          <Link to="/" id="back-to-products-link">&larr; Back to Products</Link>
        </div>
      </div>
    </div>
  );
}
