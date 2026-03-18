import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MapPin, Calendar, Compass, Sparkles, Loader2, ChevronDown, ChevronUp,
  Sun, Shirt, ClipboardList, Lightbulb, Hotel, Plane, Wifi,
  ExternalLink, Star
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TRIP_TYPES = [
  { id: 'cultural', label: 'Cultural' },
  { id: 'aventura', label: 'Aventura' },
  { id: 'relaxamento', label: 'Relaxamento' },
  { id: 'gastronomica', label: 'Gastronomica' },
  { id: 'romantica', label: 'Romantica' },
  { id: 'familia', label: 'Familia' }
];

const Section = ({ icon: Icon, title, children, defaultOpen = false, color = 'text-[#FFBE98]' }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-white rounded-2xl border border-stone-100 overflow-hidden shadow-sm">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 text-left"
        data-testid={`section-toggle-${title.toLowerCase().replace(/\s/g, '-')}`}
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

const AffiliateBar = ({ links }) => {
  const trackClick = (platform) => {
    const token = localStorage.getItem('token');
    axios.post(`${API}/affiliate-click`, { platform }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }).catch(() => {});
  };

  const items = [
    { id: 'booking', icon: Hotel, label: 'Reservar hotel' },
    { id: 'skyscanner', icon: Plane, label: 'Ver voos' },
    { id: 'getyourguide', icon: Compass, label: 'Atividades' },
    { id: 'airalo', icon: Wifi, label: 'Comprar eSIM' }
  ];

  return (
    <div className="bg-gradient-to-r from-[#FFBE98]/10 to-[#E6A07C]/10 rounded-2xl border border-[#FFBE98]/20 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Star className="w-3.5 h-3.5 text-[#FFBE98] fill-[#FFBE98]" />
        <span className="text-xs font-bold text-[#FFBE98]">Reserve ja para esta viagem</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {items.map(item => (
          <a
            key={item.id}
            href={links[item.id]?.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => trackClick(item.id)}
            data-testid={`affiliate-${item.id}`}
            className="flex items-center gap-2 bg-white py-2 px-3 rounded-xl text-xs font-semibold text-[#2D2A26] hover:bg-stone-50 transition-colors border border-stone-100"
          >
            <item.icon className="w-3.5 h-3.5 text-[#6B6661]" />
            {item.label}
            <ExternalLink className="w-3 h-3 text-[#6B6661] ml-auto" />
          </a>
        ))}
      </div>
    </div>
  );
};

const TravelPlanner = () => {
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [tripType, setTripType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [plan, setPlan] = useState(null);
  const [affiliateLinks, setAffiliateLinks] = useState({});

  useEffect(() => {
    document.title = '4Luis — AI Travel Planner';
    window.scrollTo(0, 0);
    axios.get(`${API}/affiliate-links`).then(r => setAffiliateLinks(r.data)).catch(() => {});
  }, []);

  const numDays = startDate && endDate
    ? Math.max(1, Math.ceil((new Date(endDate) - new Date(startDate)) / 86400000) + 1)
    : 0;

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

      <div className="max-w-2xl mx-auto px-6 pb-20">
        {/* Form */}
        {!plan && (
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
                placeholder="Ex: Toquio, Japao"
                className="w-full px-4 py-2.5 input-warm"
                required
                data-testid="input-destination"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-[#FFBE98]" />
                  Inicio
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
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  A gerar o teu plano...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Gerar plano de viagem
                </>
              )}
            </button>
          </motion.form>
        )}

        {/* Results */}
        {plan && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-3"
          >
            {/* Summary header */}
            <div className="bg-white rounded-2xl border border-stone-100 p-5 shadow-sm text-center">
              <h2 className="text-xl font-bold text-[#2D2A26]" data-testid="plan-destination">{plan.destination}</h2>
              <p className="text-sm text-[#6B6661] mt-1">{plan.dates}</p>
              {plan.summary && <p className="text-sm text-[#2D2A26] mt-2 italic">{plan.summary}</p>}
              <button
                onClick={() => setPlan(null)}
                className="mt-3 text-xs text-[#FFBE98] hover:underline"
                data-testid="new-plan-btn"
              >
                Gerar novo plano
              </button>
            </div>

            {/* Itinerary */}
            <Section icon={Calendar} title="Roteiro dia a dia" defaultOpen={true} color="text-sky-500">
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

            {/* Weather */}
            <Section icon={Sun} title="Clima esperado" color="text-amber-500">
              <p className="text-sm text-[#6B6661] leading-relaxed">{plan.weather}</p>
            </Section>

            {/* Packing */}
            <Section icon={Shirt} title="O que levar" color="text-violet-500">
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

            {/* Checklist */}
            <Section icon={ClipboardList} title="Checklist de viagem" color="text-emerald-500">
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

            {/* Local tips */}
            <Section icon={Lightbulb} title="Dicas locais" color="text-teal-500">
              <ul className="space-y-2">
                {plan.local_tips?.map((tip, i) => (
                  <li key={i} className="text-sm text-[#6B6661] flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                    {tip}
                  </li>
                ))}
              </ul>
            </Section>

            {/* Affiliate reservations */}
            <AffiliateBar links={affiliateLinks} />
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default TravelPlanner;
