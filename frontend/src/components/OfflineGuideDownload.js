import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Loader2, Check, Plane, Building2, Map, Calendar, Lightbulb, Train, ChevronDown } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SECTION_OPTIONS = [
  { key: 'flights', label: 'Voos', icon: Plane },
  { key: 'hotel', label: 'Hotel', icon: Building2 },
  { key: 'map', label: 'Mapa', icon: Map },
  { key: 'itinerary', label: 'Roteiro', icon: Calendar },
  { key: 'tips', label: 'Dicas & Checklist', icon: Lightbulb },
  { key: 'transport', label: 'Transportes', icon: Train },
];

const OfflineGuideDownload = ({ plan, token, geocodeData, planSlug }) => {
  const [downloading, setDownloading] = useState(false);
  const [done, setDone] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [sections, setSections] = useState({
    flights: true, hotel: true, map: true,
    itinerary: true, tips: true, transport: true
  });

  const toggleSection = (key) => {
    setSections(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleDownload = async () => {
    if (!plan || !token) return;
    setDownloading(true);
    setDone(false);

    try {
      const res = await axios.post(`${API}/ai/travel-plan/pdf`, {
        plan,
        sections,
        geocode_data: geocodeData || null,
        slug: planSlug || null
      }, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
        timeout: 30000
      });

      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const dest = (plan.destination || 'viagem').replace(/\s+/g, '-').toLowerCase();
      a.download = `guia-${dest}-4luis.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setDone(true);
      setTimeout(() => setDone(false), 3000);
    } catch {
      // Silent fail — user can retry
    } finally {
      setDownloading(false);
    }
  };

  const selectedCount = Object.values(sections).filter(Boolean).length;

  return (
    <div className="space-y-2" data-testid="offline-guide">
      {/* Main download button */}
      <button
        onClick={handleDownload}
        disabled={downloading || selectedCount === 0}
        className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-bold text-sm transition-all duration-200 ${
          done
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            : downloading
              ? 'bg-stone-100 text-stone-400 cursor-wait'
              : 'bg-[#2D2A26] text-white hover:bg-[#3D3A36] hover:shadow-md hover:-translate-y-0.5'
        }`}
        data-testid="download-pdf-btn"
      >
        {downloading ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> A gerar guia...</>
        ) : done ? (
          <><Check className="w-4 h-4" /> Guia descarregado!</>
        ) : (
          <><Download className="w-4 h-4" /> Descarregar guia offline</>
        )}
      </button>

      {/* Customize toggle */}
      <button
        onClick={() => setShowOptions(!showOptions)}
        className="w-full flex items-center justify-center gap-1.5 text-[10px] text-[#6B6661] hover:text-[#2D2A26] transition-colors py-1"
        data-testid="customize-sections-toggle"
      >
        <ChevronDown className={`w-3 h-3 transition-transform ${showOptions ? 'rotate-180' : ''}`} />
        Personalizar seccoes ({selectedCount}/{SECTION_OPTIONS.length})
      </button>

      {/* Section checkboxes */}
      <AnimatePresence>
        {showOptions && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 gap-1.5 p-3 bg-stone-50 rounded-xl border border-stone-100" data-testid="section-options">
              {SECTION_OPTIONS.map(opt => (
                <button
                  key={opt.key}
                  onClick={() => toggleSection(opt.key)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    sections[opt.key]
                      ? 'bg-white border border-[#FFBE98]/30 text-[#2D2A26] shadow-sm'
                      : 'bg-transparent border border-transparent text-[#6B6661]/50'
                  }`}
                  data-testid={`section-toggle-${opt.key}`}
                >
                  <opt.icon className={`w-3.5 h-3.5 ${sections[opt.key] ? 'text-[#FFBE98]' : 'text-stone-300'}`} />
                  {opt.label}
                  {sections[opt.key] && <Check className="w-3 h-3 text-emerald-500 ml-auto" />}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default OfflineGuideDownload;
