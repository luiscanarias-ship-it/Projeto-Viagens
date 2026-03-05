import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Check, Copy, Bitcoin, Smartphone, ExternalLink, ChevronLeft,
  Wallet, CreditCard, ArrowRight
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fixed contribution amounts
const amounts = [10, 20, 50, 100, 200, 500, 1000];

// Crypto types
const cryptoTypes = [
  { id: 'btc', name: 'Bitcoin', symbol: 'BTC', color: '#F7931A' },
  { id: 'eth', name: 'Ethereum', symbol: 'ETH', color: '#627EEA' },
  { id: 'usdt', name: 'Tether', symbol: 'USDT', color: '#26A17B' },
  { id: 'usdc', name: 'USD Coin', symbol: 'USDC', color: '#2775CA' }
];

// Payment methods
const paymentMethods = [
  { id: 'crypto', name: 'Criptomoeda', icon: Bitcoin, description: 'BTC, ETH, USDT, USDC', recommended: true },
  { id: 'mbway', name: 'MBWay', icon: Smartphone, description: '+351 968 068 535' },
  { id: 'revolut', name: 'Revolut', icon: Wallet, description: '@luis4dreams' },
  { id: 'wise', name: 'Wise', icon: CreditCard, description: 'Transferência' },
  { id: 'paypal', name: 'PayPal', icon: ExternalLink, description: 'paypal.me' }
];

