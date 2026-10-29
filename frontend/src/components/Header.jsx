import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const location = useLocation();
  const { isAuthenticated, isAdmin, email, logout } = useAuth();

  const isActive = (path) => (location.pathname === path ? 'nav-link active' : 'nav-link');

  return (
    <header className="site-header">
      <div className="header-container">
        <Link to="/" className="brand-logo" id="nav-brand-logo">
          🛒 Simple Store
        </Link>
        <nav className="main-nav">
          <Link to="/" className={isActive('/')} id="nav-link-products">
            Products
          </Link>
          <Link to="/cart" className={isActive('/cart')} id="nav-link-cart">
            Cart
          </Link>
          <Link to="/chat" className={isActive('/chat')} id="nav-link-chat">
            Chat
          </Link>

          {/* Admin only action */}
          {isAdmin && (
            <Link to="/add-product" className={isActive('/add-product')} id="nav-link-add-product">
              + Add Product
            </Link>
          )}

          {isAuthenticated ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginLeft: '0.5rem' }}>
              <span
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  backgroundColor: '#f1f5f9',
                  padding: '0.35rem 0.65rem',
                  borderRadius: '6px'
                }}
                id="user-email-display"
              >
                👤 {email} {isAdmin ? '(Admin)' : ''}
              </span>
              <button
                type="button"
                onClick={logout}
                className="nav-link"
                id="logout-btn"
                style={{
                  background: 'none',
                  border: '1px solid var(--border)',
                  cursor: 'pointer'
                }}
              >
                Logout
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className={isActive('/login')} id="nav-link-login">
                Login
              </Link>
              <Link to="/register" className={`${isActive('/register')} nav-btn`} id="nav-link-register">
                Register
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
