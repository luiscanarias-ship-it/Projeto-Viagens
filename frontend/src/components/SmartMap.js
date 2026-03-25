import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Loader2, ArrowRight, Clock, DollarSign, Users, ChevronUp, ChevronDown, X, Navigation, Check, Maximize2, Minimize2 } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Day colors — high contrast, distinct per day
const DAY_COLORS = [
  '#E85D3A', // vermelho-coral (Dia 1)
  '#2D7DD2', // azul forte (Dia 2)
  '#45B764', // verde vivo (Dia 3)
  '#9B59B6', // roxo (Dia 4)
  '#F39C12', // laranja-dourado (Dia 5)
  '#E91E63', // rosa-magenta (Dia 6)
  '#00ACC1', // ciano (Dia 7)
  '#8D6E63', // castanho (Dia 8)
  '#3F51B5', // indigo (Dia 9)
  '#FF6F00', // amber escuro (Dia 10)
];

const createDayIcon = (day, index, isActive) => {
  const color = DAY_COLORS[(day - 1) % DAY_COLORS.length];
  const size = isActive ? 36 : 28;
  const svg = `<svg width="${size}" height="${size + 10}" viewBox="0 0 36 46" xmlns="http://www.w3.org/2000/svg">
    <path d="M18 0C8.06 0 0 8.06 0 18c0 13.5 18 28 18 28s18-14.5 18-28C36 8.06 27.94 0 18 0z" fill="${color}" stroke="white" stroke-width="2"/>
    <circle cx="18" cy="18" r="11" fill="white"/>
    <text x="18" y="22" text-anchor="middle" font-size="12" font-weight="bold" fill="${color}" font-family="system-ui">${index + 1}</text>
  </svg>`;
  return L.divIcon({
    html: svg,
    className: 'smart-map-marker',
    iconSize: [size, size + 10],
    iconAnchor: [size / 2, size + 10],
    popupAnchor: [0, -(size + 5)]
  });
};

// Fly to location
const FlyTo = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, zoom || 14, { duration: 0.8 });
  }, [center, zoom, map]);
  return null;
};

// Auto fit bounds on data change
const FitBounds = ({ locations }) => {
  const map = useMap();
  useEffect(() => {
    if (locations.length > 0) {
      const bounds = locations.map(l => [l.lat, l.lng]);
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
    }
  }, [locations, map]);
  return null;
};

