import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { user_id, email, role, access_token }
  const [loading, setLoading] = useState(true);

  const login = useCallback(async (userId, password) => {
    try {
      const res = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, password })
      });
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      const userData = { user_id: data.user_id, email: data.email, role: data.role, access_token: data.access_token };
      setUser(userData);
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(userData));
      return { success: true, user: userData };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }, []);

  const register = useCallback(async (userId, email, password) => {
    try {
      const res = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, email, password })
      });
      if (!res.ok) throw new Error('Registration failed');
      const data = await res.json();
      const userData = { user_id: data.user_id, email: data.email, role: data.role, access_token: data.access_token };
      setUser(userData);
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(userData));
      return { success: true, user: userData };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }, []);

  const verify = useCallback(async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) return false;
    try {
      const res = await fetch('/auth/verify', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Token invalid');
      const data = await res.json();
      const stored = JSON.parse(localStorage.getItem('auth_user') || '{}');
      setUser({ ...stored, access_token: token });
      return true;
    } catch (e) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      setUser(null);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setUser(null);
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await verify();
      setLoading(false);
    })();
  }, [verify]);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, verify, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
