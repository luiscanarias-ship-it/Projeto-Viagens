import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Heart, Flame, ArrowRight, Users } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const timeAgo = (dateStr) => {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `há ${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `há ${hrs}h`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `há ${days}d`;
  return `há ${Math.floor(days / 7)}sem`;
};

const SocialProofBanner = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API}/homepage/main-journey`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.journey) setData(d); })
      .catch(() => {});
  }, []);

  if (!data?.journey) return null;

  const { journey, contributions, contributor_count, progress } = data;
  const pct = Math.min(progress?.percentage || 0, 100);
  const recentContribs = (contributions || []).slice(0, 3);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="my-4 rounded-xl border border-[#FFBE98]/20 overflow-hidden bg-white"
      data-testid="social-proof-banner"
    >
      {/* Header with fire emoji and count */}
      <div className="px-4 py-3 bg-gradient-to-r from-orange-50/80 to-[#FFBE98]/5 border-b border-[#FFBE98]/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flame className="w-4 h-4 text-orange-500" />
            <p className="text-xs font-bold text-[#2D2A26]">
              {contributor_count || 0} pessoas já contribuíram
            </p>
          </div>
          {pct >= 10 && pct < 100 && (
            <span className="text-[9px] font-bold text-[#FFBE98] bg-[#FFBE98]/10 px-2 py-0.5 rounded-full">
              Falta pouco!
            </span>
          )}
        </div>
      </div>

      {/* Recent contributors */}
      {recentContribs.length > 0 && (
        <div className="px-4 py-2.5 space-y-1.5">
          {recentContribs.map((c, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -8 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-2.5"
            >
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#FFBE98]/30 to-[#E6A07C]/20 flex items-center justify-center shrink-0">
                <Heart className="w-3 h-3 text-[#FFBE98]" />
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-[11px] font-medium text-[#2D2A26]">{c.display_name}</span>
                {c.amount && (
                  <span className="text-[10px] text-[#6B6661] ml-1.5">contribuiu {c.amount}€</span>
                )}
              </div>
              <span className="text-[9px] text-[#9B9590] shrink-0">{timeAgo(c.created_at)}</span>
            </motion.div>
          ))}
        </div>
      )}

      {/* Progress bar + CTA */}
      <div className="px-4 py-3 border-t border-stone-50 bg-stone-50/30">
        <div className="flex items-center gap-2 mb-2.5">
          <div className="flex-1 bg-stone-200/50 rounded-full h-1.5">
            <motion.div
              className="bg-[#FFBE98] h-1.5 rounded-full"
              initial={{ width: 0 }}
              whileInView={{ width: `${pct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
            />
          </div>
          <span className="text-[10px] font-bold text-[#FFBE98] shrink-0">{pct.toFixed(0)}%</span>
        </div>
        <Link
          to={`/journey/${journey.journey_id}`}
          className="w-full flex items-center justify-center gap-2 bg-[#2D2A26] text-white font-bold text-sm py-3 rounded-xl hover:bg-[#1D1A16] transition-all shadow-sm"
          data-testid="social-proof-cta"
        >
          <Heart className="w-4 h-4 text-[#FFBE98]" />
          Apoiar este sonho
          <ArrowRight className="w-3.5 h-3.5 opacity-60" />
        </Link>
      </div>
    </motion.div>
  );
};

export default SocialProofBanner;