const SmartMap = ({ plan, token, onApplyRefinement }) => {
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedDay, setSelectedDay] = useState(0); // 0 = all
  const [activeLocation, setActiveLocation] = useState(null);
  const [flyTarget, setFlyTarget] = useState(null);
  const [improvingLocation, setImprovingLocation] = useState(null);
  const [improveResult, setImproveResult] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizeResult, setOptimizeResult] = useState(null);
  const [mobileSheet, setMobileSheet] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const mapRef = useRef(null);
  const mapContainerRef = useRef(null);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Fullscreen: ESC to close + body scroll lock
  useEffect(() => {
    if (isFullscreen) {
      document.body.style.overflow = 'hidden';
      const handleEsc = (e) => { if (e.key === 'Escape') setIsFullscreen(false); };
      window.addEventListener('keydown', handleEsc);
      return () => { document.body.style.overflow = ''; window.removeEventListener('keydown', handleEsc); };
    }
  }, [isFullscreen]);

  // Geocode plan locations
  const fetchGeoData = useCallback(async () => {
    if (!plan?.itinerary || !token) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/ai/geocode-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ plan })
      });
      if (res.ok) {
        const data = await res.json();
        setGeoData(data);
      }
    } catch (e) {
      console.error('Geocode error:', e);
    } finally {
      setLoading(false);
    }
  }, [plan, token]);

  useEffect(() => { fetchGeoData(); }, [fetchGeoData]);

  // All locations flat
  const allLocations = useMemo(() => {
    if (!geoData?.days) return [];
    return geoData.days.flatMap(d => d.locations);
  }, [geoData]);

  // Filtered locations by day
  const filteredDays = useMemo(() => {
    if (!geoData?.days) return [];
    if (selectedDay === 0) return geoData.days;
    return geoData.days.filter(d => d.day === selectedDay);
  }, [geoData, selectedDay]);

  const filteredLocations = useMemo(() => {
    return filteredDays.flatMap(d => d.locations);
  }, [filteredDays]);

  // Invalidate map size and fit bounds when toggling fullscreen
  useEffect(() => {
    if (mapRef.current) {
      setTimeout(() => {
        mapRef.current.invalidateSize();
        if (filteredLocations.length > 0) {
          const bounds = filteredLocations.map(l => [l.lat, l.lng]);
          mapRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
        }
      }, 300);
    }
  }, [isFullscreen, filteredLocations]);

  // Map center
  const mapCenter = useMemo(() => {
    if (filteredLocations.length > 0) {
      const avgLat = filteredLocations.reduce((s, l) => s + l.lat, 0) / filteredLocations.length;
      const avgLng = filteredLocations.reduce((s, l) => s + l.lng, 0) / filteredLocations.length;
      return [avgLat, avgLng];
    }
    return [48.8566, 2.3522]; // Paris fallback
  }, [filteredLocations]);

  // Improve a location
  const handleImprove = async (location, type) => {
    setImprovingLocation({ name: location.name, type });
    setImproveResult(null);
    try {
      const res = await fetch(`${API}/ai/improve-location`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ location: location.name, type, destination: plan.destination, day: location.day })
      });
      if (res.ok) {
        const data = await res.json();
        setImproveResult(data);
      }
    } catch (e) {
      console.error('Improve error:', e);
    } finally {
      setImprovingLocation(null);
    }
  };

  // Optimize route
  const handleOptimize = async () => {
    const dayNum = selectedDay || 1;
    const dayData = geoData?.days?.find(d => d.day === dayNum);
    if (!dayData?.locations?.length) return;

    setOptimizing(true);
    setOptimizeResult(null);
    try {
      const res = await fetch(`${API}/ai/optimize-route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ locations: dayData.locations, day: dayNum, destination: plan.destination })
      });
      if (res.ok) {
        const data = await res.json();
        setOptimizeResult(data);
      }
    } catch (e) {
      console.error('Optimize error:', e);
    } finally {
      setOptimizing(false);
    }
  };

  const handleApply = (prompt) => {
    if (onApplyRefinement && prompt) {
      onApplyRefinement(prompt);
      setImproveResult(null);
      setOptimizeResult(null);
    }
  };

  const handleLocationClick = (loc) => {
    setActiveLocation(loc);
    setFlyTarget([loc.lat, loc.lng]);
    setImproveResult(null);
    if (isMobile) setMobileSheet(true);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-[#FFBE98]/20 p-8 flex flex-col items-center justify-center gap-3" data-testid="smart-map-loading">
        <Loader2 className="w-6 h-6 animate-spin text-[#FFBE98]" />
        <p className="text-xs text-[#6B6661]">A carregar o mapa do roteiro...</p>
      </div>
    );
  }

  if (!geoData || allLocations.length === 0) {
    return (
      <div className="bg-stone-50 rounded-xl border border-stone-100 p-6 text-center" data-testid="smart-map-empty">
        <Navigation className="w-8 h-8 text-stone-300 mx-auto mb-2" />
        <p className="text-sm text-[#6B6661]">Nao foi possivel localizar os pontos do roteiro no mapa.</p>
        <button onClick={fetchGeoData} className="text-xs text-[#FFBE98] font-semibold mt-2 hover:underline">Tentar novamente</button>
      </div>
    );
  }

  const totalDays = geoData.days.length;

  return (
    <div
      ref={mapContainerRef}
      className={isFullscreen ? 'fixed inset-0 z-[9999] bg-white flex flex-col' : ''}
      data-testid="smart-map"
    >
    <div className={`bg-white ${isFullscreen ? 'flex flex-col h-full' : 'rounded-xl border border-[#FFBE98]/20'} overflow-hidden`}>
      {/* Header */}
      <div className="px-4 py-3 bg-gradient-to-r from-sky-50/50 to-[#FFBE98]/5 border-b border-stone-100 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-sky-100 rounded-lg flex items-center justify-center">
            <Navigation className="w-3.5 h-3.5 text-sky-600" />
          </div>
          <div>
            <p className="text-xs font-bold text-[#2D2A26]">Mapa interativo</p>
            <p className="text-[9px] text-[#6B6661]">{allLocations.length} locais em {totalDays} dias</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleOptimize}
            disabled={optimizing}
            className="flex items-center gap-1.5 text-[10px] font-semibold bg-violet-50 hover:bg-violet-100 text-violet-600 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
            data-testid="optimize-route-btn"
          >
            {optimizing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
            Otimizar percurso
          </button>
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="flex items-center justify-center w-8 h-8 bg-stone-100 hover:bg-stone-200 rounded-lg transition-colors"
            data-testid="map-fullscreen-toggle"
            title={isFullscreen ? 'Sair do ecra inteiro' : 'Ecra inteiro'}
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4 text-[#6B6661]" /> : <Maximize2 className="w-4 h-4 text-[#6B6661]" />}
          </button>
        </div>
      </div>

      {/* Day filters */}
      <div className="px-4 py-2 border-b border-stone-100 flex items-center gap-1.5 overflow-x-auto scrollbar-hide" data-testid="day-filter">
        <button
          onClick={() => setSelectedDay(0)}
          className={`shrink-0 text-[10px] font-semibold px-3 py-1 rounded-full transition-colors ${selectedDay === 0 ? 'bg-[#FFBE98] text-white' : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'}`}
          data-testid="day-filter-all"
        >
          Todos
        </button>
        {geoData.days.map(d => (
          <button
            key={d.day}
            onClick={() => setSelectedDay(d.day)}
            className={`shrink-0 text-[10px] font-semibold px-3 py-1 rounded-full transition-colors ${selectedDay === d.day ? 'bg-[#FFBE98] text-white' : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'}`}
            data-testid={`day-filter-${d.day}`}
          >
            Dia {d.day}
          </button>
        ))}
      </div>

      {/* Map + Sidebar layout */}
      <div className={`flex ${isMobile && !isFullscreen ? 'flex-col' : 'flex-row'} ${isFullscreen ? 'flex-1 min-h-0' : ''}`} style={isFullscreen ? {} : { height: isMobile ? '70vh' : '400px' }}>
        {/* Sidebar — desktop or fullscreen */}
        {(!isMobile || isFullscreen) && (
          <div className="w-52 border-r border-stone-100 overflow-y-auto" data-testid="map-sidebar">
            {filteredDays.map(dayGroup => (
              <div key={dayGroup.day} className="border-b border-stone-50 last:border-b-0">
                <div className="px-3 py-1.5 bg-stone-50 sticky top-0">
                  <span className="text-[9px] font-bold uppercase tracking-wider" style={{ color: DAY_COLORS[(dayGroup.day - 1) % DAY_COLORS.length] }}>
                    Dia {dayGroup.day}
                  </span>
                </div>
                {dayGroup.locations.map((loc, i) => (
                  <button
                    key={`${dayGroup.day}-${i}`}
                    onClick={() => handleLocationClick(loc)}
                    className={`w-full text-left px-3 py-2 flex items-start gap-2 hover:bg-[#FFBE98]/5 transition-colors ${activeLocation?.name === loc.name ? 'bg-[#FFBE98]/10' : ''}`}
                    data-testid={`sidebar-loc-${dayGroup.day}-${i}`}
                  >
                    <span className="text-[10px] font-bold shrink-0 mt-0.5" style={{ color: DAY_COLORS[(dayGroup.day - 1) % DAY_COLORS.length] }}>
                      {i + 1}
                    </span>
                    <span className="text-[11px] text-[#2D2A26] leading-tight">{loc.name}</span>
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}

        {/* Map */}
        <div className="flex-1 relative">
          <MapContainer
            center={mapCenter}
            zoom={13}
            className="w-full h-full"
            zoomControl={true}
            ref={(map) => { mapRef.current = map; }}
            style={{ background: '#FAFAF9' }}
          >
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />

            {flyTarget && <FlyTo center={flyTarget} zoom={15} />}
            <FitBounds locations={filteredLocations} />

            {/* Day routes */}
            {filteredDays.map(dayGroup => {
              if (dayGroup.locations.length < 2) return null;
              const positions = dayGroup.locations.map(l => [l.lat, l.lng]);
              return (
                <Polyline
                  key={`route-${dayGroup.day}`}
                  positions={positions}
                  color={DAY_COLORS[(dayGroup.day - 1) % DAY_COLORS.length]}
                  weight={3}
                  opacity={0.6}
                  dashArray="8 6"
                />
              );
            })}

            {/* Markers */}
            {filteredDays.map(dayGroup =>
              dayGroup.locations.map((loc, i) => (
                <Marker
                  key={`${dayGroup.day}-${i}`}
                  position={[loc.lat, loc.lng]}
                  icon={createDayIcon(dayGroup.day, i, activeLocation?.name === loc.name)}
                  eventHandlers={{
                    click: () => handleLocationClick(loc)
                  }}
                >
                  <Popup className="smart-map-popup" maxWidth={220}>
                    <div className="p-1">
                      <p className="text-xs font-bold text-[#2D2A26] mb-0.5">{loc.name}</p>
                      <p className="text-[9px] mb-2" style={{ color: DAY_COLORS[(loc.day - 1) % DAY_COLORS.length] }}>
                        Dia {loc.day} — Ponto {i + 1}
                      </p>
                      <p className="text-[9px] font-semibold text-[#6B6661] mb-1">Melhorar este ponto:</p>
                      <div className="flex flex-wrap gap-1">
                        {[
                          { id: 'less_queues', label: 'Menos filas', icon: Users },
                          { id: 'cheaper', label: 'Mais barato', icon: DollarSign },
                          { id: 'best_time', label: 'Melhor horario', icon: Clock }
                        ].map(opt => (
                          <button
                            key={opt.id}
                            onClick={() => handleImprove(loc, opt.id)}
                            disabled={!!improvingLocation}
                            className="flex items-center gap-1 text-[8px] font-medium bg-stone-50 hover:bg-[#FFBE98]/10 border border-stone-200 px-1.5 py-0.5 rounded transition-colors"
                            data-testid={`improve-${opt.id}`}
                          >
                            <opt.icon className="w-2.5 h-2.5" />{opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))
            )}
          </MapContainer>

          {/* Improve loading overlay */}
          {improvingLocation && (
            <div className="absolute bottom-3 left-3 right-3 bg-white/95 backdrop-blur-sm rounded-lg px-3 py-2 shadow-sm border border-stone-100 flex items-center gap-2 z-[1000]">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#FFBE98]" />
              <span className="text-[11px] text-[#6B6661]">A analisar...</span>
            </div>
          )}

          {/* Improve result overlay */}
          <AnimatePresence>
            {improveResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute bottom-3 left-3 right-3 bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-lg border border-[#FFBE98]/20 z-[1000]"
                data-testid="improve-result"
              >
                <div className="flex justify-between items-start mb-2">
                  <p className="text-[11px] font-semibold text-[#2D2A26]">{improveResult.response}</p>
                  <button onClick={() => setImproveResult(null)} className="text-stone-400 hover:text-stone-600"><X className="w-3.5 h-3.5" /></button>
                </div>
                {improveResult.suggestions?.map((s, i) => (
                  <div key={i} className="flex items-start gap-1.5 mb-1">
                    <ArrowRight className="w-3 h-3 text-[#FFBE98] shrink-0 mt-0.5" />
                    <p className="text-[10px] text-[#6B6661]">{s}</p>
                  </div>
                ))}
                {improveResult.can_apply && improveResult.apply_prompt && (
                  <button
                    onClick={() => handleApply(improveResult.apply_prompt)}
                    className="mt-2 flex items-center gap-1.5 text-[10px] font-semibold text-violet-600 bg-violet-50 hover:bg-violet-100 px-3 py-1.5 rounded-lg transition-colors"
                    data-testid="improve-apply-btn"
                  >
                    <Sparkles className="w-3 h-3" />Aplicar ao roteiro
                  </button>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Optimize result overlay */}
          <AnimatePresence>
            {optimizeResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute top-3 left-3 right-3 bg-white/95 backdrop-blur-sm rounded-xl p-3 shadow-lg border border-violet-200 z-[1000]"
                data-testid="optimize-result"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-500" />
                    <p className="text-[11px] font-bold text-[#2D2A26]">Percurso otimizado</p>
                  </div>
                  <button onClick={() => setOptimizeResult(null)} className="text-stone-400 hover:text-stone-600"><X className="w-3.5 h-3.5" /></button>
                </div>
                <p className="text-[10px] text-[#6B6661] mb-1.5">{optimizeResult.savings}</p>
                {optimizeResult.tips?.map((t, i) => (
                  <div key={i} className="flex items-start gap-1.5 mb-0.5">
                    <ArrowRight className="w-3 h-3 text-violet-500 shrink-0 mt-0.5" />
                    <p className="text-[10px] text-[#6B6661]">{t}</p>
                  </div>
                ))}
                <button
                  onClick={() => handleApply(`Reordena as atividades do Dia ${selectedDay || 1} para: ${optimizeResult.optimized_order?.join(', ')}`)}
                  className="mt-2 flex items-center gap-1.5 text-[10px] font-semibold text-violet-600 bg-violet-50 hover:bg-violet-100 px-3 py-1.5 rounded-lg transition-colors"
                  data-testid="optimize-apply-btn"
                >
                  <Sparkles className="w-3 h-3" />Aplicar ao roteiro
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Mobile bottom sheet trigger */}
      {isMobile && (
        <button
          onClick={() => setMobileSheet(!mobileSheet)}
          className="w-full flex items-center justify-center gap-2 py-2.5 border-t border-stone-100 text-[11px] font-semibold text-[#6B6661]"
          data-testid="mobile-sheet-toggle"
        >
          {mobileSheet ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          {mobileSheet ? 'Fechar lista' : `${filteredLocations.length} locais`}
        </button>
      )}

      {/* Mobile bottom sheet */}
      <AnimatePresence>
        {isMobile && mobileSheet && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden border-t border-stone-100"
          >
            <div className="max-h-[40vh] overflow-y-auto" data-testid="mobile-sheet">
              {filteredDays.map(dayGroup => (
                <div key={dayGroup.day}>
                  <div className="px-4 py-1.5 bg-stone-50 sticky top-0 z-10">
                    <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: DAY_COLORS[(dayGroup.day - 1) % DAY_COLORS.length] }}>
                      Dia {dayGroup.day} — {dayGroup.title}
                    </span>
                  </div>
                  {dayGroup.locations.map((loc, i) => (
                    <button
                      key={`m-${dayGroup.day}-${i}`}
                      onClick={() => { handleLocationClick(loc); setMobileSheet(false); }}
                      className="w-full text-left px-4 py-2.5 flex items-center gap-3 border-b border-stone-50 active:bg-[#FFBE98]/5"
                    >
                      <span className="text-xs font-bold shrink-0" style={{ color: DAY_COLORS[(dayGroup.day - 1) % DAY_COLORS.length] }}>
                        {i + 1}
                      </span>
                      <span className="text-xs text-[#2D2A26]">{loc.name}</span>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
    </div>
  );
};

export default SmartMap;
