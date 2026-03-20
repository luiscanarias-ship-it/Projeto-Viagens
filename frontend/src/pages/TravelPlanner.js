import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MapPin, Calendar, Compass, Sparkles, Loader2,
  Sun, Shirt, ClipboardList, Lightbulb, Hotel, Plane, Wifi,
  ExternalLink, Globe, Ticket, Send, SlidersHorizontal, 
  CheckCircle2, Copy, Share2, Check, Eye, EyeOff, Car, Clock
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TRIP_TYPES = [
  { id: 'cultural', label: 'Cultural' },
  { id: 'aventura', label: 'Aventura' },
  { id: 'passeio', label: 'Passeio' },
  { id: 'gastronomica', label: 'Gastronómica' },
  { id: 'romantica', label: 'Romântica' },
  { id: 'familia', label: 'Família' }
];

const TABS = [
  { id: 'guia', label: 'Guia', icon: Globe },
  { id: 'roteiro', label: 'Roteiro', icon: Calendar },
  { id: 'checklist', label: 'Checklist', icon: ClipboardList },
  { id: 'dicas', label: 'Dicas', icon: Lightbulb },
];

/* ── Activity keyword detection for contextual CTAs ── */
const ACTIVITY_PATTERNS = [
  { keywords: ['museu', 'museum', 'galeria', 'exposição', 'exposicao', 'palácio', 'palacio', 'castelo', 'torre', 'catedral', 'basílica', 'basilica', 'mosteiro', 'igreja'],
    label: 'Reservar entrada', platform: 'getyourguide', icon: Ticket },
  { keywords: ['tour', 'visita guiada', 'excursão', 'excursao', 'passeio de barco', 'cruzeiro', 'safari', 'mergulho'],
    label: 'Ver atividades', platform: 'getyourguide', icon: Compass },
  { keywords: ['aeroporto', 'transfer', 'aluguer', 'rent a car', 'carro'],
    label: 'Ver transporte', platform: 'cars', icon: Car },
];

const detectActivityCTA = (text) => {
  const lower = text.toLowerCase();
  for (const p of ACTIVITY_PATTERNS) {
    if (p.keywords.some(k => lower.includes(k))) return p;
  }
  return null;
};

const TIP_BOOKING_KEYWORDS = ['reserv', 'bilhete', 'ingresso', 'anteced', 'antecipadamente', 'comprar', 'book'];
const tipHasBookingHint = (tip) => TIP_BOOKING_KEYWORDS.some(k => tip.toLowerCase().includes(k));

/* ── Inline Activity CTA (subtle, inside itinerary) ── */
const InlineActivityCTA = ({ match, link, onTrack }) => (
  <a href={link || '#'} target="_blank" rel="noopener noreferrer"
    onClick={() => onTrack(match.platform)}
    className="inline-flex items-center gap-1 text-[10px] font-bold text-[#FFBE98] hover:text-[#E6A07C] transition-colors ml-1">
    <match.icon className="w-3 h-3" />{match.label}<ExternalLink className="w-2.5 h-2.5 opacity-60" />
  </a>
);

/* ── Top Booking Bar (compact, after summary) ── */
const TopBookingBar = ({ links, onTrack }) => (
  <div className="flex items-center gap-2 pt-3" data-testid="top-booking-bar">
    <span className="text-[10px] font-semibold text-[#6B6661] whitespace-nowrap">Reservar:</span>
    {[
      { id: 'booking', icon: Hotel, label: 'Alojamento' },
      { id: 'skyscanner', icon: Plane, label: 'Voos' },
      { id: 'getyourguide', icon: Ticket, label: 'Atividades' },
    ].map(item => (
      <a key={item.id} href={links[item.id]?.url || '#'} target="_blank" rel="noopener noreferrer"
        onClick={() => onTrack(item.id)} data-testid={`top-booking-${item.id}`}
        className="flex items-center gap-1 text-[10px] font-semibold text-[#2D2A26] bg-stone-100 hover:bg-[#FFBE98]/10 hover:text-[#FFBE98] px-2.5 py-1.5 rounded-full transition-colors border border-stone-200/60 hover:border-[#FFBE98]/30">
        <item.icon className="w-3 h-3" />{item.label}
      </a>
    ))}
  </div>
);

