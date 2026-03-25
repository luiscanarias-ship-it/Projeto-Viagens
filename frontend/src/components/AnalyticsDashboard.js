import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Users, MousePointerClick, Share2, Award, ArrowUpRight, Hotel, Plane, Compass, Shield, Wifi, Car, MessageCircle, Copy, Link, ExternalLink, MapPin, Heart } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLATFORM_CONFIG = {
  booking: { label: 'Hotéis', icon: Hotel, color: 'bg-[#FFBE98]/10 text-[#FFBE98]' },
  getyourguide: { label: 'Experiências', icon: Compass, color: 'bg-emerald-50 text-emerald-600' },
  skyscanner: { label: 'Voos', icon: Plane, color: 'bg-sky-50 text-sky-600' },
  insurance: { label: 'Seguros', icon: Shield, color: 'bg-amber-50 text-amber-600' },
  airalo: { label: 'eSIM', icon: Wifi, color: 'bg-teal-50 text-teal-600' },
  holafly: { label: 'eSIM', icon: Wifi, color: 'bg-teal-50 text-teal-600' },
  cars: { label: 'Transportes', icon: Car, color: 'bg-violet-50 text-violet-600' },
};

const SHARE_CONFIG = {
  whatsapp: { label: 'WhatsApp', icon: MessageCircle, color: 'text-green-600' },
  copy: { label: 'Copiar link', icon: Copy, color: 'text-stone-600' },
  native: { label: 'Partilha nativa', icon: Share2, color: 'text-blue-600' },
  link: { label: 'Link direto', icon: Link, color: 'text-[#FFBE98]' },
};

const MetricCard = ({ label, value, sub, icon: Icon, accent }) => (
  <div className="bg-white rounded-2xl p-4 border border-stone-100 shadow-sm" data-testid={`metric-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between mb-2">
      <span className="text-xs font-medium text-[#6B6661] uppercase tracking-wider">{label}</span>
      {Icon && <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${accent || 'bg-stone-50 text-stone-400'}`}><Icon className="w-3.5 h-3.5" /></div>}
    </div>
    <p className="text-2xl font-bold text-[#2D2A26]">{value}</p>
    {sub && <p className="text-xs text-[#6B6661] mt-0.5">{sub}</p>}
  </div>
);

