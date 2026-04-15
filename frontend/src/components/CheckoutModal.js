import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Check, Copy, Bitcoin, Smartphone, CreditCard,
  Wallet, ArrowRight, Heart, Sparkles, ShieldCheck, Lock, Globe, MapPin,
  ChevronDown, Users, Flame, Award, Mail, Gift
} from 'lucide-react';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';
import QRCode from 'qrcode';
import axios from 'axios';
import ShareMenu, { buildInviteLink } from './ShareMenu';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fixed contribution amounts
const amounts = [10, 20, 50, 100, 200, 500, 1000];

// Platform tip options
const tipOptions = [
  { value: 2, label: '2€', default: true },
  { value: 5, label: '5€', default: false },
  { value: 10, label: '10€', default: false },
  { value: 0, label: 'Não quero contribuir', default: false }
];

// ========== TIP SYSTEM TOGGLE ==========
// Set to true to reactivate the voluntary tip system
// All code, backend endpoints and admin dashboard are preserved
const TIP_SYSTEM_ENABLED = false;
// ========================================

// IfthenPay configuration — replace keys when available
const IFTHENPAY_CONFIG = {
  mbway: {
    enabled: false, // Set to true when keys are configured
    key: 'IFTHENPAY_MBWAY_KEY_HERE',
  },
  multibanco: {
    enabled: false, // Set to true when keys are configured
    entity: 'IFTHENPAY_ENTITY_HERE',
    subEntity: 'IFTHENPAY_SUBENTITY_HERE',
  }
};

// Geolocation cache
let geoCache = null;
const detectUserCountry = async () => {
  if (geoCache) return geoCache;
  try {
    const res = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(3000) });
    const data = await res.json();
    geoCache = data.country_code || 'UNKNOWN';
    return geoCache;
  } catch {
    geoCache = 'UNKNOWN';
    return geoCache;
  }
};

// Crypto configurations with addresses
const cryptoConfig = {
  btc: {
    id: 'btc',
    name: 'Bitcoin',
    symbol: 'BTC',
    color: '#F7931A',
    address: 'bc1qw34att4qwerdapfpzy3e98xz894uy7kz3sd7vm',
    network: 'Bitcoin',
    protocol: 'bitcoin',
    coingeckoId: 'bitcoin'
  },
  eth: {
    id: 'eth',
    name: 'Ethereum',
    symbol: 'ETH',
    color: '#627EEA',
    address: '0x48dF0E85dA06688445f3eEabaBE9DF57bA10A991',
    network: 'ERC20',
    protocol: 'ethereum',
    coingeckoId: 'ethereum'
  },
  usdt: {
    id: 'usdt',
    name: 'Tether',
    symbol: 'USDT',
    color: '#26A17B',
    address: 'TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL',
    network: 'TRC20',
    protocol: 'tron',
    coingeckoId: 'tether'
  },
  usdc: {
    id: 'usdc',
    name: 'USD Coin',
    symbol: 'USDC',
    color: '#2775CA',
    address: 'xdc48dF0E85dA06688445f3eEabaBE9DF57bA10A991',
    network: 'XDC Network',
    protocol: 'xdc',
    coingeckoId: 'usd-coin'
  }
};

// Manual MBWay config (direct transfer — used while IfthenPay is not active)
const MBWAY_MANUAL = {
  phone: '+351 968 068 535',
  phoneClean: '351968068535'
};

