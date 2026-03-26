import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, ArrowRight, Gift, UserPlus, Award } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import CheckoutModal from '../components/CheckoutModal';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Onboarding = () => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  const [step, setStep] = useState(0);
  const [journey, setJourney] = useState(null);
  const [progress, setProgress] = useState(null);
  const [showCheckout, setShowCheckout] = useState(false);

  const inviteAlias = localStorage.getItem('invite_alias') || '';
  const inviterName = localStorage.getItem('invite_name') || inviteAlias;
  const hasInviter = !!inviterName;

  useEffect(() => {
    axios.get(`${API}/homepage/main-journey`)
      .then(r => { setJourney(r.data?.journey); setProgress(r.data?.progress); })
      .catch(() => {});
  }, []);

  const completeOnboarding = async (action) => {
    try {
      await axios.post(`${API}/user/complete-onboarding`, { initial_action: action }, { headers: getAuthHeaders() });
    } catch {}
    localStorage.removeItem('invite_alias');
    localStorage.removeItem('invite_name');
  };

  const goContribute = () => {
    completeOnboarding('support');
    setShowCheckout(true);
  };

  const goSkip = () => {
    completeOnboarding('explore');
    navigate('/');
  };

  const pct = Math.min(100, Math.round(progress?.percentage || 0));

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/20 flex items-center justify-center p-6" data-testid="onboarding-page">
      <div className="max-w-md w-full">

        {/* Dots */}
        <div className="flex gap-2 justify-center mb-6">
          {[0, 1].map(i => (
            <div key={i} className={`h-1.5 rounded-full transition-all duration-300 ${i === step ? 'w-7 bg-[#FFBE98]' : i < step ? 'w-2 bg-[#FFBE98]/60' : 'w-2 bg-stone-200'}`} />
          ))}
        </div>

        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <AnimatePresence mode="wait">

            {/* ── Step 1: Referral Context + Journey ── */}
            {step === 0 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
                <div className="p-6 text-center">
                  <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: 'spring', delay: 0.15 }}
                    className="w-14 h-14 bg-gradient-to-br from-[#FFBE98] to-[#E6A07C] rounded-full flex items-center justify-center mx-auto mb-4">
                    <Heart className="w-7 h-7 text-white" />
                  </motion.div>

                  {hasInviter ? (
                    <>
                      <h1 className="text-xl font-bold text-[#2D2A26] mb-1" data-testid="welcome-title">
                        Foste convidado por <span className="text-[#FFBE98]">{inviterName}</span>
                      </h1>
                      <p className="text-sm text-[#6B6661]">
                        {inviterName} está a apoiar uma viagem de sonho na 4Luis
                      </p>
                    </>
                  ) : (
                    <>
                      <h1 className="text-xl font-bold text-[#2D2A26] mb-1" data-testid="welcome-title">
                        Bem-vindo ao <span className="text-[#FFBE98]">4Luis</span>
                      </h1>
                      <p className="text-sm text-[#6B6661]">
                        Estamos a apoiar uma viagem de sonho em comunidade
                      </p>
                    </>
                  )}
                </div>

                {/* Journey Card */}
                {journey && (
                  <div className="px-5 pb-5">
                    <div className="rounded-xl overflow-hidden border border-stone-100">
                      <div className="relative h-36 overflow-hidden">
                        <img src={journey.image_url} alt={journey.name} className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                        <div className="absolute bottom-3 left-4">
                          <p className="text-white/70 text-[10px] font-medium uppercase tracking-wider">Viagem principal</p>
                          <h2 className="text-lg font-bold text-white">{journey.name}</h2>
                        </div>
                      </div>
                      <div className="p-4">
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-[#6B6661]">Progresso</span>
                          <span className="font-bold text-[#2D2A26]">{pct}%</span>
                        </div>
                        <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }}
                            transition={{ duration: 1.2, ease: 'easeOut', delay: 0.4 }}
                            className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full" />
                        </div>
                      </div>
                    </div>

                    <button onClick={() => setStep(1)}
                      className="w-full mt-4 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#E6A07C] transition-colors"
                      data-testid="onboarding-view-journey-btn">
                      Ver viagem <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </motion.div>
            )}

            {/* ── Step 2: Quick Explanation + CTA ── */}
            {step === 1 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
                <div className="p-6">
                  <h2 className="text-lg font-bold text-[#2D2A26] text-center mb-5" data-testid="how-it-works-title">Como funciona</h2>

                  <div className="space-y-2.5 mb-6">
                    {[
                      { num: 1, icon: Gift, text: 'Apoias uma viagem', color: 'bg-[#FFBE98]' },
                      { num: 2, icon: UserPlus, text: 'Convidas amigos', color: 'bg-[#E6F4F1]' },
                      { num: 3, icon: Award, text: 'Tornas-te Embaixador', color: 'bg-gradient-to-br from-[#F2C94C] to-[#FFBE98]' },
                    ].map((s, i) => (
                      <motion.div key={s.num}
                        initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.12 }}
                        className="flex items-center gap-3 p-3 bg-stone-50 rounded-xl">
                        <div className={`w-9 h-9 ${s.color} rounded-full flex items-center justify-center shrink-0`}>
                          <s.icon className="w-4 h-4 text-white" />
                        </div>
                        <p className="text-sm font-semibold text-[#2D2A26]">{s.num}. {s.text}</p>
                      </motion.div>
                    ))}
                  </div>

                  {/* Primary CTA */}
                  <button onClick={goContribute}
                    className="w-full py-3.5 bg-[#2D2A26] text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#1D1A16] transition-colors"
                    style={{ animation: 'pulse 4s cubic-bezier(0.4,0,0.6,1) infinite' }}
                    data-testid="onboarding-contribute-btn">
                    <Heart className="w-4 h-4 text-[#FFBE98]" /> Apoiar a viagem principal
                  </button>

                  <button onClick={goSkip}
                    className="w-full mt-2 py-2 text-xs text-[#6B6661] hover:text-[#2D2A26] transition-colors text-center"
                    data-testid="skip-onboarding-btn">
                    Explorar primeiro
                  </button>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>

      {/* Checkout Modal */}
      {journey && (
        <CheckoutModal
          isOpen={showCheckout}
          onClose={() => { setShowCheckout(false); navigate('/'); }}
          journeyName={journey.name}
          journeyId={journey.journey_id}
          getAuthHeaders={getAuthHeaders}
          user={user}
        />
      )}
    </div>
  );
};

export default Onboarding;
