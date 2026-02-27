import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, Share2, Home, Copy, Check } from 'lucide-react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const { getAuthHeaders } = useAuth();
  
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [copied, setCopied] = useState(false);
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    const checkPayment = async () => {
      if (!sessionId) {
        setPaymentStatus('error');
        return;
      }

      const maxAttempts = 5;
      const pollInterval = 2000;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
          const response = await axios.get(`${API}/contributions/checkout-status/${sessionId}`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });

          if (response.data.payment_status === 'paid') {
            setPaymentStatus('success');
            return;
          } else if (response.data.status === 'expired') {
            setPaymentStatus('error');
            return;
          }
        } catch (error) {
          console.error('Error checking payment:', error);
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }

      setPaymentStatus('success'); // Assume success after polling
    };

    checkPayment();
  }, [sessionId, getAuthHeaders]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(window.location.origin);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (paymentStatus === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center dream-mesh pt-20">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#6B6661]">A verificar pagamento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center dream-mesh pt-20 px-6" data-testid="payment-success">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full bg-white rounded-3xl p-8 shadow-xl text-center"
      >
        {paymentStatus === 'success' ? (
          <>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.2 }}
              className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
            >
              <CheckCircle className="w-10 h-10 text-green-500" />
            </motion.div>

            <h1 className="text-3xl font-bold text-[#2D2A26] mb-4">
              {t('success.title')}
            </h1>

            <p className="text-[#6B6661] mb-6 font-handwritten text-xl">
              "{t('success.message')}"
            </p>

            <div className="bg-[#E6F4F1]/50 rounded-2xl p-4 mb-6">
              <p className="text-sm text-[#2D2A26]">
                {t('success.sponsor_note')}
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <button
                onClick={copyToClipboard}
                className="btn-primary flex items-center justify-center gap-2"
                data-testid="share-btn"
              >
                {copied ? (
                  <><Check className="w-5 h-5" /> Copiado!</>
                ) : (
                  <><Share2 className="w-5 h-5" /> {t('success.share')}</>
                )}
              </button>

              <Link
                to="/"
                className="btn-secondary flex items-center justify-center gap-2"
              >
                <Home className="w-5 h-5" />
                {t('nav.home')}
              </Link>
            </div>
          </>
        ) : (
          <>
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">!</span>
            </div>
            <h1 className="text-2xl font-bold text-[#2D2A26] mb-4">
              Algo correu mal
            </h1>
            <p className="text-[#6B6661] mb-6">
              Não foi possível confirmar o pagamento. Por favor, entre em contacto.
            </p>
            <Link to="/" className="btn-primary inline-block">
              Voltar ao Início
            </Link>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default PaymentSuccess;
