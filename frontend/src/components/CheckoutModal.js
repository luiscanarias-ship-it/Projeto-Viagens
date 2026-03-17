import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Check, Copy, Bitcoin, Smartphone, ExternalLink,
  Wallet, CreditCard, ArrowRight, QrCode, Heart
} from 'lucide-react';
import QRCode from 'qrcode';
import axios from 'axios';
import ShareMenu, { buildInviteLink } from './ShareMenu';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fixed contribution amounts
const amounts = [10, 20, 50, 100, 200, 500, 1000];

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

// Payment methods configuration
const paymentMethodsConfig = {
  mbway: {
    id: 'mbway',
    name: 'MBWay',
    icon: Smartphone,
    phone: '+351 968 068 535',
    phoneClean: '351968068535'
  },
  revolut: {
    id: 'revolut',
    name: 'Revolut',
    icon: Wallet,
    username: '@luism2npb',
    link: 'https://revolut.me/luism2npb'
  },
  wise: {
    id: 'wise',
    name: 'Wise',
    icon: CreditCard,
    username: '@luisc8030',
    link: 'https://wise.com/pay/me/luisc8030'
  },
  paypal: {
    id: 'paypal',
    name: 'PayPal',
    icon: ExternalLink,
    username: 'LuisCanarias',
    link: 'https://paypal.me/LuisCanarias'
  }
};

