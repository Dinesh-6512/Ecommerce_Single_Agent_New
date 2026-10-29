import React, { createContext, useContext, useState, useEffect } from 'react';
import { getStoredAuth, setStoredAuth, clearStoredAuth } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(getStoredAuth());

  useEffect(() => {
    setAuth(getStoredAuth());
  }, []);

  const login = (token, isAdmin, email) => {
    setStoredAuth(token, isAdmin, email);
    setAuth({ token, isAdmin, email, isAuthenticated: true });
  };

  const logout = () => {
    clearStoredAuth();
    setAuth({ token: null, isAdmin: false, email: '', isAuthenticated: false });
  };

  return (
    <AuthContext.Provider value={{ ...auth, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
