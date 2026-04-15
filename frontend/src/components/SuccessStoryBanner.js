import React from 'react';
import { motion } from 'framer-motion';
import { Heart, Users, Clock, ShieldCheck, Share2, Copy, Check, ExternalLink, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import ShareMenu, { buildInviteLink } from './ShareMenu';

/**
 * SuccessStoryBanner — two modes:
 * 1. Ambassador journey "financiada" → full success story (closed)
 * 2. Main trip at 100%+ → continuous model (keep contributing)
 */
const SuccessStoryBanner = ({ journey, progress, contributions, user }) => {
  const isMainTrip = journey?.is_main_trip;
  const isAmbassador = journey?.is_ambassador_journey;
  const isFunded = progress?.is_funded || progress?.percentage >= 100;
  const [copied, setCopied] = React.useState(false);

  if (!isFunded) return null;

  const contributorCount = progress?.contributor_count || contributions?.length || 0;
  const percentFunded = Math.round(progress?.percentage || 0);

  // ========== MAIN TRIP: CONTINUOUS MODEL ==========
  if (isMainTrip) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-[#FFBE98]/15 to-[#F2C94C]/10 rounded-3xl p-6 md:p-8 border border-[#FFBE98]/20 mb-8"
        data-testid="main-trip-success"
      >
        <div className="text-center space-y-4">
          <div className="text-3xl">🎉</div>
          <h2 className="text-xl font-bold text-[#2D2A26]">
            O sonho já ganhou forma!
          </h2>
          <p className="text-sm text-[#6B6661]">
            Mas a viagem continua...
          </p>

          {/* Social proof - no absolute values */}
          <div className="inline-flex items-center gap-2 bg-white/70 rounded-full px-4 py-2">
            <Users className="w-4 h-4 text-[#FFBE98]" />
            <span className="text-sm font-medium text-[#2D2A26]">
              {contributorCount} {contributorCount === 1 ? 'pessoa já faz' : 'pessoas já fazem'} parte deste sonho
            </span>
          </div>

          <div className="flex items-center justify-center gap-2">
            <span className="text-sm font-bold text-[#F2C94C]">{percentFunded}% financiado</span>
          </div>

          <p className="text-xs text-[#6B6661] max-w-sm mx-auto">
            As contribuições continuam a impulsionar esta viagem
          </p>

          <p className="text-sm font-semibold text-[#2D2A26]">
            Faz parte deste momento
          </p>
        </div>
      </motion.div>
    );
  }

  // ========== AMBASSADOR JOURNEY: FUNDED (CLOSED) ==========
  if (isAmbassador && (journey?.status === 'financiada' || journey?.status === 'realizada')) {
    const ambassador = journey?.ambassador_info;
    const certLabel = ambassador?.certification_label;
    const certLevel = ambassador?.certification_level;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-emerald-50 to-[#E6F4F1]/50 rounded-3xl p-6 md:p-8 border border-emerald-200 mb-8"
        data-testid="ambassador-success-story"
      >
        <div className="text-center space-y-5">
          <div className="text-3xl">🎉</div>
          <h2 className="text-xl font-bold text-[#2D2A26]">
            Este sonho foi financiado
          </h2>

          {/* Journey name + ambassador */}
          <div>
            <p className="text-lg font-handwritten text-[#FFBE98]">{journey.poetic_name || journey.name}</p>
            {ambassador && (
              <div className="flex items-center justify-center gap-2 mt-2">
                {ambassador.avatar && (
                  <img src={ambassador.avatar} alt="" className="w-8 h-8 rounded-full border-2 border-emerald-200" />
                )}
                <span className="text-sm font-medium text-[#2D2A26]">{ambassador.display_name}</span>
                {certLabel && (
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold ${
                    certLevel === 'confiavel' ? 'bg-emerald-100 text-emerald-700'
                    : certLevel === 'verificado' ? 'bg-blue-100 text-blue-700'
                    : 'bg-[#FFBE98]/20 text-[#2D2A26]'
                  }`}>
                    <ShieldCheck className="w-2.5 h-2.5" />
                    {certLabel}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-3 gap-3 max-w-md mx-auto">
            <div className="bg-white rounded-xl p-3">
              <p className="text-lg font-bold text-[#2D2A26]">{contributorCount}</p>
              <p className="text-[10px] text-[#6B6661]">contribuidores</p>
            </div>
            <div className="bg-white rounded-xl p-3">
              <p className="text-lg font-bold text-emerald-600">100%</p>
              <p className="text-[10px] text-[#6B6661]">financiado</p>
            </div>
            <div className="bg-white rounded-xl p-3">
              <p className="text-lg font-bold text-[#2D2A26]">
                <Check className="w-5 h-5 text-emerald-500 mx-auto" />
              </p>
              <p className="text-[10px] text-[#6B6661]">pagamentos confirmados</p>
            </div>
          </div>

          {/* Share */}
          <div className="space-y-2 pt-2">
            <p className="text-xs text-[#6B6661]">Inspira outros a criar o seu próprio sonho</p>
            <div className="flex justify-center gap-2">
              <a
                href={`https://wa.me/?text=${encodeURIComponent(`O sonho "${journey.name}" foi financiado na 4Luis! 🎉 Descobre mais: ${window.location.href}`)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-[#25D366] text-white rounded-xl text-xs font-semibold hover:bg-[#1DA851] transition-colors"
              >
                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 fill-current"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.121.553 4.113 1.519 5.845L.054 23.524l5.838-1.531A11.94 11.94 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.82c-1.975 0-3.856-.527-5.508-1.523l-.395-.234-4.1 1.075 1.093-3.998-.257-.41A9.79 9.79 0 012.18 12c0-5.422 4.398-9.82 9.82-9.82 5.422 0 9.82 4.398 9.82 9.82 0 5.422-4.398 9.82-9.82 9.82z"/></svg>
                Partilhar
              </a>
              <button
                onClick={() => { navigator.clipboard.writeText(window.location.href); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-stone-200 rounded-xl text-xs font-medium text-[#2D2A26] hover:border-[#FFBE98] transition-colors"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? 'Copiado!' : 'Copiar link'}
              </button>
            </div>
          </div>

          {/* CTAs */}
          <div className="flex flex-wrap justify-center gap-3 pt-2">
            <Link
              to="/explore"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#2D2A26] text-white rounded-xl text-sm font-semibold hover:bg-[#4A4640] transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              Explorar viagens
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-semibold hover:bg-[#FFB080] transition-colors"
            >
              <Heart className="w-4 h-4" />
              Criar um sonho
            </Link>
          </div>
        </div>
      </motion.div>
    );
  }

  return null;
};

export default SuccessStoryBanner;
