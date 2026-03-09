import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles } from 'lucide-react';

const MILESTONE_CHAPTERS = {
  25: { num: 2, label: 'O sonho ganha forma' },
  50: { num: 3, label: 'O sonho esta a caminho' },
  75: { num: 4, label: 'O sonho quase acontece' },
  100: { num: 5, label: 'O sonho torna-se realidade' },
};

function ConfettiParticle({ delay, left }) {
  const colors = ['#FFBE98', '#F2C94C', '#E6A07C', '#FFD700', '#FF8C42'];
  const color = colors[Math.floor(Math.random() * colors.length)];
  const size = 6 + Math.random() * 6;

  return (
    <motion.div
      initial={{ y: -20, x: 0, opacity: 1, rotate: 0 }}
      animate={{ y: 300, x: (Math.random() - 0.5) * 120, opacity: 0, rotate: 360 + Math.random() * 360 }}
      transition={{ duration: 2 + Math.random(), delay, ease: 'easeOut' }}
      className="absolute pointer-events-none"
      style={{
        left: `${left}%`,
        width: size,
        height: size,
        backgroundColor: color,
        borderRadius: Math.random() > 0.5 ? '50%' : '2px',
      }}
    />
  );
}

export default function MilestoneCelebration({ journey, customChapters }) {
  const [visible, setVisible] = useState(false);
  const [milestoneData, setMilestoneData] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!journey || dismissed) return;

    const milestoneAt = journey.last_milestone_at;
    const milestoneVal = journey.last_milestone_reached;

    if (!milestoneAt || !milestoneVal) return;

    const milestoneTime = new Date(milestoneAt).getTime();
    const now = Date.now();
    const hoursSince = (now - milestoneTime) / (1000 * 60 * 60);

    if (hoursSince > 48) return;

    const storageKey = `celebration_${journey.journey_id}_${milestoneVal}`;
    if (sessionStorage.getItem(storageKey)) return;

    const chapterInfo = MILESTONE_CHAPTERS[milestoneVal];
    if (!chapterInfo) return;

    let chapterTitle = chapterInfo.label;
    if (customChapters && customChapters[String(chapterInfo.num)]) {
      chapterTitle = customChapters[String(chapterInfo.num)].title || chapterTitle;
    }

    setMilestoneData({ percentage: milestoneVal, chapterTitle });
    setVisible(true);

    sessionStorage.setItem(storageKey, 'true');

    const timer = setTimeout(() => setVisible(false), 8000);
    return () => clearTimeout(timer);
  }, [journey, customChapters, dismissed]);

  const handleDismiss = () => {
    setVisible(false);
    setDismissed(true);
  };

  if (!milestoneData) return null;

  const confettiParticles = Array.from({ length: 24 }, (_, i) => ({
    id: i,
    delay: Math.random() * 0.8,
    left: Math.random() * 100,
  }));

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -30 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="relative overflow-hidden rounded-2xl mb-6"
          data-testid="milestone-celebration"
        >
          <div className="relative bg-gradient-to-r from-[#FFBE98]/20 via-[#F2C94C]/15 to-[#FFBE98]/20 border border-[#FFBE98]/30 rounded-2xl p-6 text-center">
            {/* Confetti */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              {confettiParticles.map(p => (
                <ConfettiParticle key={p.id} delay={p.delay} left={p.left} />
              ))}
            </div>

            {/* Close button */}
            <button
              onClick={handleDismiss}
              className="absolute top-3 right-3 p-1 hover:bg-white/50 rounded-full transition-colors z-10"
              data-testid="celebration-dismiss"
            >
              <X className="w-4 h-4 text-[#6B6661]" />
            </button>

            {/* Content */}
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
              className="relative z-10"
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <Sparkles className="w-5 h-5 text-[#F2C94C]" />
                <span className="text-sm font-bold text-[#FFBE98] uppercase tracking-wider">
                  {milestoneData.percentage}% alcancado
                </span>
                <Sparkles className="w-5 h-5 text-[#F2C94C]" />
              </div>
              <h3 className="text-xl font-bold text-[#2D2A26] mb-1">
                O sonho entrou numa nova fase
              </h3>
              <p className="text-[#6B6661] font-medium italic font-handwritten text-lg">
                &ldquo;{milestoneData.chapterTitle}&rdquo;
              </p>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
