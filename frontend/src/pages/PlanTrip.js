import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Plane, Hotel, Compass, Car, Wifi, Shield, MapPin, 
  ExternalLink, Star, Heart, Sparkles, ArrowRight
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PlanTrip = () => {
  const [affiliateLinks, setAffiliateLinks] = useState({});
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const destinationParam = searchParams.get('destination') || '';

  useEffect(() => {
    document.title = '4Luis — Planeia a tua viagem com IA';
    window.scrollTo(0, 0);
    axios.get(`${API}/affiliate-links`).then(r => setAffiliateLinks(r.data)).catch(() => {});
  }, []);

  const trackClick = (platform) => {
    const token = localStorage.getItem('token');
    axios.post(`${API}/affiliate-click`, { platform }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }).catch(() => {});
  };

  const getLink = (id) => affiliateLinks[id]?.url || '#';

  const sections = [
    {
      id: 'hotels',
      icon: Hotel,
      iconBg: 'bg-[#FFBE98]/10',
      iconColor: 'text-[#FFBE98]',
      title: 'Encontra o hotel com melhor localização',
      description: 'Ficar no centro faz toda a diferença. Escolhe entre as opções que recomendamos — com cancelamento gratuito.',
      ctas: [
        { id: 'booking', icon: Hotel, label: 'Ver hotéis no centro', primary: true },
        { id: 'hotels', icon: Star, label: 'Ofertas com benefícios exclusivos', primary: false }
      ],
      micro: 'Cancelamento gratuito · Preços sobem rapidamente',
      badge: 'Recomendado pela 4Luis'
    },
    {
      id: 'flights',
      icon: Plane,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-500',
      title: 'Compara voos e poupa no preço',
      description: 'Os preços mudam constantemente. Compara agora e garante o melhor voo para as tuas datas.',
      ctas: [
        { id: 'skyscanner', icon: Plane, label: 'Comparar voos (melhor preço)', primary: true }
      ],
      micro: 'Sem custos adicionais para ti',
      badge: 'Recomendado pela 4Luis'
    },
    {
      id: 'activities',
      icon: Compass,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-500',
      title: 'Evita filas — reserva experiências',
      description: 'As melhores atividades esgotam rápido. Reserva com antecedência e evita filas à entrada.',
      ctas: [
        { id: 'getyourguide', icon: Compass, label: 'Reservar experiências (sem filas)', primary: true }
      ],
      micro: 'Cancelamento flexível · Muito procurado',
      badge: 'Recomendado pela 4Luis'
    },
    {
      id: 'transport',
      icon: Car,
      iconBg: 'bg-violet-50',
      iconColor: 'text-violet-500',
      title: 'Do aeroporto ao hotel sem stress',
      description: 'Compara transfers e aluguer de carro. Chega ao destino sem complicações.',
      ctas: [
        { id: 'cars', icon: Car, label: 'Ver opções de transporte', primary: true }
      ],
      micro: 'Sem custos adicionais para ti'
    },
    {
      id: 'esim',
      icon: Wifi,
      iconBg: 'bg-teal-50',
      iconColor: 'text-teal-500',
      title: 'Internet mal aterras — sem roaming',
      description: 'Ativa o eSIM antes de viajar e fica ligado desde o momento em que chegas.',
      ctas: [
        { id: 'airalo', icon: Wifi, label: 'Comprar eSIM (ativa antes de ir)', primary: true },
        { id: 'holafly', icon: Wifi, label: 'Dados ilimitados', primary: false }
      ],
      micro: 'Funciona mal aterras · Sem surpresas na fatura'
    },
    {
      id: 'insurance',
      icon: Shield,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-500',
      title: 'Os imprevistos acontecem — protege-te',
      description: 'Cancelamentos, emergências médicas, bagagem perdida. O seguro cobre tudo por pouco.',
      ctas: [
        { id: 'insurance', icon: Shield, label: 'Fazer seguro de viagem', primary: true }
      ],
      micro: 'Recomendado pela 4Luis · Cobertura completa'
    },
    {
      id: 'map',
      icon: MapPin,
      iconBg: 'bg-red-50',
      iconColor: 'text-red-500',
      title: 'Explora o destino antes de ir',
      description: 'Descobre os pontos de interesse e planeia as tuas rotas com antecedência.',
      ctas: [
        { id: 'googlemaps', icon: MapPin, label: 'Abrir Google Maps', primary: true, isMap: true }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-[#F5F3F0]">
      {/* Hero */}
      <div className="bg-gradient-to-b from-[#FFBE98]/12 to-transparent pt-28 pb-14 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center gap-2 bg-white/70 backdrop-blur-sm rounded-full px-4 py-1.5 mb-5 border border-[#FFBE98]/15">
              <Heart className="w-3.5 h-3.5 text-[#FFBE98] fill-[#FFBE98]" />
              <span className="text-xs font-medium text-[#6B6661]">Ferramentas selecionadas pela 4Luis</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#2D2A26] mb-3" data-testid="plan-trip-title">
              Planeia a tua viagem com IA
            </h1>
            <p className="text-base text-[#6B6661] max-w-lg mx-auto">
              Tudo o que precisas para transformar o teu sonho em viagem
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 pb-20">
        {/* AI Planner Hero — main feature */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl border border-[#F2CBB7] bg-[#FFF1E8] shadow-[0_10px_30px_rgba(0,0,0,0.06)] mb-8"
          data-testid="ai-planner-cta"
        >
          <div className="absolute top-0 right-0 w-48 h-48 bg-[#FFBE98]/8 rounded-full -translate-y-1/2 translate-x-1/3" />
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-[#E6A07C]/6 rounded-full translate-y-1/2 -translate-x-1/4" />
          <div className="relative p-6 sm:p-8">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-white/80 rounded-xl flex items-center justify-center shrink-0 shadow-sm border border-[#FFBE98]/15">
                <Sparkles className="w-5.5 h-5.5 text-[#FFBE98]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[10px] font-semibold text-[#FFBE98] bg-white/70 backdrop-blur-sm px-2.5 py-0.5 rounded-full tracking-wide border border-[#FFBE98]/15">
                    Planeamento inteligente
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-[#2D2A26] mb-1.5" data-testid="ai-planner-cta-title">
                  Planeia a tua viagem com IA
                </h2>
                <p className="text-sm text-[#6B6661] leading-relaxed mb-5">
                  Recebe um roteiro completo, dicas locais e sugestões de reserva — tudo personalizado para o teu destino e datas.
                </p>
                <button
                  onClick={() => navigate(`/travel-planner${destinationParam ? `?destination=${encodeURIComponent(destinationParam)}` : ''}`)}
                  className="inline-flex items-center gap-2 bg-[#FFBE98] text-white font-semibold px-6 py-3 rounded-full hover:bg-[#E6A07C] transition-all shadow-[0_2px_8px_rgba(255,190,152,0.35)] hover:shadow-[0_4px_14px_rgba(255,190,152,0.45)]"
                  data-testid="ai-planner-cta-btn"
                >
                  <Sparkles className="w-4 h-4" />
                  Gerar plano de viagem
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Sections — 2-col grid on desktop, single col on mobile */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sections.map((section, idx) => (
            <motion.div
              key={section.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: (idx + 1) * 0.04 }}
              className="bg-white rounded-2xl border border-stone-200/70 overflow-hidden shadow-[0_2px_8px_rgba(0,0,0,0.05)] transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_12px_35px_rgba(0,0,0,0.10)] hover:border-[#E6D5C8]"
              data-testid={`section-${section.id}`}
            >
            <div className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 ${section.iconBg} rounded-xl flex items-center justify-center shrink-0`}>
                  <section.icon className={`w-5 h-5 ${section.iconColor}`} />
                </div>
                <h2 className="text-base font-bold text-[#2D2A26] leading-snug">{section.title}</h2>
              </div>
              <p className="text-sm text-[#6B6661] leading-relaxed mb-4">{section.description}</p>

              {/* CTAs - compact, left-aligned, pill-style */}
              <div className="flex flex-wrap items-center gap-2.5">
                {section.ctas.map((cta) => (
                  <a
                    key={cta.id}
                    href={cta.isMap ? 'https://maps.google.com' : getLink(cta.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => trackClick(cta.id)}
                    data-testid={`cta-${cta.id}`}
                    className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      cta.primary
                        ? 'bg-[#FFBE98] text-white hover:bg-[#E6A07C] shadow-sm'
                        : 'bg-transparent text-[#6B6661] border border-stone-200 hover:border-[#FFBE98]/40 hover:text-[#2D2A26]'
                    }`}
                  >
                    <cta.icon className="w-3.5 h-3.5" />
                    {cta.label}
                    <ExternalLink className="w-3 h-3 opacity-50" />
                  </a>
                ))}
              </div>

              {/* Micro text + badge */}
              {(section.micro || section.badge) && (
                <div className="flex flex-wrap items-center gap-3 mt-3">
                  {section.micro && (
                    <span className="text-[11px] text-[#6B6661]/60">{section.micro}</span>
                  )}
                  {section.badge && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-[#FFBE98] font-medium">
                      <Star className="w-2.5 h-2.5 fill-[#FFBE98]" />
                      {section.badge}
                    </span>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        ))}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-[#6B6661]/50 pt-8">
          Alguns dos links nesta página são de parceiros. Ao usares estes links,<br/>
          ajudas a 4Luis a continuar a apoiar viagens de sonho.
        </p>
        <p className="text-center text-xs text-[#FFBE98]/60 italic mt-2 pb-4">
          Este pode ser o início da tua próxima grande viagem
        </p>
      </div>
    </div>
  );
};

export default PlanTrip;
