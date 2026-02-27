import React, { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthCallback = () => {
  const { processGoogleSession, getAuthHeaders } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      // Extract session_id from URL fragment
      const hash = location.hash;
      const params = new URLSearchParams(hash.replace('#', ''));
      const sessionId = params.get('session_id');

      if (sessionId) {
        try {
          const user = await processGoogleSession(sessionId);
          
          // Check if user has completed onboarding
          try {
            const onboardingRes = await axios.get(`${API}/user/onboarding-status`, {
              headers: getAuthHeaders(),
              withCredentials: true
            });
            
            if (!onboardingRes.data.onboarding_completed) {
              // New user or hasn't completed onboarding
              navigate('/onboarding', { replace: true });
              return;
            }
          } catch (e) {
            // If error checking onboarding, redirect to onboarding to be safe
            navigate('/onboarding', { replace: true });
            return;
          }
          
          // Navigate to dashboard with user data
          navigate('/dashboard', { state: { user }, replace: true });
        } catch (error) {
          console.error('Auth callback error:', error);
          navigate('/login', { replace: true });
        }
      } else {
        navigate('/login', { replace: true });
      }
    };

    processSession();
  }, [location, processGoogleSession, navigate, getAuthHeaders]);

  return (
    <div className="min-h-screen flex items-center justify-center" data-testid="auth-callback">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-[#6B6661]">A processar autenticação...</p>
      </div>
    </div>
  );
};

export default AuthCallback;
