import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Helper to get sponsor_code from URL or sessionStorage
const getSponsorCode = () => {
  // First check URL params
  const urlParams = new URLSearchParams(window.location.search);
  const refFromUrl = urlParams.get('ref');
  
  if (refFromUrl) {
    // Save to sessionStorage for persistence through navigation
    sessionStorage.setItem('sponsor_code', refFromUrl);
    return refFromUrl;
  }
  
  // Fallback to sessionStorage
  return sessionStorage.getItem('sponsor_code');
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [sponsorCode, setSponsorCode] = useState(getSponsorCode());

  // Check for sponsor_code on mount and URL changes
  useEffect(() => {
    const code = getSponsorCode();
    if (code) {
      setSponsorCode(code);
    }
  }, []);

  const checkAuth = useCallback(async () => {
    try {
      // Try cookie auth first (Google)
      const response = await axios.get(`${API}/auth/me`, {
        withCredentials: true,
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setUser(response.data);
    } catch (error) {
      setUser(null);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, name, surname) => {
    // Include sponsor_code if available (CRITICAL - links new user to sponsor)
    const payload = { email, password, name, surname };
    if (sponsorCode) {
      payload.sponsor_code = sponsorCode;
    }
    
    const response = await axios.post(`${API}/auth/register`, payload);
    const { token: newToken, user: userData } = response.data;
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);
    
    // Clear sponsor_code after successful registration
    sessionStorage.removeItem('sponsor_code');
    setSponsorCode(null);
    
    return userData;
  };

  const loginWithGoogle = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + '/auth/callback';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}&app_name=${encodeURIComponent('4Luis')}`;
  };

  const processGoogleSession = async (sessionId) => {
    const response = await axios.post(`${API}/auth/google/session`, 
      { session_id: sessionId },
      { withCredentials: true }
    );
    // Store JWT token for Authorization header
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      setToken(response.data.token);
    }
    setUser(response.data.user);
    return response.data.user;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (error) {
      // Ignore errors
    }
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const getAuthHeaders = () => {
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return {};
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      token,
      sponsorCode,
      login,
      register,
      loginWithGoogle,
      processGoogleSession,
      logout,
      getAuthHeaders,
      checkAuth
    }}>
      {children}
    </AuthContext.Provider>
  );
};
