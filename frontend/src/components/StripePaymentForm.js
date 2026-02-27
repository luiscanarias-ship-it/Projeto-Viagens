import React, { useState, useEffect, useRef } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { CreditCard, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Inner form component that uses Stripe hooks
const CheckoutForm = ({ amount, onSuccess, onError }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setProcessing(true);
    setErrorMessage(null);

    try {
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/payment-success`,
        },
        redirect: 'if_required',
      });

      if (error) {
        setErrorMessage(error.message);
        onError?.(error.message);
      } else if (paymentIntent && paymentIntent.status === 'succeeded') {
        onSuccess?.(paymentIntent);
      } else if (paymentIntent && paymentIntent.status === 'requires_action') {
        setErrorMessage('Autenticação adicional necessária. Por favor complete a verificação.');
      }
    } catch (err) {
      setErrorMessage('Erro ao processar pagamento. Tente novamente.');
      onError?.(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="bg-white rounded-xl p-4 border border-stone-200">
        <PaymentElement 
          options={{
            layout: 'tabs',
            paymentMethodOrder: ['card'],
          }}
        />
      </div>

      {errorMessage && (
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-xl text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || processing}
        className="w-full bg-[#FFBE98] text-[#2D2A26] py-4 px-6 rounded-xl font-bold hover:bg-[#FFAB7D] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        data-testid="stripe-pay-btn"
      >
        {processing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            A processar...
          </>
        ) : (
          <>
            <CreditCard className="w-5 h-5" />
            Pagar €{amount}
          </>
        )}
      </button>

      <p className="text-xs text-center text-[#6B6661]">
        Pagamento seguro processado pelo Stripe
      </p>
    </form>
  );
};

// Main component that wraps with Elements provider
const StripePaymentForm = ({ 
  amount, 
  journeyId, 
  sponsorCode, 
  contributorName,
  contributorEmail,
  publicMessage,
  showName,
  onSuccess, 
  onError,
  onCancel,
  getAuthHeaders 
}) => {
  const [clientSecret, setClientSecret] = useState(null);
  const [contributionId, setContributionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stripePromise, setStripePromise] = useState(null);
  const initialized = useRef(false);

  useEffect(() => {
    // Prevent double initialization
    if (initialized.current) return;
    initialized.current = true;

    const initializePayment = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get Stripe publishable key and load Stripe
        const configResponse = await axios.get(`${API}/stripe/config`);
        const { publishable_key } = configResponse.data;
        
        if (!publishable_key) {
          throw new Error('Stripe não está configurado');
        }
        
        const stripe = loadStripe(publishable_key);
        setStripePromise(stripe);

        // Create PaymentIntent via backend
        const response = await axios.post(
          `${API}/contributions/create`,
          {
            amount: amount,
            payment_method: 'stripe',
            journey_id: journeyId,
            sponsor_code: sponsorCode || null,
            contributor_name: contributorName || null,
            contributor_email: contributorEmail || null,
            public_message: publicMessage || null,
            show_name: showName
          },
          {
            headers: getAuthHeaders?.() || {},
            withCredentials: true
          }
        );

        if (response.data.client_secret) {
          setClientSecret(response.data.client_secret);
          setContributionId(response.data.contribution_id);
          // Scroll modal to show pay button after Stripe form renders
          setTimeout(() => {
            const modal = document.querySelector('[data-testid="payment-modal"]');
            if (modal) {
              modal.scrollTo({ top: modal.scrollHeight, behavior: 'smooth' });
            }
          }, 1000);
        } else {
          throw new Error('Erro ao criar sessão de pagamento');
        }
      } catch (err) {
        console.error('Payment initialization error:', err);
        setError(err.response?.data?.detail || err.message || 'Erro ao inicializar pagamento');
      } finally {
        setLoading(false);
      }
    };

    if (amount && journeyId) {
      initializePayment();
    }
  }, []); // Empty dependency array - only run once

  const handleSuccess = (paymentIntent) => {
    onSuccess?.({
      paymentIntentId: paymentIntent.id,
      contributionId: contributionId,
      status: paymentIntent.status
    });
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-8 space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-[#FFBE98]" />
        <p className="text-sm text-[#6B6661]">A preparar pagamento...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 p-4 bg-red-50 text-red-700 rounded-xl">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
        <button
          onClick={onCancel}
          className="w-full py-3 px-6 border border-stone-300 rounded-xl text-[#6B6661] hover:bg-stone-50 transition-colors"
        >
          Voltar
        </button>
      </div>
    );
  }

  if (!clientSecret || !stripePromise) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-[#FFBE98] mr-2" />
        <p className="text-sm text-[#6B6661]">A carregar formulário de pagamento...</p>
      </div>
    );
  }

  const appearance = {
    theme: 'stripe',
    variables: {
      colorPrimary: '#FFBE98',
      colorBackground: '#ffffff',
      colorText: '#2D2A26',
      colorDanger: '#ef4444',
      fontFamily: 'system-ui, sans-serif',
      borderRadius: '12px',
      spacingUnit: '4px',
    },
    rules: {
      '.Input': {
        border: '1px solid #e7e5e4',
        boxShadow: 'none',
        padding: '12px',
      },
      '.Input:focus': {
        border: '1px solid #FFBE98',
        boxShadow: '0 0 0 1px #FFBE98',
      },
      '.Label': {
        fontWeight: '500',
        color: '#2D2A26',
      },
    },
  };

  return (
    <Elements 
      stripe={stripePromise} 
      options={{ 
        clientSecret,
        appearance,
        locale: 'pt'
      }}
    >
      <CheckoutForm 
        amount={amount} 
        onSuccess={handleSuccess}
        onError={onError}
      />
    </Elements>
  );
};

export default StripePaymentForm;
