import React from 'react';
import { Smartphone, Bitcoin, CreditCard, ShieldCheck, Lock, MapPin } from 'lucide-react';
import { PayPalScriptProvider, PayPalButtons } from '@paypal/react-paypal-js';

/**
 * PaymentMethods — renders geo-prioritized payment method buttons.
 * Extracted from CheckoutModal Step 2.
 */
const PaymentMethods = ({
  isPortugal,
  paypalClientId,
  paypalError,
  paypalProcessing,
  totalPayment,
  journeyId,
  selectedTip,
  selectedMethod,
  loading,
  handleMethodSelect,
  createPayPalOrder,
  onPayPalApprove,
  onPayPalError,
  setPaypalProcessing
}) => {
  return (
    <>
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
            <PayPalBlock
              paypalClientId={paypalClientId}
              paypalError={paypalError}
              paypalProcessing={paypalProcessing}
              totalPayment={totalPayment}
              journeyId={journeyId}
              selectedTip={selectedTip}
              createPayPalOrder={createPayPalOrder}
              onPayPalApprove={onPayPalApprove}
              onPayPalError={onPayPalError}
              setPaypalProcessing={setPaypalProcessing}
            />
          )}
        </>
      ) : (
        <>
          {paypalClientId && (
            <PayPalBlock
              paypalClientId={paypalClientId}
              paypalError={paypalError}
              paypalProcessing={paypalProcessing}
              totalPayment={totalPayment}
              journeyId={journeyId}
              selectedTip={selectedTip}
              createPayPalOrder={createPayPalOrder}
              onPayPalApprove={onPayPalApprove}
              onPayPalError={onPayPalError}
              setPaypalProcessing={setPaypalProcessing}
              showTrustText
            />
          )}
        </>
      )}

      {/* SECONDARY METHODS */}
      <div className="grid grid-cols-2 gap-1.5">
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

        {isPortugal && (
          <div className="p-2.5 rounded-xl border-2 border-stone-200 bg-stone-50/50 text-center opacity-60 cursor-not-allowed" data-testid="multibanco-soon-btn">
            <CreditCard className="w-5 h-5 text-[#6B6661] mx-auto" />
            <span className="text-xs font-medium block mt-1">Multibanco</span>
            <span className="text-[9px] text-[#6B6661]">Em breve</span>
          </div>
        )}
      </div>
    </>
  );
};

// Internal PayPal block component
const PayPalBlock = ({
  paypalClientId, paypalError, paypalProcessing, totalPayment,
  journeyId, selectedTip, createPayPalOrder, onPayPalApprove, onPayPalError,
  setPaypalProcessing, showTrustText = false
}) => (
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
      {paypalError && <p className="text-xs text-red-500 mb-2">{paypalError}</p>}
      <PayPalScriptProvider options={{ clientId: paypalClientId, currency: "EUR", intent: "capture", "enable-funding": "card" }}>
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
      {showTrustText && (
        <p className="text-[10px] text-center text-[#6B6661]/70 mt-1.5" data-testid="paypal-trust-text">
          Não partilhamos os teus dados bancários.
        </p>
      )}
    </div>
  </div>
);

export default PaymentMethods;