/* ── Contextual CTA ── */
const ContextualCTA = ({ icon: Icon, text, label, sublabel, link, platform, onTrack }) => (
  <div className="bg-gradient-to-r from-[#FFBE98]/8 to-[#E6A07C]/5 rounded-xl border border-[#FFBE98]/15 p-3.5 flex items-center gap-3 my-3">
    <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shadow-sm shrink-0">
      <Icon className="w-4 h-4 text-[#FFBE98]" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-semibold text-[#2D2A26]">{text}</p>
      {sublabel && <p className="text-[10px] text-[#6B6661] mt-0.5">{sublabel}</p>}
    </div>
    <a href={link || '#'} target="_blank" rel="noopener noreferrer" onClick={() => onTrack(platform)}
      data-testid={`cta-contextual-${platform}`}
      className="shrink-0 flex items-center gap-1.5 bg-[#2D2A26] text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-[#1a1816] transition-colors">
      {label}<ExternalLink className="w-3 h-3" />
    </a>
  </div>
);

/* ── Build dynamic affiliate links with destination/dates ── */
const buildDynamicLinks = (baseLinks, destination, startDate, endDate) => {
  const enc = encodeURIComponent;
  const links = { ...baseLinks };
  if (links.booking) links.booking = { ...links.booking, url: `https://www.booking.com/searchresults.html?ss=${enc(destination)}&checkin=${startDate}&checkout=${endDate}` };
  if (links.skyscanner) links.skyscanner = { ...links.skyscanner, url: `https://www.skyscanner.pt/transport/flights/?query=${enc(destination)}` };
  if (links.getyourguide) links.getyourguide = { ...links.getyourguide, url: `https://www.getyourguide.com/s/?q=${enc(destination)}` };
  if (links.airalo) links.airalo = { ...links.airalo, url: `https://www.airalo.com/search?keyword=${enc(destination)}` };
  if (links.cars) links.cars = { ...links.cars, url: `https://www.rentalcars.com/search-results?location=${enc(destination)}` };
  return links;
};
/* ── Sticky Booking Bar ── */
const StickyBar = ({ links, onTrack, visible }) => {
  const items = [
    { id: 'booking', icon: Hotel, label: 'Hotéis' },
    { id: 'skyscanner', icon: Plane, label: 'Voos' },
    { id: 'getyourguide', icon: Ticket, label: 'Atividades' },
  ];
  return (
    <AnimatePresence>
      {visible && (
        <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 80, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-stone-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
          data-testid="sticky-booking-bar">
          <div className="max-w-2xl mx-auto px-4 py-2.5 flex items-center gap-2">
            <span className="text-xs font-semibold text-[#6B6661] hidden sm:block whitespace-nowrap mr-1">Reservar:</span>
            {items.map(item => (
              <a key={item.id} href={links[item.id]?.url || '#'} target="_blank" rel="noopener noreferrer"
                onClick={() => onTrack(item.id)} data-testid={`sticky-cta-${item.id}`}
                className="flex-1 flex items-center justify-center gap-1.5 bg-[#2D2A26] text-white text-xs font-semibold py-2.5 px-3 rounded-xl hover:bg-[#1a1816] transition-colors">
                <item.icon className="w-3.5 h-3.5" /><span>{item.label}</span>
              </a>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/* ── Refine Panel ── */
const RefinePanel = ({ onSubmit, loading, success }) => {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const inputRef = useRef(null);
  const handleOpen = () => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 100); };
  const handleSubmit = () => {
    if (!text.trim() || loading) return;
    onSubmit(text.trim());
    setText('');
  };

  useEffect(() => {
    if (success) {
      const t = setTimeout(() => setOpen(false), 2000);
      return () => clearTimeout(t);
    }
  }, [success]);

  if (success) {
    return (
      <div className="flex items-center gap-2 text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-2.5 rounded-lg w-full" data-testid="refine-success">
        <Check className="w-4 h-4" />Plano atualizado com sucesso!
      </div>
    );
  }

  if (!open) {
    return (
      <button onClick={handleOpen} data-testid="refine-btn"
        className="flex items-center justify-center gap-2 bg-[#FFBE98] text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-[#E6A07C] transition-colors shadow-sm w-full">
        <SlidersHorizontal className="w-4 h-4" />Ajustar o seu plano
      </button>
    );
  }

  return (
    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="overflow-hidden w-full" data-testid="refine-panel-open">
      <div className="space-y-2">
        <label className="text-xs font-medium text-[#6B6661] block">Quer acrescentar algo ao plano?</label>
        <div className="flex gap-2 items-center">
          <input ref={inputRef} type="text" value={text} onChange={e => setText(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            placeholder="Ex: Adicionar mais restaurantes, evitar museus..."
            className="flex-1 px-3 py-2 text-sm rounded-lg border border-stone-200 focus:border-[#FFBE98] focus:ring-1 focus:ring-[#FFBE98]/30 outline-none transition-all"
            disabled={loading} data-testid="refine-input" />
          <button onClick={handleSubmit} disabled={!text.trim() || loading} data-testid="refine-submit"
            className="flex items-center gap-1.5 bg-[#FFBE98] text-white text-xs font-semibold px-4 py-2.5 rounded-lg hover:bg-[#E6A07C] transition-colors disabled:opacity-50 whitespace-nowrap">
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            {loading ? 'A ajustar...' : 'Ajustar'}
          </button>
          <button onClick={() => { setOpen(false); setText(''); }}
            className="text-xs text-[#6B6661] hover:text-[#2D2A26] px-2 py-2.5 whitespace-nowrap">Cancelar</button>
        </div>
        {loading && (
          <div className="flex items-center gap-2 mt-1">
            <div className="flex gap-[3px]">
              <span className="w-1 h-1 rounded-full bg-[#FFBE98] animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1 h-1 rounded-full bg-[#FFBE98] animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1 h-1 rounded-full bg-[#FFBE98] animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            <span className="text-sm font-semibold bg-gradient-to-r from-[#FFBE98] via-[#E6A07C] to-[#FFBE98] bg-[length:200%_100%] bg-clip-text text-transparent animate-[shimmer_2s_linear_infinite]">
              A IA está a ajustar o plano
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

/* ── Section Wrapper with hide toggle ── */
const HideableSection = ({ id, children, hiddenSections, toggleSection }) => {
  const isHidden = hiddenSections.includes(id);
  return (
    <div className="relative">
      {!isHidden && children}
      <button onClick={() => toggleSection(id)} data-testid={`toggle-section-${id}`}
        className="flex items-center gap-1 text-[10px] text-[#6B6661]/50 hover:text-[#6B6661] transition-colors mt-1">
        {isHidden ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
        {isHidden ? 'Mostrar secção' : 'Ocultar esta secção'}
      </button>
    </div>
  );
};

/* ════════════════════════════════════════════ */
/* ── MAIN COMPONENT ── */
/* ════════════════════════════════════════════ */
const TravelPlanner = () => {
  const [searchParams] = useSearchParams();
  const [destination, setDestination] = useState(searchParams.get('destination') || '');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [tripTypes, setTripTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refining, setRefining] = useState(false);
  const [refineSuccess, setRefineSuccess] = useState(false);
  const [error, setError] = useState('');
  const [plan, setPlan] = useState(null);
  const [affiliateLinks, setAffiliateLinks] = useState({});
  const [dynamicLinks, setDynamicLinks] = useState({});
  const [copied, setCopied] = useState(false);
  const [shared, setShared] = useState(false);
  const [showStickyBar, setShowStickyBar] = useState(false);
  const [activeTab, setActiveTab] = useState('guia');
  const [rateLimited, setRateLimited] = useState(false);
  const [rateLimitExpiry, setRateLimitExpiry] = useState(null);
  const [rateLimitMinutes, setRateLimitMinutes] = useState(0);
  const [hiddenSections, setHiddenSections] = useState(() => {
    try { return JSON.parse(localStorage.getItem('planner_hidden') || '[]'); } catch { return []; }
  });
  const resultsRef = useRef(null);
  const startDateRef = useRef(null);
  const tabRefs = { guia: useRef(null), roteiro: useRef(null), checklist: useRef(null), dicas: useRef(null) };

  useEffect(() => {
    document.title = '4Luis — Planeie a sua viagem com IA';
    axios.get(`${API}/affiliate-links`).then(r => setAffiliateLinks(r.data)).catch(() => {});
    // If destination pre-filled, scroll to form and focus date
    if (searchParams.get('destination')) {
      setTimeout(() => {
        document.querySelector('[data-testid="planner-form"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        startDateRef.current?.focus();
      }, 400);
    } else {
      window.scrollTo(0, 0);
    }
  }, []);

  // Build dynamic links when plan/destination/dates available
  useEffect(() => {
    if (plan && destination && startDate && endDate && Object.keys(affiliateLinks).length) {
      setDynamicLinks(buildDynamicLinks(affiliateLinks, plan.destination || destination, startDate, endDate));
    }
  }, [plan, destination, startDate, endDate, affiliateLinks]);

  useEffect(() => {
    if (!plan) { setShowStickyBar(false); return; }
    const onScroll = () => {
      if (resultsRef.current) {
        setShowStickyBar(resultsRef.current.getBoundingClientRect().top < -100);
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [plan]);

  // Countdown timer for rate limit
  useEffect(() => {
    if (!rateLimitExpiry) return;
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((rateLimitExpiry - Date.now()) / 60000));
      setRateLimitMinutes(remaining);
      if (remaining <= 0) { setRateLimited(false); setRateLimitExpiry(null); }
    };
    tick();
    const interval = setInterval(tick, 30000);
    return () => clearInterval(interval);
  }, [rateLimitExpiry]);

  const toggleSection = (id) => {
    setHiddenSections(prev => {
      const next = prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id];
      localStorage.setItem('planner_hidden', JSON.stringify(next));
      return next;
    });
  };

  const toggleTripType = (id) => {
    setTripTypes(prev => prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]);
  };

  const numDays = startDate && endDate
    ? Math.max(1, Math.ceil((new Date(endDate) - new Date(startDate)) / 86400000) + 1) : 0;

  const trackClick = (platform) => {
    const token = localStorage.getItem('token');
    axios.post(`${API}/affiliate-click`, { platform }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }).catch(() => {});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(''); setPlan(null);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API}/ai/travel-plan`, {
        destination, start_date: startDate, end_date: endDate,
        trip_type: tripTypes.length > 0 ? tripTypes : ''
      }, { headers: token ? { Authorization: `Bearer ${token}` } : {}, timeout: 60000 });
      setPlan(res.data.plan);
      setActiveTab('guia');
      setRateLimited(false);
    } catch (err) {
      if (err.response?.status === 429) {
        setRateLimited(true);
        setRateLimitExpiry(Date.now() + 60 * 60 * 1000);
        setError(err.response?.data?.detail || 'Já criaste vários planos! ✈️ Podes gerar um novo dentro de 1 hora.');
      } else {
        setError(err.response?.data?.detail || 'Erro ao gerar plano. Tente novamente.');
      }
    } finally { setLoading(false); }
  };

  const handleRefine = async (refinement) => {
    if (!plan) return;
    setRefining(true);
    setRefineSuccess(false);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API}/ai/travel-plan/refine`, {
        destination, start_date: startDate, end_date: endDate,
        trip_type: tripTypes.length > 0 ? tripTypes : '',
        previous_plan: plan, refinement
      }, { headers: token ? { Authorization: `Bearer ${token}` } : {}, timeout: 60000 });
      setPlan(res.data.plan);
      setRefineSuccess(true);
      // Scroll to top of document
      resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setTimeout(() => setRefineSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao ajustar plano. Tente novamente.');
    } finally { setRefining(false); }
  };

  const scrollToTab = (tabId) => {
    setActiveTab(tabId);
    tabRefs[tabId]?.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const buildPlanText = () => {
    if (!plan) return '';
    const l = [`GUIA DE VIAGEM: ${plan.destination}`, `Datas: ${plan.dates}`];
    if (plan.summary) l.push(`\n${plan.summary}`);
    if (plan.weather) l.push(`\nClima: ${plan.weather}`);
    if (plan.packing) {
      l.push('\nO que levar:');
      if (plan.packing.clothing?.length) { l.push('  Roupa:'); plan.packing.clothing.forEach(i => l.push(`    - ${i}`)); }
      if (plan.packing.essentials?.length) { l.push('  Essenciais:'); plan.packing.essentials.forEach(i => l.push(`    - ${i}`)); }
    }
    l.push('\n--- ROTEIRO ---');
    plan.itinerary?.forEach(d => { l.push(`\nDia ${d.day}: ${d.title}`); d.activities?.forEach(a => l.push(`  - ${a}`)); });
    if (plan.checklist) {
      l.push('\n--- CHECKLIST ---');
      Object.entries(plan.checklist).forEach(([key, items]) => {
        const label = key === 'documents' ? 'Documentos' : key === 'hygiene' ? 'Higiene' : 'Tecnologia';
        l.push(`  ${label}:`);
        items?.forEach(i => l.push(`    - ${i}`));
      });
    }
    if (plan.local_tips?.length) { l.push('\n--- DICAS LOCAIS ---'); plan.local_tips.forEach(t => l.push(`  - ${t}`)); }
    l.push('\n\nGerado por 4Luis AI Travel Planner\nSonha connosco ✈️');
    return l.join('\n');
  };

  const handleCopy = async () => {
    const text = buildPlanText();
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
    }
    setTimeout(() => setCopied(false), 2000);
  };
  const handleShare = async () => {
    if (!plan) return;
    const fullText = buildPlanText();
    if (navigator.share) {
      try {
        await navigator.share({ title: `Plano de viagem: ${plan.destination}`, text: fullText });
        return;
      } catch (e) {
        if (e.name === 'AbortError') return; // user cancelled
      }
    }
    // Fallback: copy to clipboard
    try {
      await navigator.clipboard.writeText(fullText);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = fullText; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
    }
    setShared(true);
    setTimeout(() => setShared(false), 2500);
  };

  return (
    <div className="min-h-screen bg-[#FAFAF9]">
      {/* Hero */}
      <div className="bg-gradient-to-b from-[#FFBE98]/15 to-[#FAFAF9] pt-24 pb-4 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="inline-flex items-center gap-2 bg-white/80 rounded-full px-4 py-1.5 mb-3 border border-[#FFBE98]/20">
              <Sparkles className="w-3.5 h-3.5 text-[#FFBE98]" />
              <span className="text-xs font-medium text-[#6B6661]">Powered by AI</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#2D2A26]" data-testid="planner-title">Planeie a sua viagem com IA</h1>
          </motion.div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 pb-24">
        {/* ── Form ── */}
        {!plan && !loading && (
          <motion.form initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
            onSubmit={handleSubmit} className="bg-white rounded-2xl border border-stone-100 p-5 shadow-sm space-y-3" data-testid="planner-form">
            <div>
              <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-[#FFBE98]" />Destino
              </label>
              <input type="text" value={destination} onChange={(e) => setDestination(e.target.value)}
                placeholder="Ex: Tóquio, Japão" className="w-full px-4 py-2.5 input-warm" required data-testid="input-destination" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-[#FFBE98]" />Início
                </label>
                <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-4 py-2.5 input-warm" required data-testid="input-start-date" ref={startDateRef} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-[#FFBE98]" />Fim
                </label>
                <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
                  min={startDate} className="w-full px-4 py-2.5 input-warm" required data-testid="input-end-date" />
              </div>
            </div>
            {numDays > 0 && <p className="text-xs text-[#6B6661] text-center">{numDays} {numDays === 1 ? 'dia' : 'dias'} de viagem</p>}
            <div>
              <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-[#FFBE98]" />
                Tipo de viagem <span className="text-[#6B6661] font-normal">(selecione um ou mais)</span>
              </label>
              <div className="flex flex-wrap gap-1.5">
                {TRIP_TYPES.map(t => (
                  <button key={t.id} type="button" onClick={() => toggleTripType(t.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      tripTypes.includes(t.id) ? 'bg-[#FFBE98] text-white' : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'
                    }`} data-testid={`trip-type-${t.id}`}>{t.label}</button>
                ))}
              </div>
              {tripTypes.length > 1 && (
                <p className="text-[10px] text-[#FFBE98] mt-1.5">{tripTypes.length} tipos selecionados</p>
              )}
            </div>
            {error && (
              <div className={`text-sm text-center px-4 py-3 rounded-xl ${
                error.includes('✈️') ? 'bg-sky-50 text-sky-700' : 'bg-red-50 text-red-500'
              }`} data-testid="planner-error">
                {error}
              </div>
            )}
            <div className="space-y-1.5">
              <button type="submit" disabled={loading || rateLimited || !destination || !startDate || !endDate}
                className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2" data-testid="generate-btn">
                <Sparkles className="w-4 h-4" />Gerar plano de viagem
              </button>
              {rateLimited && rateLimitMinutes > 0 && (
                <p className="text-xs text-center text-[#6B6661] flex items-center justify-center gap-1" data-testid="rate-limit-countdown">
                  <Clock className="w-3 h-3" />Novo plano disponível em {rateLimitMinutes} {rateLimitMinutes === 1 ? 'minuto' : 'minutos'}
                </p>
              )}
            </div>
          </motion.form>
        )}

        {/* Loading */}
        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="bg-white rounded-2xl border border-stone-100 p-10 shadow-sm text-center">
            <Loader2 className="w-8 h-8 animate-spin text-[#FFBE98] mx-auto mb-4" />
            <p className="text-sm font-semibold text-[#2D2A26]">A gerar o seu guia de viagem...</p>
            <p className="text-xs text-[#6B6661] mt-1">Isto pode demorar até 30 segundos</p>
          </motion.div>
        )}

        {/* ════════ UNIFIED TRAVEL DOCUMENT ════════ */}
        {plan && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} ref={resultsRef}>

            {/* Refining overlay */}
            {refining && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="bg-[#FFBE98]/8 border border-[#FFBE98]/25 rounded-xl p-4 flex items-center gap-3 mb-3 shadow-sm">
                <Loader2 className="w-5 h-5 animate-spin text-[#FFBE98]" />
                <div>
                  <div className="flex items-center gap-2">
                    <div className="flex gap-[3px]">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FFBE98] animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FFBE98] animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FFBE98] animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                    <span className="text-sm font-semibold bg-gradient-to-r from-[#FFBE98] via-[#E6A07C] to-[#FFBE98] bg-[length:200%_100%] bg-clip-text text-transparent animate-[shimmer_2s_linear_infinite]">
                      A ajustar o seu plano com IA
                    </span>
                  </div>
                  <p className="text-xs text-[#6B6661] mt-0.5">Isto pode demorar até 30 segundos.</p>
                </div>
              </motion.div>
            )}

            {/* ── Single Document Card ── */}
            <div className="bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden" data-testid="travel-document">
              {/* Document header */}
              <div className="bg-gradient-to-r from-[#FFBE98]/10 to-[#E6A07C]/5 px-5 py-5 border-b border-stone-100/50">
                <p className="text-[10px] font-semibold text-[#FFBE98] uppercase tracking-wider mb-1">O seu guia de viagem</p>
                <h2 className="text-xl font-bold text-[#2D2A26]" data-testid="plan-destination">{plan.destination}</h2>
                <p className="text-sm text-[#6B6661] mt-0.5">{plan.dates}</p>
                {plan.summary && <p className="text-sm text-[#2D2A26]/80 mt-2 italic leading-relaxed">{plan.summary}</p>}
                <TopBookingBar links={dynamicLinks} onTrack={trackClick} />
              </div>

              {/* Tab Navigation */}
              <div className="flex border-b border-stone-100 sticky top-16 bg-white z-10" data-testid="tab-navigation">
                {TABS.map(tab => (
                  <button key={tab.id} onClick={() => scrollToTab(tab.id)} data-testid={`tab-${tab.id}`}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-semibold transition-all border-b-2 ${
                      activeTab === tab.id
                        ? 'text-[#FFBE98] border-[#FFBE98]'
                        : 'text-[#6B6661] border-transparent hover:text-[#2D2A26]'
                    }`}>
                    <tab.icon className="w-3.5 h-3.5" />{tab.label}
                  </button>
                ))}
              </div>

              {/* ── TAB: Guia ── */}
              <div ref={tabRefs.guia} className="px-5 pt-5 pb-3" data-testid="tab-content-guia">
                <HideableSection id="weather" hiddenSections={hiddenSections} toggleSection={toggleSection}>
                  {plan.weather && (
                    <div className="flex items-start gap-3 bg-amber-50/50 rounded-xl p-3 mb-3">
                      <Sun className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-xs font-bold text-[#2D2A26] mb-0.5">Clima esperado</p>
                        <p className="text-xs text-[#6B6661] leading-relaxed">{plan.weather}</p>
                      </div>
                    </div>
                  )}
                </HideableSection>

                <HideableSection id="packing" hiddenSections={hiddenSections} toggleSection={toggleSection}>
                  {plan.packing && (
                    <div className="flex items-start gap-3 bg-violet-50/50 rounded-xl p-3 mb-3">
                      <Shirt className="w-4 h-4 text-violet-500 mt-0.5 shrink-0" />
                      <div className="flex-1">
                        <p className="text-xs font-bold text-[#2D2A26] mb-1.5">O que levar</p>
                        <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                          {plan.packing.clothing?.map((item, i) => (
                            <p key={`c-${i}`} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                              <span className="w-1 h-1 bg-violet-400 rounded-full shrink-0" />{item}
                            </p>
                          ))}
                          {plan.packing.essentials?.map((item, i) => (
                            <p key={`e-${i}`} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                              <span className="w-1 h-1 bg-[#FFBE98] rounded-full shrink-0" />{item}
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </HideableSection>
              </div>

              {/* Divider */}
              <div className="h-px bg-stone-100 mx-5" />

              {/* ── TAB: Roteiro ── */}
              <div ref={tabRefs.roteiro} className="px-5 pt-5 pb-3" data-testid="tab-content-roteiro">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-9 h-9 bg-sky-50 rounded-xl flex items-center justify-center">
                    <Calendar className="w-4.5 h-4.5 text-sky-500" />
                  </div>
                  <h3 className="font-bold text-[#2D2A26]">Roteiro dia a dia</h3>
                </div>
                <HideableSection id="itinerary" hiddenSections={hiddenSections} toggleSection={toggleSection}>
                  <div className="space-y-4">
                    {plan.itinerary?.map((day, i) => (
                      <div key={i} className="border-l-2 border-[#FFBE98]/40 pl-3">
                        <p className="text-xs font-bold text-[#FFBE98]">Dia {day.day}</p>
                        <p className="text-sm font-semibold text-[#2D2A26]">{day.title}</p>
                        <ul className="mt-1 space-y-0.5">
                          {day.activities?.map((a, j) => {
                            const match = detectActivityCTA(a);
                            return (
                              <li key={j} className="text-xs text-[#6B6661] flex items-start gap-1.5 flex-wrap">
                                <span className="text-[#FFBE98] mt-0.5 shrink-0">&#8226;</span>
                                <span className="flex-1">{a}</span>
                                {match && (
                                  <InlineActivityCTA match={match}
                                    link={dynamicLinks[match.platform]?.url}
                                    onTrack={trackClick} />
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    ))}
                  </div>
                </HideableSection>

                <ContextualCTA icon={Plane} text="Ver voos disponíveis" label="Ver voos"
                  sublabel="Compare preços de centenas de companhias"
                  link={dynamicLinks.skyscanner?.url} platform="skyscanner" onTrack={trackClick} />
              </div>

              <div className="h-px bg-stone-100 mx-5" />

              {/* ── TAB: Checklist ── */}
              <div ref={tabRefs.checklist} className="px-5 pt-5 pb-3" data-testid="tab-content-checklist">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center">
                    <ClipboardList className="w-4.5 h-4.5 text-emerald-500" />
                  </div>
                  <h3 className="font-bold text-[#2D2A26]">Checklist de viagem</h3>
                </div>
                <HideableSection id="checklist" hiddenSections={hiddenSections} toggleSection={toggleSection}>
                  {plan.checklist && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {Object.entries(plan.checklist).map(([key, items]) => (
                        <div key={key} className="bg-stone-50/50 rounded-lg p-2.5">
                          <p className="text-[10px] font-bold text-[#2D2A26] uppercase tracking-wide mb-1.5">
                            {key === 'documents' ? 'Documentos' : key === 'hygiene' ? 'Higiene' : 'Tecnologia'}
                          </p>
                          {items?.map((item, i) => (
                            <p key={i} className="text-xs text-[#6B6661] flex items-center gap-1.5 py-0.5">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />{item}
                            </p>
                          ))}
                          {key === 'tech' && (
                            <a href={dynamicLinks.airalo?.url || '#'} target="_blank" rel="noopener noreferrer"
                              onClick={() => trackClick('airalo')} data-testid="checklist-esim-cta"
                              className="flex items-center gap-1 mt-1.5 text-[10px] font-bold text-[#FFBE98] hover:text-[#E6A07C] transition-colors">
                              <Wifi className="w-3 h-3" />Internet no destino<ExternalLink className="w-2.5 h-2.5 opacity-60" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </HideableSection>
              </div>

              <div className="h-px bg-stone-100 mx-5" />

              {/* ── TAB: Dicas ── */}
              <div ref={tabRefs.dicas} className="px-5 pt-5 pb-3" data-testid="tab-content-dicas">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 bg-teal-50 rounded-xl flex items-center justify-center">
                    <Lightbulb className="w-4.5 h-4.5 text-teal-500" />
                  </div>
                  <h3 className="font-bold text-[#2D2A26]">Dicas locais</h3>
                </div>
                <HideableSection id="local_tips" hiddenSections={hiddenSections} toggleSection={toggleSection}>
                  {plan.local_tips && (
                    <ul className="space-y-2">
                      {plan.local_tips.map((tip, i) => (
                        <li key={i} className="text-sm text-[#6B6661] flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                          <span className="flex-1">
                            {tip}
                            {tipHasBookingHint(tip) && (
                              <a href={dynamicLinks.getyourguide?.url || '#'} target="_blank" rel="noopener noreferrer"
                                onClick={() => trackClick('getyourguide')}
                                className="inline-flex items-center gap-1 text-[10px] font-bold text-[#FFBE98] hover:text-[#E6A07C] transition-colors ml-1">
                                <Ticket className="w-3 h-3" />Ver disponibilidade<ExternalLink className="w-2.5 h-2.5 opacity-60" />
                              </a>
                            )}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </HideableSection>

                <ContextualCTA icon={Compass} text="Reservar atividades e experiências" label="Descobrir"
                  sublabel="Tours, visitas guiadas e muito mais"
                  link={dynamicLinks.getyourguide?.url} platform="getyourguide" onTrack={trackClick} />
              </div>

              {/* ── Actions Footer ── */}
              <div className="px-5 py-4 border-t border-stone-100 bg-[#FFBE98]/[0.03]" data-testid="actions-footer">
                <div className="space-y-3">
                  {/* Primary: Ajustar */}
                  <RefinePanel onSubmit={handleRefine} loading={refining} success={refineSuccess} />
                  {/* Secondary: Copy + Share */}
                  <div className="flex items-center gap-2">
                    <button onClick={handleCopy} data-testid="copy-btn"
                      className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#6B6661] border border-stone-200 bg-white hover:bg-stone-50 hover:border-stone-300 px-3 py-2 rounded-lg transition-colors">
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? 'Copiado!' : 'Copiar plano'}
                    </button>
                    <button onClick={handleShare} data-testid="share-btn"
                      className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#6B6661] border border-stone-200 bg-white hover:bg-stone-50 hover:border-stone-300 px-3 py-2 rounded-lg transition-colors">
                      {shared ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Share2 className="w-3.5 h-3.5" />}
                      {shared ? 'Plano copiado! Partilha onde quiseres' : 'Partilhar'}
                    </button>
                  </div>
                </div>
                {error && (
                  <div className={`text-xs text-center mt-2 px-3 py-2 rounded-lg w-full ${
                    error.includes('✈️') ? 'bg-sky-50 text-sky-700' : 'bg-red-50 text-red-500'
                  }`} data-testid="refine-error">
                    {error}
                    {error.includes('✈️') && (
                      <p className="text-[10px] mt-1 opacity-70">Podes continuar a ajustar, copiar ou partilhar o plano atual.</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Disclaimer */}
            <p className="text-center text-xs text-[#6B6661]/60 pt-4">
              Alguns dos links nesta página são de parceiros. Ao usar estes links,<br/>
              ajuda a 4Luis a continuar a apoiar viagens de sonho.
            </p>
          </motion.div>
        )}
      </div>

      <StickyBar links={dynamicLinks} onTrack={trackClick} visible={showStickyBar} />
    </div>
  );
};

export default TravelPlanner;
