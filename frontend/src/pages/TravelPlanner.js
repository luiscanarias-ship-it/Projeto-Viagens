import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MapPin, Calendar, Compass, Sparkles, Loader2, ChevronDown, ChevronUp,
  Sun, Shirt, ClipboardList, Lightbulb, Hotel, Plane, Wifi,
  ExternalLink, Star, RefreshCw, Copy, Share2, Check,
  Globe, Ticket
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TRIP_TYPES = [
  { id: 'cultural', label: 'Cultural' },
  { id: 'aventura', label: 'Aventura' },
  { id: 'relaxamento', label: 'Relaxamento' },
  { id: 'gastronomica', label: 'Gastronómica' },
  { id: 'romantica', label: 'Romântica' },
  { id: 'familia', label: 'Família' }
];

/* ── Collapsible Section ── */
const Section = ({ icon: Icon, title, children, defaultOpen = false, color = 'text-[#FFBE98]', testId }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-white rounded-2xl border border-stone-100 overflow-hidden shadow-sm">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left"
        data-testid={testId || `section-toggle-${title.toLowerCase().replace(/\s/g, '-')}`}
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-stone-50 rounded-xl flex items-center justify-center">
            <Icon className={`w-4.5 h-4.5 ${color}`} />
          </div>
          <h3 className="font-bold text-[#2D2A26]">{title}</h3>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-[#6B6661]" /> : <ChevronDown className="w-4 h-4 text-[#6B6661]" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

/* ── Contextual CTA Block ── */
const ContextualCTA = ({ icon: Icon, text, label, sublabel, link, platform, onTrack }) => (
  <motion.div
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-gradient-to-r from-[#FFBE98]/8 to-[#E6A07C]/6 rounded-xl border border-[#FFBE98]/15 p-3.5 flex items-center gap-3"
  >
    <div className="w-9 h-9 bg-white rounded-lg flex items-center justify-center shadow-sm shrink-0">
      <Icon className="w-4 h-4 text-[#FFBE98]" />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-xs font-semibold text-[#2D2A26]">{text}</p>
      {sublabel && <p className="text-[10px] text-[#6B6661] mt-0.5">{sublabel}</p>}
    </div>
    <a
      href={link || '#'}
      target="_blank"
      rel="noopener noreferrer"
      onClick={() => onTrack(platform)}
      data-testid={`cta-contextual-${platform}`}
      className="shrink-0 flex items-center gap-1.5 bg-[#2D2A26] text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-[#1a1816] transition-colors"
    >
      {label}
      <ExternalLink className="w-3 h-3" />
    </a>
  </motion.div>
);

/* ── Enhanced Booking Section ── */
const BookingSection = ({ links, onTrack }) => {
  const items = [
    { id: 'booking', icon: Hotel, label: 'Reservar alojamento', desc: 'Cancelamento flexível na maioria', tag: 'Recomendado pela 4Luis', primary: true },
    { id: 'skyscanner', icon: Plane, label: 'Pesquisar voos', desc: 'Compare centenas de opções', tag: 'Melhores preços', primary: true },
    { id: 'getyourguide', icon: Ticket, label: 'Reservar atividades', desc: 'Tours e experiências únicas', tag: 'Recomendado pela 4Luis', primary: false },
    { id: 'airalo', icon: Wifi, label: 'Obter eSIM', desc: 'Internet sem roaming', tag: null, primary: false },
  ];

  return (
    <div className="bg-white rounded-2xl border border-stone-100 overflow-hidden shadow-sm" data-testid="booking-section">
      <div className="p-4 pb-1">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 bg-[#FFBE98]/10 rounded-xl flex items-center justify-center">
            <Globe className="w-4.5 h-4.5 text-[#FFBE98]" />
          </div>
          <div>
            <h3 className="font-bold text-[#2D2A26]">Reservar esta viagem</h3>
            <p className="text-xs text-[#6B6661]">Tudo o que precisa para concretizar o seu plano</p>
          </div>
        </div>
      </div>
      <div className="px-4 pb-4 space-y-2">
        {items.map(item => (
          <a
            key={item.id}
            href={links[item.id]?.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => onTrack(item.id)}
            data-testid={`booking-cta-${item.id}`}
            className={`flex items-center gap-3 p-3 rounded-xl border transition-all group ${
              item.primary 
                ? 'border-[#FFBE98]/20 bg-[#FFBE98]/5 hover:bg-[#FFBE98]/10' 
                : 'border-stone-100 bg-white hover:bg-stone-50'
            }`}
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
              item.primary ? 'bg-white shadow-sm' : 'bg-stone-50'
            }`}>
              <item.icon className={`w-4 h-4 ${item.primary ? 'text-[#FFBE98]' : 'text-[#6B6661]'}`} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-[#2D2A26]">{item.label}</span>
                {item.tag && (
                  <span className="text-[9px] font-medium text-[#FFBE98] bg-[#FFBE98]/10 px-1.5 py-0.5 rounded-full whitespace-nowrap">
                    {item.tag}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-[#6B6661]">{item.desc}</p>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-[#6B6661] group-hover:text-[#FFBE98] transition-colors shrink-0" />
          </a>
        ))}
      </div>
    </div>
  );
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
        <motion.div
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 80, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-stone-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
          data-testid="sticky-booking-bar"
        >
          <div className="max-w-2xl mx-auto px-4 py-2.5 flex items-center gap-2">
            <span className="text-xs font-semibold text-[#6B6661] hidden sm:block whitespace-nowrap mr-1">Reservar:</span>
            {items.map(item => (
              <a
                key={item.id}
                href={links[item.id]?.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => onTrack(item.id)}
                data-testid={`sticky-cta-${item.id}`}
                className="flex-1 flex items-center justify-center gap-1.5 bg-[#2D2A26] text-white text-xs font-semibold py-2.5 px-3 rounded-xl hover:bg-[#1a1816] transition-colors"
              >
                <item.icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </a>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

/* ── Main Component ── */
const TravelPlanner = () => {
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [tripType, setTripType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [plan, setPlan] = useState(null);
  const [affiliateLinks, setAffiliateLinks] = useState({});
  const [copied, setCopied] = useState(false);
  const [showStickyBar, setShowStickyBar] = useState(false);
  const resultsRef = useRef(null);

  useEffect(() => {
    document.title = '4Luis — AI Travel Planner';
    window.scrollTo(0, 0);
    axios.get(`${API}/affiliate-links`).then(r => setAffiliateLinks(r.data)).catch(() => {});
  }, []);

  // Show sticky bar when scrolled past results header
  useEffect(() => {
    if (!plan) { setShowStickyBar(false); return; }
    const onScroll = () => {
      if (resultsRef.current) {
        const rect = resultsRef.current.getBoundingClientRect();
        setShowStickyBar(rect.top < -100);
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, [plan]);

  const numDays = startDate && endDate
    ? Math.max(1, Math.ceil((new Date(endDate) - new Date(startDate)) / 86400000) + 1)
    : 0;

  const trackClick = (platform) => {
    const token = localStorage.getItem('token');
    axios.post(`${API}/affiliate-click`, { platform }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }).catch(() => {});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setPlan(null);

    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${API}/ai/travel-plan`, {
        destination, start_date: startDate, end_date: endDate, trip_type: tripType
      }, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        timeout: 60000
      });
      setPlan(res.data.plan);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao gerar plano. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = () => {
    setPlan(null);
    setShowStickyBar(false);
    setTimeout(() => {
      handleSubmit({ preventDefault: () => {} });
    }, 100);
  };

  const handleCopy = () => {
    if (!plan) return;
    const lines = [];
    lines.push(`Plano de viagem: ${plan.destination}`);
    lines.push(`Datas: ${plan.dates}`);
    if (plan.summary) lines.push(`\n${plan.summary}`);
    lines.push('\n--- ROTEIRO ---');
    plan.itinerary?.forEach(day => {
      lines.push(`\nDia ${day.day}: ${day.title}`);
      day.activities?.forEach(a => lines.push(`  - ${a}`));
    });
    if (plan.weather) { lines.push('\n--- CLIMA ---'); lines.push(plan.weather); }
    if (plan.packing) {
      lines.push('\n--- O QUE LEVAR ---');
      plan.packing.clothing?.forEach(i => lines.push(`  Roupa: ${i}`));
      plan.packing.essentials?.forEach(i => lines.push(`  Essencial: ${i}`));
    }
    if (plan.local_tips) {
      lines.push('\n--- DICAS LOCAIS ---');
      plan.local_tips.forEach(t => lines.push(`  - ${t}`));
    }
    lines.push('\n\nGerado por 4Luis AI Travel Planner');

    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleShare = async () => {
    if (!plan) return;
    const text = `Plano de viagem para ${plan.destination} (${plan.dates}) — Gerado por 4Luis AI Travel Planner`;
    if (navigator.share) {
      try { await navigator.share({ title: `Viagem: ${plan.destination}`, text, url: window.location.href }); } catch {}
    } else {
      handleCopy();
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAF9]">
      {/* Hero */}
      <div className="bg-gradient-to-b from-[#FFBE98]/15 to-[#FAFAF9] pt-28 pb-10 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="inline-flex items-center gap-2 bg-white/80 rounded-full px-4 py-1.5 mb-5 border border-[#FFBE98]/20">
              <Sparkles className="w-3.5 h-3.5 text-[#FFBE98]" />
              <span className="text-xs font-medium text-[#6B6661]">Powered by AI</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#2D2A26] mb-3" data-testid="planner-title">
              AI Travel Planner
            </h1>
            <p className="text-base text-[#6B6661]">
              Gera um plano de viagem personalizado em segundos.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 pb-24">
        {/* Form */}
        {!plan && !loading && (
          <motion.form
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            onSubmit={handleSubmit}
            className="bg-white rounded-2xl border border-stone-100 p-5 shadow-sm space-y-4"
            data-testid="planner-form"
          >
            <div>
              <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-[#FFBE98]" />
                Destino
              </label>
              <input
                type="text"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="Ex: Tóquio, Japão"
                className="w-full px-4 py-2.5 input-warm"
                required
                data-testid="input-destination"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-[#FFBE98]" />
                  Início
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-4 py-2.5 input-warm"
                  required
                  data-testid="input-start-date"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-[#FFBE98]" />
                  Fim
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  min={startDate}
                  className="w-full px-4 py-2.5 input-warm"
                  required
                  data-testid="input-end-date"
                />
              </div>
            </div>

            {numDays > 0 && (
              <p className="text-xs text-[#6B6661] text-center">{numDays} {numDays === 1 ? 'dia' : 'dias'} de viagem</p>
            )}

            <div>
              <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-[#FFBE98]" />
                Tipo de viagem <span className="text-[#6B6661] font-normal">(opcional)</span>
              </label>
              <div className="flex flex-wrap gap-1.5">
                {TRIP_TYPES.map(t => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setTripType(tripType === t.id ? '' : t.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      tripType === t.id
                        ? 'bg-[#FFBE98] text-white'
                        : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'
                    }`}
                    data-testid={`trip-type-${t.id}`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {error && <p className="text-sm text-red-500 text-center" data-testid="planner-error">{error}</p>}

            <button
              type="submit"
              disabled={loading || !destination || !startDate || !endDate}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              data-testid="generate-btn"
            >
              <Sparkles className="w-4 h-4" />
              Gerar plano de viagem
            </button>
          </motion.form>
        )}

        {/* Loading State */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="bg-white rounded-2xl border border-stone-100 p-10 shadow-sm text-center"
          >
            <Loader2 className="w-8 h-8 animate-spin text-[#FFBE98] mx-auto mb-4" />
            <p className="text-sm font-semibold text-[#2D2A26]">A gerar o teu plano...</p>
            <p className="text-xs text-[#6B6661] mt-1">Isto pode demorar até 30 segundos</p>
          </motion.div>
        )}

        {/* Results */}
        {plan && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-3"
            ref={resultsRef}
          >
            {/* Summary header */}
            <div className="bg-white rounded-2xl border border-stone-100 p-5 shadow-sm">
              <div className="text-center">
                <h2 className="text-xl font-bold text-[#2D2A26]" data-testid="plan-destination">{plan.destination}</h2>
                <p className="text-sm text-[#6B6661] mt-1">{plan.dates}</p>
                {plan.summary && <p className="text-sm text-[#2D2A26] mt-2 italic">{plan.summary}</p>}
              </div>
              {/* Action buttons */}
              <div className="flex items-center justify-center gap-2 mt-4">
                <button
                  onClick={handleRegenerate}
                  className="flex items-center gap-1.5 text-xs font-semibold text-[#6B6661] bg-stone-100 hover:bg-stone-200 px-3 py-2 rounded-lg transition-colors"
                  data-testid="regenerate-btn"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Gerar novo plano
                </button>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs font-semibold text-[#6B6661] bg-stone-100 hover:bg-stone-200 px-3 py-2 rounded-lg transition-colors"
                  data-testid="copy-btn"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copiado!' : 'Copiar'}
                </button>
                <button
                  onClick={handleShare}
                  className="flex items-center gap-1.5 text-xs font-semibold text-[#6B6661] bg-stone-100 hover:bg-stone-200 px-3 py-2 rounded-lg transition-colors"
                  data-testid="share-btn"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  Partilhar
                </button>
              </div>
            </div>

            {/* ── 1. ITINERARY ── */}
            <Section icon={Calendar} title="Roteiro dia a dia" defaultOpen={true} color="text-sky-500" testId="section-itinerary">
              <div className="space-y-3">
                {plan.itinerary?.map((day, i) => (
                  <div key={i} className="border-l-2 border-[#FFBE98]/40 pl-3">
                    <p className="text-xs font-bold text-[#FFBE98]">Dia {day.day}</p>
                    <p className="text-sm font-semibold text-[#2D2A26]">{day.title}</p>
                    <ul className="mt-1 space-y-0.5">
                      {day.activities?.map((a, j) => (
                        <li key={j} className="text-xs text-[#6B6661] flex items-start gap-1.5">
                          <span className="text-[#FFBE98] mt-0.5">&#8226;</span> {a}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </Section>

            {/* CTA: After itinerary → accommodation */}
            <ContextualCTA
              icon={Hotel}
              text="Ver alojamento recomendado"
              label="Ver hotéis"
              sublabel="Cancelamento flexível na maioria das opções"
              link={affiliateLinks.booking?.url}
              platform="booking"
              onTrack={trackClick}
            />

            {/* ── 2. BOOKING SECTION ── */}
            <BookingSection links={affiliateLinks} onTrack={trackClick} />

            {/* ── 3. WEATHER ── */}
            <Section icon={Sun} title="Clima esperado" color="text-amber-500" testId="section-weather">
              <p className="text-sm text-[#6B6661] leading-relaxed">{plan.weather}</p>
            </Section>

            {/* CTA: After weather → flights */}
            <ContextualCTA
              icon={Plane}
              text="Ver voos disponíveis"
              label="Ver voos"
              sublabel="Compare preços de centenas de companhias"
              link={affiliateLinks.skyscanner?.url}
              platform="skyscanner"
              onTrack={trackClick}
            />

            {/* ── 4. PACKING ── */}
            <Section icon={Shirt} title="O que levar" color="text-violet-500" testId="section-packing">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs font-bold text-[#2D2A26] mb-1.5">Roupa</p>
                  <ul className="space-y-1">
                    {plan.packing?.clothing?.map((item, i) => (
                      <li key={i} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                        <span className="w-1 h-1 bg-[#FFBE98] rounded-full" /> {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-bold text-[#2D2A26] mb-1.5">Essenciais</p>
                  <ul className="space-y-1">
                    {plan.packing?.essentials?.map((item, i) => (
                      <li key={i} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                        <span className="w-1 h-1 bg-[#FFBE98] rounded-full" /> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </Section>

            {/* ── 5. CHECKLIST ── */}
            <Section icon={ClipboardList} title="Checklist de viagem" color="text-emerald-500" testId="section-checklist">
              <div className="space-y-3">
                {plan.checklist && Object.entries(plan.checklist).map(([key, items]) => (
                  <div key={key}>
                    <p className="text-xs font-bold text-[#2D2A26] mb-1 capitalize">
                      {key === 'documents' ? 'Documentos' : key === 'hygiene' ? 'Higiene' : 'Tecnologia'}
                    </p>
                    <ul className="space-y-0.5">
                      {items?.map((item, i) => (
                        <li key={i} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                          <span className="w-1 h-1 bg-emerald-400 rounded-full" /> {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </Section>

            {/* CTA: After checklist → eSIM */}
            <ContextualCTA
              icon={Wifi}
              text="Comprar eSIM para a viagem"
              label="Ver eSIM"
              sublabel="Evite custos de roaming"
              link={affiliateLinks.airalo?.url}
              platform="airalo"
              onTrack={trackClick}
            />

            {/* ── 6. LOCAL TIPS ── */}
            <Section icon={Lightbulb} title="Dicas locais" color="text-teal-500" testId="section-local-tips">
              <ul className="space-y-2">
                {plan.local_tips?.map((tip, i) => (
                  <li key={i} className="text-sm text-[#6B6661] flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </Section>

            {/* CTA: After tips → activities */}
            <ContextualCTA
              icon={Compass}
              text="Reservar atividades e experiências"
              label="Descobrir"
              sublabel="Tours, visitas guiadas e muito mais"
              link={affiliateLinks.getyourguide?.url}
              platform="getyourguide"
              onTrack={trackClick}
            />

            {/* Footer disclaimer */}
            <p className="text-center text-xs text-[#6B6661]/60 pt-2">
              Alguns dos links nesta página são de parceiros. Ao usar estes links,<br/>
              ajuda a 4Luis a continuar a apoiar viagens de sonho.
            </p>
          </motion.div>
        )}
      </div>

      {/* Sticky Booking Bar */}
      <StickyBar links={affiliateLinks} onTrack={trackClick} visible={showStickyBar} />
    </div>
  );
};

export default TravelPlanner;