const CheckoutModal = ({ 
  isOpen, 
  onClose, 
  journeyName = 'China',
  journeyId,
  paymentInfo,
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
  const [showConfirmation, setShowConfirmation] = useState(false);

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
    }
  }, [isOpen]);

  // Create contribution when reaching step 3
  const createContribution = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/contributions/create`, {
        amount: selectedAmount,
        payment_method: selectedMethod,
        journey_id: journeyId,
        crypto_type: selectedMethod === 'crypto' ? selectedCrypto : null,
        contributor_name: user?.name || null,
        contributor_email: user?.email || null
      }, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      });
      
      setContribution(response.data);
      setStep(3);
    } catch (error) {
      console.error('Error creating contribution:', error);
      alert(error.response?.data?.detail || 'Erro ao registar contribuição');
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
    setLoading(true);
    try {
      const response = await axios.post(`${API}/contributions/create`, {
        amount: selectedAmount,
        payment_method: methodId,
        journey_id: journeyId,
        contributor_name: user?.name || null,
        contributor_email: user?.email || null
      }, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      });
      
      setContribution(response.data);
      setStep(3);
    } catch (error) {
      console.error('Error creating contribution:', error);
      alert(error.response?.data?.detail || 'Erro ao registar contribuição');
    } finally {
      setLoading(false);
    }
  };

  // Handle crypto selection
  const handleCryptoSelect = async (cryptoId) => {
    setSelectedCrypto(cryptoId);
    
    // Create contribution with crypto
    setLoading(true);
    try {
      const response = await axios.post(`${API}/contributions/create`, {
        amount: selectedAmount,
        payment_method: 'crypto',
        journey_id: journeyId,
        crypto_type: cryptoId,
        contributor_name: user?.name || null,
        contributor_email: user?.email || null
      }, {
        headers: getAuthHeaders ? getAuthHeaders() : {}
      });
      
      setContribution(response.data);
      setStep(3);
    } catch (error) {
      console.error('Error creating contribution:', error);
      alert(error.response?.data?.detail || 'Erro ao registar contribuição');
    } finally {
      setLoading(false);
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Handle close
  const handleClose = () => {
    onClose();
  };

  // Get payment details based on method
  const getPaymentDetails = () => {
    if (!paymentInfo) return null;
    
    switch (selectedMethod) {
      case 'mbway':
        return {
          label: 'Enviar pagamento para:',
          value: paymentInfo.mbway?.phone || '+351 968 068 535',
          copyValue: paymentInfo.mbway?.phone || '+351968068535'
        };
      case 'revolut':
        return {
          label: 'Enviar pagamento para:',
          value: paymentInfo.revolut?.tag || '@luis4dreams',
          copyValue: paymentInfo.revolut?.tag || '@luis4dreams'
        };
      case 'wise':
        return {
          label: 'Enviar pagamento para:',
          value: paymentInfo.wise?.email || 'luis@4luis.com',
          copyValue: paymentInfo.wise?.email || 'luis@4luis.com'
        };
      case 'paypal':
        return {
          label: 'Enviar pagamento via:',
          value: paymentInfo.paypal?.link || 'paypal.me/LuisCanarias',
          copyValue: `https://${paymentInfo.paypal?.link || 'paypal.me/LuisCanarias'}/${selectedAmount}EUR`,
          isLink: true
        };
      case 'crypto':
        if (selectedCrypto && paymentInfo.crypto?.[selectedCrypto]) {
          return {
            label: `Enviar ${paymentInfo.crypto[selectedCrypto].symbol} para:`,
            value: paymentInfo.crypto[selectedCrypto].address,
            copyValue: paymentInfo.crypto[selectedCrypto].address,
            network: paymentInfo.crypto[selectedCrypto].network,
            showQR: true,
            color: paymentInfo.crypto[selectedCrypto].color
          };
        }
        return null;
      default:
        return null;
    }
  };

  if (!isOpen) return null;

  const paymentDetails = getPaymentDetails();

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
          <div className="bg-gradient-to-r from-[#FFBE98]/20 to-[#E6F4F1]/30 p-4 border-b border-stone-100">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="font-bold text-[#2D2A26]">Contribuir para a Viagem</h2>
                <p className="text-sm text-[#6B6661]">Destino: {journeyName}</p>
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
          <div className="p-4 overflow-y-auto max-h-[60vh]">
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
                      onClick={() => setStep(1)}
                      className="text-sm text-[#FFBE98] hover:underline"
                    >
                      Alterar valor
                    </button>
                  </div>

                  <p className="text-sm text-[#6B6661]">Escolhe o método de pagamento:</p>

                  {/* Payment methods */}
                  <div className="space-y-2">
                    {paymentMethods.map((method) => {
                      const Icon = method.icon;
                      return (
                        <button
                          key={method.id}
                          onClick={() => handleMethodSelect(method.id)}
                          disabled={loading}
                          className={`w-full p-3 rounded-xl border-2 transition-all flex items-center gap-3 ${
                            selectedMethod === method.id
                              ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                              : method.recommended
                              ? 'border-[#F7931A]/40 bg-gradient-to-r from-[#F7931A]/5 to-[#627EEA]/5 hover:border-[#F7931A]'
                              : 'border-stone-200 hover:border-stone-300'
                          }`}
                        >
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            method.recommended ? 'bg-[#F7931A]/20' : 'bg-stone-100'
                          }`}>
                            <Icon className={`w-5 h-5 ${method.recommended ? 'text-[#F7931A]' : 'text-[#6B6661]'}`} />
                          </div>
                          <div className="flex-1 text-left">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{method.name}</span>
                              {method.recommended && (
                                <span className="text-[10px] bg-[#F7931A] text-white px-2 py-0.5 rounded-full font-bold">
                                  TOP
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-[#6B6661]">{method.description}</span>
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
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="space-y-2"
                    >
                      <p className="text-sm text-[#6B6661]">Escolhe a moeda:</p>
                      <div className="grid grid-cols-4 gap-2">
                        {cryptoTypes.map((crypto) => (
                          <button
                            key={crypto.id}
                            onClick={() => handleCryptoSelect(crypto.id)}
                            disabled={loading}
                            className={`p-3 rounded-xl border-2 transition-all flex flex-col items-center ${
                              selectedCrypto === crypto.id
                                ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                                : 'border-stone-200 hover:border-stone-300'
                            }`}
                          >
                            <span className="font-bold text-sm" style={{ color: crypto.color }}>
                              {crypto.symbol}
                            </span>
                            {loading && selectedCrypto === crypto.id && (
                              <div className="w-4 h-4 border-2 border-[#FFBE98] border-t-transparent rounded-full animate-spin mt-1" />
                            )}
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              )}

              {/* STEP 3: Payment Instructions - Compact */}
              {step === 3 && !showConfirmation && contribution && (
                <motion.div
                  key="step3"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-3"
                >
                  {/* Summary - Single line */}
                  <div className="flex items-center justify-between text-sm bg-stone-50 rounded-lg px-3 py-2">
                    <span className="text-[#6B6661]">
                      <strong className="text-[#2D2A26]">€{selectedAmount}</strong> via <strong className="text-[#2D2A26]">{paymentMethods.find(m => m.id === selectedMethod)?.name}{selectedCrypto && ` (${selectedCrypto.toUpperCase()})`}</strong>
                    </span>
                    <button
                      onClick={() => { setStep(1); setContribution(null); }}
                      className="text-xs text-[#FFBE98] hover:underline"
                    >
                      Alterar
                    </button>
                  </div>

                  {/* Payment details - Compact */}
                  {paymentDetails && (
                    <div className="bg-white border border-stone-200 rounded-xl p-3">
                      {paymentDetails.showQR ? (
                        <div className="flex items-center gap-3">
                          <QRCodeSVG value={paymentDetails.value} size={80} />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-[#6B6661] mb-1">{paymentDetails.label}</p>
                            <p className="text-xs font-mono break-all bg-stone-50 p-2 rounded">{paymentDetails.value}</p>
                            {paymentDetails.network && (
                              <p className="text-xs mt-1" style={{ color: paymentDetails.color }}>Rede: {paymentDetails.network}</p>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs text-[#6B6661]">{paymentDetails.label}</p>
                            <p className="font-bold text-[#2D2A26]">{paymentDetails.value}</p>
                          </div>
                          {paymentDetails.isLink ? (
                            <a
                              href={paymentDetails.copyValue}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1.5 bg-[#0070BA] text-white rounded-lg text-sm flex items-center gap-1"
                            >
                              <ExternalLink className="w-3 h-3" />
                              Abrir
                            </a>
                          ) : (
                            <button
                              onClick={() => copyToClipboard(paymentDetails.copyValue)}
                              className="px-3 py-1.5 bg-stone-100 rounded-lg text-sm flex items-center gap-1 hover:bg-stone-200"
                            >
                              {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                              {copied ? 'OK' : 'Copiar'}
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Reference code - Compact */}
                  <div className="bg-[#FFBE98]/10 border border-[#FFBE98]/30 rounded-xl p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-[#6B6661]">Referência:</p>
                        <p className="text-xl font-bold text-[#2D2A26] tracking-wider">{contribution.payment_reference}</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(contribution.payment_reference)}
                        className="px-3 py-2 bg-[#FFBE98]/20 rounded-lg hover:bg-[#FFBE98]/30 flex items-center gap-1 text-sm"
                      >
                        {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4 text-[#FFBE98]" />}
                        <span className="text-[#FFBE98]">{copied ? 'OK' : 'Copiar'}</span>
                      </button>
                    </div>
                    <p className="text-xs text-[#6B6661] mt-1">Inclui este código na descrição do pagamento</p>
                    <p className="text-xs text-red-500 font-medium">⚠️ Sem esta referência não conseguiremos identificar o pagamento</p>
                  </div>

                  {/* Trust line - Compact */}
                  <p className="text-xs text-green-600 bg-green-50 p-2 rounded-lg flex items-center gap-1">
                    <Check className="w-3 h-3" />
                    Contribuição confirmada assim que recebermos o pagamento
                  </p>

                  {/* Confirm button */}
                  <button
                    onClick={() => setShowConfirmation(true)}
                    className="w-full bg-[#2D2A26] text-white py-3 px-6 rounded-xl font-medium hover:bg-[#4A4640] transition-all"
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
