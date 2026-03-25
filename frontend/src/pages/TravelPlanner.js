import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MapPin, Calendar, Compass, Sparkles, Loader2,
  Sun, Shirt, ClipboardList, Lightbulb, Hotel, Plane, Wifi,
  ExternalLink, Globe, Ticket, Send, SlidersHorizontal, 
  CheckCircle2, Copy, Share2, Check, Eye, EyeOff, Car, Clock, Star, Shield, Lock, Map
} from 'lucide-react';
import axios from 'axios';
import { AmbassadorProgress, PremiumGate, InlineReferralCTA } from '../components/AmbassadorProgress';
import AIAssistant from '../components/AIAssistant';
const SmartMap = React.lazy(() => import('../components/SmartMap'));

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
  { keywords: ['museu', 'museum', 'galeria', 'exposição', 'exposicao', 'palácio', 'palacio', 'castelo', 'torre', 'catedral', 'basílica', 'basilica', 'mosteiro', 'igreja', 'templo', 'santuário', 'shrine', 'temple'],
    label: 'Reservar entrada (evita filas)', platform: 'getyourguide', icon: Ticket },
  { keywords: ['restaurante', 'gastronomia', 'food tour', 'mercado', 'market', 'degustação', 'sabores', 'culinária'],
    label: 'Reservar experiência', platform: 'getyourguide', icon: Ticket },
  { keywords: ['tour', 'visita guiada', 'excursão', 'excursao', 'passeio de barco', 'cruzeiro', 'safari', 'mergulho', 'walking tour', 'day trip'],
    label: 'Garantir vaga (muito procurado)', platform: 'getyourguide', icon: Ticket },
  { keywords: ['bilhete', 'ingresso', 'entrada', 'ticket', 'espetáculo', 'show', 'concerto', 'ópera', 'teatro'],
    label: 'Garantir bilhete antes de esgotar', platform: 'getyourguide', icon: Ticket },
  { keywords: ['atividade', 'experiência', 'adventure', 'snorkel', 'surf', 'kayak', 'hiking', 'trekking', 'zip', 'bungee'],
    label: 'Reservar atividade', platform: 'getyourguide', icon: Compass },
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

const TIP_BOOKING_KEYWORDS = ['reserv', 'bilhete', 'ingresso', 'anteced', 'antecipadamente', 'comprar', 'book', 'teamlab', 'teamLab', 'popular', 'procurad', 'esgota', 'fila'];
const tipHasBookingHint = (tip) => TIP_BOOKING_KEYWORDS.some(k => tip.toLowerCase().includes(k));

/* ── CTA type → platform + icon mapping ── */
const CTA_MAP = {
  activity: { platform: 'getyourguide', icon: Ticket },
  hotel: { platform: 'booking', icon: Hotel },
  flight: { platform: 'skyscanner', icon: Plane },
  esim: { platform: 'airalo', icon: Wifi },
  transport: { platform: 'cars', icon: Car },
  insurance: { platform: 'insurance', icon: Shield },
};

/* ── Parse text with [CTA:type:label] markers ── */
const parseCTAText = (text) => {
  const regex = /\[CTA:(\w+):([^\]]+)\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push({ type: 'text', value: text.slice(lastIndex, match.index).trim() });
    parts.push({ type: 'cta', ctaType: match[1], label: match[2] });
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) parts.push({ type: 'text', value: text.slice(lastIndex).trim() });
  return parts;
};

