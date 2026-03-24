import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Sparkles, PartyPopper, Heart } from 'lucide-react';
import confetti from 'canvas-confetti';

export const CelebrationBanner = ({ journeyName, variant = 'completed' }) => {
  const fired = useRef(false);

  useEffect(() => {
    if (variant === 'completed' && !fired.current) {
      fired.current = true;
      const end = Date.now() + 2500;
      const colors = ['#FFBE98', '#F2C94C', '#E6A07C', '#ffffff'];
      (function frame() {
        confetti({ particleCount: 3, angle: 60, spread: 55, origin: { x: 0 }, colors });
        confetti({ particleCount: 3, angle: 120, spread: 55, origin: { x: 1 }, colors });
        if (Date.now() < end) requestAnimationFrame(frame);
      })();
    }
  }, [variant]);

  if (variant === 'pending_validation') {
    return (
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-amber-50 border border-amber-200 rounded-2xl p-4 sm:p-5 text-center"
        data-testid="funding-pending-banner"
      >
        <div className="flex items-center justify-center gap-2 mb-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          <span className="font-bold text-amber-800 text-sm sm:text-base">Objetivo atingido!</span>
        </div>
        <p className="text-amber-700 text-xs sm:text-sm leading-relaxed">
          Financiamento concluído — a aguardar confirmação final.
        </p>
        <p className="text-amber-600/70 text-[11px] mt-1.5">
          As contribuições continuam abertas.
        </p>
      </motion.div>
    );
  }

  if (variant === 'completed') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="relative bg-gradient-to-br from-[#FFBE98]/15 via-[#F2C94C]/10 to-[#FFBE98]/15 border border-[#FFBE98]/30 rounded-2xl p-5 sm:p-6 text-center overflow-hidden"
        data-testid="funding-completed-banner"
      >
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMSIgZmlsbD0icmdiYSgyNTUsMTkwLDE1MiwwLjEpIi8+PC9zdmc+')] opacity-50" />
        <div className="relative">
          <motion.div
            animate={{ rotate: [0, -10, 10, -10, 0] }}
            transition={{ duration: 1, delay: 0.5 }}
            className="inline-flex items-center justify-center w-14 h-14 bg-[#FFBE98]/20 rounded-full mb-3"
          >
            <Trophy className="w-7 h-7 text-[#FFBE98]" />
          </motion.div>
          <h3 className="text-lg sm:text-xl font-bold text-[#2D2A26] mb-1">
            Sonho 100% Financiado
          </h3>
          {journeyName && (
            <p className="font-handwritten text-[#FFBE98] text-base sm:text-lg mb-2">{journeyName}</p>
          )}
          <p className="text-[#6B6661] text-xs sm:text-sm leading-relaxed max-w-md mx-auto">
            A comunidade tornou este sonho possível. Obrigado a todos os que contribuíram.
          </p>
          <div className="flex items-center justify-center gap-1.5 mt-3">
            <Heart className="w-3.5 h-3.5 text-[#FFBE98]" />
            <span className="text-xs font-medium text-[#FFBE98]">100% financiado pela comunidade</span>
          </div>
        </div>
      </motion.div>
    );
  }

  return null;
};

export const FundedBadge = () => (
  <motion.span
    initial={{ scale: 0 }}
    animate={{ scale: 1 }}
    className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#FFBE98]/15 border border-[#FFBE98]/30 rounded-full text-[11px] font-bold text-[#FFBE98]"
    data-testid="funded-badge"
  >
    <PartyPopper className="w-3 h-3" /> 100% Financiado
  </motion.span>
);

export const PendingBadge = () => (
  <span
    className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-50 border border-amber-200 rounded-full text-[11px] font-bold text-amber-700"
    data-testid="pending-badge"
  >
    <Sparkles className="w-3 h-3" /> Em validação
  </span>
);
