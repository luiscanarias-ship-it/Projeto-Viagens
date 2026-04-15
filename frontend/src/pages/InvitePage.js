import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Heart, Users, ArrowRight } from 'lucide-react';
import axios from 'axios';
import ShareMenu, { buildInviteLink } from '../components/ShareMenu';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const InvitePage = () => {
  const { alias } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Store invite context for post-registration onboarding
    localStorage.setItem('invite_alias', alias);
    if (data?.inviter_name) localStorage.setItem('invite_name', data.inviter_name);
    
    axios.get(`${API}/invite/${encodeURIComponent(alias)}`)
      .then(res => {
        setData(res.data);
        if (res.data?.inviter_name) localStorage.setItem('invite_name', res.data.inviter_name);
      })
      .catch(() => setError('Convite não encontrado'))
      .finally(() => setLoading(false));
  }, [alias]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAF9]">
        <div className="w-8 h-8 border-3 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAF9] px-6">
        <div className="text-center">
          <p className="text-lg text-[#6B6661] mb-4">Convite não encontrado</p>
          <button onClick={() => navigate('/')} className="text-[#FFBE98] font-medium hover:underline">
            Ir para a homepage
          </button>
        </div>
      </div>
    );
  }

  const journey = data.journey;
  const progress = journey && journey.goal ? Math.min(100, Math.round((journey.current_amount / journey.goal) * 100)) : 0;
  const sponsorParam = data.sponsor_link_id ? `?sponsor=${data.sponsor_link_id}` : '';

  return (
    <div className="min-h-screen bg-[#FAFAF9] flex flex-col items-center justify-center px-6 py-12" data-testid="invite-page">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-md w-full"
      >
        {/* Invite card */}
        <div className="bg-white rounded-3xl shadow-xl overflow-hidden border border-stone-100">
          {/* Header with journey image */}
          {journey?.image_url && (
            <div className="relative h-48 overflow-hidden">
              <img src={journey.image_url} alt={journey.name} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-4 left-4 right-4">
                <p className="text-white/80 text-sm">Viagem Principal</p>
                <h2 className="text-2xl font-bold text-white">{journey.name}</h2>
              </div>
            </div>
          )}

          <div className="p-6 space-y-5">
            {/* Social proof messages */}
            <div className="text-center space-y-2">
              <div className="w-14 h-14 bg-[#FFBE98]/15 rounded-full flex items-center justify-center mx-auto mb-3">
                <Users className="w-7 h-7 text-[#FFBE98]" />
              </div>
              <p className="text-lg text-[#2D2A26]" data-testid="invite-main-msg">
                <strong>{data.inviter_name}</strong> convidou-te para ajudar a realizar este sonho.
              </p>
              {data.inviter_has_contributed && (
                <p className="text-sm text-[#FFBE98] font-semibold" data-testid="inviter-contributed-msg">
                  {data.inviter_name} já contribuiu para este sonho.
                </p>
              )}
              <p className="text-sm text-[#6B6661] leading-relaxed" data-testid="cooperative-msg">
                Ao participar, também podes tornar-te Embaixador<br />
                e desbloquear acesso especial.
              </p>
            </div>

            {/* Progress bar */}
            {journey && (
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-[#6B6661]">Progresso</span>
                  <span className="font-bold text-[#2D2A26]">{progress}%</span>
                </div>
                <div className="h-3 bg-stone-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full"
                  />
                </div>
                <div className="flex justify-between text-xs text-[#6B6661] mt-1">
                  <span>{journey.current_amount?.toFixed(0) || 0}€</span>
                  <span>{journey.goal?.toFixed(0) || 0}€</span>
                </div>
              </div>
            )}

            {/* CTA Button */}
            <button
              onClick={() => navigate(journey ? `/journey/${journey.journey_id}${sponsorParam}` : '/')}
              className="w-full py-3.5 bg-[#2D2A26] text-white rounded-xl font-semibold flex items-center justify-center gap-2 hover:bg-[#4A4640] transition-colors"
              data-testid="invite-contribute-btn"
            >
              <Heart className="w-5 h-5" />
              Contribuir para a viagem
              <ArrowRight className="w-4 h-4" />
            </button>

            <p className="text-xs text-center text-[#6B6661]/80 italic" data-testid="invite-register-hint">
              Cria uma conta para acompanhar este sonho e desbloquear novas funcionalidades.
            </p>

            {/* Share this dream */}
            <div className="pt-2 flex justify-center">
              <ShareMenu
                inviteLink={buildInviteLink(alias)}
                senderName={data?.inviter_name}
                buttonLabel="Partilhar este sonho"
                buttonClassName="flex items-center justify-center gap-2 py-2.5 px-5 bg-stone-100 text-[#2D2A26] rounded-xl text-sm font-semibold hover:bg-stone-200 transition-colors"
              />
            </div>
          </div>
        </div>
      </motion.div>
      {/* Brand tagline */}
      <div className="text-center py-8">
        <span className="text-lg font-bold text-[#2D2A26]">4Luis</span>
        <p className="font-handwritten text-[#FFBE98] text-lg mt-1">Sonha connosco.</p>
      </div>
    </div>
  );
};

export default InvitePage;
