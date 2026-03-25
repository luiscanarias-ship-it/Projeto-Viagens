import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  MapPin, Calendar, Sun, Shirt, ClipboardList, Lightbulb,
  Sparkles, Loader2, Globe, CheckCircle2, Share2,
  Plane, Building2, ArrowRight, Heart, Copy, Check, Lock, Map,
  ChevronDown
} from 'lucide-react';
import axios from 'axios';
import SEO from '../components/SEO';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* Country flag lookup */
const COUNTRY_FLAGS = {
  'portugal': '\u{1F1F5}\u{1F1F9}', 'franca': '\u{1F1EB}\u{1F1F7}', 'france': '\u{1F1EB}\u{1F1F7}', 'paris': '\u{1F1EB}\u{1F1F7}',
  'espanha': '\u{1F1EA}\u{1F1F8}', 'spain': '\u{1F1EA}\u{1F1F8}', 'madrid': '\u{1F1EA}\u{1F1F8}', 'barcelona': '\u{1F1EA}\u{1F1F8}',
  'italia': '\u{1F1EE}\u{1F1F9}', 'italy': '\u{1F1EE}\u{1F1F9}', 'roma': '\u{1F1EE}\u{1F1F9}', 'rome': '\u{1F1EE}\u{1F1F9}', 'milano': '\u{1F1EE}\u{1F1F9}',
  'japan': '\u{1F1EF}\u{1F1F5}', 'japao': '\u{1F1EF}\u{1F1F5}', 'tokyo': '\u{1F1EF}\u{1F1F5}', 'kyoto': '\u{1F1EF}\u{1F1F5}', 'osaka': '\u{1F1EF}\u{1F1F5}',
  'uk': '\u{1F1EC}\u{1F1E7}', 'london': '\u{1F1EC}\u{1F1E7}', 'londres': '\u{1F1EC}\u{1F1E7}', 'england': '\u{1F1EC}\u{1F1E7}',
  'germany': '\u{1F1E9}\u{1F1EA}', 'alemanha': '\u{1F1E9}\u{1F1EA}', 'berlin': '\u{1F1E9}\u{1F1EA}', 'munich': '\u{1F1E9}\u{1F1EA}',
  'usa': '\u{1F1FA}\u{1F1F8}', 'new york': '\u{1F1FA}\u{1F1F8}', 'nova iorque': '\u{1F1FA}\u{1F1F8}', 'los angeles': '\u{1F1FA}\u{1F1F8}',
  'brasil': '\u{1F1E7}\u{1F1F7}', 'brazil': '\u{1F1E7}\u{1F1F7}', 'rio': '\u{1F1E7}\u{1F1F7}',
  'grecia': '\u{1F1EC}\u{1F1F7}', 'greece': '\u{1F1EC}\u{1F1F7}', 'atenas': '\u{1F1EC}\u{1F1F7}', 'santorini': '\u{1F1EC}\u{1F1F7}',
  'tailandia': '\u{1F1F9}\u{1F1ED}', 'thailand': '\u{1F1F9}\u{1F1ED}', 'bangkok': '\u{1F1F9}\u{1F1ED}',
  'turquia': '\u{1F1F9}\u{1F1F7}', 'turkey': '\u{1F1F9}\u{1F1F7}', 'istanbul': '\u{1F1F9}\u{1F1F7}', 'istambul': '\u{1F1F9}\u{1F1F7}',
  'holanda': '\u{1F1F3}\u{1F1F1}', 'netherlands': '\u{1F1F3}\u{1F1F1}', 'amsterdam': '\u{1F1F3}\u{1F1F1}',
  'marrocos': '\u{1F1F2}\u{1F1E6}', 'morocco': '\u{1F1F2}\u{1F1E6}', 'marrakech': '\u{1F1F2}\u{1F1E6}',
  'croacia': '\u{1F1ED}\u{1F1F7}', 'croatia': '\u{1F1ED}\u{1F1F7}', 'dubrovnik': '\u{1F1ED}\u{1F1F7}',
  'lisboa': '\u{1F1F5}\u{1F1F9}', 'porto': '\u{1F1F5}\u{1F1F9}', 'algarve': '\u{1F1F5}\u{1F1F9}', 'acores': '\u{1F1F5}\u{1F1F9}', 'madeira': '\u{1F1F5}\u{1F1F9}',
};

