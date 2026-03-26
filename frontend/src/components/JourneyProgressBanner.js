import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Heart, ArrowRight, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const JourneyProgressBanner = ({ variant = 'top' }) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API}/homepage/main-journey`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.journey) setData(d); })
      .catch(() => {});
  }, []);

  if (!data?.journey) return null;

  const { journey, progress, contributor_count } = data;
  const pct = Math.min(progress?.percentage || 0, 100);
  const displayCount = contributor_count || 0;

  if (variant === 'mid') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="my-5 rounded-xl overflow-hidden border border-[#FFBE98]/25"
        data-testid="journey-banner-mid"
      >
        <div className="bg-gradient-to-r from-[#2D2A26] to-[#3D3A36] px-5 py-5">
          <p className="text-[11px] font-semibold text-[#FFBE98] uppercase tracking-wider mb-1">Viagem de sonho</p>
          <p className="text-base font-bold text-white leading-snug">
            Gostaste deste roteiro?
          </p>
          <p className="text-sm text-white/60 mt-0.5">
            Ajuda a tornar esta viagem real
          </p>

          <div className="mt-3 mb-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-white/50">{journey.name}</span>
              <span className="text-[10px] font-bold text-[#FFBE98]">{pct.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-1.5">
              <motion.div
                className="bg-[#FFBE98] h-1.5 rounded-full"
                initial={{ width: 0 }}
                whileInView={{ width: `${pct}%` }}
                viewport={{ once: true }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between mt-3">
            <span className="text-[10px] text-white/40 flex items-center gap-1">
              <Users className="w-3 h-3" />{displayCount} sonhadores
            </span>
            <Link
              to={`/journey/${journey.journey_id}`}
              className="inline-flex items-center gap-1.5 bg-[#FFBE98] text-[#2D2A26] text-xs font-bold px-4 py-2 rounded-xl shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 animate-pulse"
              data-testid="journey-contribute-mid"
            >
              <Heart className="w-3.5 h-3.5" />Contribuir
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </motion.div>
    );
  }

  // variant === 'top'
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="mb-4 rounded-xl overflow-hidden border border-[#FFBE98]/20 bg-gradient-to-r from-[#FFBE98]/10 to-transparent"
      data-testid="journey-banner-top"
    >
      <div className="px-4 py-3 flex items-center gap-3">
        <div className="w-10 h-10 bg-[#FFBE98]/15 rounded-xl flex items-center justify-center shrink-0">
          <Heart className="w-5 h-5 text-[#FFBE98]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-semibold text-[#2D2A26]">
            Estamos a financiar uma viagem de sonho
          </p>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex-1 bg-stone-200/50 rounded-full h-1.5">
              <motion.div
                className="bg-[#FFBE98] h-1.5 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 1, ease: 'easeOut', delay: 0.5 }}
              />
            </div>
            <span className="text-[10px] font-bold text-[#FFBE98] shrink-0">{pct.toFixed(0)}%</span>
          </div>
          <p className="text-[9px] text-[#6B6661] mt-0.5 flex items-center gap-1">
            <Users className="w-2.5 h-2.5" />{displayCount} pessoas ja contribuiram
          </p>
        </div>
        <Link
          to={`/journey/${journey.journey_id}`}
          className="shrink-0 inline-flex items-center gap-1.5 bg-[#FFBE98] text-white text-[11px] font-bold px-3.5 py-2 rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
          style={{ animation: 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite' }}
          data-testid="journey-contribute-top"
        >
          <Heart className="w-3.5 h-3.5" />Contribuir
        </Link>
      </div>
    </motion.div>
  );
};

export default JourneyProgressBanner;