const CheckoutModal = ({ 
  isOpen, 
  onClose, 
  journeyName = 'China',
  journeyId,
  contributionDescriptions,
  getAuthHeaders,
  user 
}) => {
  // Checkout state
  const [step, setStep] = useState(1);
  const [selectedAmount, setSelectedAmount] = useState(10);
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

  // QR code states
  const [cryptoAmountCalc, setCryptoAmountCalc] = useState(null);
  const [cryptoURI, setCryptoURI] = useState(null);
  const [qrImageUrl, setQrImageUrl] = useState(null);
  const [nonCryptoQrUrl, setNonCryptoQrUrl] = useState(null);

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
    } else {
      // Fetch crypto prices when modal opens
      fetchCryptoPrices();
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
        generateCryptoURI(crypto.symbol, crypto.address, selectedAmount);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, selectedMethod, selectedCrypto, selectedAmount, cryptoPrices]);

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
    const method = paymentMethodsConfig[methodId];
    if (!method) return '';
    
    switch (methodId) {
      case 'paypal':
        return `${method.link}/${selectedAmount}EUR`;
      case 'revolut':
        return method.link;
      case 'wise':
        return method.link;
      case 'mbway':
        return `tel:${method.phoneClean}`;
      default:
        return '';
    }
  };

  // Create contribution
  const createContribution = async (method, cryptoType = null) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/contributions/create`, {
        amount: selectedAmount,
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
  const methodData = selectedMethod && selectedMethod !== 'crypto' ? paymentMethodsConfig[selectedMethod] : null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-hidden shadow-2xl"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-[#FFBE98]/20 to-[#E6F4F1]/30 px-4 py-3 border-b border-stone-100">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="font-bold text-[#2D2A26] text-sm">Contribuir para a Viagem Principal</h2>
                <p className="text-xs text-[#6B6661]">Destino: {journeyName}</p>
              </div>
              <button
                onClick={step === 3 ? goToStep2 : step === 2 ? goToStep1 : handleClose}
                className="p-2 hover:bg-stone-100 rounded-full transition-colors"
              >
                {step > 1 && !showConfirmation ? (
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
          <div className="px-4 py-3 overflow-y-auto max-h-[70vh]">
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
                  <p className="text-sm text-[#6B6661]">Escolhe o valor da tua contribuição:</p>
                  
                  <div className="grid grid-cols-2 sm:grid-cols-1 gap-2">
                    {amounts.map((amt) => (
                      <button
                        key={amt}
                        onClick={() => setSelectedAmount(amt)}
                        data-testid={`amount-btn-${amt}`}
                        className={`py-2.5 px-3 rounded-xl font-semibold transition-all text-left flex items-center justify-between ${
                          selectedAmount === amt
                            ? 'bg-[#FFBE98] text-white shadow-md ring-2 ring-[#FFBE98]/30'
                            : amt === 20
                              ? 'bg-[#FFBE98]/15 text-[#2D2A26] hover:bg-[#FFBE98]/25 ring-2 ring-[#FFBE98]/50 shadow-sm'
                              : 'bg-stone-100 text-[#2D2A26] hover:bg-stone-200'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-base font-bold min-w-[45px]">€{amt}</span>
                          {amt === 20 && selectedAmount !== amt && (
                            <span 
                              className="text-[10px] font-bold text-white bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] px-2 py-0.5 rounded-full shadow-sm animate-pulse-subtle ring-1 ring-[#FFBE98]/50" 
                              data-testid="most-popular-badge"
                              style={{ animationDuration: '2.5s' }}
                            >
                              Mais popular
                            </span>
                          )}}
                          {contributionDescriptions?.[String(amt)] && (
                            <span className={`text-sm font-normal ${
                              selectedAmount === amt ? 'text-white/85' : 'text-[#6B6661]'
                            }`}>
                              {contributionDescriptions[String(amt)]}
                            </span>
                          )}
                        </div>
                        {selectedAmount === amt && (
                          <Check className="w-5 h-5 flex-shrink-0" />
                        )}
                      </button>
                    ))}
                  </div>

                  {selectedAmount && (
                    <p className="text-center text-sm text-[#6B6661] italic mt-2" data-testid="impact-message">
                      {selectedAmount >= 50
                        ? 'Com este apoio estás a aproximar muito este sonho da realidade.'
                        : selectedAmount >= 20
                          ? 'A tua contribuição ajuda este sonho a dar um grande passo.'
                          : 'A tua contribuição ajuda este sonho a ganhar forma.'}
                    </p>
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
                  className="space-y-4"
                >
                  {/* Selected amount summary */}
                  <div className="flex items-center justify-between bg-stone-50 rounded-xl p-3">
                    <div>
                      <p className="text-xs text-[#6B6661]">Contribuição:</p>
                      <p className="font-bold text-lg text-[#2D2A26]">€{selectedAmount}</p>
                    </div>
                    <button
                      onClick={goToStep1}
                      className="text-sm text-[#FFBE98] hover:underline"
                    >
                      Alterar valor
                    </button>
                  </div>

                  <p className="text-center text-sm text-[#6B6661] italic leading-relaxed" data-testid="motivational-text">
                    Mesmo uma pequena contribuição<br />ajuda este sonho a ganhar forma.
                  </p>

                  {/* Micro-testimonial - social proof at critical moment */}
                  <div className="flex items-start gap-2.5 bg-stone-50/80 rounded-xl p-3 border border-stone-100" data-testid="micro-testimonial">
                    <span className="text-[#FFBE98] text-lg leading-none mt-0.5">"</span>
                    <div>
                      <p className="text-xs text-[#2D2A26] italic leading-relaxed">Contribuí em menos de 1 minuto</p>
                      <p className="text-[10px] text-[#6B6661] mt-1">— João</p>
                    </div>
                  </div>

                  <p className="text-sm text-[#6B6661]">Escolhe o método de pagamento:</p>

                  {/* Payment methods */}
                  <div className="space-y-2">
                    {/* Crypto option */}
                    <button
                      onClick={() => handleMethodSelect('crypto')}
                      disabled={loading}
                      className={`w-full p-3 rounded-xl border-2 transition-all flex items-center gap-3 ${
                        selectedMethod === 'crypto'
                          ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                          : 'border-[#F7931A]/40 bg-gradient-to-r from-[#F7931A]/5 to-[#627EEA]/5 hover:border-[#F7931A]'
                      }`}
                    >
                      <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#F7931A]/20">
                        <Bitcoin className="w-5 h-5 text-[#F7931A]" />
                      </div>
                      <div className="flex-1 text-left">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">Criptomoeda</span>
                          <span className="text-[10px] bg-[#F7931A] text-white px-2 py-0.5 rounded-full font-bold">
                            TOP
                          </span>
                        </div>
                        <span className="text-xs text-[#6B6661]">BTC, ETH, USDT, USDC</span>
                      </div>
                    </button>

                    {/* Other payment methods */}
                    {Object.values(paymentMethodsConfig).map((method) => {
                      const Icon = method.icon;
                      return (
                        <button
                          key={method.id}
                          onClick={() => handleMethodSelect(method.id)}
                          disabled={loading}
                          className={`w-full p-3 rounded-xl border-2 transition-all flex items-center gap-3 ${
                            selectedMethod === method.id
                              ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                              : 'border-stone-200 hover:border-stone-300'
                          }`}
                        >
                          <div className="w-10 h-10 rounded-full flex items-center justify-center bg-stone-100">
                            <Icon className="w-5 h-5 text-[#6B6661]" />
                          </div>
                          <div className="flex-1 text-left">
                            <span className="font-medium">{method.name}</span>
                            <span className="text-xs text-[#6B6661] block">
                              {method.phone || method.username || method.link?.replace('https://', '')}
                            </span>
                          </div>
                          {loading && selectedMethod === method.id && (
                            <div className="w-5 h-5 border-2 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
                          )}
                        </button>
                      );
                    })}
                  </div>

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

              {/* STEP 3: Payment Instructions */}
              {step === 3 && !showConfirmation && contribution && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-2.5"
                >
                  {/* ===== CRYPTO STEP 3 ===== */}
                  {selectedMethod === 'crypto' && cryptoData && (
                    <>
                      {/* Incentive banner */}
                      <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5 text-center">
                        <p className="text-xs font-semibold text-emerald-700">Pagamento instantâneo e sem taxas bancárias</p>
                      </div>

                      {/* QR Code centered */}
                      <div className="flex justify-center">
                        <div className="bg-white p-2 rounded-xl shadow-sm border border-stone-100">
                          {qrImageUrl ? (
                            <img src={qrImageUrl} alt="QR Code" width={140} height={140} />
                          ) : (
                            <div className="w-[140px] h-[140px] flex items-center justify-center">
                              <div className="w-6 h-6 border-2 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Amount box */}
                      <div className="bg-stone-50 rounded-xl p-3 text-center">
                        <p className="text-[10px] text-[#6B6661] uppercase tracking-wide">Valor a enviar</p>
                        <p className="text-xl font-bold text-[#2D2A26] mt-0.5">
                          {cryptoAmountCalc} {cryptoData.symbol}
                        </p>
                        <p className="text-sm text-[#6B6661]">
                          ≈ {selectedAmount} €
                        </p>
                      </div>

                      {/* 3 visual steps */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2.5">
                          <span className="w-5 h-5 rounded-full bg-[#2D2A26] text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">1</span>
                          <p className="text-xs text-[#2D2A26]">Copia o endereço ou abre a tua carteira</p>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <span className="w-5 h-5 rounded-full bg-[#2D2A26] text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">2</span>
                          <p className="text-xs text-[#2D2A26]">Envia exatamente <strong>{cryptoAmountCalc} {cryptoData.symbol}</strong></p>
                        </div>
                        <div className="flex items-center gap-2.5">
                          <span className="w-5 h-5 rounded-full bg-[#2D2A26] text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">3</span>
                          <p className="text-xs text-[#2D2A26]">Depois clica em <strong>Já efetuei o pagamento</strong></p>
                        </div>
                      </div>

                      {/* Action buttons: Copy + Open Wallet */}
                      <div className="flex gap-2">
                        <button
                          onClick={() => copyToClipboard(cryptoData.address, 'address')}
                          className="flex-1 py-2.5 bg-[#2D2A26] text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-[#4A4640] transition-colors"
                        >
                          {copiedField === 'address' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                          {copiedField === 'address' ? 'Copiado!' : 'Copiar endereço'}
                        </button>
                        <a
                          href={cryptoURI}
                          className="flex-1 py-2.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-emerald-700 transition-colors"
                        >
                          <Wallet className="w-3.5 h-3.5" />
                          Abrir carteira
                        </a>
                      </div>

                      {/* Network warning */}
                      <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                        <p className="text-[11px] text-amber-800">
                          Enviar apenas pela rede <strong>{cryptoData.network}</strong>. Outras redes podem resultar na perda dos fundos.
                        </p>
                      </div>
                    </>
                  )}

                  {/* ===== NON-CRYPTO STEP 3 ===== */}
                  {selectedMethod !== 'crypto' && (
                    <div className="space-y-2.5">
                      {/* Amount summary */}
                      <div className="bg-stone-50 rounded-xl p-3 text-center">
                        <p className="text-[10px] text-[#6B6661] uppercase tracking-wide">Valor a enviar</p>
                        <p className="text-2xl font-bold text-[#2D2A26] mt-0.5">€{selectedAmount}</p>
                      </div>

                      {/* MBWay */}
                      {selectedMethod === 'mbway' && methodData && (
                        <div className="space-y-2">
                          <div className="bg-white border border-stone-200 rounded-xl p-3">
                            <p className="text-xs text-[#6B6661] mb-1">Enviar para o número:</p>
                            <p className="text-lg font-bold text-[#2D2A26]">{methodData.phone}</p>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => copyToClipboard(methodData.phoneClean, 'phone')}
                              className="flex-1 py-2.5 bg-[#2D2A26] text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-[#4A4640] transition-colors"
                            >
                              {copiedField === 'phone' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                              {copiedField === 'phone' ? 'Copiado!' : 'Copiar número'}
                            </button>
                            <a
                              href="mbway://transfer"
                              className="flex-1 py-2.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold flex flex-col items-center justify-center gap-0.5 hover:bg-emerald-700 transition-colors"
                            >
                              <span className="flex items-center gap-1.5"><Smartphone className="w-3.5 h-3.5" /> Abrir MBWay</span>
                              <span className="text-[9px] font-normal opacity-80">apenas para telemóvel</span>
                            </a>
                          </div>
                        </div>
                      )}

                      {/* Revolut */}
                      {selectedMethod === 'revolut' && methodData && (
                        <div className="space-y-2">
                          <div className="bg-white border border-stone-200 rounded-xl p-3">
                            <p className="text-xs text-[#6B6661] mb-1">Enviar para:</p>
                            <p className="text-lg font-bold text-[#2D2A26]">{methodData.username}</p>
                          </div>
                          <a
                            href={methodData.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-emerald-700 transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                            Abrir Revolut
                          </a>
                        </div>
                      )}

                      {/* Wise */}
                      {selectedMethod === 'wise' && methodData && (
                        <div className="space-y-2">
                          <div className="bg-white border border-stone-200 rounded-xl p-3">
                            <p className="text-xs text-[#6B6661] mb-1">Enviar para:</p>
                            <p className="text-lg font-bold text-[#2D2A26]">{methodData.username}</p>
                          </div>
                          <a
                            href={methodData.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-emerald-700 transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                            Abrir Wise
                          </a>
                        </div>
                      )}

                      {/* PayPal */}
                      {selectedMethod === 'paypal' && methodData && (
                        <div className="space-y-2">
                          <div className="bg-white border border-stone-200 rounded-xl p-3">
                            <p className="text-xs text-[#6B6661] mb-1">Enviar para:</p>
                            <p className="text-lg font-bold text-[#2D2A26]">{methodData.username}</p>
                            <p className="text-xs text-[#6B6661] mt-1">paypal.me/{methodData.username}/{selectedAmount}</p>
                          </div>
                          <a
                            href={`${methodData.link}/${selectedAmount}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full py-2.5 bg-emerald-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 hover:bg-emerald-700 transition-colors"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                            Abrir PayPal (€{selectedAmount})
                          </a>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Reference code */}
                  <div className="bg-red-50 border-2 border-red-300 rounded-xl px-3 py-2.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[10px] text-[#6B6661] leading-none mb-0.5">Referência:</p>
                        <p className="text-lg font-bold text-[#2D2A26] tracking-wider leading-tight">{contribution.payment_reference}</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(contribution.payment_reference, 'ref')}
                        className="px-2.5 py-1.5 bg-[#FFBE98]/20 rounded-lg hover:bg-[#FFBE98]/30 flex items-center gap-1 text-xs"
                      >
                        {copiedField === 'ref' ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5 text-[#FFBE98]" />}
                        <span className="text-[#FFBE98]">{copiedField === 'ref' ? 'OK' : 'Copiar'}</span>
                      </button>
                    </div>
                    <p className="text-xs text-red-600 font-bold mt-1">Inclui esta referência na descrição do pagamento!</p>
                  </div>

                  {/* Return reminder */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-center">
                    <p className="text-xs text-blue-700">Depois de enviar o pagamento, volte aqui e clique <strong>"Já efetuei o pagamento"</strong></p>
                  </div>

                  {/* Confirm button */}
                  <button
                    onClick={() => setShowConfirmation(true)}
                    className="w-full bg-[#2D2A26] text-white py-2.5 px-6 rounded-xl font-medium hover:bg-[#4A4640] transition-all text-sm"
                  >
                    Já efetuei o pagamento
                  </button>
                </motion.div>
              )}

              {/* CONFIRMATION */}
              {showConfirmation && (
                <motion.div
                  key="confirmation"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center py-6 space-y-5"
                >
                  <div className="w-16 h-16 bg-[#FFBE98]/20 rounded-full flex items-center justify-center mx-auto">
                    <Heart className="w-8 h-8 text-[#FFBE98]" />
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-bold text-[#2D2A26]" data-testid="thank-you-title">
                      Acabaste de ajudar este sonho a ganhar forma.
                    </h3>
                    <p className="text-sm text-[#6B6661] mt-2">
                      Obrigado. A tua contribuição foi registada<br />
                      e será confirmada assim que o pagamento for recebido.
                    </p>
                    <p className="text-xs text-[#FFBE98] mt-3 italic" data-testid="post-contrib-proof">
                      Cada contribuição aproxima este sonho da realidade.
                    </p>
                  </div>

                  {contribution && (
                    <div className="bg-stone-50 rounded-xl p-3 inline-block">
                      <p className="text-xs text-[#6B6661]">Referência:</p>
                      <p className="font-bold text-lg">{contribution.payment_reference}</p>
                    </div>
                  )}

                  {user?.anonymous_alias && (
                    <div className="border-t border-stone-100 pt-4 space-y-2">
                      <p className="text-sm text-[#6B6661]">
                        Convida amigos a fazer parte deste sonho
                      </p>
                      <div className="flex justify-center" data-testid="thank-you-share">
                        <ShareMenu
                          inviteLink={buildInviteLink(user.anonymous_alias)}
                          senderName={null}
                          customMessage={`Acredito que os sonhos podem tornar-se realidade.\n\nAcabei de ajudar a financiar uma viagem na 4Luis.\nSe quiseres participar também:\n\n${buildInviteLink(user.anonymous_alias)}`}
                          buttonLabel="Partilhar convite"
                        />
                      </div>
                    </div>
                  )}

                  {!user && (
                    <div className="border-t border-stone-100 pt-4 space-y-3" data-testid="register-incentive">
                      <p className="text-sm font-semibold text-[#2D2A26]">Cria uma conta gratuita para:</p>
                      <div className="space-y-1.5 text-left max-w-[220px] mx-auto">
                        {['Acompanhar a evolução da viagem', 'Convidar amigos', 'Desbloquear o teu próprio sonho'].map((t) => (
                          <span key={t} className="flex items-center gap-2 text-sm text-[#6B6661]">
                            <Check className="w-4 h-4 text-[#FFBE98] flex-shrink-0" />
                            {t}
                          </span>
                        ))}
                      </div>
                      <a
                        href="/login"
                        className="inline-flex items-center justify-center gap-2 w-full py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-semibold text-sm hover:bg-[#FFAB7D] transition-colors"
                        data-testid="register-cta-btn"
                      >
                        Criar conta
                      </a>
                    </div>
                  )}

                  <button
                    onClick={handleClose}
                    className="w-full bg-[#2D2A26] text-white py-3 px-6 rounded-xl font-medium hover:bg-[#4A4640] transition-all"
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
                className="w-full bg-[#2D2A26] text-white py-3 px-6 rounded-xl font-medium hover:bg-[#4A4640] transition-all flex items-center justify-center gap-2"
                data-testid="step1-continue-btn"
              >
                Continuar com €{selectedAmount}
                <ArrowRight className="w-4 h-4" />
              </button>
              <p className="text-[10px] leading-relaxed text-[#6B6661]/70 text-center mt-2">
                As contribuições são voluntárias e destinam-se a apoiar sonhos de viagem.
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default CheckoutModal;