const BarRow = ({ label, value, max, icon: Icon, iconClass }) => {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-3 py-2" data-testid={`bar-${label.toLowerCase().replace(/\s/g, '-')}`}>
      {Icon && <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${iconClass || 'bg-stone-50 text-stone-500'}`}><Icon className="w-3.5 h-3.5" /></div>}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-[#2D2A26] truncate">{label}</span>
          <span className="text-xs font-bold text-[#2D2A26] ml-2">{value}</span>
        </div>
        <div className="w-full h-1.5 bg-stone-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-[#FFBE98] rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>
      </div>
    </div>
  );
};

const AnalyticsDashboard = ({ token }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      try {
        const res = await axios.get(`${API}/admin/analytics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(res.data);
      } catch (e) {
        console.error('Analytics load error:', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  if (loading) return (
    <div className="flex items-center justify-center py-20">
      <div className="w-6 h-6 border-2 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!data) return (
    <div className="text-center py-12 text-[#6B6661]">Erro ao carregar analytics</div>
  );

  const { funnel, affiliates, shares, referrals, top_plans_shared, top_plans_affiliate, top_converting_journeys } = data;

  const maxAffClicks = Math.max(...Object.values(affiliates.by_platform || {}), 1);
  const maxShareCount = Math.max(...Object.values(shares.by_type || {}), 1);

  return (
    <div className="space-y-6" data-testid="analytics-dashboard">
      {/* Section 1: FUNNEL */}
      <div>
        <h3 className="text-sm font-bold text-[#2D2A26] mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-[#FFBE98]" />Funil de Crescimento
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard label="Registos" value={funnel.total_users} icon={Users} accent="bg-blue-50 text-blue-500" />
          <MetricCard label="Contribuições" value={funnel.completed_contributions} sub={`${funnel.pending_contributions} pendentes`} icon={Heart} accent="bg-[#FFBE98]/10 text-[#FFBE98]" />
          <MetricCard label="Total Angariado" value={`${funnel.total_raised.toFixed(0)}€`} icon={TrendingUp} accent="bg-emerald-50 text-emerald-500" />
          <MetricCard label="Embaixadores" value={funnel.ambassadors} sub={`${funnel.ambassador_rate}% conversão`} icon={Award} accent="bg-amber-50 text-amber-500" />
        </div>
      </div>

      {/* Section 2: AFFILIATES + SHARES side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Affiliates */}
        <div className="bg-white rounded-2xl p-5 border border-stone-100 shadow-sm" data-testid="affiliates-section">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-[#2D2A26] flex items-center gap-2">
              <MousePointerClick className="w-4 h-4 text-[#FFBE98]" />Afiliados
            </h3>
            <span className="text-xs font-bold text-[#FFBE98] bg-[#FFBE98]/10 px-2 py-0.5 rounded-full">{affiliates.total_clicks} clicks</span>
          </div>
          <div className="space-y-0.5">
            {Object.entries(affiliates.by_platform || {}).map(([platform, clicks]) => {
              const cfg = PLATFORM_CONFIG[platform] || { label: platform, icon: ExternalLink, color: 'bg-stone-50 text-stone-500' };
              return (
                <BarRow key={platform} label={cfg.label} value={clicks} max={maxAffClicks} icon={cfg.icon} iconClass={cfg.color} />
              );
            })}
            {Object.keys(affiliates.by_platform || {}).length === 0 && (
              <p className="text-xs text-[#6B6661] py-4 text-center">Sem dados de afiliados</p>
            )}
          </div>
        </div>

        {/* Shares */}
        <div className="bg-white rounded-2xl p-5 border border-stone-100 shadow-sm" data-testid="shares-section">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-[#2D2A26] flex items-center gap-2">
              <Share2 className="w-4 h-4 text-[#FFBE98]" />Partilhas
            </h3>
            <span className="text-xs font-bold text-[#FFBE98] bg-[#FFBE98]/10 px-2 py-0.5 rounded-full">{shares.total} total</span>
          </div>
          <div className="space-y-0.5">
            {Object.entries(shares.by_type || {}).map(([type, count]) => {
              const cfg = SHARE_CONFIG[type] || { label: type, icon: Share2, color: 'text-stone-500' };
              return (
                <BarRow key={type} label={cfg.label} value={count} max={maxShareCount} icon={cfg.icon} iconClass={`bg-stone-50 ${cfg.color}`} />
              );
            })}
            {Object.keys(shares.by_type || {}).length === 0 && (
              <p className="text-xs text-[#6B6661] py-4 text-center">Sem dados de partilhas</p>
            )}
          </div>
        </div>
      </div>

      {/* Section 3: REFERRALS */}
      <div className="bg-white rounded-2xl p-5 border border-stone-100 shadow-sm" data-testid="referrals-section">
        <h3 className="text-sm font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
          <Users className="w-4 h-4 text-[#FFBE98]" />Sistema de Referrals
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="text-center p-3 rounded-xl bg-stone-50">
            <p className="text-xl font-bold text-[#2D2A26]">{referrals.total_valid}</p>
            <p className="text-[10px] text-[#6B6661] mt-0.5">Referrals válidos</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-stone-50">
            <p className="text-xl font-bold text-[#2D2A26]">{referrals.active_referrers}</p>
            <p className="text-[10px] text-[#6B6661] mt-0.5">Referrers ativos</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-stone-50">
            <p className="text-xl font-bold text-[#FFBE98]">{referrals.avg_per_referrer}</p>
            <p className="text-[10px] text-[#6B6661] mt-0.5">Média por referrer</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-[#FFBE98]/10">
            <p className="text-xl font-bold text-[#FFBE98]">{referrals.ambassador_conversion}%</p>
            <p className="text-[10px] text-[#6B6661] mt-0.5">Taxa embaixador</p>
          </div>
        </div>
      </div>

      {/* Section 4: TOP PLANS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Most shared */}
        <div className="bg-white rounded-2xl p-5 border border-stone-100 shadow-sm" data-testid="top-shared-plans">
          <h4 className="text-xs font-bold text-[#2D2A26] mb-3 flex items-center gap-1.5">
            <Share2 className="w-3.5 h-3.5 text-[#FFBE98]" />Mais partilhados
          </h4>
          {top_plans_shared.length > 0 ? top_plans_shared.map((p, i) => (
            <div key={p.slug} className="flex items-center justify-between py-1.5 border-b border-stone-50 last:border-0">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-[10px] font-bold text-[#FFBE98] w-4">{i + 1}.</span>
                <span className="text-xs text-[#2D2A26] truncate">{p.destination}</span>
              </div>
              <span className="text-xs font-bold text-[#6B6661] flex items-center gap-0.5 ml-2 flex-shrink-0">{p.shares} <ArrowUpRight className="w-3 h-3 text-[#FFBE98]" /></span>
            </div>
          )) : <p className="text-xs text-[#6B6661] py-2 text-center">Sem dados</p>}
        </div>

        {/* Most affiliate clicks */}
        <div className="bg-white rounded-2xl p-5 border border-stone-100 shadow-sm" data-testid="top-affiliate-plans">
          <h4 className="text-xs font-bold text-[#2D2A26] mb-3 flex items-center gap-1.5">
            <MousePointerClick className="w-3.5 h-3.5 text-[#FFBE98]" />Mais clicks afiliados
          </h4>
          {top_plans_affiliate.length > 0 ? top_plans_affiliate.map((p, i) => (
            <div key={p.slug} className="flex items-center justify-between py-1.5 border-b border-stone-50 last:border-0">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-[10px] font-bold text-[#FFBE98] w-4">{i + 1}.</span>
                <span className="text-xs text-[#2D2A26] truncate">{p.destination}</span>
              </div>
              <span className="text-xs font-bold text-[#6B6661] flex items-center gap-0.5 ml-2 flex-shrink-0">{p.clicks} <MousePointerClick className="w-3 h-3 text-[#FFBE98]" /></span>
            </div>
          )) : <p className="text-xs text-[#6B6661] py-2 text-center">Sem dados</p>}
        </div>

        {/* Top converting journeys */}
        <div className="bg-white rounded-2xl p-5 border border-stone-100 shadow-sm" data-testid="top-converting-journeys">
          <h4 className="text-xs font-bold text-[#2D2A26] mb-3 flex items-center gap-1.5">
            <Heart className="w-3.5 h-3.5 text-[#FFBE98]" />Mais conversões
          </h4>
          {top_converting_journeys.length > 0 ? top_converting_journeys.map((j, i) => (
            <div key={j.journey_id} className="flex items-center justify-between py-1.5 border-b border-stone-50 last:border-0">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-[10px] font-bold text-[#FFBE98] w-4">{i + 1}.</span>
                <span className="text-xs text-[#2D2A26] truncate">{j.name}</span>
              </div>
              <span className="text-xs font-bold text-emerald-600 ml-2 flex-shrink-0">{j.amount.toFixed(0)}€</span>
            </div>
          )) : <p className="text-xs text-[#6B6661] py-2 text-center">Sem dados</p>}
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
