import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Shield } from 'lucide-react';

const COOKIE_KEY = '4luis_cookie_consent';
const CONSENT_DURATION_MS = 6 * 30 * 24 * 60 * 60 * 1000; // ~6 months

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

function saveConsent(preferences) {
  localStorage.setItem(COOKIE_KEY, JSON.stringify({
    ...preferences,
    timestamp: Date.now(),
    expires: Date.now() + CONSENT_DURATION_MS,
  }));
}

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [prefs, setPrefs] = useState({ essential: true, analytics: true, marketing: false });

  useEffect(() => {
    const consent = getConsent();
    if (!consent) {
      const timer = setTimeout(() => setVisible(true), 1500);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleAccept = () => {
    saveConsent({ essential: true, analytics: true, marketing: true });
    setVisible(false);
  };

  const handleSavePrefs = () => {
    saveConsent(prefs);
    setVisible(false);
    setShowSettings(false);
  };

  if (!visible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed bottom-0 left-0 right-0 z-[9999] p-4 md:p-6"
        data-testid="cookie-banner"
      >
        <div className="max-w-4xl mx-auto bg-[#2D2A26] rounded-2xl shadow-2xl overflow-hidden border border-white/10">
          {!showSettings ? (
            /* Main Banner */
            <div className="flex flex-col sm:flex-row items-center gap-4 p-5 md:p-6">
              <img
                src={COOKIE_IMG}
                alt="Cookie a sonhar"
                className="w-16 h-16 md:w-20 md:h-20 rounded-xl object-cover flex-shrink-0"
              />
              <div className="flex-1 text-center sm:text-left">
                <p className="text-white text-sm md:text-base leading-relaxed">
                  Utilizamos cookies para melhorar a experiencia
                  na plataforma <strong className="text-[#FFBE98]">4Luis</strong> e analisar o trafego do site.
                </p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => setShowSettings(true)}
                  className="px-4 py-2.5 text-white/70 hover:text-white border border-white/20 hover:border-white/40 rounded-xl text-sm font-medium transition-all"
                  data-testid="cookie-configure-btn"
                >
                  Configurar
                </button>
                <button
                  onClick={handleAccept}
                  className="px-6 py-2.5 bg-[#FFBE98] hover:bg-[#FFAB7D] text-[#2D2A26] rounded-xl text-sm font-bold transition-colors"
                  data-testid="cookie-accept-btn"
                >
                  Aceitar
                </button>
              </div>
            </div>
          ) : (
            /* Settings Panel */
            <div className="p-5 md:p-6">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-[#FFBE98]" />
                  <h3 className="text-white font-bold text-base">Preferencias de Cookies</h3>
                </div>
                <button
                  onClick={() => setShowSettings(false)}
                  className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-white/60" />
                </button>
              </div>

              <div className="space-y-3 mb-5">
                <label className="flex items-center justify-between p-3 bg-white/5 rounded-xl">
                  <div>
                    <p className="text-white text-sm font-medium">Essenciais</p>
                    <p className="text-white/50 text-xs">Necessarios para o funcionamento do site</p>
                  </div>
                  <input type="checkbox" checked disabled className="w-5 h-5 rounded accent-[#FFBE98]" />
                </label>
                <label className="flex items-center justify-between p-3 bg-white/5 rounded-xl cursor-pointer">
                  <div>
                    <p className="text-white text-sm font-medium">Analiticos</p>
                    <p className="text-white/50 text-xs">Ajudam a entender como o site e utilizado</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={prefs.analytics}
                    onChange={(e) => setPrefs({ ...prefs, analytics: e.target.checked })}
                    className="w-5 h-5 rounded accent-[#FFBE98] cursor-pointer"
                    data-testid="cookie-analytics-toggle"
                  />
                </label>
                <label className="flex items-center justify-between p-3 bg-white/5 rounded-xl cursor-pointer">
                  <div>
                    <p className="text-white text-sm font-medium">Marketing</p>
                    <p className="text-white/50 text-xs">Permitem personalizar conteudo e anuncios</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={prefs.marketing}
                    onChange={(e) => setPrefs({ ...prefs, marketing: e.target.checked })}
                    className="w-5 h-5 rounded accent-[#FFBE98] cursor-pointer"
                    data-testid="cookie-marketing-toggle"
                  />
                </label>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowSettings(false)}
                  className="px-4 py-2.5 text-white/70 hover:text-white text-sm font-medium transition-colors"
                >
                  Voltar
                </button>
                <button
                  onClick={handleSavePrefs}
                  className="px-6 py-2.5 bg-[#FFBE98] hover:bg-[#FFAB7D] text-[#2D2A26] rounded-xl text-sm font-bold transition-colors"
                  data-testid="cookie-save-prefs-btn"
                >
                  Guardar preferencias
                </button>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
