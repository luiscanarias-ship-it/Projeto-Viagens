import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Check, Copy, Bitcoin, Smartphone, ExternalLink,
  Wallet, CreditCard, ArrowRight, QrCode
} from 'lucide-react';
import QRCode from 'qrcode';
import axios from 'axios';

// Canvas-based QR code component using qrcode library directly
const QRCanvas = ({ value, size = 120 }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (canvasRef.current && value) {
      QRCode.toCanvas(canvasRef.current, value, {
        width: size,
        margin: 1,
        errorCorrectionLevel: 'M'
      }, (error) => {
        if (error) console.error('QR generation error:', error);
      });
    }
  }, [value, size]);

  return <canvas ref={canvasRef} />;
};

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
    } else {
      // Fetch crypto prices when modal opens
      fetchCryptoPrices();
    }
  }, [isOpen, fetchCryptoPrices]);

  // Calculate crypto amount from EUR
  const getCryptoAmount = (euroAmount, cryptoId) => {
    const crypto = cryptoConfig[cryptoId];
    if (!crypto || !cryptoPrices[crypto.coingeckoId]) return null;
    
    const priceInEur = cryptoPrices[crypto.coingeckoId].eur;
    const amount = euroAmount / priceInEur;
    
    // Format based on crypto type
    if (cryptoId === 'btc') {
      return amount.toFixed(8);
    } else if (cryptoId === 'eth') {
      return amount.toFixed(6);
    } else {
      return amount.toFixed(2);
    }
  };

  // Generate QR code value for crypto - blockchain URI format: protocol:address?amount=value
  const getCryptoQRValue = (cryptoId, euroAmount) => {
    const crypto = cryptoConfig[cryptoId];
    if (!crypto) return '';
    
    const cryptoAmount = getCryptoAmount(euroAmount, cryptoId);
    if (!cryptoAmount) return `${crypto.protocol}:${crypto.address}`;
    
    return `${crypto.protocol}:${crypto.address}?amount=${cryptoAmount}`;
  };

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
                onClick={handleClose}
                className="p-2 hover:bg-stone-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-[#6B6661]" />
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
                  
                  <div className="grid grid-cols-4 gap-2">
                    {amounts.map((amt) => (
                      <button
                        key={amt}
                        onClick={() => setSelectedAmount(amt)}
                        className={`py-3 px-2 rounded-xl font-semibold transition-all ${
                          selectedAmount === amt
                            ? 'bg-[#FFBE98] text-white shadow-md scale-105'
                            : 'bg-stone-100 text-[#2D2A26] hover:bg-stone-200'
                        }`}
                      >
                        €{amt}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => setStep(2)}
                    className="w-full mt-4 bg-[#2D2A26] text-white py-3 px-6 rounded-xl font-medium hover:bg-[#4A4640] transition-all flex items-center justify-center gap-2"
                  >
                    Continuar
                    <ArrowRight className="w-4 h-4" />
                  </button>
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
                  className="space-y-2"
                >
                  {/* QR Code + Payment Details - side by side on larger, stacked compact on small */}
                  <div className="bg-white border border-stone-200 rounded-xl p-3">
                    <div className="flex items-start gap-3">
                      {/* QR Code - canvas based for reliable URI encoding */}
                      <div className="bg-white p-2 rounded-lg shadow-sm border border-stone-100 flex-shrink-0">
                        <QRCanvas 
                          value={
                            selectedMethod === 'crypto' 
                              ? getCryptoQRValue(selectedCrypto, selectedAmount)
                              : getPaymentQRValue(selectedMethod)
                          }
                          size={100}
                        />
                        {/* Network + amount note under QR for crypto */}
                        {selectedMethod === 'crypto' && cryptoData && (
                          <div className="mt-1.5 text-center space-y-0.5">
                            <p className="text-[9px] font-bold text-red-600 leading-tight">
                              Rede: {cryptoData.network}
                            </p>
                            {getCryptoAmount(selectedAmount, selectedCrypto) && (
                              <p className="text-[9px] font-bold text-[#2D2A26] leading-tight">
                                {getCryptoAmount(selectedAmount, selectedCrypto)} {cryptoData.symbol}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Payment details next to QR */}
                      <div className="flex-1 min-w-0">
                        {/* Crypto specific details */}
                        {selectedMethod === 'crypto' && cryptoData && (
                          <div className="space-y-1.5">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold" style={{ color: cryptoData.color }}>
                                {cryptoData.symbol}
                              </span>
                              <span className="text-[10px] bg-stone-100 px-1.5 py-0.5 rounded-full">
                                {cryptoData.network}
                              </span>
                            </div>
                            {getCryptoAmount(selectedAmount, selectedCrypto) && (
                              <div className="bg-[#FFBE98]/10 rounded-md px-2 py-1.5">
                                <p className="text-[10px] text-[#6B6661]">Valor aprox:</p>
                                <p className="font-bold text-sm text-[#2D2A26]">
                                  {getCryptoAmount(selectedAmount, selectedCrypto)} {cryptoData.symbol}
                                </p>
                              </div>
                            )}
                            <p className="text-[10px] font-mono break-all text-[#6B6661] leading-tight">
                              {cryptoData.address}
                            </p>
                            <button
                              onClick={() => copyToClipboard(cryptoData.address, 'address')}
                              className="w-full py-1.5 bg-stone-100 rounded-md text-xs flex items-center justify-center gap-1.5 hover:bg-stone-200"
                            >
                              {copiedField === 'address' ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                              {copiedField === 'address' ? 'Copiado!' : 'Copiar endereço'}
                            </button>
                          </div>
                        )}

                        {/* MBWay details */}
                        {selectedMethod === 'mbway' && methodData && (
                          <div className="space-y-1.5">
                            <p className="text-xs text-[#6B6661]">Enviar <strong>€{selectedAmount}</strong> para:</p>
                            <p className="text-lg font-bold text-[#2D2A26]">{methodData.phone}</p>
                            <button
                              onClick={() => copyToClipboard(methodData.phoneClean, 'phone')}
                              className="w-full py-1.5 bg-stone-100 rounded-md text-xs flex items-center justify-center gap-1.5 hover:bg-stone-200"
                            >
                              {copiedField === 'phone' ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                              {copiedField === 'phone' ? 'Copiado!' : 'Copiar número'}
                            </button>
                          </div>
                        )}

                        {/* PayPal, Revolut, Wise details */}
                        {(selectedMethod === 'paypal' || selectedMethod === 'revolut' || selectedMethod === 'wise') && methodData && (
                          <div className="space-y-1.5">
                            <p className="text-xs text-[#6B6661]">Enviar <strong>€{selectedAmount}</strong> para:</p>
                            <p className="font-bold text-[#2D2A26]">{methodData.username}</p>
                            <a
                              href={selectedMethod === 'paypal' ? `${methodData.link}/${selectedAmount}EUR` : methodData.link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="w-full py-1.5 bg-[#2D2A26] text-white rounded-md text-xs flex items-center justify-center gap-1.5 hover:bg-[#4A4640]"
                            >
                              <ExternalLink className="w-3 h-3" />
                              Abrir {methodData.name}
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Reference code - compact */}
                  <div className="bg-[#FFBE98]/10 border border-[#FFBE98]/30 rounded-xl px-3 py-2">
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
                    <p className="text-[10px] text-red-500 font-medium mt-0.5">Inclui esta referência na descrição do pagamento</p>
                  </div>

                  {/* Trust line + Confirm button combined */}
                  <div className="flex items-center gap-1.5 text-[10px] text-green-600 bg-green-50 px-2 py-1.5 rounded-lg">
                    <Check className="w-3 h-3 flex-shrink-0" />
                    Contribuição confirmada assim que o pagamento for recebido
                  </div>

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
                  className="text-center py-6 space-y-4"
                >
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                    <Check className="w-8 h-8 text-green-500" />
                  </div>
                  
                  <div>
                    <h3 className="text-xl font-bold text-[#2D2A26]">Obrigado!</h3>
                    <p className="text-[#6B6661] mt-2">
                      A tua contribuição foi registada.<br />
                      Será confirmada assim que o pagamento for recebido.
                    </p>
                  </div>

                  {contribution && (
                    <div className="bg-stone-50 rounded-xl p-4 inline-block">
                      <p className="text-xs text-[#6B6661]">Referência:</p>
                      <p className="font-bold text-lg">{contribution.payment_reference}</p>
                    </div>
                  )}

                  <button
                    onClick={handleClose}
                    className="w-full bg-[#2D2A26] text-white py-3 px-6 rounded-xl font-medium hover:bg-[#4A4640] transition-all"
                  >
                    Fechar
                  </button>
                </motion.div>
              )}

            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default CheckoutModal;
