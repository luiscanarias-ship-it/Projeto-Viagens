import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  MapPin, Calendar, Sun, Shirt, ClipboardList, Lightbulb,
  Sparkles, Loader2, Globe, CheckCircle2, ArrowLeft
} from 'lucide-react';
import axios from 'axios';
import SEO from '../components/SEO';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PublicPlan = () => {
  const { slug } = useParams();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const res = await axios.get(`${API}/plan/${slug}`);
        setPlan(res.data);
      } catch {
        setError('Plano não encontrado.');
      } finally {
        setLoading(false);
      }
    };
    fetchPlan();
  }, [slug]);

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
        <p className="text-[#6B6661] mb-4">{error || 'Plano não encontrado.'}</p>
        <Link to="/travel-planner" className="text-[#FFBE98] hover:text-[#E6A07C] font-medium">
          Criar o seu próprio plano
        </Link>
      </div>
    );
  }

  const p = plan.plan;
  const destination = p.destination || plan.destination || '';

  return (
    <div className="min-h-screen bg-[#FAFAF9]" data-testid="public-plan-page">
      <SEO
        title={`Guia de viagem: ${destination}`}
        description={p.summary || `Plano de viagem para ${destination} gerado por IA. Roteiro, dicas locais, checklist e muito mais.`}
      />

      {/* Header */}
      <div className="bg-gradient-to-b from-[#FFBE98]/15 to-[#FAFAF9] pt-24 pb-6 px-4 sm:px-6">
        <div className="max-w-2xl mx-auto">
          <Link to="/travel-planner" className="inline-flex items-center gap-1.5 text-sm text-[#6B6661] hover:text-[#FFBE98] mb-4 transition-colors" data-testid="back-to-planner">
            <ArrowLeft className="w-4 h-4" /> Criar o meu plano
          </Link>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="inline-flex items-center gap-2 bg-white/80 rounded-full px-4 py-1.5 mb-3 border border-[#FFBE98]/20">
              <Sparkles className="w-3.5 h-3.5 text-[#FFBE98]" />
              <span className="text-xs font-medium text-[#6B6661]">Plano gerado por IA</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-[#2D2A26]" data-testid="public-plan-title">
              {destination}
            </h1>
            {p.dates && <p className="text-sm text-[#6B6661] mt-1">{p.dates}</p>}
            {p.summary && <p className="text-sm text-[#2D2A26]/80 mt-2 italic leading-relaxed">{p.summary}</p>}
          </motion.div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 sm:px-6 pb-24">
        <div className="bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden" data-testid="public-plan-content">
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

          {/* Local Tips */}
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
                <p className="text-xs text-[#FFBE98] mt-3 font-medium">
                  + {p.local_tips.length - 3} dicas exclusivas para Embaixadores 4Luis
                </p>
              )}
            </div>
          )}

          {/* CTA Footer */}
          <div className="px-5 py-5 border-t border-stone-100 bg-[#FFBE98]/[0.03] text-center">
            <p className="text-sm text-[#6B6661] mb-3">Quer um plano personalizado para si?</p>
            <Link
              to="/travel-planner"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-sm hover:bg-[#FFAB7D] transition-colors"
              data-testid="public-plan-cta"
            >
              <Sparkles className="w-4 h-4" /> Criar o meu plano com IA
            </Link>
          </div>
        </div>

        {/* Attribution */}
        <p className="text-center text-xs text-[#6B6661]/60 pt-4">
          Plano gerado por 4Luis AI Travel Planner
        </p>
      </div>
    </div>
  );
};

export default PublicPlan;
