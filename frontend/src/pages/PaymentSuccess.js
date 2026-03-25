import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, Home, Users, Trophy, Lock } from 'lucide-react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import ShareMenu, { buildInviteLink } from '../components/ShareMenu';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const WhatsAppIcon = ({ className = "w-5 h-5" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

const PaymentSuccess = () => {
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const { user, getAuthHeaders } = useAuth();
  
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [ambassadorData, setAmbassadorData] = useState(null);
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    const checkPayment = async () => {
      if (!sessionId) {
        setPaymentStatus('error');
        return;
      }

      const maxAttempts = 5;
      const pollInterval = 2000;

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
          const response = await axios.get(`${API}/contributions/checkout-status/${sessionId}`, {
            headers: getAuthHeaders(),
            withCredentials: true
          });

          if (response.data.payment_status === 'paid') {
            setPaymentStatus('success');
            return;
          } else if (response.data.status === 'expired') {
            setPaymentStatus('error');
            return;
          }
        } catch (error) {
          console.error('Error checking payment:', error);
        }

        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }

      setPaymentStatus('success');
    };

    checkPayment();
  }, [sessionId, getAuthHeaders]);

  // Fetch ambassador progress for logged-in users
  useEffect(() => {
    if (!user) return;
    const fetchProgress = async () => {
      try {
        const res = await axios.get(`${API}/ambassador/progress`, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        if (res.data) setAmbassadorData(res.data);
      } catch (e) { /* silent */ }
    };
    fetchProgress();
  }, [user, getAuthHeaders]);

  const inviteLink = user?.anonymous_alias ? buildInviteLink(user.anonymous_alias) : null;
  const remaining = ambassadorData ? Math.max(0, ambassadorData.required - ambassadorData.valid_referrals) : null;
  const isAmbassador = ambassadorData?.is_ambassador;
  const progressPct = ambassadorData?.progress_pct || 0;

  const shareWhatsApp = () => {
    if (!inviteLink) return;
    const msg = `Acabei de ajudar a financiar uma viagem de sonho na 4Luis! Junta-te a mim:\n\n${inviteLink}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank');
  };

  if (paymentStatus === 'checking') {
    return (
      <div className="min-h-screen flex items-center justify-center dream-mesh pt-20">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#6B6661]">A verificar pagamento...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center dream-mesh pt-20 px-6" data-testid="payment-success">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="max-w-md w-full bg-white rounded-3xl p-8 shadow-xl text-center"
      >
        {paymentStatus === 'success' ? (
          <>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.2 }}
              className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
            >
              <CheckCircle className="w-10 h-10 text-green-500" />
            </motion.div>

            <h1 className="text-2xl font-bold text-[#2D2A26] mb-2" data-testid="success-title">
              Ja fazes parte deste sonho!
            </h1>

            <p className="text-[#FFBE98] text-sm italic mb-6" data-testid="success-subtitle">
              A tua contribuicao esta a ajudar a tornar este sonho realidade
            </p>

            {/* Ambassador Referral CTA — Primary action */}
            {user && !isAmbassador && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-gradient-to-br from-[#FFF8F0] to-[#FFBE98]/10 rounded-xl border border-[#FFBE98]/30 p-5 mb-4 text-left"
                data-testid="referral-cta-success"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-[#FFBE98]/15 rounded-xl flex items-center justify-center shrink-0">
                    <Trophy className="w-5 h-5 text-[#FFBE98]" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-[#2D2A26]">Queres acelerar este sonho?</p>
                    {remaining !== null && remaining > 0 && (
                      <p className="text-xs text-[#6B6661]" data-testid="remaining-referrals">
                        Faltam-te <strong className="text-[#FFBE98]">{remaining}</strong> amigo{remaining > 1 ? 's' : ''} para seres Embaixador
                      </p>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                {ambassadorData && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-medium text-[#6B6661]">Progresso</span>
                      <span className="text-[10px] font-bold text-[#FFBE98]">{ambassadorData.valid_referrals}/{ambassadorData.required}</span>
                    </div>
                    <div className="w-full bg-stone-100 rounded-full h-2">
                      <motion.div
                        className="bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] h-2 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${progressPct}%` }}
                        transition={{ duration: 0.8, delay: 0.6 }}
                      />
                    </div>
                    <div className="flex justify-between mt-1">
                      {[...Array(ambassadorData.required)].map((_, i) => (
                        <div key={i} className={`flex items-center gap-0.5 text-[9px] ${i < ambassadorData.valid_referrals ? 'text-[#FFBE98] font-semibold' : 'text-stone-400'}`}>
                          <Users className="w-2.5 h-2.5" />
                          <span>{i + 1}</span>
                          {i < ambassadorData.valid_referrals && <CheckCircle className="w-2.5 h-2.5" />}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* WhatsApp primary + ShareMenu */}
                {inviteLink ? (
                  <div className="space-y-2">
                    <button
                      onClick={shareWhatsApp}
                      className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#25D366] text-white rounded-xl text-sm font-semibold hover:bg-[#20bd5a] transition-colors"
                      data-testid="whatsapp-invite-btn"
                    >
                      <WhatsAppIcon className="w-4 h-4" />
                      Convidar amigos por WhatsApp
                    </button>
                    <ShareMenu
                      inviteLink={inviteLink}
                      senderName={user?.name}
                      customMessage={`Acabei de ajudar a financiar uma viagem de sonho na 4Luis! Junta-te a mim:\n\n${inviteLink}`}
                      buttonLabel="Mais formas de convidar"
                      buttonClassName="w-full flex items-center justify-center gap-2 py-2 bg-white border border-stone-200 text-[#2D2A26] rounded-xl text-xs font-medium hover:bg-stone-50 transition-colors"
                    />
                  </div>
                ) : (
                  <Link
                    to="/login"
                    className="w-full inline-flex items-center justify-center gap-2 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-semibold hover:bg-[#FFB080] transition-colors"
                    data-testid="register-to-invite-btn"
                  >
                    <Users className="w-4 h-4" />
                    Convidar amigos
                  </Link>
                )}

                {/* What you unlock */}
                <div className="mt-3 pt-3 border-t border-[#FFBE98]/15">
                  <p className="text-[10px] font-semibold text-[#6B6661] mb-1.5">Como Embaixador desbloqueia:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {['Mapa interativo', 'Assistente IA', 'Dicas locais', 'Guia Premium'].map(f => (
                      <span key={f} className="text-[9px] px-2 py-0.5 bg-white rounded-full border border-stone-100 text-[#6B6661] flex items-center gap-1">
                        <Lock className="w-2.5 h-2.5 text-[#FFBE98]" />{f}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Ambassador badge */}
            {user && isAmbassador && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="bg-gradient-to-r from-[#FFBE98]/15 to-transparent rounded-xl border border-[#FFBE98]/20 p-4 mb-4"
                data-testid="ambassador-badge-success"
              >
                <div className="flex items-center justify-center gap-2">
                  <Trophy className="w-5 h-5 text-[#FFBE98]" />
                  <p className="text-sm font-bold text-[#2D2A26]">Embaixador 4Luis</p>
                </div>
                <p className="text-[11px] text-[#6B6661] mt-1">Obrigado por continuares a apoiar sonhos!</p>
              </motion.div>
            )}

            {/* Non-logged user — register CTA with referral hook */}
            {!user && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-stone-50 rounded-xl p-5 mb-4 space-y-3"
                data-testid="register-referral-cta"
              >
                <p className="text-sm font-semibold text-[#2D2A26]">Queres acelerar este sonho?</p>
                <p className="text-xs text-[#6B6661]">
                  Cria conta para convidar amigos e desbloquear funcionalidades exclusivas
                </p>
                <Link
                  to="/login"
                  className="w-full inline-flex items-center justify-center gap-2 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-semibold hover:bg-[#FFB080] transition-colors"
                  data-testid="register-cta-success"
                >
                  <Users className="w-4 h-4" />
                  Criar conta e convidar amigos
                </Link>
              </motion.div>
            )}

            <Link
              to="/"
              className="inline-flex items-center justify-center gap-2 text-sm text-[#6B6661] hover:text-[#2D2A26] transition-colors mt-2"
              data-testid="back-home-btn"
            >
              <Home className="w-4 h-4" />
              Voltar ao inicio
            </Link>
          </>
        ) : (
          <>
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">!</span>
            </div>
            <h1 className="text-2xl font-bold text-[#2D2A26] mb-4">
              Algo correu mal
            </h1>
            <p className="text-[#6B6661] mb-6">
              Nao foi possivel confirmar o pagamento. Por favor, entre em contacto.
            </p>
            <Link to="/" className="btn-primary inline-block" data-testid="error-home-btn">
              Voltar ao Inicio
            </Link>
          </>
        )}
      </motion.div>
    </div>
  );
};

export default PaymentSuccess;
