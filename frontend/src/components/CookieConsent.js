import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';

const COOKIE_KEY = '4luis_cookie_consent';
const CONSENT_DURATION_MS = 6 * 30 * 24 * 60 * 60 * 1000;

const COOKIE_IMG = 'https://static.prod-images.emergentagent.com/jobs/8a5b92db-fc59-4780-b378-fec6b9aa8e90/images/60d59430be7bad45065488503910150dede4ed708858f32128aeaf27e89e35e3.png';

function getConsent() {
  try {
    const raw = localStorage.getItem(COOKIE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (Date.now() > data.expires) {
      localStorage.removeItem(COOKIE_KEY);
      return null;
    }
    return data;
  } catch { return null; }
}

function saveConsent(accepted) {
  localStorage.setItem(COOKIE_KEY, JSON.stringify({
    accepted,
    timestamp: Date.now(),
    expires: Date.now() + CONSENT_DURATION_MS,
  }));
}

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = getConsent();
    if (!consent) {
      const timer = setTimeout(() => setVisible(true), 15000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    saveConsent(true);
    setVisible(false);
  };

  const handleDecline = () => {
    saveConsent(false);
    setVisible(false);
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ y: 40, opacity: 0, scale: 0.95 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 40, opacity: 0, scale: 0.95 }}
          transition={{ type: 'spring', damping: 20, stiffness: 250 }}
          className="fixed bottom-6 right-6 z-[9999] max-w-sm"
          data-testid="cookie-banner"
        >
          <div className="bg-white rounded-2xl shadow-2xl border border-stone-100 p-6 relative">
            {/* Cookie image */}
            <div className="flex justify-center mb-4">
              <img
                src={COOKIE_IMG}
                alt="Cookie a sonhar"
                className="w-20 h-20 object-cover rounded-full"
              />
            </div>

            {/* Text */}
            <div className="text-center space-y-3 mb-5">
              <p className="text-[#2D2A26] font-bold text-lg">
                Ola... Nos somos as cookies!
              </p>
              <p className="text-[#6B6661] text-sm leading-relaxed">
                Esperamos um pouco para ter a certeza que o conteudo do nosso site te interessava antes de te incomodar.
              </p>
              <p className="text-[#2D2A26] font-semibold text-base">
                Autorizas-nos?
              </p>
              <p className="text-xs text-[#6B6661]">
                Podes ler a nossa politica{' '}
                <Link
                  to="/politica-cookies"
                  className="text-[#FFBE98] font-semibold underline hover:text-[#E6A07C] transition-colors"
                  data-testid="cookie-policy-link"
                >
                  aqui
                </Link>
              </p>
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleDecline}
                className="flex-1 py-2.5 text-[#6B6661] border border-stone-200 rounded-xl text-sm font-medium hover:bg-stone-50 transition-colors"
                data-testid="cookie-decline-btn"
              >
                Nao, obrigado
              </button>
              <button
                onClick={handleAccept}
                className="flex-1 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-bold hover:bg-[#FFAB7D] transition-colors"
                data-testid="cookie-accept-btn"
              >
                Aceitar
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
