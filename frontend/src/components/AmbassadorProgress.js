import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Users, Copy, Check, Share2, Lock, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export const AmbassadorProgress = ({ token, compact = false }) => {
  const [progress, setProgress] = useState(null);
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [generating, setGenerating] = useState(false);

  const fetchProgress = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/ambassador/progress`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setProgress(await res.json());
    } catch (e) { /* silent */ }
  }, [token]);

  useEffect(() => { fetchProgress(); }, [fetchProgress]);

  const generateLink = async () => {
    if (!token || generating) return;
    setGenerating(true);
    try {
      const res = await fetch(`${API}/api/ambassador/generate-referral`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        await fetchProgress();
      }
    } catch (e) { /* silent */ }
    setGenerating(false);
  };

  const shareLink = () => {
    if (!progress?.referral_code) return;
    const url = `${window.location.origin}/?ref=${progress.referral_code}`;
    const msg = `Ajuda-me a realizar esta viagem e desbloqueia o acesso ao Roteiro Premium para as tuas viagens! ${url}`;
    const waUrl = `https://wa.me/?text=${encodeURIComponent(msg)}`;
    window.open(waUrl, '_blank');
  };

  const copyLink = () => {
    if (!progress?.referral_code) return;
    const url = `${window.location.origin}/?ref=${progress.referral_code}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!token || !progress) return null;

  if (progress.is_ambassador) {
    return (
      <div className="bg-gradient-to-r from-[#FFBE98]/15 to-transparent rounded-xl border border-[#FFBE98]/20 p-4" data-testid="ambassador-badge">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-[#FFBE98] rounded-xl flex items-center justify-center shadow-sm">
            <Trophy className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-[#2D2A26]">Embaixador 4Luis</p>
            <p className="text-[11px] text-[#6B6661]">Todas as funcionalidades premium desbloqueadas</p>
          </div>
        </div>
      </div>
    );
  }

  const { valid_referrals, required, remaining, progress_pct, referral_code, referrals } = progress;

  if (compact) {
    return (
      <div className="bg-white rounded-xl border border-stone-100 p-3 shadow-sm" data-testid="ambassador-progress-compact">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-[#FFBE98]/10 rounded-lg flex items-center justify-center">
            <Lock className="w-4 h-4 text-[#FFBE98]" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-semibold text-[#2D2A26]">
              {remaining > 0 ? `Faltam ${remaining} amigo${remaining > 1 ? 's' : ''} para Embaixador` : 'Quase lá!'}
            </p>
            <div className="w-full bg-stone-100 rounded-full h-1.5 mt-1">
              <div className="bg-[#FFBE98] h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${progress_pct}%` }} />
            </div>
          </div>
          <span className="text-[10px] font-bold text-[#FFBE98]">{valid_referrals}/{required}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-stone-100 p-5 shadow-sm space-y-4" data-testid="ambassador-progress">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-[#FFBE98]/10 rounded-xl flex items-center justify-center">
          <Trophy className="w-5 h-5 text-[#FFBE98]" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-bold text-[#2D2A26]">Modo Embaixador</p>
          <p className="text-[11px] text-[#6B6661]">
            {remaining > 0
              ? `Faltam ${remaining} amigo${remaining > 1 ? 's' : ''} para desbloquear funcionalidades avançadas`
              : 'A validar as contribuições...'
            }
          </p>
        </div>
      </div>

      {/* Progress bar */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-medium text-[#6B6661]">Progresso</span>
          <span className="text-[10px] font-bold text-[#FFBE98]">{valid_referrals} de {required} amigos com contribuição</span>
        </div>
        <div className="w-full bg-stone-100 rounded-full h-2.5">
          <motion.div
            className="bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] h-2.5 rounded-full"
            initial={{ width: 0 }} animate={{ width: `${progress_pct}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
        <div className="flex justify-between mt-1">
          {[...Array(required)].map((_, i) => (
            <div key={i} className={`flex items-center gap-1 text-[10px] ${i < valid_referrals ? 'text-[#FFBE98] font-semibold' : 'text-stone-400'}`}>
              <Users className="w-3 h-3" />
              <span>Amigo {i + 1}</span>
              {i < valid_referrals && <Check className="w-3 h-3" />}
            </div>
          ))}
        </div>
      </div>

      {/* Referral details (expandable) */}
      {referrals && referrals.length > 0 && (
        <div>
          <button onClick={() => setExpanded(!expanded)} className="flex items-center gap-1 text-[11px] font-semibold text-[#6B6661] hover:text-[#2D2A26] transition-colors">
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {referrals.length} amigo{referrals.length > 1 ? 's' : ''} convidado{referrals.length > 1 ? 's' : ''}
          </button>
          <AnimatePresence>
            {expanded && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden mt-2 space-y-1.5">
                {referrals.map((r, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px] px-2 py-1.5 rounded-lg bg-stone-50">
                    <div className={`w-2 h-2 rounded-full ${r.contributed ? 'bg-emerald-400' : r.registered ? 'bg-amber-400' : 'bg-stone-300'}`} />
                    <span className="flex-1 font-medium text-[#2D2A26]">{r.name}</span>
                    <span className={`text-[10px] ${r.contributed ? 'text-emerald-600' : 'text-stone-400'}`}>
                      {r.contributed ? 'Contribuiu' : 'Aguarda contribuição'}
                    </span>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Referral CTA */}
      <div className="bg-[#FFBE98]/8 rounded-xl p-4 border border-[#FFBE98]/15">
        <p className="text-xs font-bold text-[#2D2A26] mb-1">Convida amigos e desbloqueia funcionalidades avançadas</p>
        <p className="text-[10px] text-[#6B6661] mb-3">
          Cada amigo que se registar e contribuir para a Viagem Principal conta para o teu progresso.
        </p>
        {referral_code ? (
          <div className="flex gap-2">
            <button onClick={copyLink} data-testid="copy-referral-link"
              className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold bg-white border border-stone-200 hover:border-stone-300 px-3 py-2 rounded-xl transition-all duration-200 hover:shadow-sm hover:-translate-y-0.5">
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5 text-[#6B6661]" />}
              {copied ? 'Copiado!' : 'Copiar link'}
            </button>
            <button onClick={shareLink} data-testid="share-referral-whatsapp"
              className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold bg-[#25D366] text-white px-3 py-2 rounded-xl transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
              <Share2 className="w-3.5 h-3.5" />WhatsApp
            </button>
          </div>
        ) : (
          <button onClick={generateLink} disabled={generating} data-testid="generate-referral-link"
            className="w-full flex items-center justify-center gap-1.5 text-xs font-semibold bg-[#FFBE98] text-white px-4 py-2.5 rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50">
            <ExternalLink className="w-3.5 h-3.5" />
            {generating ? 'A gerar...' : 'Gerar o meu link de convite'}
          </button>
        )}
      </div>

      {/* Premium features preview */}
      <div className="space-y-1.5">
        <p className="text-[10px] font-semibold text-[#6B6661] uppercase tracking-wider">Funcionalidades premium</p>
        {[
          { label: 'Mapa interativo do roteiro', icon: '🗺️' },
          { label: 'Dicas secretas locais', icon: '🤫' },
          { label: 'CTAs de reserva avançados', icon: '🎯' },
          { label: 'Assistente IA durante a viagem', icon: '🤖' },
        ].map((f, i) => (
          <div key={i} className="flex items-center gap-2 text-[11px] text-stone-400 px-2 py-1">
            <span>{f.icon}</span>
            <span>{f.label}</span>
            <Lock className="w-3 h-3 ml-auto" />
          </div>
        ))}
      </div>
    </div>
  );
};

export const PremiumGate = ({ isAmbassador, children, label = 'Disponível para Embaixadores', compact = false }) => {
  if (isAmbassador) return <>{children}</>;

  return (
    <div className="relative" data-testid="premium-gate">
      <div className="filter blur-[3px] opacity-50 pointer-events-none select-none" aria-hidden="true">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className={`bg-white/90 backdrop-blur-sm rounded-xl border border-stone-200 shadow-sm flex items-center gap-2 ${compact ? 'px-3 py-2' : 'px-5 py-3'}`}>
          <Lock className={`${compact ? 'w-3.5 h-3.5' : 'w-4 h-4'} text-[#FFBE98]`} />
          <span className={`${compact ? 'text-[11px]' : 'text-xs'} font-semibold text-[#2D2A26]`}>{label}</span>
        </div>
      </div>
    </div>
  );
};

export default AmbassadorProgress;