/* ── Render text with inline CTAs ── */
const TextWithCTA = ({ text, links, onTrack, variant = 'inline', destination }) => {
  const parts = parseCTAText(text);
  if (parts.length === 1 && parts[0].type === 'text') return <span>{text}</span>;
  return (
    <span>
      {parts.map((p, i) => {
        if (p.type === 'text') return <span key={i}>{p.value} </span>;
        const mapping = CTA_MAP[p.ctaType];
        if (!mapping) return <span key={i}>{p.label}</span>;
        const Icon = mapping.icon;
        // Smart GYG link for activity CTAs
        const href = (mapping.platform === 'getyourguide' && destination)
          ? buildGYGLink(destination, p.label)
          : (links[mapping.platform]?.url || '#');
        if (variant === 'card') return (
          <span key={i} className="block mt-2">
            <a href={href} target="_blank" rel="noopener noreferrer"
              onClick={() => onTrack(mapping.platform)}
              className="flex items-center gap-2.5 bg-[#FFBE98]/8 rounded-xl border border-[#FFBE98]/15 p-3 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 group">
              <span className="w-8 h-8 bg-white rounded-xl flex items-center justify-center shadow-sm shrink-0 group-hover:shadow-md transition-shadow">
                <Icon className="w-4 h-4 text-[#FFBE98]" />
              </span>
              <span className="flex-1 text-[12px] font-bold text-[#2D2A26]">{p.label}</span>
              <span className="text-[11px] font-bold text-[#FFBE98] group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
                Ver <ExternalLink className="w-3 h-3" />
              </span>
            </a>
          </span>
        );
        return (
          <a key={i} href={href} target="_blank" rel="noopener noreferrer"
            onClick={() => onTrack(mapping.platform)}
            className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[#FFBE98] bg-[#FFBE98]/8 hover:bg-[#FFBE98]/15 border border-[#FFBE98]/15 hover:border-[#FFBE98]/30 px-3 py-1.5 rounded-xl transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ml-1 group">
            <Icon className="w-3.5 h-3.5" />
            <span>{p.label}</span>
            <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-90 transition-opacity" />
          </a>
        );
      })}
    </span>
  );
};
const InlineActivityCTA = ({ match, link, onTrack, activityText, destination }) => {
  // Smart GYG link: activity-specific when possible
  const smartLink = (match.platform === 'getyourguide' && activityText && destination)
    ? buildGYGLink(destination, extractActivityName(activityText))
    : link;
  return (
    <a href={smartLink || link || '#'} target="_blank" rel="noopener noreferrer"
      onClick={() => onTrack(match.platform)}
      className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-[#FFBE98] bg-[#FFBE98]/8 hover:bg-[#FFBE98]/15 border border-[#FFBE98]/15 hover:border-[#FFBE98]/30 px-3 py-1.5 rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ml-1 group"
      data-testid={`inline-cta-${match.platform}`}>
      <match.icon className="w-3.5 h-3.5" />
      <span>{match.label}</span>
      <ExternalLink className="w-3 h-3 opacity-60 group-hover:opacity-90 transition-opacity" />
    </a>
  );
};

/* ── Top Booking Bar (compact, after summary) ── */
const TopBookingBar = ({ links, onTrack, destination }) => (
  <div className="pt-3 space-y-1.5" data-testid="top-booking-bar">
    <div className="flex items-center gap-2 flex-wrap">
      {[
        { id: 'booking', icon: Hotel, label: destination ? `\ud83c\udfe8 Hotéis bem localizados em ${destination}` : '\ud83c\udfe8 Alojamento', trust: true },
        { id: 'skyscanner', icon: Plane, label: '\u2708\ufe0f Voos para estas datas (melhor preço)', trust: false },
        { id: 'getyourguide', icon: Ticket, label: destination ? `\ud83c\udf9f\ufe0f Experiências em ${destination} (evita filas)` : '\ud83c\udf9f\ufe0f Atividades', trust: true },
      ].map(item => (
        <a key={item.id} href={links[item.id]?.url || '#'} target="_blank" rel="noopener noreferrer"
          onClick={() => onTrack(item.id)} data-testid={`top-booking-${item.id}`}
          className="flex items-center gap-1.5 text-[11px] font-semibold text-[#2D2A26] bg-stone-50 hover:text-[#FFBE98] px-3 py-2 rounded-xl transition-all duration-200 border border-stone-200/60 hover:border-[#FFBE98]/30 hover:shadow-md hover:-translate-y-0.5 group">
          <item.icon className="w-4 h-4 text-[#FFBE98]" />
          {item.label}
          {item.trust && <span className="text-[8px] font-bold text-[#FFBE98]/80 bg-[#FFBE98]/10 px-1.5 py-0.5 rounded-full">4Luis</span>}
          <ExternalLink className="w-2.5 h-2.5 opacity-0 group-hover:opacity-70 transition-opacity" />
        </a>
      ))}
    </div>
  </div>
);

/* ── Contextual CTA Copy Generator ── */
const getCTACopy = (destination, tripTypes = []) => {
  const dest = destination || 'o destino';
  const primary = tripTypes[0] || '';

  const typeSpecific = {
    cultural: {
      hotel: { text: `\ud83c\udfe8 Hotéis no centro histórico de ${dest}`, sublabel: 'Melhor localização \u00b7 Cancelamento gratuito', label: `Ver hotéis no centro de ${dest}` },
      activitiesMid: { text: `\ud83c\udfcc Experiências imperdíveis em ${dest}`, sublabel: 'Evita filas \u00b7 Bilhetes sem espera', label: 'Reservar experiências (evita filas)' },
      flights: { text: `\u2708\ufe0f Encontrar voos para estas datas (melhor preço)`, sublabel: 'Preços sobem rapidamente \u00b7 Compare agora', label: 'Comparar voos' },
      insurance: { text: `\ud83d\udee1\ufe0f Os imprevistos acontecem \u2014 faz o teu seguro`, sublabel: 'Cancelamento + assistência médica', label: 'Fazer seguro' },
      activitiesDicas: { text: `\ud83c\udfcc Descubra ${dest} com guias culturais locais`, sublabel: 'Muito procurado \u00b7 Reservar com antecedência', label: 'Reservar com antecedência' },
    },
    gastronomica: {
      hotel: { text: `\ud83c\udfe8 Hotéis perto dos melhores restaurantes de ${dest}`, sublabel: 'Melhor localização \u00b7 Cancelamento gratuito', label: `Ver hotéis em ${dest}` },
      activitiesMid: { text: `\ud83c\udf7d\ufe0f Experiências gastronómicas em ${dest}`, sublabel: 'Muito procurado \u00b7 Sabores autênticos', label: 'Reservar experiências' },
      flights: { text: `\u2708\ufe0f Voos para estas datas (melhor preço)`, sublabel: 'Preços sobem rapidamente \u00b7 Compare agora', label: 'Comparar voos' },
      insurance: { text: `\ud83d\udee1\ufe0f Os imprevistos acontecem \u2014 faz o teu seguro`, sublabel: 'Cancelamento + assistência médica', label: 'Fazer seguro' },
      activitiesDicas: { text: `\ud83c\udf7d\ufe0f Tours gastronómicos e sabores de ${dest}`, sublabel: 'Muito procurado \u00b7 Reservar com antecedência', label: 'Reservar com antecedência' },
    },
    romantica: {
      hotel: { text: `\ud83c\udfe8 Hotéis românticos recomendados em ${dest}`, sublabel: 'Melhor localização \u00b7 Cancelamento gratuito', label: `Ver hotéis em ${dest}` },
      activitiesMid: { text: `\u2764\ufe0f Experiências românticas deste roteiro`, sublabel: 'Muito procurado \u00b7 Momentos únicos a dois', label: 'Reservar experiências' },
      flights: { text: `\u2708\ufe0f Voos para a vossa escapadela (melhor preço)`, sublabel: 'Preços sobem rapidamente \u00b7 Compare agora', label: 'Comparar voos' },
      insurance: { text: `\ud83d\udee1\ufe0f Os imprevistos acontecem \u2014 faz o teu seguro`, sublabel: 'Cancelamento + assistência médica', label: 'Fazer seguro' },
      activitiesDicas: { text: `\u2764\ufe0f Experiências a dois em ${dest}`, sublabel: 'Muito procurado \u00b7 Reservar com antecedência', label: 'Reservar com antecedência' },
    },
    aventura: {
      hotel: { text: `\ud83c\udfe8 Alojamento para aventureiros em ${dest}`, sublabel: 'Melhor localização \u00b7 Cancelamento gratuito', label: `Ver hotéis em ${dest}` },
      activitiesMid: { text: `\ud83c\udfd4\ufe0f Atividades ao ar livre deste roteiro`, sublabel: 'Vagas limitadas \u00b7 Reservar com antecedência', label: 'Reservar atividades' },
      flights: { text: `\u2708\ufe0f Voos para a aventura (melhor preço)`, sublabel: 'Preços sobem rapidamente \u00b7 Compare agora', label: 'Comparar voos' },
      insurance: { text: `\ud83d\udee1\ufe0f Seguro essencial para aventura \u2014 não arrisques`, sublabel: 'Cobertura para atividades radicais', label: 'Fazer seguro' },
      activitiesDicas: { text: `\ud83c\udfd4\ufe0f Aventuras imperdíveis em ${dest}`, sublabel: 'Vagas limitadas \u00b7 Reservar com antecedência', label: 'Reservar com antecedência' },
    },
    familia: {
      hotel: { text: `\ud83c\udfe8 Hotéis family-friendly em ${dest}`, sublabel: 'Melhor localização \u00b7 Cancelamento gratuito', label: `Ver hotéis em ${dest}` },
      activitiesMid: { text: `\ud83c\udfa0 Atividades para toda a família`, sublabel: 'Evita filas \u00b7 Bilhetes sem espera', label: 'Reservar experiências (evita filas)' },
      flights: { text: `\u2708\ufe0f Voos para a família (melhor preço)`, sublabel: 'Preços sobem rapidamente \u00b7 Compare agora', label: 'Comparar voos' },
      insurance: { text: `\ud83d\udee1\ufe0f Os imprevistos acontecem \u2014 protege a família`, sublabel: 'Cobertura para toda a família', label: 'Fazer seguro' },
      activitiesDicas: { text: `\ud83c\udfa0 Atividades para crianças em ${dest}`, sublabel: 'Muito procurado \u00b7 Reservar com antecedência', label: 'Reservar com antecedência' },
    },
  };

  const defaults = {
    hotel: { text: `\ud83c\udfe8 Hotéis bem localizados em ${dest}`, sublabel: 'Melhor localização \u00b7 Cancelamento gratuito', label: `Ver hotéis no centro de ${dest}` },
    activitiesMid: { text: `\ud83c\udfab Experiências imperdíveis em ${dest}`, sublabel: 'Evita filas \u00b7 Bilhetes sem espera', label: 'Reservar experiências (evita filas)' },
    flights: { text: `\u2708\ufe0f Encontrar voos para estas datas (melhor preço)`, sublabel: 'Preços sobem rapidamente \u00b7 Compare agora', label: 'Comparar voos' },
    insurance: { text: `\ud83d\udee1\ufe0f Os imprevistos acontecem \u2014 faz o teu seguro`, sublabel: 'Cancelamento + assistência médica', label: 'Fazer seguro' },
    activitiesDicas: { text: `\ud83c\udfab Experiências e atividades em ${dest}`, sublabel: 'Muito procurado \u00b7 Reservar com antecedência', label: 'Reservar com antecedência' },
  };

  const specific = typeSpecific[primary] || {};
  return {
    hotel: specific.hotel || defaults.hotel,
    activitiesMid: specific.activitiesMid || defaults.activitiesMid,
    flights: specific.flights || defaults.flights,
    insurance: specific.insurance || defaults.insurance,
    activitiesDicas: specific.activitiesDicas || defaults.activitiesDicas,
  };
};

/* ── Contextual CTA (micro-card between sections) ── */
const ContextualCTA = ({ icon: Icon, text, label, sublabel, link, platform, onTrack, trust }) => (
  <div className={`rounded-xl p-4 my-3 transition-all duration-200 group border ${
    trust
      ? 'bg-gradient-to-r from-[#FFBE98]/8 to-transparent border-[#FFBE98]/15 hover:shadow-lg hover:border-[#FFBE98]/25'
      : 'bg-white border-stone-200/60 hover:shadow-md hover:border-stone-300'
  }`}
    data-testid={`cta-card-${platform}`}>
    <div className="flex items-center gap-3">
      <div className={`flex items-center justify-center shrink-0 rounded-xl bg-white shadow-sm group-hover:shadow-md transition-shadow ${
        trust ? 'w-11 h-11' : 'w-10 h-10'
      }`}>
        <Icon className={`${trust ? 'w-[22px] h-[22px]' : 'w-5 h-5'} text-[#FFBE98]`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={`font-bold text-[#2D2A26] ${trust ? 'text-sm' : 'text-[13px]'}`}>{text}</p>
        <p className="text-[11px] text-[#6B6661] mt-0.5">{sublabel}</p>
      </div>
      <a href={link || '#'} target="_blank" rel="noopener noreferrer" onClick={() => onTrack(platform)}
        data-testid={`cta-contextual-${platform}`}
        className={`shrink-0 flex items-center gap-1.5 rounded-xl hover:-translate-y-0.5 transition-all duration-200 ${
          trust
            ? 'bg-[#2D2A26] text-white text-xs font-bold px-5 py-2.5 shadow-sm hover:shadow-lg hover:bg-[#1a1816]'
            : 'bg-stone-50 text-[#2D2A26] text-[11px] font-semibold px-4 py-2 border border-stone-200 hover:border-stone-300 hover:shadow-md'
        }`}>
        {label}<ExternalLink className={`${trust ? 'w-3.5 h-3.5' : 'w-3 h-3'}`} />
      </a>
    </div>
    {trust && (
      <div className="flex items-center gap-1.5 mt-2.5 ml-[56px]">
        <Star className="w-3.5 h-3.5 text-[#FFBE98] fill-[#FFBE98]" />
        <span className="text-[11px] font-semibold text-[#FFBE98]">Recomendado pela 4Luis</span>
      </div>
    )}
  </div>
);

/* ── eSIM Micro-Card (inside tech checklist) ── */
const EsimMicroCard = ({ link, onTrack, destination }) => (
  <a href={link || '#'} target="_blank" rel="noopener noreferrer"
    onClick={() => onTrack('airalo')} data-testid="checklist-esim-cta"
    className="block mt-2.5 bg-[#FFBE98]/8 rounded-xl border border-[#FFBE98]/15 p-3 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 group">
    <div className="flex items-center gap-2.5">
      <div className="w-8 h-8 bg-white rounded-xl flex items-center justify-center shadow-sm shrink-0 group-hover:shadow-md transition-shadow">
        <Wifi className="w-4 h-4 text-[#FFBE98]" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[12px] font-bold text-[#2D2A26]">{destination ? `Comprar eSIM para ${destination}` : 'Comprar eSIM internacional'}</p>
        <p className="text-[10px] text-[#6B6661]">Ativa antes de viajar · Sem roaming</p>
      </div>
      <span className="text-[11px] font-bold text-[#FFBE98] group-hover:translate-x-0.5 transition-transform flex items-center gap-0.5">
        Comprar <ExternalLink className="w-3 h-3" />
      </span>
    </div>
  </a>
);

/* ── Tip Booking CTA (inline action at end of sentence) ── */
const TipBookingLink = ({ link, onTrack, tipText, destination }) => {
  const smartLink = (tipText && destination) ? buildGYGLink(destination, extractActivityName(tipText)) : link;
  return (
    <a href={smartLink || link || '#'} target="_blank" rel="noopener noreferrer"
      onClick={() => onTrack('getyourguide')}
      className="inline-flex items-center gap-1.5 text-[12px] font-bold text-[#FFBE98] hover:text-[#E6A07C] bg-[#FFBE98]/8 hover:bg-[#FFBE98]/15 border border-[#FFBE98]/15 hover:border-[#FFBE98]/30 px-3 py-1 rounded-xl shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 ml-1">
      Reservar com antecedência <ExternalLink className="w-3 h-3 opacity-70" />
    </a>
  );
};

/* ── Smart GetYourGuide Link Builder ── */
/* Generates destination-based or activity-specific GYG search links.
   Future-ready: add curated experience mappings to GYG_CURATED_EXPERIENCES. */
const GYG_PARTNER_ID = 'WFPE9ME';
const GYG_BASE = 'https://www.getyourguide.com/s/';

// Future: map specific activities to exact GYG product URLs
// e.g. { 'teamlab tokyo': 'https://www.getyourguide.com/tokyo-l193/teamlab-planets-t12345/' }
const GYG_CURATED_EXPERIENCES = {};

const buildGYGLink = (destination, activityName = null) => {
  const raw = activityName
    ? `${activityName} ${destination}`
    : destination;
  const clean = raw
    .toLowerCase()
    .replace(/[^a-záàâãéèêíïóôõúüçñ\w\s]/gi, '')
    .replace(/\s+/g, ' ')
    .trim();

  // Check curated mapping first (exact match)
  const curatedUrl = GYG_CURATED_EXPERIENCES[clean];
  if (curatedUrl) return `${curatedUrl}${curatedUrl.includes('?') ? '&' : '?'}partner_id=${GYG_PARTNER_ID}`;

  return `${GYG_BASE}?q=${encodeURIComponent(clean)}&partner_id=${GYG_PARTNER_ID}`;
};

/* Strips common Portuguese verbs/prepositions to extract meaningful activity name */
const extractActivityName = (text) => {
  const stopWords = /^(visitar|ir a[os]?|conhecer|explorar|passear|passar|ver|admirar|descobrir|experimentar|provar|comprar|fazer|o|a|os|as|no|na|nos|nas|do|da|dos|das|de|pelo|pela|pelos|pelas|em|com|um|uma|e|ou)\s+/gi;
  let name = text.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim();
  // Iteratively strip leading stop words
  let prev = '';
  while (prev !== name) {
    prev = name;
    name = name.replace(stopWords, '').trim();
  }
  return name || text.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim();
};

/* ── Build dynamic affiliate links with destination/dates ── */
/* Appends ?destination=...&checkin=...&checkout=... to each base URL.
   When real affiliate URLs replace the placeholders, this logic stays the same. */
const buildDynamicLinks = (baseLinks, destination, startDate, endDate) => {
  const enc = encodeURIComponent;
  const links = {};
  Object.entries(baseLinks).forEach(([key, val]) => {
    if (key === 'getyourguide') {
      // Smart GYG link: destination-based fallback with partner_id
      links[key] = { ...val, url: buildGYGLink(destination) };
    } else {
      const base = val.url || '';
      const sep = base.includes('?') ? '&' : '?';
      links[key] = { ...val, url: `${base}${sep}destination=${enc(destination)}&checkin=${startDate}&checkout=${endDate}` };
    }
  });
  return links;
};
/* ── Sticky Booking Bar ── */
const StickyBar = ({ links, onTrack, visible, destination }) => {
  const dest = destination || '';
  const items = [
    { id: 'booking', icon: Hotel, label: dest ? `Hotéis em ${dest}` : 'Hotéis' },
    { id: 'skyscanner', icon: Plane, label: 'Voos (melhor preço)' },
    { id: 'getyourguide', icon: Ticket, label: dest ? `Atividades em ${dest}` : 'Atividades' },
  ];
  return (
    <AnimatePresence>
      {visible && (
        <motion.div initial={{ y: 80, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 80, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-stone-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
          data-testid="sticky-booking-bar">
          <div className="max-w-2xl mx-auto px-3 sm:px-4 py-2.5">
            <p className="text-[10px] font-medium text-[#6B6661] text-center mb-1.5 flex items-center justify-center gap-1">
              <Sparkles className="w-3 h-3 text-[#FFBE98]" />Planeie e reserve a sua viagem
            </p>
            <div className="flex items-center gap-1.5 sm:gap-2">
              {items.map(item => (
                <a key={item.id} href={links[item.id]?.url || '#'} target="_blank" rel="noopener noreferrer"
                  onClick={() => onTrack(item.id)} data-testid={`sticky-cta-${item.id}`}
                  className="flex-1 flex items-center justify-center gap-1 sm:gap-1.5 bg-[#2D2A26] text-white text-[10px] sm:text-xs font-bold py-2.5 px-2 sm:px-3 rounded-xl shadow-sm hover:shadow-lg hover:-translate-y-0.5 hover:bg-[#1a1816] transition-all duration-200">
                  <item.icon className="w-3.5 sm:w-4 h-3.5 sm:h-4" /><span className="truncate">{item.label}</span>
                </a>
              ))}
            </div>
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
        className="flex items-center justify-center gap-2 bg-[#FFBE98] text-white text-sm font-semibold px-5 py-2.5 rounded-xl shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:bg-[#E6A07C] transition-all duration-200 w-full">
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
            className="flex-1 px-3 py-2 text-sm rounded-xl border border-stone-200 focus:border-[#FFBE98] focus:ring-1 focus:ring-[#FFBE98]/30 outline-none transition-all"
            disabled={loading} data-testid="refine-input" />
          <button onClick={handleSubmit} disabled={!text.trim() || loading} data-testid="refine-submit"
            className="flex items-center gap-1.5 bg-[#FFBE98] text-white text-xs font-semibold px-4 py-2.5 rounded-xl hover:bg-[#E6A07C] transition-all duration-200 disabled:opacity-50 whitespace-nowrap shadow-sm">
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
  const [ambassadorData, setAmbassadorData] = useState(null);
  const resultsRef = useRef(null);
  const startDateRef = useRef(null);
  const tabRefs = { guia: useRef(null), roteiro: useRef(null), checklist: useRef(null), dicas: useRef(null) };

  useEffect(() => {
    document.title = '4Luis — Planeia a tua viagem com IA';
    axios.get(`${API}/affiliate-links`).then(r => setAffiliateLinks(r.data)).catch(() => {});
    // Fetch ambassador status
    const token = localStorage.getItem('token');
    if (token) {
      fetch(`${API}/ambassador/features`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) setAmbassadorData(d); })
        .catch(() => {});
    }
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

  // Resolved links: dynamic when available, fallback to static affiliate links
  const links = Object.keys(dynamicLinks).length ? dynamicLinks : affiliateLinks;

  // Contextual CTA copy based on destination and trip type
  const ctaCopy = plan ? getCTACopy(plan.destination || destination, tripTypes) : getCTACopy(destination, tripTypes);

  const token = localStorage.getItem('token');
  const isAmbassador = ambassadorData?.is_ambassador || false;

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
    const strip = (t) => t.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim();
    const l = [`GUIA DE VIAGEM: ${plan.destination}`, `Datas: ${plan.dates}`];
    if (plan.summary) l.push(`\n${strip(plan.summary)}`);
    if (plan.weather) l.push(`\nClima: ${strip(plan.weather)}`);
    if (plan.packing) {
      l.push('\nO que levar:');
      if (plan.packing.clothing?.length) { l.push('  Roupa:'); plan.packing.clothing.forEach(i => l.push(`    - ${strip(i)}`)); }
      if (plan.packing.essentials?.length) { l.push('  Essenciais:'); plan.packing.essentials.forEach(i => l.push(`    - ${strip(i)}`)); }
    }
    l.push('\n--- ROTEIRO ---');
    plan.itinerary?.forEach(d => { l.push(`\nDia ${d.day}: ${d.title}`); d.activities?.forEach(a => l.push(`  - ${strip(a)}`)); });
    if (plan.checklist) {
      l.push('\n--- CHECKLIST ---');
      Object.entries(plan.checklist).forEach(([key, items]) => {
        const label = key === 'documents' ? 'Documentos' : key === 'hygiene' ? 'Higiene' : 'Tecnologia';
        l.push(`  ${label}:`);
        items?.forEach(i => l.push(`    - ${strip(i)}`));
      });
    }
    if (plan.local_tips?.length) { l.push('\n--- DICAS LOCAIS ---'); plan.local_tips.forEach(t => l.push(`  - ${strip(t)}`)); }
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
      <div className="bg-gradient-to-b from-[#FFBE98]/15 to-[#FAFAF9] pt-24 pb-4 px-4 sm:px-6">
        <div className="max-w-2xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="inline-flex items-center gap-2 bg-white/80 rounded-full px-4 py-1.5 mb-3 border border-[#FFBE98]/20">
              <Sparkles className="w-3.5 h-3.5 text-[#FFBE98]" />
              <span className="text-xs font-medium text-[#6B6661]">Powered by AI</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#2D2A26]" data-testid="planner-title">Planeia a tua viagem com IA</h1>
          </motion.div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 pb-24">
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
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
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
                className="bg-[#FFBE98]/6 border border-[#FFBE98]/15 rounded-xl p-4 flex items-center gap-3 mb-3 shadow-sm">
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
                <TopBookingBar links={links} onTrack={trackClick} destination={plan.destination} />

                {/* Referral CTA at peak motivation (after seeing the guide) */}
                {token && !isAmbassador && <InlineReferralCTA token={token} />}
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

                {/* Fixed CTA: Alojamento (always visible) */}
                <ContextualCTA icon={Hotel} text={ctaCopy.hotel.text} label={ctaCopy.hotel.label}
                  sublabel={ctaCopy.hotel.sublabel}
                  link={links.booking?.url} platform="booking" onTrack={trackClick} trust={true} />
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
                      <React.Fragment key={i}>
                        <div className="border-l-2 border-[#FFBE98]/30 pl-3">
                          <p className="text-xs font-bold text-[#FFBE98]">Dia {day.day}</p>
                          <p className="text-sm font-semibold text-[#2D2A26]">{day.title}</p>
                          <ul className="mt-1 space-y-0.5">
                            {day.activities?.map((a, j) => {
                              const hasCTAMarker = /\[CTA:\w+:[^\]]+\]/.test(a);
                              const keywordMatch = !hasCTAMarker ? detectActivityCTA(a) : null;
                              const cleanText = a.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim();
                              return (
                                <li key={j} className="text-xs text-[#6B6661] flex items-start gap-1.5 flex-wrap">
                                  <span className="text-[#FFBE98] mt-0.5 shrink-0">&#8226;</span>
                                  <span className="flex-1">
                                    {hasCTAMarker ? (
                                      <TextWithCTA text={a} links={links} onTrack={trackClick} variant="inline" destination={plan.destination} />
                                    ) : (
                                      <>{cleanText}</>
                                    )}
                                  </span>
                                  {keywordMatch && (
                                    <InlineActivityCTA match={keywordMatch}
                                      link={links[keywordMatch.platform]?.url}
                                      onTrack={trackClick}
                                      activityText={cleanText}
                                      destination={plan.destination} />
                                  )}
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                        {/* Mid-itinerary CTA: after ~half of days */}
                        {i === Math.floor((plan.itinerary.length - 1) / 2) && (
                          <ContextualCTA icon={Ticket} text={ctaCopy.activitiesMid.text} label={ctaCopy.activitiesMid.label}
                            sublabel={ctaCopy.activitiesMid.sublabel}
                            link={links.getyourguide?.url} platform="getyourguide" onTrack={trackClick} trust={true} />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </HideableSection>

                <ContextualCTA icon={Plane} text={ctaCopy.flights.text} label={ctaCopy.flights.label}
                  sublabel={ctaCopy.flights.sublabel}
                  link={links.skyscanner?.url} platform="skyscanner" onTrack={trackClick} trust={false} />
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
                        <div key={key} className="bg-stone-50/50 rounded-xl p-2.5">
                          <p className="text-[10px] font-bold text-[#2D2A26] uppercase tracking-wide mb-1.5">
                            {key === 'documents' ? 'Documentos' : key === 'hygiene' ? 'Higiene' : 'Tecnologia'}
                          </p>
                          {items?.map((item, i) => (
                            <p key={i} className="text-xs text-[#6B6661] flex items-center gap-1.5 py-0.5">
                              <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                              <TextWithCTA text={item} links={links} onTrack={trackClick} variant="inline" destination={plan.destination} />
                            </p>
                          ))}
                          {key === 'tech' && (
                            <EsimMicroCard link={links.airalo?.url} onTrack={trackClick} destination={plan.destination} />
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </HideableSection>

                {/* Fixed CTA: Seguro de viagem (always visible) */}
                <ContextualCTA icon={Shield} text={ctaCopy.insurance.text} label={ctaCopy.insurance.label}
                  sublabel={ctaCopy.insurance.sublabel}
                  link={links.insurance?.url} platform="insurance" onTrack={trackClick} trust={true} />
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
                      {plan.local_tips.slice(0, isAmbassador ? undefined : 3).map((tip, i) => (
                        <li key={i} className="text-sm text-[#6B6661] flex items-start gap-2">
                          <Lightbulb className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                          <span className="flex-1">
                            <TextWithCTA text={tip} links={links} onTrack={trackClick} variant="inline" destination={plan.destination} />
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {/* Secret tips — gated for non-ambassadors */}
                  {plan.local_tips && plan.local_tips.length > 3 && !isAmbassador && (
                    <PremiumGate isAmbassador={isAmbassador} label="Dicas secretas para Embaixadores" compact>
                      <ul className="space-y-2 mt-2">
                        {plan.local_tips.slice(3).map((tip, i) => (
                          <li key={i} className="text-sm text-[#6B6661] flex items-start gap-2">
                            <Lightbulb className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                            <span>{tip}</span>
                          </li>
                        ))}
                      </ul>
                    </PremiumGate>
                  )}
                </HideableSection>

                <ContextualCTA icon={Compass} text={ctaCopy.activitiesDicas.text} label={ctaCopy.activitiesDicas.label}
                  sublabel={ctaCopy.activitiesDicas.sublabel}
                  link={links.getyourguide?.url} platform="getyourguide" onTrack={trackClick} trust={true} />
              </div>

              {/* ── Actions Footer ── */}
              <div className="px-5 py-4 border-t border-stone-100 bg-[#FFBE98]/[0.03]" data-testid="actions-footer">
                <div className="space-y-3">
                  {/* Premium: Smart Map */}
                  <PremiumGate isAmbassador={isAmbassador} label="Desbloqueia o mapa interativo">
                    <Suspense fallback={<div className="bg-white rounded-xl border border-[#FFBE98]/20 p-8 flex items-center justify-center gap-2"><Loader2 className="w-5 h-5 animate-spin text-[#FFBE98]" /><span className="text-xs text-[#6B6661]">A carregar mapa...</span></div>}>
                      <SmartMap plan={plan} token={token} onApplyRefinement={handleRefine} />
                    </Suspense>
                  </PremiumGate>

                  {/* Premium: AI Assistant */}
                  <PremiumGate isAmbassador={isAmbassador} label="Desbloqueia o assistente completo">
                    <AIAssistant plan={plan} token={token} onApplyRefinement={handleRefine} />
                  </PremiumGate>

                  {/* Ambassador Progress */}
                  {token && !isAmbassador && (
                    <AmbassadorProgress token={token} compact={false} />
                  )}

                  {/* Primary: Ajustar */}
                  <RefinePanel onSubmit={handleRefine} loading={refining} success={refineSuccess} />
                  {/* Secondary: Copy + Share */}
                  <div className="flex items-center gap-2">
                    <button onClick={handleCopy} data-testid="copy-btn"
                      className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#6B6661] border border-stone-200 bg-white hover:bg-stone-50 hover:border-stone-300 px-3 py-2 rounded-xl transition-all duration-200">
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? 'Copiado!' : 'Copiar plano'}
                    </button>
                    <button onClick={handleShare} data-testid="share-btn"
                      className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#6B6661] border border-stone-200 bg-white hover:bg-stone-50 hover:border-stone-300 px-3 py-2 rounded-xl transition-all duration-200">
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

      <StickyBar links={links} onTrack={trackClick} visible={showStickyBar} destination={plan?.destination || destination} />
    </div>
  );
};

export default TravelPlanner;