const CheckoutModal = ({ 
  isOpen, 
  onClose, 
  journeyName = 'China',
  journeyId,
  contributionDescriptions,
  getAuthHeaders,
  user,
  progressData
}) => {
  // Checkout state
  const [step, setStep] = useState(1);
  const [selectedAmount, setSelectedAmount] = useState(10);
  const [selectedTip, setSelectedTip] = useState(TIP_SYSTEM_ENABLED ? 2 : 0); // Tip disabled: default 0
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [selectedCrypto, setSelectedCrypto] = useState(null);
  const [contribution, setContribution] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copiedField, setCopiedField] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [cryptoPrices, setCryptoPrices] = useState({});
  const [loadingPrices, setLoadingPrices] = useState(false);
  const cryptoSectionRef = useRef(null);

  // Calculate total payment
  const totalPayment = selectedAmount + selectedTip;

  // QR code states
  const [cryptoAmountCalc, setCryptoAmountCalc] = useState(null);
  const [cryptoURI, setCryptoURI] = useState(null);
  const [qrImageUrl, setQrImageUrl] = useState(null);
  const [nonCryptoQrUrl, setNonCryptoQrUrl] = useState(null);

  // PayPal state
  const [paypalClientId, setPaypalClientId] = useState(null);
  const [paypalProcessing, setPaypalProcessing] = useState(false);
  const [paypalError, setPaypalError] = useState(null);

  // Geolocation state
  const [userCountry, setUserCountry] = useState(null);
  const isPortugal = userCountry === 'PT';

  // MBWay details toggle
  const [showMbwayDetails, setShowMbwayDetails] = useState(false);

  // Step 3 confirmation form
  const [showConfirmForm, setShowConfirmForm] = useState(false);
  const [confirmName, setConfirmName] = useState(user?.name || '');
  const [confirmEmail, setConfirmEmail] = useState(user?.email || '');
  const [confirmingPayment, setConfirmingPayment] = useState(false);

  // Fetch crypto prices from CoinGecko
  const fetchCryptoPrices = useCallback(async () => {
    setLoadingPrices(true);
    try {
      const ids = Object.values(cryptoConfig).map(c => c.coingeckoId).join(',');
      const response = await axios.get(
        `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=eur`
      );
      setCryptoPrices(response.data);
    } catch (error) {
      console.error('Error fetching crypto prices:', error);
      // Fallback prices if API fails
      setCryptoPrices({
        bitcoin: { eur: 85000 },
        ethereum: { eur: 3200 },
        tether: { eur: 0.92 },
        'usd-coin': { eur: 0.92 }
      });
    } finally {
      setLoadingPrices(false);
    }
  }, []);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setStep(1);
      setSelectedAmount(10);
      setSelectedTip(TIP_SYSTEM_ENABLED ? 2 : 0); // Reset tip based on toggle
      setSelectedMethod(null);
      setSelectedCrypto(null);
      setContribution(null);
      setShowConfirmation(false);
      setCopied(false);
      setCopiedField(null);
      setCryptoAmountCalc(null);
      setCryptoURI(null);
      setQrImageUrl(null);
      setNonCryptoQrUrl(null);
      setPaypalProcessing(false);
      setPaypalError(null);
    } else {
      // Fetch crypto prices when modal opens
      fetchCryptoPrices();
      // Fetch PayPal config
      axios.get(`${API}/paypal/config`).then(res => {
        setPaypalClientId(res.data.client_id);
      }).catch(() => {});
      // Detect user country for smart payment prioritization
      detectUserCountry().then(code => setUserCountry(code));
    }
  }, [isOpen, fetchCryptoPrices]);

  // Calculate crypto amount from EUR (for display in step 2 crypto selection)
  const getCryptoAmount = (euroAmount, cryptoId) => {
    const crypto = cryptoConfig[cryptoId];
    if (!crypto || !cryptoPrices[crypto.coingeckoId]) return null;
    
    const priceInEur = cryptoPrices[crypto.coingeckoId].eur;
    const amount = euroAmount / priceInEur;
    
    if (cryptoId === 'btc') return amount.toFixed(8);
    if (cryptoId === 'eth') return amount.toFixed(8);
    return amount.toFixed(2);
  };

  // Generate blockchain URI for crypto QR code (per user snippet)
  function generateCryptoURI(symbol, address, eurAmount) {
    const map = { BTC: "bitcoin", ETH: "ethereum", USDT: "tether", USDC: "usd-coin" };
    const coingeckoId = map[symbol];
    
    // Use already-fetched prices from cryptoPrices state
    const priceData = cryptoPrices[coingeckoId];
    if (!priceData) {
      console.error('No price data for', symbol);
      // Fallback: just use address
      const crypto = cryptoConfig[symbol.toLowerCase()];
      setCryptoURI(`${crypto?.protocol || ''}:${address}`);
      return;
    }
    
    const price = priceData.eur;
    const amount = eurAmount / price;

    let uri = "";
    if (symbol === "BTC") {
      uri = `bitcoin:${address}?amount=${amount.toFixed(8)}`;
    }
    if (symbol === "ETH") {
      uri = `ethereum:${address}?amount=${amount.toFixed(8)}`;
    }
    if (symbol === "USDT") {
      uri = `tron:${address}`;
    }
    if (symbol === "USDC") {
      uri = `xdc:${address}`;
    }

    console.log('Generated crypto URI:', uri);
    setCryptoAmountCalc(symbol === "USDT" || symbol === "USDC" ? eurAmount.toFixed(2) : amount.toFixed(8));
    setCryptoURI(uri);
  }

  // Generate QR image when cryptoURI changes
  useEffect(() => {
    if (!cryptoURI) return;
    QRCode.toDataURL(cryptoURI, {
      width: 200,
      margin: 2,
      errorCorrectionLevel: 'M'
    })
    .then(url => {
      console.log('QR generated for URI:', cryptoURI);
      setQrImageUrl(url);
    })
    .catch(err => console.error('QR generation error:', err));
  }, [cryptoURI]);

  // Trigger crypto URI generation when entering step 3 with crypto (per user snippet)
  useEffect(() => {
    if (step === 3 && selectedMethod === 'crypto' && selectedCrypto && Object.keys(cryptoPrices).length > 0) {
      const crypto = cryptoConfig[selectedCrypto];
      if (crypto) {
        // Use totalPayment to include tip in crypto payment
        generateCryptoURI(crypto.symbol, crypto.address, totalPayment);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, selectedMethod, selectedCrypto, totalPayment, cryptoPrices]);

  // Generate QR for non-crypto payment methods
  useEffect(() => {
    if (step === 3 && selectedMethod && selectedMethod !== 'crypto') {
      const qrValue = getPaymentQRValue(selectedMethod);
      if (qrValue) {
        QRCode.toDataURL(qrValue, { width: 200, margin: 2 })
          .then(url => setNonCryptoQrUrl(url))
          .catch(err => console.error('Non-crypto QR error:', err));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, selectedMethod]);

  // Generate QR code value for payment methods
  const getPaymentQRValue = (methodId) => {
    switch (methodId) {
      case 'mbway':
        return `tel:${MBWAY_MANUAL.phoneClean}`;
      default:
        return '';
    }
  };

  // PayPal handlers (shared between Portugal/International views)
  const createPayPalOrder = async () => {
    setPaypalProcessing(true);
    setPaypalError(null);
    try {
      const res = await axios.post(`${API}/paypal/create-order`, {
        support_amount: selectedAmount,
        tip_amount: selectedTip,
        amount: totalPayment, // For backward compatibility
        journey_id: journeyId,
        contributor_name: user?.name || null,
        contributor_email: user?.email || null
      }, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      });
      return res.data.paypal_order_id;
    } catch (err) {
      setPaypalError(err.response?.data?.detail || 'Erro ao criar ordem PayPal');
      setPaypalProcessing(false);
      throw err;
    }
  };

  const onPayPalApprove = async (data) => {
    try {
      const res = await axios.post(`${API}/paypal/capture-order/${data.orderID}`, {}, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      });
      setContribution(res.data);
      setShowConfirmation(true);
    } catch (err) {
      setPaypalError(err.response?.data?.detail || 'Erro ao capturar pagamento');
    } finally {
      setPaypalProcessing(false);
    }
  };

  const onPayPalError = () => {
    setPaypalError('Erro no pagamento PayPal. Tente novamente.');
    setPaypalProcessing(false);
  };

  // Create contribution
  const createContribution = async (method, cryptoType = null) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/contributions/create`, {
        support_amount: selectedAmount,
        tip_amount: selectedTip,
        amount: totalPayment, // For backward compatibility
        payment_method: method,
        journey_id: journeyId,
        crypto_type: cryptoType,
        contributor_name: user?.name || null,
        contributor_email: user?.email || null
      }, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      });
      
      setContribution(response.data);
      return response.data;
    } catch (error) {
      console.error('Error creating contribution:', error);
      alert(error.response?.data?.detail || 'Erro ao registar contribuição');
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Handle method selection
  const handleMethodSelect = async (methodId) => {
    setSelectedMethod(methodId);
    
    if (methodId === 'crypto') {
      // Don't advance yet, need to select crypto type
      return;
    }
    
    // Create contribution and go to step 3
    const contrib = await createContribution(methodId);
    if (contrib) {
      setStep(3);
    }
  };

  // Handle crypto selection
  const handleCryptoSelect = async (cryptoId) => {
    setSelectedCrypto(cryptoId);
    
    // Create contribution immediately for crypto (to avoid losing payments)
    const contrib = await createContribution('crypto', cryptoId);
    if (contrib) {
      setStep(3);
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text, field = null) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setCopiedField(field);
    setTimeout(() => {
      setCopied(false);
      setCopiedField(null);
    }, 2000);
  };

  // Handle close
  const handleClose = () => {
    onClose();
  };

  // Handle payment confirmation with user details
  const handleConfirmPayment = async () => {
    if (!confirmEmail) return;
    setConfirmingPayment(true);
    try {
      await axios.put(`${API}/contributions/${contribution.contribution_id}/confirm-details`, {
        contributor_name: confirmName || null,
        contributor_email: confirmEmail
      });
      setShowConfirmation(true);
      setShowConfirmForm(false);
    } catch (error) {
      console.error('Error confirming:', error);
      setShowConfirmation(true);
      setShowConfirmForm(false);
    } finally {
      setConfirmingPayment(false);
    }
  };

  // Method display label
  const getMethodLabel = (method) => {
    if (method === 'mbway') return 'MB WAY';
    if (method === 'crypto') return `Crypto (${selectedCrypto?.toUpperCase() || 'BTC'})`;
    if (method === 'paypal') return 'PayPal';
    return method;
  };

  // Go back to step 1
  const goToStep1 = () => {
    setStep(1);
    setSelectedMethod(null);
    setSelectedCrypto(null);
    setContribution(null);
  };

  // Go back to step 2
  const goToStep2 = () => {
    setStep(2);
    setContribution(null);
    setCryptoAmountCalc(null);
    setCryptoURI(null);
    setQrImageUrl(null);
    setNonCryptoQrUrl(null);
  };

  if (!isOpen) return null;

  const cryptoData = selectedCrypto ? cryptoConfig[selectedCrypto] : null;
  const methodData = null; // Legacy — MBWay uses MBWAY_MANUAL directly

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-hidden shadow-2xl flex flex-col"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-[#FFBE98]/20 to-[#E6F4F1]/30 px-4 py-3 border-b border-stone-100">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="font-bold text-[#2D2A26] text-sm">Ajuda a realizar este sonho</h2>
                <p className="text-xs text-[#6B6661]">Destino: {journeyName}</p>
              </div>
              <button
                onClick={() => {
                  if (showConfirmForm) {
                    // From confirm form → back to payment instructions
                    setShowConfirmForm(false);
                  } else if (step === 3) {
                    goToStep2();
                  } else if (step === 2) {
                    goToStep1();
                  } else {
                    handleClose();
                  }
                }}
                className="p-2 hover:bg-stone-100 rounded-full transition-colors"
              >
                {(step > 1 || showConfirmForm) && !showConfirmation ? (
                  <ArrowRight className="w-5 h-5 text-[#6B6661] rotate-180" />
                ) : (
                  <X className="w-5 h-5 text-[#6B6661]" />
                )}
              </button>
            </div>
            
            {/* Progress bar */}
            {!showConfirmation && (
              <div className="flex items-center gap-2">
                {[
                  { num: 1, label: 'Valor' },
                  { num: 2, label: 'Pagamento' },
                  { num: 3, label: 'Instruções' }
                ].map((s, idx) => (
                  <React.Fragment key={s.num}>
                    <div className="flex items-center gap-1.5">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                        step >= s.num 
                          ? 'bg-[#FFBE98] text-white' 
                          : 'bg-stone-200 text-[#6B6661]'
                      }`}>
                        {step > s.num ? <Check className="w-3.5 h-3.5" /> : s.num}
                      </div>
                      <span className={`text-xs ${step >= s.num ? 'text-[#2D2A26] font-medium' : 'text-[#6B6661]'}`}>
                        {s.label}
                      </span>
                    </div>
                    {idx < 2 && (
                      <div className={`flex-1 h-0.5 ${step > s.num ? 'bg-[#FFBE98]' : 'bg-stone-200'}`} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>

          {/* Content */}
          <div className="px-4 py-3 overflow-y-auto flex-1 min-h-0">
            <AnimatePresence mode="wait">
              
              {/* STEP 1: Choose Amount */}
              {step === 1 && !showConfirmation && (
                <motion.div
                  key="step1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-4"
                >
                  <p className="text-sm text-[#6B6661]">Quanto queres contribuir?</p>
                  
                  <div className="grid grid-cols-3 gap-1.5">
                    {amounts.map((amt) => (
                      <button
                        key={amt}
                        onClick={() => setSelectedAmount(amt)}
                        data-testid={`amount-btn-${amt}`}
                        className={`py-2 px-2.5 rounded-xl font-semibold transition-all text-center relative ${
                          selectedAmount === amt
                            ? 'bg-[#FFBE98] text-white shadow-md ring-2 ring-[#FFBE98]/30'
                            : amt === 20
                              ? 'bg-[#FFBE98]/15 text-[#2D2A26] hover:bg-[#FFBE98]/25 ring-2 ring-[#FFBE98]/50 shadow-sm'
                              : 'bg-stone-100 text-[#2D2A26] hover:bg-stone-200'
                        }`}
                      >
                        <span className="text-base font-bold">€{amt}</span>
                        {selectedAmount === amt && (
                          <Check className="w-3.5 h-3.5 absolute top-1.5 right-1.5" />
                        )}
                        {amt === 20 && selectedAmount !== amt && (
                          <div className="mt-0.5">
                            <span 
                              className="text-[9px] font-bold text-white bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] px-1.5 py-0.5 rounded-full inline-flex items-center gap-0.5 animate-pulse shadow-sm"
                              data-testid="most-popular-badge"
                              style={{ animationDuration: '2.5s' }}
                            >
                              <Sparkles className="w-2.5 h-2.5" />
                              Popular
                            </span>
                          </div>
                        )}
                      </button>
                    ))}
                  </div>

                  {selectedAmount && contributionDescriptions?.[String(selectedAmount)] && (
                    <p className="text-center text-xs text-[#6B6661] italic" data-testid="impact-message">
                      {contributionDescriptions[String(selectedAmount)]}
                    </p>
                  )}

                  {/* Platform Tip Section - controlled by TIP_SYSTEM_ENABLED flag */}
                  {TIP_SYSTEM_ENABLED && (
                  <div className="mt-4 pt-4 border-t border-stone-100" data-testid="tip-section">
                    <div className="flex items-center gap-2 mb-2">
                      <Gift className="w-4 h-4 text-[#FFBE98]" />
                      <p className="text-sm font-semibold text-[#2D2A26]">Ajuda-nos a manter esta plataforma gratuita para todos</p>
                    </div>
                    <p className="text-xs text-[#6B6661] mb-3">Sem esta contribuição, não conseguiríamos operar.</p>
                    
                    <div className="flex flex-wrap gap-2">
                      {tipOptions.map((tip) => (
                        <button
                          key={tip.value}
                          onClick={() => setSelectedTip(tip.value)}
                          data-testid={`tip-btn-${tip.value}`}
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                            selectedTip === tip.value
                              ? 'bg-[#FFBE98] text-white shadow-sm'
                              : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'
                          } ${tip.value === 0 ? 'text-xs' : ''}`}
                        >
                          {tip.label}
                          {selectedTip === tip.value && <Check className="w-3 h-3 inline ml-1" />}
                        </button>
                      ))}
                    </div>
                    
                    {/* Microcopy de reforço */}
                    <p className="text-[10px] text-[#6B6661]/70 mt-2" data-testid="tip-microcopy">
                      Contribuição opcional. Podes remover a qualquer momento.
                    </p>
                  </div>
                  )}

                </motion.div>
              )}

              {/* STEP 2: Choose Payment Method */}
              {step === 2 && !showConfirmation && (
                <motion.div
                  key="step2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-3"
                >
                  {/* Title + amount */}
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-[#2D2A26]" data-testid="step2-title">Escolhe como queres apoiar este sonho</p>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="font-bold text-[#2D2A26]">€{totalPayment}</span>
                        {TIP_SYSTEM_ENABLED && selectedTip > 0 && (
                          <span className="text-[10px] text-[#6B6661] block">
                            (€{selectedAmount} + €{selectedTip} plataforma)
                          </span>
                        )}
                      </div>
                      <button
                        onClick={goToStep1}
                        className="text-xs text-[#FFBE98] hover:underline"
                      >
                        Alterar
                      </button>
                    </div>
                  </div>

                  {/* Emotional message */}
                  <p className="text-xs text-[#6B6661] text-center -mt-1" data-testid="step2-emotional-msg">
                    Mesmo uma pequena contribuição<br />ajuda este sonho a ganhar forma.
                  </p>

                  {/* ═══ SMART PAYMENT METHODS — Geo-prioritized ═══ */}

                  {/* PRIMARY: Portugal → MBWay + PayPal | International → PayPal */}
                  {isPortugal ? (
                    <>
                      {/* MBWay — primary for Portugal */}
                      <button
                        onClick={() => handleMethodSelect('mbway')}
                        disabled={loading}
                        className={`w-full rounded-xl border-2 overflow-hidden transition-all ${
                          selectedMethod === 'mbway'
                            ? 'border-[#FFBE98] bg-[#FFBE98]/5 shadow-sm'
                            : 'border-[#FFBE98] hover:bg-[#FFBE98]/5'
                        }`}
                        data-testid="mbway-primary-btn"
                      >
                        <div className="px-3 py-2.5 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-[#FFBE98]/20 rounded-lg flex items-center justify-center">
                              <Smartphone className="w-4 h-4 text-[#FFBE98]" />
                            </div>
                            <div className="text-left">
                              <span className="text-sm font-bold text-[#2D2A26] block">MBWay</span>
                              <span className="text-[10px] text-[#6B6661]">Rápido e simples (Portugal)</span>
                            </div>
                          </div>
                          <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <MapPin className="w-3 h-3" /> Portugal
                          </span>
                        </div>
                      </button>
                      {paypalClientId && (
                        <div className="border-2 border-[#FFBE98] rounded-xl overflow-hidden" data-testid="paypal-section">
                          <div className="px-3 py-2 flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <ShieldCheck className="w-4 h-4 text-[#FFBE98]" />
                              <span className="text-[11px] font-bold text-[#2D2A26]">Cartão ou PayPal</span>
                            </div>
                            <span className="text-[10px] text-[#6B6661] flex items-center gap-1">
                              <Lock className="w-3 h-3" /> 100% seguro
                            </span>
                          </div>
                          <p className="px-3 text-[9px] text-[#6B6661] -mt-0.5 mb-1">Pagamento simples e seguro (via PayPal)</p>
                          <div className="px-3 pb-2">
                            {paypalError && (
                              <p className="text-xs text-red-500 mb-2">{paypalError}</p>
                            )}
                            <PayPalScriptProvider options={{ 
                              clientId: paypalClientId, 
                              currency: "EUR",
                              intent: "capture",
                              "enable-funding": "card"
                            }}>
                              <PayPalButtons
                                style={{ layout: "vertical", height: 45, tagline: false, label: "pay", shape: "rect" }}
                                disabled={paypalProcessing}
                                forceReRender={[totalPayment, journeyId, selectedTip]}
                                createOrder={createPayPalOrder}
                                onApprove={onPayPalApprove}
                                onError={onPayPalError}
                                onCancel={() => setPaypalProcessing(false)}
                              />
                            </PayPalScriptProvider>
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <>
                      {/* PayPal + Card — Primary for International */}
                      {paypalClientId && (
                        <div className="border-2 border-[#FFBE98] rounded-xl overflow-hidden" data-testid="paypal-section">
                          <div className="px-3 py-2 flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <ShieldCheck className="w-4 h-4 text-[#FFBE98]" />
                              <span className="text-[11px] font-bold text-[#2D2A26]">Cartão ou PayPal</span>
                            </div>
                            <span className="text-[10px] text-[#6B6661] flex items-center gap-1">
                              <Lock className="w-3 h-3" /> 100% seguro
                            </span>
                          </div>
                          <p className="px-3 text-[9px] text-[#6B6661] -mt-0.5 mb-1">Pagamento simples e seguro (via PayPal)</p>
                          <div className="px-3 pb-2">
                            {paypalError && (
                              <p className="text-xs text-red-500 mb-2">{paypalError}</p>
                            )}
                            <PayPalScriptProvider options={{ 
                              clientId: paypalClientId, 
                              currency: "EUR",
                              intent: "capture",
                              "enable-funding": "card"
                            }}>
                              <PayPalButtons
                                style={{ layout: "vertical", height: 45, tagline: false, label: "pay", shape: "rect" }}
                                disabled={paypalProcessing}
                                forceReRender={[totalPayment, journeyId, selectedTip]}
                                createOrder={createPayPalOrder}
                                onApprove={onPayPalApprove}
                                onError={onPayPalError}
                                onCancel={() => setPaypalProcessing(false)}
                              />
                            </PayPalScriptProvider>
                            <p className="text-[10px] text-center text-[#6B6661]/70 mt-1.5" data-testid="paypal-trust-text">
                              Não partilhamos os teus dados bancários.
                            </p>
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {/* SECONDARY METHODS */}
                  <div className="grid grid-cols-2 gap-1.5">
                    {/* Crypto option */}
                    <button
                      onClick={() => handleMethodSelect('crypto')}
                      disabled={loading}
                      className={`p-2.5 rounded-xl border-2 transition-all text-center ${
                        selectedMethod === 'crypto'
                          ? 'border-[#FFBE98] bg-[#FFBE98]/10 shadow-sm'
                          : 'border-stone-200 hover:border-[#FFBE98]/50 hover:bg-[#FFBE98]/5'
                      }`}
                      data-testid="crypto-method-btn"
                    >
                      <Bitcoin className="w-5 h-5 text-[#F7931A] mx-auto" />
                      <span className="text-xs font-medium block mt-1">Criptomoeda</span>
                      <span className="text-[9px] text-[#6B6661]">Apoio direto e imediato</span>
                    </button>

                    {/* MBWay — secondary for international users */}
                    {!isPortugal && (
                      <button
                        onClick={() => handleMethodSelect('mbway')}
                        disabled={loading}
                        className={`p-2.5 rounded-xl border-2 transition-all text-center ${
                          selectedMethod === 'mbway'
                            ? 'border-[#FFBE98] bg-[#FFBE98]/10 shadow-sm'
                            : 'border-stone-200 hover:border-[#FFBE98]/50 hover:bg-[#FFBE98]/5'
                        }`}
                        data-testid="mbway-secondary-btn"
                      >
                        <Smartphone className="w-5 h-5 text-[#FFBE98] mx-auto" />
                        <span className="text-xs font-medium block mt-1">MBWay</span>
                        <span className="text-[9px] text-[#6B6661]">Rápido e simples (Portugal)</span>
                      </button>
                    )}

                    {/* Multibanco — coming soon (Portugal only) */}
                    {isPortugal && (
                      <div className="p-2.5 rounded-xl border-2 border-stone-200 bg-stone-50/50 text-center opacity-60 cursor-not-allowed" data-testid="multibanco-soon-btn">
                        <CreditCard className="w-5 h-5 text-[#6B6661] mx-auto" />
                        <span className="text-xs font-medium block mt-1">Multibanco</span>
                        <span className="text-[9px] text-[#6B6661]">Em breve</span>
                      </div>
                    )}
                  </div>

                  {/* Terms + trust line */}
                  <p className="text-[11px] text-[#6B6661]/70 text-center mt-2" data-testid="terms-acceptance">
                    Pagamento seguro. Ao continuar, aceitas os{' '}
                    <a
                      href="/terms"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#6B6661] underline hover:text-[#2D2A26] transition-colors"
                      data-testid="terms-link"
                    >
                      Termos e Condições
                    </a>
                  </p>

                  {/* Crypto selection */}
                  {selectedMethod === 'crypto' && (
                    <motion.div
                      ref={cryptoSectionRef}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      onAnimationComplete={() => {
                        cryptoSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
                      }}
                      className="space-y-3 pt-2 border-t border-stone-100"
                    >
                      <p className="text-sm text-[#6B6661]">Escolhe a criptomoeda:</p>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.values(cryptoConfig).map((crypto) => {
                          const cryptoAmount = getCryptoAmount(selectedAmount, crypto.id);
                          return (
                            <button
                              key={crypto.id}
                              onClick={() => handleCryptoSelect(crypto.id)}
                              disabled={loading}
                              className={`p-3 rounded-xl border-2 transition-all ${
                                selectedCrypto === crypto.id
                                  ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                                  : 'border-stone-200 hover:border-stone-300'
                              }`}
                            >
                              <p className="font-bold text-sm" style={{ color: crypto.color }}>
                                {crypto.symbol}
                              </p>
                              <p className="text-[10px] text-[#6B6661]">{crypto.network}</p>
                              {cryptoAmount && !loadingPrices && (
                                <p className="text-xs text-[#6B6661] mt-1">≈ {cryptoAmount}</p>
                              )}
                              {loading && selectedCrypto === crypto.id && (
                                <div className="w-4 h-4 border-2 border-[#FFBE98] border-t-transparent rounded-full animate-spin mx-auto mt-1" />
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              )}

              {/* STEP 3: Payment Instructions & Confirmation */}
              {step === 3 && !showConfirmation && !showConfirmForm && contribution && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-3"
                >
                  {/* ===== MBWAY — Clean, high-conversion ===== */}
                  {selectedMethod === 'mbway' && (
                    <>
                      {/* Amount — large, centered */}
                      <div className="text-center pt-1" data-testid="step3-summary">
                        <p className="text-3xl font-bold text-[#2D2A26]">Enviar {totalPayment}€</p>
                        {TIP_SYSTEM_ENABLED && selectedTip > 0 && (
                          <p className="text-xs text-[#6B6661] mt-1">
                            (€{selectedAmount} apoio + €{selectedTip} para a plataforma)
                          </p>
                        )}
                      </div>

                      {/* Open MBWay button — replaces "via MB WAY" text */}
                      <a
                        href={`mbway://transfer?phone=${MBWAY_MANUAL.phoneClean}&amount=${totalPayment}`}
                        className="mx-auto w-fit px-5 py-1.5 bg-[#FFBE98]/20 hover:bg-[#FFBE98]/40 text-[#2D2A26] rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                        data-testid="open-mbway-btn"
                      >
                        <Smartphone className="w-3.5 h-3.5" /> Abrir MB WAY
                      </a>

                      {/* 1. Phone number — inline row with copy */}
                      <div className="flex items-center justify-between px-3 py-2.5 bg-stone-50 rounded-xl" data-testid="mbway-phone-block">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-[#FFBE98] text-[#2D2A26] flex items-center justify-center text-[10px] font-bold flex-shrink-0">1</span>
                          <p className="text-sm font-bold text-[#2D2A26] tracking-wide" data-testid="mbway-phone">{MBWAY_MANUAL.phone}</p>
                        </div>
                        <button
                          onClick={() => copyToClipboard(MBWAY_MANUAL.phoneClean, 'phone')}
                          className="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 rounded-lg flex items-center gap-1.5 text-xs font-medium text-[#2D2A26] transition-colors"
                          data-testid="copy-phone-btn"
                        >
                          {copiedField === 'phone' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedField === 'phone' ? 'Copiado' : 'Copiar número'}
                        </button>
                      </div>

                      {/* 2. Reference — inline row with copy */}
                      <div className="flex items-center justify-between px-3 py-2.5 bg-stone-50 rounded-xl" data-testid="reference-block">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-[#FFBE98] text-[#2D2A26] flex items-center justify-center text-[10px] font-bold flex-shrink-0">2</span>
                          <div>
                            <p className="text-[10px] text-[#6B6661] leading-none">Referência</p>
                            <p className="text-sm font-bold text-[#2D2A26] tracking-wider" data-testid="payment-reference">{contribution.payment_reference}</p>
                          </div>
                        </div>
                        <button
                          onClick={() => copyToClipboard(contribution.payment_reference, 'ref')}
                          className="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 rounded-lg flex items-center gap-1.5 text-xs font-medium text-[#2D2A26] transition-colors"
                          data-testid="copy-reference-btn"
                        >
                          {copiedField === 'ref' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedField === 'ref' ? 'Copiado' : 'Copiar referência'}
                        </button>
                      </div>

                      {/* Validation note */}
                      <p className="text-[11px] text-[#6B6661] text-center">Escreve esta referência nas notas quando efetuares o pagamento</p>

                      {/* Arrow indicator pointing to CTA */}
                      <div className="flex items-center justify-center gap-1 text-[#FFBE98]" data-testid="step3-arrow-hint">
                        <span className="text-[11px] text-[#6B6661] font-bold">Depois de efetuares o pagamento, carrega aqui</span>
                      </div>
                      <div className="flex justify-center gap-3 animate-bounce">
                        <ArrowRight className="w-4 h-4 text-[#FFBE98] rotate-90" />
                        <ArrowRight className="w-4 h-4 text-[#FFBE98] rotate-90" />
                      </div>

                      {/* Primary CTA — peach brand */}
                      <button
                        onClick={() => setShowConfirmForm(true)}
                        className="w-full bg-[#FFBE98] text-[#2D2A26] py-3 rounded-xl font-semibold hover:bg-[#FFB080] transition-all text-sm min-h-[44px] shadow-sm"
                        data-testid="confirm-payment-btn"
                      >
                        Já enviei {selectedAmount}€
                      </button>

                      {/* Trust */}
                      <p className="text-[10px] text-[#6B6661]/50 text-center flex items-center justify-center gap-1" data-testid="trust-footer">
                        <Check className="w-3 h-3" /> Confirmação em poucos minutos
                      </p>
                    </>
                  )}

                  {/* ===== CRYPTO — Optimized for conversion ===== */}
                  {selectedMethod === 'crypto' && cryptoData && (
                    <div className="space-y-2.5" data-testid="crypto-instructions">
                      {/* QR + Amount block */}
                      <div className="flex items-center gap-3">
                        <div className="bg-white p-1.5 rounded-xl shadow-sm border border-stone-100 flex-shrink-0">
                          {qrImageUrl ? (
                            <img src={qrImageUrl} alt="QR Code" width={90} height={90} />
                          ) : (
                            <div className="w-[90px] h-[90px] flex items-center justify-center">
                              <div className="w-5 h-5 border-2 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
                            </div>
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="text-[10px] text-[#6B6661]">Envia exatamente</p>
                          <p className="text-lg font-bold text-[#2D2A26]">{cryptoAmountCalc} {cryptoData.symbol}</p>
                          <p className="text-[10px] text-[#6B6661]">≈ {selectedAmount}€</p>
                          <p className="text-[10px] text-[#FFBE98] font-medium mt-0.5">Leva menos de 1 minuto</p>
                        </div>
                      </div>

                      {/* Action buttons — Copy is primary, Wallet is mobile-only secondary */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => copyToClipboard(cryptoData.address, 'address')}
                          className="flex-1 py-2.5 bg-[#2D2A26] text-white rounded-lg text-xs font-semibold flex flex-col items-center justify-center gap-0.5 hover:bg-[#4A4640] transition-colors"
                          data-testid="crypto-copy-address"
                        >
                          <span className="flex items-center gap-1.5">
                            {copiedField === 'address' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                            {copiedField === 'address' ? 'Copiado!' : 'Copiar endereço'}
                          </span>
                          <span className="text-[9px] font-normal text-white/60">Cola este endereço na tua carteira</span>
                        </button>
                        {/* Wallet button — mobile only (hidden on md+ screens) */}
                        <a
                          href={cryptoURI}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="md:hidden flex-shrink-0 w-[100px] py-2.5 bg-stone-100 text-[#2D2A26] rounded-lg text-xs font-medium flex flex-col items-center justify-center gap-0.5 hover:bg-stone-200 transition-colors border border-stone-200"
                          data-testid="crypto-open-wallet"
                          onClick={(e) => {
                            const timeout = setTimeout(() => {
                              alert('Nenhuma carteira de criptomoeda detetada.\n\nCopia o endereço e cola na tua carteira (MetaMask, Trust Wallet, etc.).');
                            }, 1500);
                            window.addEventListener('blur', () => clearTimeout(timeout), { once: true });
                          }}
                        >
                          <span className="flex items-center gap-1">
                            <Wallet className="w-3 h-3" /> Abrir app
                          </span>
                          <span className="text-[8px] font-normal text-[#6B6661]">Abre a tua app de crypto</span>
                        </a>
                      </div>

                      {/* Simplified steps */}
                      <div className="flex items-center gap-3 px-1">
                        <div className="flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-[#2D2A26] text-white flex items-center justify-center text-[9px] font-bold">1</span>
                          <span className="text-[10px] text-[#6B6661]">Copia ou lê o QR</span>
                        </div>
                        <ArrowRight className="w-3 h-3 text-[#6B6661]/40" />
                        <div className="flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-[#2D2A26] text-white flex items-center justify-center text-[9px] font-bold">2</span>
                          <span className="text-[10px] text-[#6B6661]">Envia exatamente este valor</span>
                        </div>
                        <ArrowRight className="w-3 h-3 text-[#6B6661]/40" />
                        <div className="flex items-center gap-1.5">
                          <span className="w-4 h-4 rounded-full bg-[#FFBE98] text-white flex items-center justify-center text-[9px] font-bold">3</span>
                          <span className="text-[10px] text-[#6B6661] font-medium">Confirma abaixo</span>
                        </div>
                      </div>

                      {/* Network warning — softer tone */}
                      <p className="text-[10px] text-amber-700 bg-amber-50 rounded-lg px-3 py-1.5 text-center">
                        Usa apenas a rede <strong>{cryptoData.network}</strong> para garantir a receção correta.
                      </p>

                      {/* Reference */}
                      <div className="bg-stone-50 border border-stone-200 rounded-xl px-3 py-1.5 flex items-center justify-between" data-testid="crypto-reference-block">
                        <div>
                          <p className="text-[9px] text-[#6B6661]">Referência (para validação do pagamento)</p>
                          <p className="text-sm font-bold text-[#2D2A26]" data-testid="payment-reference">{contribution.payment_reference}</p>
                        </div>
                        <button
                          onClick={() => copyToClipboard(contribution.payment_reference, 'ref')}
                          className="px-2 py-1 bg-stone-200 hover:bg-stone-300 rounded-lg text-[10px] font-medium text-[#2D2A26] transition-colors"
                        >
                          {copiedField === 'ref' ? 'Copiado!' : 'Copiar'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* 4. Reference Block — for non-crypto, non-mbway (fallback) */}
                  {selectedMethod !== 'crypto' && selectedMethod !== 'mbway' && (
                    <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl px-3 py-3" data-testid="reference-block">
                      <p className="text-[10px] text-emerald-700 font-medium text-center mb-1">Referência de pagamento</p>
                      <div className="flex items-center justify-center gap-3">
                        <p className="text-2xl font-bold text-[#2D2A26] tracking-wider" data-testid="payment-reference">{contribution.payment_reference}</p>
                        <button
                          onClick={() => copyToClipboard(contribution.payment_reference, 'ref')}
                          className="px-3 py-1.5 bg-emerald-100 hover:bg-emerald-200 rounded-lg flex items-center gap-1.5 text-xs font-semibold text-emerald-700 transition-colors"
                          data-testid="copy-reference-btn"
                        >
                          {copiedField === 'ref' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedField === 'ref' ? 'Copiado!' : 'Copiar'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Crypto reference - now inline above, old block removed */}

                  {/* Warning + Confirm — for crypto: simplified final block */}
                  {selectedMethod === 'crypto' && (
                    <>
                      {/* Guide to final action */}
                      <div className="text-center">
                        <span className="text-[11px] text-[#6B6661]">Depois de enviares o pagamento,<br />clica no botão abaixo</span>
                      </div>
                    </>
                  )}

                  {/* Warning + Confirm + Social — for non-crypto, non-mbway only */}
                  {selectedMethod !== 'crypto' && selectedMethod !== 'mbway' && (
                    <>
                      <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2" data-testid="step3-warning">
                        <p className="text-[11px] text-amber-800 text-center">
                          Usa exatamente este valor para validação automática
                        </p>
                      </div>

                      {/* Arrow indicator pointing to CTA */}
                      <div className="text-center" data-testid="step3-arrow-hint-crypto">
                        <span className="text-[11px] text-[#6B6661] font-bold">Depois de efetuares o pagamento, carrega aqui</span>
                      </div>
                      <div className="flex justify-center gap-3 animate-bounce">
                        <ArrowRight className="w-4 h-4 text-[#FFBE98] rotate-90" />
                        <ArrowRight className="w-4 h-4 text-[#FFBE98] rotate-90" />
                      </div>

                      <button
                        onClick={() => setShowConfirmForm(true)}
                        className="w-full bg-[#2D2A26] text-white py-3 rounded-xl font-semibold hover:bg-[#4A4640] transition-all text-sm min-h-[44px]"
                        data-testid="confirm-payment-btn"
                      >
                        Já enviei o pagamento
                      </button>

                      <div className="text-center pt-1 space-y-0.5" data-testid="trust-footer">
                        <p className="text-[10px] text-[#6B6661]/70 flex items-center justify-center gap-1">
                          <ShieldCheck className="w-3 h-3" />
                          100% seguro · Confirmação em poucos minutos
                        </p>
                      </div>
                    </>
                  )}
                </motion.div>
              )}

              {/* STEP 3.5: Confirmation Form */}
              {step === 3 && showConfirmForm && !showConfirmation && contribution && (
                <motion.div
                  key="confirm-form"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="space-y-4"
                  data-testid="confirm-form"
                >
                  <div className="text-center">
                    <p className="text-xs text-[#FFBE98] font-semibold mb-1">Último passo</p>
                    <h3 className="text-base font-bold text-[#2D2A26]">Confirmar contribuição</h3>
                    <p className="text-xs text-[#6B6661] mt-1.5 leading-relaxed">
                      Deixa o teu email para receberes a confirmação<br />e acompanhar este sonho.
                    </p>
                    <p className="text-[10px] text-[#6B6661]/70 mt-1">
                      Vamos confirmar o teu pagamento e enviar atualização por email.
                    </p>
                  </div>

                  <div className="space-y-2.5">
                    <div>
                      <label className="text-[11px] text-[#6B6661] font-medium block mb-1">Nome (opcional – como queres aparecer)</label>
                      <input
                        type="text"
                        value={confirmName}
                        onChange={e => setConfirmName(e.target.value)}
                        placeholder="O teu nome"
                        className="w-full px-3 py-2.5 border border-stone-200 rounded-xl text-sm text-[#2D2A26] focus:outline-none focus:border-[#FFBE98] transition-colors min-h-[44px]"
                        data-testid="confirm-name-input"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-[#6B6661] font-medium block mb-1">Email (para confirmação do pagamento) *</label>
                      <input
                        type="email"
                        value={confirmEmail}
                        onChange={e => setConfirmEmail(e.target.value)}
                        placeholder="o-teu@email.com"
                        required
                        className="w-full px-3 py-2.5 border border-stone-200 rounded-xl text-sm text-[#2D2A26] focus:outline-none focus:border-[#FFBE98] transition-colors min-h-[44px]"
                        data-testid="confirm-email-input"
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleConfirmPayment}
                    disabled={!confirmEmail || confirmingPayment}
                    className="w-full bg-[#2D2A26] text-white py-3 rounded-xl font-semibold hover:bg-[#4A4640] transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed min-h-[44px]"
                    data-testid="submit-confirmation-btn"
                  >
                    {confirmingPayment ? 'A confirmar...' : 'Confirmar e acompanhar o sonho'}
                  </button>

                  <p className="text-[10px] text-[#6B6661]/60 text-center">
                    Recebes confirmação em poucos minutos
                  </p>

                  <button
                    onClick={() => setShowConfirmForm(false)}
                    className="w-full text-xs text-[#6B6661] hover:text-[#2D2A26] transition-colors py-1"
                    data-testid="back-to-step3-btn"
                  >
                    Voltar às instruções
                  </button>
                </motion.div>
              )}

              {/* CONFIRMATION / SUCCESS */}
              {showConfirmation && (
                <motion.div
                  key="confirmation"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center py-4 space-y-4"
                >
                  {/* Icon + Title */}
                  <div>
                    <div className="w-14 h-14 bg-[#FFBE98]/20 rounded-full flex items-center justify-center mx-auto mb-3">
                      <Heart className="w-7 h-7 text-[#FFBE98]" />
                    </div>
                    <h3 className="text-xl font-bold text-[#2D2A26]" data-testid="thank-you-title">
                      Obrigado!
                    </h3>
                  </div>

                  {/* Status message */}
                  {contribution?.status === 'COMPLETED' ? (
                    <p className="text-sm text-[#2D2A26]">
                      Pagamento de <strong>{contribution.amount || totalPayment}€</strong> confirmado via PayPal.
                    </p>
                  ) : (
                    <p className="text-sm text-[#6B6661]">
                      Recebemos o teu pedido de contribuição. Estamos a validar o pagamento.
                    </p>
                  )}

                  {/* Platform tip thank you message - only if tip system enabled and tip > 0 */}
                  {TIP_SYSTEM_ENABLED && selectedTip > 0 && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="bg-gradient-to-r from-rose-50 to-amber-50 rounded-xl p-3 border border-rose-100"
                      data-testid="tip-thank-you-message"
                    >
                      <p className="text-sm font-medium text-rose-700">
                        Sem pessoas como tu, esta plataforma não existia ❤️
                      </p>
                    </motion.div>
                  )}

                  {/* Emotional reinforcement */}
                  <p className="text-xs text-[#FFBE98] italic" data-testid="post-contrib-proof">
                    Já estás a ajudar a tornar este sonho realidade
                  </p>

                  {/* Ambassador progression — PRIMARY CTA */}
                  <div className="bg-stone-50 rounded-xl p-4 space-y-2" data-testid="referral-cta-block">
                    <p className="text-sm font-semibold text-[#2D2A26]">Queres acelerar este sonho?</p>
                    {user?.valid_referrals_count !== undefined && (
                      <p className="text-xs text-[#6B6661]" data-testid="ambassador-progress">
                        Faltam-te <strong>{Math.max(0, 3 - (user.valid_referrals_count || 0))}</strong> amigos para te tornares Embaixador
                      </p>
                    )}
                    {user?.anonymous_alias ? (
                      <div className="flex justify-center pt-1" data-testid="thank-you-share">
                        <ShareMenu
                          inviteLink={buildInviteLink(user.anonymous_alias)}
                          senderName={null}
                          customMessage={`Acabei de ajudar a financiar uma viagem de sonho na 4Luis.\nSe quiseres participar também:\n\n${buildInviteLink(user.anonymous_alias)}`}
                          buttonLabel="Convidar amigos"
                        />
                      </div>
                    ) : (
                      <a
                        href="/login"
                        className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-semibold text-sm hover:bg-[#FFB080] transition-colors"
                        data-testid="register-cta-btn"
                      >
                        Convidar amigos
                      </a>
                    )}
                  </div>

                  {/* Register incentive for non-users */}
                  {!user && (
                    <div className="border-t border-stone-100 pt-3 space-y-2" data-testid="register-incentive">
                      <p className="text-xs font-semibold text-[#2D2A26]">Cria conta para acompanhar tudo</p>
                      <div className="space-y-1 text-left max-w-[240px] mx-auto">
                        {['Acompanhar a evolução da viagem', 'Convidar amigos e ganhar recompensas', 'Desbloquear o teu próprio sonho'].map((t) => (
                          <span key={t} className="flex items-center gap-2 text-xs text-[#6B6661]">
                            <Check className="w-3.5 h-3.5 text-[#FFBE98] flex-shrink-0" />
                            {t}
                          </span>
                        ))}
                      </div>
                      <a
                        href="/login"
                        className="inline-flex items-center justify-center gap-2 w-full py-2.5 bg-[#2D2A26] text-white rounded-xl font-semibold text-sm hover:bg-[#4A4640] transition-colors"
                        data-testid="register-btn"
                      >
                        Criar conta
                      </a>
                    </div>
                  )}

                  <button
                    onClick={handleClose}
                    className="w-full text-xs text-[#6B6661] hover:text-[#2D2A26] transition-colors py-1"
                    data-testid="thank-you-close-btn"
                  >
                    Fechar
                  </button>
                </motion.div>
              )}

            </AnimatePresence>
          </div>

          {/* Sticky footer for step 1 */}
          {step === 1 && !showConfirmation && selectedAmount && (
            <div className="px-4 pb-3 pt-2 border-t border-stone-100 bg-white">
              <button
                onClick={() => setStep(2)}
                className="w-full bg-[#FFBE98] text-[#2D2A26] py-3 px-6 rounded-xl font-semibold hover:bg-[#FFB080] transition-all flex items-center justify-center gap-2"
                data-testid="step1-continue-btn"
              >
                Continuar com €{totalPayment} <Heart className="w-3.5 h-3.5" />
                <ArrowRight className="w-4 h-4" />
              </button>
              <p className="text-[10px] leading-relaxed text-[#6B6661]/70 text-center mt-2">
                {selectedTip > 0 
                  ? `€${selectedAmount} para o sonho + €${selectedTip} para a plataforma`
                  : 'Promoções, descontos e vouchers para quem contribui'
                }
              </p>
            </div>
          )}

          {/* Sticky footer for step 3 crypto — always visible confirm button */}
          {step === 3 && selectedMethod === 'crypto' && !showConfirmation && !showConfirmForm && contribution && (
            <div className="px-4 pb-3 pt-2 border-t border-stone-100 bg-white">
              <button
                onClick={() => setShowConfirmForm(true)}
                className="w-full bg-[#2D2A26] text-white py-3 rounded-xl font-semibold hover:bg-[#4A4640] transition-all text-sm min-h-[44px]"
                data-testid="crypto-confirm-sticky-btn"
              >
                Já enviei o pagamento
              </button>
              <p className="text-[10px] text-[#6B6661]/50 text-center mt-1.5 flex items-center justify-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                100% seguro · Confirmação em poucos minutos
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default CheckoutModal;
