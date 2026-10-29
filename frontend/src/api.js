const RAW_API_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.vite_api_url ||
  (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')
    ? 'https://ecommerce-new-j82m.onrender.com/api'
    : 'http://127.0.0.1:8000');
const API_BASE = RAW_API_URL.endsWith('/api') ? RAW_API_URL : `${RAW_API_URL.replace(/\/+$/, '')}/api`;

// Token and Session Storage Helpers
export const getStoredAuth = () => {
  const token = localStorage.getItem('token');
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  const email = localStorage.getItem('userEmail') || '';
  return { token, isAdmin, email, isAuthenticated: !!token };
};

export const setStoredAuth = (token, isAdmin, email) => {
  localStorage.setItem('token', token);
  localStorage.setItem('isAdmin', isAdmin ? 'true' : 'false');
  localStorage.setItem('userEmail', email);
};

export const clearStoredAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('isAdmin');
  localStorage.removeItem('userEmail');
};

// 1. Authentication APIs
export const registerUser = async (email, password, isAdmin = false) => {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, is_admin: isAdmin })
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Registration failed');
  }
  return data;
};

export const loginUser = async (email, password) => {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Invalid email or password');
  }
  return data;
};

// 2. Product APIs
export const fetchProducts = async () => {
  const res = await fetch(`${API_BASE}/products`);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to fetch products');
  }
  return data;
};

export const createProduct = async (token, productData) => {
  const res = await fetch(`${API_BASE}/products`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(productData)
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to create product');
  }
  return data;
};

// 3. Cart APIs
export const fetchCart = async (token) => {
  const res = await fetch(`${API_BASE}/cart`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to fetch cart');
  }
  return data;
};

export const addToCart = async (token, productId, quantity = 1) => {
  const res = await fetch(`${API_BASE}/cart`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ product_id: productId, quantity })
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to add item to cart');
  }
  return data;
};

// 4. Agent API
export const askAgent = async (token, question) => {
  const res = await fetch(`${API_BASE}/agent/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ question })
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to get answer from assistant');
  }
  return data;
};

