import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Heart, Users, Award, Plane, Gift, UserPlus, 
  Sparkles, ChevronRight, Star, Briefcase
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import CheckoutModal from '../components/CheckoutModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const InviteOnboarding = () => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  const [journey, setJourney] = useState(null);
  const [progress, setProgress] = useState(null);
  const [showCheckout, setShowCheckout] = useState(false);

  const inviteAlias = localStorage.getItem('invite_alias') || '';
  const inviterName = localStorage.getItem('invite_name') || inviteAlias;

  useEffect(() => {
    const fetchMainJourney = async () => {
      try {
        const res = await axios.get(`${API}/homepage/main-journey`);
        if (res.data?.journey) {
          setJourney(res.data.journey);
          setProgress(res.data.progress);
        }
      } catch (e) {
        console.error('Error fetching main journey:', e);
      }
    };
    fetchMainJourney();
  }, []);

  const handleContinue = () => {
    localStorage.removeItem('invite_alias');
    localStorage.removeItem('invite_name');
    navigate('/dashboard');
  };

  const progressPercent = progress?.percentage
    ? Math.min(100, Math.round(progress.percentage))
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FAFAF9] via-white to-[#E6F4F1]/20" data-testid="invite-onboarding">

      {/* 1 — Welcome message */}
      <section className="pt-24 pb-12 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-lg mx-auto text-center"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-[#FFBE98] to-[#E6A07C] rounded-full flex items-center justify-center mx-auto mb-6">
            <Heart className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4" data-testid="welcome-title">
            Bem-vindo à comunidade de sonhadores.
          </h1>
          <p className="text-lg text-[#6B6661] leading-relaxed">
            Foste convidado por <strong className="text-[#FFBE98]">{inviterName}</strong> para ajudar a financiar uma viagem de sonho.
          </p>
        </motion.div>
      </section>

      {/* 2 — Main journey */}
      {journey && (
        <section className="pb-12 px-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-lg mx-auto"
          >
            <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-stone-100">
              <div className="relative h-56 overflow-hidden">
                <img src={journey.image_url} alt={journey.name} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                <div className="absolute bottom-4 left-5 right-5">
                  <p className="text-white/80 text-sm font-medium">Viagem Principal</p>
                  <h2 className="text-2xl font-bold text-white">{journey.name}</h2>
                </div>
              </div>

              <div className="p-6 space-y-4">
                {/* Progress bar */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-[#6B6661]">Progresso</span>
                    <span className="font-bold text-[#2D2A26]">{progressPercent}%</span>
                  </div>
                  <div className="h-3 bg-stone-100 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${progressPercent}%` }}
                      transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
                      className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full"
                    />
                  </div>
                </div>

                {/* CTA */}
                <button
                  onClick={() => setShowCheckout(true)}
                  className="w-full py-3.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-[#FFAB7D] transition-colors"
                  data-testid="onboarding-contribute-btn"
                >
                  <Heart className="w-5 h-5" />
                  Contribuir para este sonho
                </button>
              </div>
            </div>
          </motion.div>
        </section>
      )}

      {/* 3 — How to unlock your dream */}
      <section className="pb-12 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-lg mx-auto"
        >
          <h2 className="text-2xl font-bold text-[#2D2A26] text-center mb-6" data-testid="progression-title">
            Como desbloquear o teu próprio sonho
          </h2>

          <div className="space-y-3">
            {[
              { num: 1, icon: Gift, title: 'Contribui para a viagem principal', color: 'bg-[#FFBE98]' },
              { num: 2, icon: UserPlus, title: 'Convida 3 amigos a contribuir', color: 'bg-[#E6F4F1]' },
              { num: 3, icon: Award, title: 'Torna-te Embaixador', color: 'bg-gradient-to-br from-[#F2C94C] to-[#FFBE98]' },
            ].map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="flex items-center gap-4 p-4 bg-white rounded-xl border border-stone-100 shadow-sm"
              >
                <div className={`w-11 h-11 ${step.color} rounded-full flex items-center justify-center flex-shrink-0`}>
                  <step.icon className="w-5 h-5 text-white" />
                </div>
                <p className="font-semibold text-[#2D2A26]">{step.title}</p>
                <ChevronRight className="w-5 h-5 text-stone-300 ml-auto flex-shrink-0" />
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* 4 — Ambassador benefits */}
      <section className="pb-12 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-lg mx-auto"
        >
          <div className="bg-gradient-to-br from-[#2D2A26] to-[#4A4640] rounded-3xl p-6 md:p-8 text-white" data-testid="benefits-block">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-[#F2C94C] rounded-full flex items-center justify-center">
                <Star className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-bold">Quando te tornas Embaixador:</h3>
            </div>

            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <Plane className="w-5 h-5 text-[#FFBE98] flex-shrink-0 mt-0.5" />
                <p className="text-white/90">Podes angariar financiamento para a tua própria viagem</p>
              </li>
              <li className="flex items-start gap-3">
                <Briefcase className="w-5 h-5 text-[#FFBE98] flex-shrink-0 mt-0.5" />
                <p className="text-white/90">Ganhas acesso a vouchers e ofertas especiais de parceiros</p>
              </li>
              <li className="flex items-start gap-3">
                <Users className="w-5 h-5 text-[#FFBE98] flex-shrink-0 mt-0.5" />
                <p className="text-white/90">Participas mais ativamente na comunidade de sonhadores</p>
              </li>
            </ul>
          </div>
        </motion.div>
      </section>

      {/* 5 — Initial progress */}
      <section className="pb-12 px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-lg mx-auto"
        >
          <div className="bg-white rounded-3xl p-6 md:p-8 shadow-lg border border-stone-100" data-testid="progress-block">
            <h3 className="text-lg font-bold text-[#2D2A26] mb-5">Progresso para Embaixador</h3>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-3 bg-stone-50 rounded-xl">
                <div className="w-7 h-7 rounded-full border-2 border-stone-300 flex-shrink-0" />
                <p className="text-[#6B6661]">Contribuir para a viagem principal</p>
              </div>
              <div className="flex items-center gap-3 p-3 bg-stone-50 rounded-xl">
                <div className="w-7 h-7 rounded-full border-2 border-stone-300 flex-shrink-0" />
                <p className="text-[#6B6661]">Convidar 3 amigos</p>
              </div>
            </div>

            <div className="mt-4 h-2 bg-stone-100 rounded-full overflow-hidden">
              <div className="h-full w-0 bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full" />
            </div>
            <p className="text-xs text-[#6B6661] mt-2 text-right">0 / 2 requisitos</p>
          </div>
        </motion.div>
      </section>

      {/* 6 — Inspirational message */}
      <section className="pb-8 px-6">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="max-w-lg mx-auto text-center"
        >
          <p className="font-handwritten text-2xl md:text-3xl text-[#6B6661] leading-relaxed" data-testid="inspirational-quote">
            "Quando os sonhos são partilhados,<br />
            <span className="text-[#FFBE98]">tornam-se possíveis.</span>"
          </p>
        </motion.div>
      </section>

      {/* Continue button */}
      <section className="pb-16 px-6">
        <div className="max-w-lg mx-auto">
          <button
            onClick={handleContinue}
            className="w-full py-4 bg-[#2D2A26] text-white rounded-xl font-bold text-lg flex items-center justify-center gap-2 hover:bg-[#4A4640] transition-colors"
            data-testid="onboarding-continue-btn"
          >
            Ir para o Meu Painel
            <Sparkles className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Checkout Modal */}
      {journey && (
        <CheckoutModal
          isOpen={showCheckout}
          onClose={() => setShowCheckout(false)}
          journeyName={journey.name}
          journeyId={journey.journey_id}
          getAuthHeaders={getAuthHeaders}
          user={user}
        />
      )}
    </div>
  );
};

export default InviteOnboarding;
