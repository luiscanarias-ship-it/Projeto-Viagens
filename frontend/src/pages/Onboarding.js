import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Heart, ArrowRight } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Onboarding = () => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  const [journey, setJourney] = useState(null);
  const [progress, setProgress] = useState(null);

  const inviteAlias = localStorage.getItem('invite_alias') || '';
  const inviterName = localStorage.getItem('invite_name') || inviteAlias;
  const hasInviter = !!inviterName;

  useEffect(() => {
    axios.get(`${API}/homepage/main-journey`)
      .then(r => { setJourney(r.data?.journey); setProgress(r.data?.progress); })
      .catch(() => {});
  }, []);

  const goToJourney = () => {
    localStorage.removeItem('invite_alias');
    localStorage.removeItem('invite_name');
    try {
      axios.post(`${API}/user/complete-onboarding`, { initial_action: 'support' }, { headers: getAuthHeaders() }).catch(() => {});
    } catch {}
    if (journey?.journey_id) {
      navigate(`/journey/${journey.journey_id}`);
    } else {
      navigate('/');
    }
  };

  const pct = Math.min(100, Math.round(progress?.percentage || 0));

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/20 flex items-center justify-center p-6" data-testid="onboarding-page">
      <div className="max-w-md w-full">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-xl overflow-hidden">
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
                  Bem-vindo à <span className="text-[#FFBE98]">4Luis</span>
                </h1>
                <p className="text-sm text-[#6B6661]">
                  Todos juntos, ajudamos a realizar viagens de sonho
                </p>
              </>
            )}
          </div>

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
                  <p className="text-xs text-[#6B6661] text-center leading-relaxed" data-testid="onboarding-context-msg">
                    {hasInviter
                      ? `Foste convidado por ${inviterName} para ajudares a que esta viagem de sonho se torne uma realidade`
                      : 'Obrigado por ajudares a que esta viagem de sonho se torne uma realidade'}
                  </p>
                </div>
              </div>

              <button onClick={goToJourney}
                className="w-full mt-4 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#E6A07C] transition-colors"
                data-testid="onboarding-view-journey-btn">
                Ver viagem <ArrowRight className="w-4 h-4" />
              </button>

              <p className="text-sm font-semibold text-[#2D2A26] text-center mt-4 italic leading-relaxed"
                style={{ animation: 'pulse 4s cubic-bezier(0.4,0,0.6,1) infinite' }}
                data-testid="onboarding-dream-msg">
                Quem sabe se ao apoiares esta viagem de sonho não podes também tu realizares a tua...
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Onboarding;