const getFlag = (destination) => {
  const lower = (destination || '').toLowerCase();
  for (const [key, flag] of Object.entries(COUNTRY_FLAGS)) {
    if (lower.includes(key)) return flag;
  }
  return '\u{1F30D}';
};

const PublicPlan = () => {
  const { slug } = useParams();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [shared, setShared] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    window.scrollTo(0, 0);
    const fetchPlan = async () => {
      try {
        const res = await axios.get(`${API}/plan/${slug}`);
        setPlan(res.data);
      } catch {
        setError('Plano nao encontrado.');
      } finally {
        setLoading(false);
      }
    };
    fetchPlan();
  }, [slug]);

  const trackShare = (type) => {
    axios.post(`${API}/track-share`, { type, page: 'public-plan', slug: slug || '' }).catch(() => {});
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = window.location.href;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    trackShare('copy');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = async () => {
    const p = plan?.plan;
    const dest = p?.destination || '';
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Plano de viagem: ${dest}`,
          text: `Ve este roteiro para ${dest} gerado por IA!`,
          url: window.location.href
        });
        trackShare('native');
        return;
      } catch (e) {
        if (e.name === 'AbortError') return;
      }
    }
    handleCopy();
    setShared(true);
    setTimeout(() => setShared(false), 2500);
  };

  const handleWhatsApp = () => {
    const p = plan?.plan;
    const dest = p?.destination || 'esta viagem';
    const text = `Ve este roteiro incrivel para ${dest}! ${window.location.href}`;
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
    trackShare('whatsapp');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAF9] pt-20" data-testid="public-plan-loading">
        <Loader2 className="w-8 h-8 animate-spin text-[#FFBE98]" />
      </div>
    );
  }

  if (error || !plan?.plan) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#FAFAF9] pt-20 px-4" data-testid="public-plan-error">
        <Globe className="w-12 h-12 text-stone-300 mb-4" />
        <p className="text-[#6B6661] mb-4">{error || 'Plano nao encontrado.'}</p>
        <Link to="/travel-planner" className="text-[#FFBE98] hover:text-[#E6A07C] font-medium">
          Criar o teu proprio plano
        </Link>
      </div>
    );
  }

  const p = plan.plan;
  const destination = p.destination || plan.destination || '';
  const numDays = p.itinerary?.length || 0;
  const ogImage = `${process.env.REACT_APP_BACKEND_URL}/api/og-image/${slug}`;
  const flag = getFlag(destination);

  const scrollToContent = () => {
    contentRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-screen bg-[#FAFAF9]" data-testid="public-plan-page">
      <SEO
        title={`${destination} em ${numDays} dias`}
        description={p.summary || `Roteiro inteligente para ${destination} com ${numDays} dias. Gerado com IA.`}
        image={ogImage}
        type="article"
      />

      {/* Hero — Full viewport with OG image background */}
      <div className="relative min-h-[100vh] flex flex-col items-center justify-center overflow-hidden" data-testid="hero-section">
        {/* OG image background with blur */}
        <div className="absolute inset-0 z-0">
          <img src={ogImage} alt="" className="w-full h-full object-cover scale-110" style={{ filter: 'blur(20px) brightness(0.3)' }} />
          <div className="absolute inset-0 bg-gradient-to-b from-[#2D2A26]/60 via-[#2D2A26]/40 to-[#2D2A26]/80" />
        </div>

        {/* Content */}
        <div className="relative z-10 text-center px-6 max-w-2xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight" data-testid="public-plan-title">
              {destination} em {numDays} dias {flag}
            </h1>

            {/* Subtitle */}
            <p className="text-base sm:text-lg text-white/70 leading-relaxed max-w-lg mx-auto mb-6">
              Roteiro inteligente para viver o melhor da cidade<br className="hidden sm:block" />
              sem perder tempo nem cair em armadilhas
            </p>

            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md rounded-full px-5 py-2 mb-8 border border-white/10">
              <Sparkles className="w-4 h-4 text-[#FFBE98]" />
              <span className="text-sm font-medium text-white/80">Gerado com IA</span>
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                onClick={scrollToContent}
                className="flex items-center gap-2 bg-white text-[#2D2A26] font-bold text-sm px-8 py-3.5 rounded-2xl hover:shadow-2xl hover:-translate-y-0.5 transition-all duration-300"
                data-testid="cta-explore"
              >
                <Map className="w-4 h-4" /> Explorar roteiro
              </button>
              <Link
                to="/travel-planner"
                className="flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white font-semibold text-sm px-8 py-3.5 rounded-2xl border border-white/15 hover:bg-white/20 hover:-translate-y-0.5 transition-all duration-300"
                data-testid="cta-create-plan"
              >
                <Sparkles className="w-4 h-4 text-[#FFBE98]" /> Criar o meu
              </Link>
            </div>

            {/* Dates */}
            {p.dates && (
              <p className="text-xs text-white/40 mt-5">{p.dates}</p>
            )}
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            className="absolute bottom-8 left-1/2 -translate-x-1/2 cursor-pointer"
            animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 1.5 }}
            onClick={scrollToContent}
          >
            <ChevronDown className="w-6 h-6 text-white/30" />
          </motion.div>
        </div>
      </div>

      {/* Share bar (sticky below header on scroll) */}
      <div className="sticky top-20 z-30 bg-white/80 backdrop-blur-xl border-b border-stone-100" data-testid="share-bar">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-sm font-bold text-[#2D2A26] truncate">{destination}</span>
            <span className="text-xs text-[#6B6661]">{numDays} dias</span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button onClick={handleWhatsApp} data-testid="share-whatsapp"
              className="flex items-center gap-1 bg-[#25D366] text-white text-[10px] font-bold px-3 py-1.5 rounded-lg hover:bg-[#20BA5A] transition-colors">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.611.611l4.458-1.495A11.934 11.934 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.24 0-4.326-.693-6.05-1.876l-.424-.295-3.072 1.03 1.03-3.072-.296-.424A9.935 9.935 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z"/></svg>
              Partilhar
            </button>
            <button onClick={handleCopy} data-testid="share-copy-link"
              className="flex items-center gap-1 bg-stone-100 text-[#2D2A26] text-[10px] font-semibold px-3 py-1.5 rounded-lg hover:bg-stone-200 transition-colors">
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
              {copied ? 'Copiado!' : 'Copiar'}
            </button>
            <button onClick={handleShare} data-testid="share-native"
              className="flex items-center gap-1 bg-stone-100 text-[#2D2A26] text-[10px] font-semibold px-2.5 py-1.5 rounded-lg hover:bg-stone-200 transition-colors">
              <Share2 className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      <div ref={contentRef} className="max-w-2xl mx-auto px-4 sm:px-6 pb-24 pt-4">
        {/* Travel Context: Flight + Hotel (public preview) */}
        {(p.flight_info || p.hotel_info) && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl border border-stone-100 shadow-sm p-4 mb-3 space-y-2.5" data-testid="public-travel-context">
            {p.flight_info?.outbound && (
              <div className="flex items-center gap-3 bg-sky-50/50 rounded-lg p-2.5">
                <Plane className="w-4 h-4 text-sky-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] font-bold text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded">{p.flight_info.outbound.flight_number}</span>
                    <span className="text-[10px] text-[#6B6661]">Ida</span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <div className="text-left">
                      <p className="text-[11px] font-semibold text-[#2D2A26]">{p.flight_info.outbound.departure_time}</p>
                      <p className="text-[9px] text-[#6B6661] truncate max-w-[140px]">{p.flight_info.outbound.departure_airport}</p>
                    </div>
                    <ArrowRight className="w-3 h-3 text-stone-300 shrink-0 mx-1" />
                    <div className="text-left">
                      <p className="text-[11px] font-semibold text-[#2D2A26]">{p.flight_info.outbound.arrival_time}</p>
                      <p className="text-[9px] text-[#6B6661] truncate max-w-[140px]">{p.flight_info.outbound.arrival_airport}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {p.hotel_info?.name && (
              <div className="flex items-start gap-3 bg-amber-50/30 rounded-lg p-2.5">
                <Building2 className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-[11px] font-semibold text-[#2D2A26]">{p.hotel_info.name}</p>
                  {p.hotel_info.address && <p className="text-[9px] text-[#6B6661] mt-0.5">{p.hotel_info.address}</p>}
                  {p.hotel_info.area && <span className="text-[9px] text-amber-600 font-medium">{p.hotel_info.area}</span>}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Main content card */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
          className="bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden" data-testid="public-plan-content">

          {/* Map Preview (gated teaser) */}
          <div className="relative bg-gradient-to-br from-sky-50 to-stone-50 px-5 py-6 border-b border-stone-100" data-testid="map-preview-teaser">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 bg-sky-100 rounded-xl flex items-center justify-center">
                <Map className="w-4 h-4 text-sky-600" />
              </div>
              <div>
                <h3 className="font-bold text-[#2D2A26] text-sm">Mapa interativo</h3>
                <p className="text-[10px] text-[#6B6661]">{p.itinerary?.reduce((acc, d) => acc + (d.activities?.length || 0), 0) || 0} locais em {numDays} dias</p>
              </div>
            </div>
            {/* Fake map pins visual */}
            <div className="flex items-center gap-2 flex-wrap mb-3">
              {p.itinerary?.slice(0, 5).map((day, i) => (
                <div key={i} className="flex items-center gap-1 bg-white rounded-full px-2.5 py-1 border border-stone-200 shadow-sm">
                  <MapPin className="w-3 h-3 text-[#FFBE98]" />
                  <span className="text-[10px] font-medium text-[#2D2A26]">Dia {day.day}</span>
                  <span className="text-[9px] text-[#6B6661]">{day.activities?.length || 0} pontos</span>
                </div>
              ))}
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-white/90 via-transparent to-transparent pointer-events-none" />
            <div className="relative flex items-center gap-2 justify-center">
              <Lock className="w-3.5 h-3.5 text-[#FFBE98]" />
              <span className="text-xs font-semibold text-[#6B6661]">Mapa interativo exclusivo para Embaixadores</span>
            </div>
          </div>

          {/* Weather */}
          {p.weather && (
            <div className="px-5 pt-5">
              <div className="flex items-start gap-3 bg-amber-50/50 rounded-xl p-3">
                <Sun className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-xs font-bold text-[#2D2A26] mb-0.5">Clima esperado</p>
                  <p className="text-xs text-[#6B6661] leading-relaxed">{p.weather}</p>
                </div>
              </div>
            </div>
          )}

          {/* Packing */}
          {p.packing && (
            <div className="px-5 pt-3">
              <div className="flex items-start gap-3 bg-violet-50/50 rounded-xl p-3">
                <Shirt className="w-4 h-4 text-violet-500 mt-0.5 shrink-0" />
                <div className="flex-1">
                  <p className="text-xs font-bold text-[#2D2A26] mb-1.5">O que levar</p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                    {p.packing.clothing?.map((item, i) => (
                      <p key={`c-${i}`} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                        <span className="w-1 h-1 bg-violet-400 rounded-full shrink-0" />{item.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim()}
                      </p>
                    ))}
                    {p.packing.essentials?.map((item, i) => (
                      <p key={`e-${i}`} className="text-xs text-[#6B6661] flex items-center gap-1.5">
                        <span className="w-1 h-1 bg-[#FFBE98] rounded-full shrink-0" />{item.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim()}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="h-px bg-stone-100 mx-5 mt-4" />

          {/* Itinerary */}
          {p.itinerary?.length > 0 && (
            <div className="px-5 pt-5 pb-3">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 bg-sky-50 rounded-xl flex items-center justify-center">
                  <Calendar className="w-4 h-4 text-sky-500" />
                </div>
                <h3 className="font-bold text-[#2D2A26]">Roteiro dia a dia</h3>
              </div>
              <div className="space-y-4">
                {p.itinerary.map((day, i) => (
                  <div key={i} className="border-l-2 border-[#FFBE98]/30 pl-3">
                    <p className="text-xs font-bold text-[#FFBE98]">Dia {day.day}</p>
                    <p className="text-sm font-semibold text-[#2D2A26]">{day.title}</p>
                    <ul className="mt-1 space-y-0.5">
                      {day.activities?.map((a, j) => (
                        <li key={j} className="text-xs text-[#6B6661] flex items-start gap-1.5">
                          <span className="text-[#FFBE98] mt-0.5 shrink-0">&#8226;</span>
                          <span>{a.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim()}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="h-px bg-stone-100 mx-5" />

          {/* Checklist */}
          {p.checklist && (
            <div className="px-5 pt-5 pb-3">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center">
                  <ClipboardList className="w-4 h-4 text-emerald-500" />
                </div>
                <h3 className="font-bold text-[#2D2A26]">Checklist de viagem</h3>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {Object.entries(p.checklist).map(([key, items]) => (
                  <div key={key} className="bg-stone-50/50 rounded-xl p-2.5">
                    <p className="text-[10px] font-bold text-[#2D2A26] uppercase tracking-wide mb-1.5">
                      {key === 'documents' ? 'Documentos' : key === 'hygiene' ? 'Higiene' : 'Tecnologia'}
                    </p>
                    {items?.map((item, i) => (
                      <p key={i} className="text-xs text-[#6B6661] flex items-center gap-1.5 py-0.5">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                        {item.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim()}
                      </p>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="h-px bg-stone-100 mx-5" />

          {/* Local Tips (limited for non-premium) */}
          {p.local_tips?.length > 0 && (
            <div className="px-5 pt-5 pb-3">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 bg-teal-50 rounded-xl flex items-center justify-center">
                  <Lightbulb className="w-4 h-4 text-teal-500" />
                </div>
                <h3 className="font-bold text-[#2D2A26]">Dicas locais</h3>
              </div>
              <ul className="space-y-2">
                {p.local_tips.slice(0, 3).map((tip, i) => (
                  <li key={i} className="text-sm text-[#6B6661] flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                    <span>{tip.replace(/\[CTA:\w+:[^\]]+\]/g, '').trim()}</span>
                  </li>
                ))}
              </ul>
              {p.local_tips.length > 3 && (
                <div className="flex items-center gap-2 mt-3 text-xs text-[#FFBE98] font-medium">
                  <Lock className="w-3 h-3" />
                  + {p.local_tips.length - 3} dicas exclusivas para Embaixadores 4Luis
                </div>
              )}
            </div>
          )}

          {/* CTAs Footer */}
          <div className="px-5 py-6 border-t border-stone-100 bg-gradient-to-b from-[#FFBE98]/5 to-white space-y-3" data-testid="public-plan-ctas">
            {/* CTA 1: Create own plan */}
            <Link
              to="/travel-planner"
              className="w-full flex items-center justify-center gap-2 px-6 py-3.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-sm hover:bg-[#E6A07C] transition-all hover:shadow-md hover:-translate-y-0.5"
              data-testid="cta-create-plan"
            >
              <Sparkles className="w-4 h-4" /> Criar o meu roteiro com IA
            </Link>

            {/* CTA 2: Contribute to journey (if linked) */}
            {plan.journey_id && (
              <Link
                to={`/journey/${plan.journey_id}`}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-white text-[#2D2A26] rounded-xl font-semibold text-sm border-2 border-[#FFBE98] hover:bg-[#FFBE98]/10 transition-all"
                data-testid="cta-contribute"
              >
                <Heart className="w-4 h-4 text-[#FFBE98]" /> Contribuir para esta viagem
              </Link>
            )}

            {/* Share again */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleWhatsApp}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#6B6661] border border-stone-200 bg-white hover:bg-stone-50 px-3 py-2.5 rounded-xl transition-colors"
                data-testid="cta-share-whatsapp"
              >
                <Share2 className="w-3.5 h-3.5" /> Partilhar via WhatsApp
              </button>
              <button
                onClick={handleCopy}
                className="flex-1 flex items-center justify-center gap-1.5 text-xs font-semibold text-[#6B6661] border border-stone-200 bg-white hover:bg-stone-50 px-3 py-2.5 rounded-xl transition-colors"
                data-testid="cta-copy-link"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copiado!' : 'Copiar link'}
              </button>
            </div>
          </div>
        </motion.div>

        {/* Attribution */}
        <p className="text-center text-xs text-[#6B6661]/60 pt-4">
          Plano gerado por 4Luis AI Travel Planner
        </p>
      </div>
    </div>
  );
};

export default PublicPlan;
