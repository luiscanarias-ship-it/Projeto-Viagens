import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Plane, Hotel, Compass, Car, Wifi, Shield, MapPin, 
  ExternalLink, Star, Heart, Sparkles, ArrowRight
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PlanTrip = () => {
  const [affiliateLinks, setAffiliateLinks] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    document.title = '4Luis — Planeie a Sua Viagem';
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
      title: 'Reservar alojamento com confiança',
      description: 'Selecionámos as melhores plataformas para encontrar o alojamento ideal.',
      ctas: [
        { id: 'booking', label: 'Ver opções recomendadas', primary: true, micro: 'Cancelamento flexível' },
        { id: 'hotels', label: 'Ver ofertas com benefícios', primary: false }
      ],
      badge: 'Recomendado pela 4Luis'
    },
    {
      id: 'flights',
      icon: Plane,
      iconBg: 'bg-sky-50',
      iconColor: 'text-sky-500',
      title: 'Encontrar voos ao melhor preço',
      description: 'Compare centenas de opções e escolha o melhor voo para a sua viagem.',
      ctas: [
        { id: 'skyscanner', label: 'Pesquisar voos', primary: true, micro: 'Sem custos adicionais para si' }
      ],
      badge: 'Recomendado pela 4Luis'
    },
    {
      id: 'activities',
      icon: Compass,
      iconBg: 'bg-emerald-50',
      iconColor: 'text-emerald-500',
      title: 'Descobrir experiências únicas',
      description: 'Reserve atividades, tours e experiências no seu destino.',
      ctas: [
        { id: 'getyourguide', label: 'Descobrir atividades', primary: true, micro: 'Cancelamento flexível' }
      ],
      badge: 'Melhores opções disponíveis'
    },
    {
      id: 'transport',
      icon: Car,
      iconBg: 'bg-violet-50',
      iconColor: 'text-violet-500',
      title: 'Aluguer de carro ao melhor preço',
      description: 'Compare opções e encontre o carro ideal para a sua viagem.',
      ctas: [
        { id: 'cars', label: 'Pesquisar carros', primary: true, micro: 'Sem custos adicionais para si' }
      ]
    },
    {
      id: 'esim',
      icon: Wifi,
      iconBg: 'bg-teal-50',
      iconColor: 'text-teal-500',
      title: 'Internet em viagem sem complicações',
      description: 'Evite roaming caro e fique sempre ligado.',
      ctas: [
        { id: 'airalo', label: 'Ver opções económicas', primary: true },
        { id: 'holafly', label: 'Ver dados ilimitados', primary: false }
      ]
    },
    {
      id: 'insurance',
      icon: Shield,
      iconBg: 'bg-amber-50',
      iconColor: 'text-amber-500',
      title: 'Viajar com segurança',
      description: 'Proteja a sua viagem com seguro adequado.',
      ctas: [
        { id: 'insurance', label: 'Ver planos de seguro', primary: true, micro: 'Recomendado pela 4Luis' }
      ]
    },
    {
      id: 'map',
      icon: MapPin,
      iconBg: 'bg-red-50',
      iconColor: 'text-red-500',
      title: 'Explorar o destino',
      description: 'Descubra pontos de interesse e planeie as suas rotas.',
      ctas: [
        { id: 'googlemaps', label: 'Abrir Google Maps', primary: true, isMap: true }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-[#FAFAF9]">
      {/* Hero */}
      <div className="bg-gradient-to-b from-[#FFBE98]/15 to-[#FAFAF9] pt-28 pb-12 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center gap-2 bg-white/80 rounded-full px-4 py-1.5 mb-5 border border-[#FFBE98]/20">
              <Heart className="w-3.5 h-3.5 text-[#FFBE98] fill-[#FFBE98]" />
              <span className="text-xs font-medium text-[#6B6661]">Ferramentas selecionadas pela 4Luis</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#2D2A26] mb-3" data-testid="plan-trip-title">
              Planeie a Sua Viagem
            </h1>
            <p className="text-base text-[#6B6661] max-w-lg mx-auto">
              Tudo o que precisa para planear a sua viagem num só lugar.
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 pb-20 space-y-4">
        {/* AI Planner Integration */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl border border-[#FFBE98]/30 bg-gradient-to-br from-[#FFBE98]/10 via-white to-[#E6A07C]/8 shadow-sm"
          data-testid="ai-planner-cta"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#FFBE98]/5 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="relative p-5 sm:p-6">
            <div className="flex items-start gap-4">
              <div className="w-11 h-11 bg-[#FFBE98]/15 rounded-xl flex items-center justify-center shrink-0">
                <Sparkles className="w-5 h-5 text-[#FFBE98]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-bold text-[#FFBE98] bg-[#FFBE98]/10 px-2 py-0.5 rounded-full uppercase tracking-wide">Novo</span>
                </div>
                <h2 className="text-lg font-bold text-[#2D2A26] mb-1" data-testid="ai-planner-cta-title">
                  Planeie a sua viagem automaticamente com IA
                </h2>
                <p className="text-sm text-[#6B6661] leading-relaxed mb-4">
                  Receba um roteiro completo, dicas locais e sugestões de reserva — tudo personalizado para o seu destino e datas.
                </p>
                <button
                  onClick={() => navigate('/travel-planner')}
                  className="w-full flex items-center justify-center gap-2 bg-[#2D2A26] text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-[#1a1816] transition-colors"
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

        {/* Sections */}
        {sections.map((section, idx) => (
          <motion.div
            key={section.id}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: (idx + 1) * 0.05 }}
            className="bg-white rounded-2xl border border-stone-100 overflow-hidden shadow-sm"
            data-testid={`section-${section.id}`}
          >
            <div className="p-5">
              <div className="flex items-start gap-4">
                <div className={`w-11 h-11 ${section.iconBg} rounded-xl flex items-center justify-center shrink-0`}>
                  <section.icon className={`w-5.5 h-5.5 ${section.iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <h2 className="text-lg font-bold text-[#2D2A26]">{section.title}</h2>
                  <p className="text-sm text-[#6B6661] mt-0.5 leading-relaxed">{section.description}</p>
                </div>
              </div>

              <div className={`mt-4 ${section.ctas.length > 1 ? 'grid grid-cols-2 gap-2' : ''}`}>
                {section.ctas.map((cta) => (
                  <div key={cta.id} className="flex flex-col">
                    <a
                      href={cta.isMap ? 'https://maps.google.com' : getLink(cta.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => trackClick(cta.id)}
                      data-testid={`cta-${cta.id}`}
                      className={`flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-sm font-semibold transition-all ${
                        cta.primary
                          ? 'bg-[#2D2A26] text-white hover:bg-[#1a1816]'
                          : 'bg-stone-100 text-[#2D2A26] hover:bg-stone-200'
                      }`}
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      {cta.label}
                    </a>
                    {cta.micro && (
                      <span className="text-[10px] text-[#6B6661]/70 text-center mt-1">{cta.micro}</span>
                    )}
                  </div>
                ))}
              </div>

              {section.badge && (
                <div className="mt-2.5 flex items-center gap-1.5">
                  <Star className="w-3 h-3 text-[#FFBE98] fill-[#FFBE98]" />
                  <span className="text-[11px] text-[#FFBE98] font-medium">
                    {section.badge}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {/* Footer note */}
        <p className="text-center text-xs text-[#6B6661]/60 pt-4">
          Alguns dos links nesta página são de parceiros. Ao usar estes links,<br/>
          ajuda a 4Luis a continuar a apoiar viagens de sonho.
        </p>
      </div>
    </div>
  );
};

export default PlanTrip;
