import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Heart, Share2, Copy, Check, CreditCard, Smartphone, Bitcoin, ExternalLink } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const amounts = [
  { key: '5', value: 5, tickets: 1 },
  { key: '10', value: 10, tickets: 2 },
  { key: '20', value: 20, tickets: 4 },
  { key: '50', value: 50, tickets: 10 },
  { key: '100', value: 100, tickets: 20 },
  { key: '200', value: 200, tickets: 40 },
  { key: '500', value: 500, tickets: 100 },
  { key: '1000', value: 1000, tickets: 200 }
];

const paymentMethods = [
  { id: 'stripe', name: 'Cartão', icon: CreditCard, description: 'Visa, Mastercard, etc.' },
  { id: 'mbway', name: 'MBWay', icon: Smartphone, description: 'Pagamento móvel' },
  { id: 'paypal', name: 'PayPal', icon: ExternalLink, description: 'paypal.me/LuisCanarias' },
  { id: 'crypto', name: 'Crypto', icon: Bitcoin, description: 'USDT (TRC20) - Bilhetes em dobro!' }
];

const JourneyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const { user, getAuthHeaders } = useAuth();
  
  const [journey, setJourney] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPayment, setShowPayment] = useState(false);
  const [selectedAmount, setSelectedAmount] = useState(null);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [copied, setCopied] = useState(false);
  const [processing, setProcessing] = useState(false);
  
  const sponsorCode = searchParams.get('sponsor');

  useEffect(() => {
    const fetchJourney = async () => {
      try {
        const response = await axios.get(`${API}/journeys/${id}`);
        setJourney(response.data);
      } catch (error) {
        console.error('Error fetching journey:', error);
        navigate('/');
      } finally {
        setLoading(false);
      }
    };

    const fetchPaymentInfo = async () => {
      try {
        const response = await axios.get(`${API}/payment-info`);
        setPaymentInfo(response.data);
      } catch (error) {
        console.error('Error fetching payment info:', error);
      }
    };

    fetchJourney();
    fetchPaymentInfo();
  }, [id, navigate]);

  const handleSupport = () => {
    setShowPayment(true);
  };

  const handlePayment = async () => {
    if (!selectedAmount || !selectedMethod) return;
    
    setProcessing(true);
    
    try {
      if (selectedMethod === 'stripe') {
        const response = await axios.post(`${API}/contributions/create-checkout`, {
          amount_key: selectedAmount.key,
          journey_id: id,
          origin_url: window.location.origin,
          sponsor_code: sponsorCode
        }, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        
        window.location.href = response.data.url;
      } else {
        // Manual payment - show instructions
        setSelectedMethod(selectedMethod);
      }
    } catch (error) {
      console.error('Payment error:', error);
      alert('Erro ao processar pagamento. Tente novamente.');
    } finally {
      setProcessing(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const progress = journey ? Math.min((journey.current_amount / journey.goal_amount) * 100, 100) : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!journey) return null;

  return (
    <div className="min-h-screen pt-20" data-testid="journey-detail">
      {/* Hero Image */}
      <div className="relative h-[50vh] md:h-[60vh]">
        <img
          src={journey.image_url}
          alt={journey.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
        
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          className="absolute top-6 left-6 flex items-center gap-2 text-white/90 hover:text-white transition-colors"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>{t('payment.back')}</span>
        </button>

        {/* Title */}
        <div className="absolute bottom-0 left-0 right-0 p-8 md:p-12">
          <div className="max-w-4xl mx-auto">
            <span className="text-white/80 font-handwritten text-2xl">
              {journey.poetic_name}
            </span>
            <h1 className="text-4xl md:text-6xl font-bold text-white mt-2">
              {journey.name}
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 md:px-12 py-12">
        {/* Progress Bar */}
        <div className="bg-white rounded-3xl p-8 shadow-lg -mt-16 relative z-10 mb-8">
          <div className="h-4 bg-stone-100 rounded-full overflow-hidden mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 1.5, ease: 'easeOut' }}
              className="h-full progress-bar-warm rounded-full"
            />
          </div>
          <p className="text-center text-2xl font-bold text-[#2D2A26]">
            {Math.round(progress)}% {t('journeys.progress')}
          </p>
        </div>

        {/* Content */}
        <div className="grid md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-8">
            {/* Dream */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#E6F4F1]/50 rounded-3xl p-8"
            >
              <h2 className="text-xl font-bold mb-4 text-[#2D2A26]">{t('journey.dream')}</h2>
              <p className="text-[#6B6661] text-lg leading-relaxed font-handwritten text-2xl">
                "{journey.emotional_message}"
              </p>
            </motion.div>

            {/* Impact */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-3xl p-8 border border-stone-100"
            >
              <h2 className="text-xl font-bold mb-4 text-[#2D2A26]">{t('journey.impact')}</h2>
              <p className="text-[#6B6661] leading-relaxed">
                {journey.impact_description}
              </p>
            </motion.div>

            {/* Description */}
            <div className="prose prose-stone max-w-none">
              <p className="text-[#6B6661] leading-relaxed">
                {journey.description}
              </p>
            </div>
          </div>

          {/* Support Card */}
          <div className="md:col-span-1">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100 sticky top-28"
            >
              <button
                onClick={handleSupport}
                className="w-full btn-primary flex items-center justify-center gap-2 mb-4"
                data-testid="support-btn"
              >
                <Heart className="w-5 h-5" />
                {t('journey.support_btn')}
              </button>
              
              <div className="bg-gradient-to-r from-[#F2C94C]/20 to-[#E0C097]/20 rounded-2xl p-4">
                <p className="text-sm text-[#2D2A26] flex items-start gap-2">
                  <Bitcoin className="w-5 h-5 text-[#F2C94C] flex-shrink-0 mt-0.5" />
                  <span>{t('journey.crypto_bonus')}</span>
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Payment Modal */}
      {showPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-3xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            data-testid="payment-modal"
          >
            <div className="p-6 border-b border-stone-100">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">{t('payment.title')}</h2>
                <button
                  onClick={() => {
                    setShowPayment(false);
                    setSelectedAmount(null);
                    setSelectedMethod(null);
                  }}
                  className="text-[#6B6661] hover:text-[#2D2A26]"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Step 1: Amount */}
              <div>
                <h3 className="font-semibold mb-4">{t('payment.amount')}</h3>
                <div className="grid grid-cols-4 gap-2">
                  {amounts.map((amt) => (
                    <button
                      key={amt.key}
                      onClick={() => setSelectedAmount(amt)}
                      className={`p-3 rounded-xl border-2 transition-all ${
                        selectedAmount?.key === amt.key
                          ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                          : 'border-stone-200 hover:border-stone-300'
                      }`}
                      data-testid={`amount-${amt.key}`}
                    >
                      <span className="font-semibold">€{amt.value}</span>
                      <span className="text-xs text-[#6B6661] block">
                        {amt.tickets} {t('payment.tickets')}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Step 2: Method */}
              {selectedAmount && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <h3 className="font-semibold mb-4">{t('payment.method')}</h3>
                  <div className="space-y-2">
                    {paymentMethods.map((method) => {
                      const Icon = method.icon;
                      const isCrypto = method.id === 'crypto';
                      return (
                        <button
                          key={method.id}
                          onClick={() => setSelectedMethod(method.id)}
                          className={`w-full p-4 rounded-xl border-2 transition-all flex items-center gap-4 ${
                            selectedMethod === method.id
                              ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                              : isCrypto
                              ? 'border-[#F2C94C]/50 bg-[#F2C94C]/5 hover:border-[#F2C94C]'
                              : 'border-stone-200 hover:border-stone-300'
                          }`}
                          data-testid={`method-${method.id}`}
                        >
                          <Icon className={`w-6 h-6 ${isCrypto ? 'text-[#F2C94C]' : 'text-[#6B6661]'}`} />
                          <div className="text-left">
                            <span className="font-medium block">{method.name}</span>
                            <span className={`text-xs ${isCrypto ? 'text-[#F2C94C]' : 'text-[#6B6661]'}`}>
                              {method.description}
                            </span>
                          </div>
                          {isCrypto && (
                            <span className="ml-auto text-xs bg-[#F2C94C] text-white px-2 py-1 rounded-full">
                              2x
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </motion.div>
              )}

              {/* Payment Details */}
              {selectedAmount && selectedMethod && selectedMethod !== 'stripe' && paymentInfo && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-stone-50 rounded-2xl p-4"
                >
                  {selectedMethod === 'mbway' && (
                    <div className="text-center">
                      <p className="text-sm text-[#6B6661] mb-2">Envie para:</p>
                      <p className="text-2xl font-bold text-[#2D2A26]">{paymentInfo.mbway.phone}</p>
                      <p className="text-sm text-[#6B6661] mt-1">Nome: {paymentInfo.mbway.name}</p>
                      <button
                        onClick={() => copyToClipboard(paymentInfo.mbway.phone)}
                        className="mt-4 flex items-center gap-2 mx-auto text-[#FFBE98]"
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        {copied ? 'Copiado!' : 'Copiar número'}
                      </button>
                    </div>
                  )}

                  {selectedMethod === 'paypal' && (
                    <div className="text-center">
                      <p className="text-sm text-[#6B6661] mb-4">Clique para abrir PayPal:</p>
                      <a
                        href={`https://${paymentInfo.paypal.link}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-primary inline-flex items-center gap-2"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Abrir PayPal
                      </a>
                    </div>
                  )}

                  {selectedMethod === 'crypto' && (
                    <div className="text-center">
                      <div className="bg-white p-4 rounded-xl inline-block mb-4">
                        <QRCodeSVG value={paymentInfo.crypto.address} size={150} />
                      </div>
                      <p className="text-sm text-[#6B6661] mb-2">
                        {paymentInfo.crypto.currency} ({paymentInfo.crypto.network})
                      </p>
                      <p className="text-xs font-mono bg-stone-100 p-2 rounded break-all">
                        {paymentInfo.crypto.address}
                      </p>
                      <button
                        onClick={() => copyToClipboard(paymentInfo.crypto.address)}
                        className="mt-4 flex items-center gap-2 mx-auto text-[#FFBE98]"
                      >
                        {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                        {copied ? 'Copiado!' : 'Copiar endereço'}
                      </button>
                      <p className="mt-4 text-xs text-red-500 bg-red-50 p-3 rounded-xl">
                        ⚠️ {paymentInfo.crypto.warning}
                      </p>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Continue Button */}
              {selectedAmount && selectedMethod && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {selectedMethod === 'stripe' ? (
                    <button
                      onClick={handlePayment}
                      disabled={processing}
                      className="w-full btn-primary flex items-center justify-center gap-2"
                      data-testid="continue-payment-btn"
                    >
                      {processing ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <>
                          <CreditCard className="w-5 h-5" />
                          {t('payment.continue')} - €{selectedAmount.value}
                        </>
                      )}
                    </button>
                  ) : (
                    <p className="text-center text-sm text-[#6B6661]">
                      Após o pagamento, entre em contacto para confirmar a sua contribuição.
                    </p>
                  )}
                </motion.div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default JourneyDetail;
