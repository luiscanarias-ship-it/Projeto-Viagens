import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  ArrowDown, Users, Star, MapPin, Map, Hotel, Plane, 
  Sparkles, ChevronDown, ExternalLink, Compass, Globe, 
  Heart, Bitcoin, Clock, Camera, ChevronRight, Play
} from 'lucide-react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Region icons/colors
const REGION_CONFIG = {
  europa: { color: '#3B82F6', emoji: '🇪🇺' },
  asia: { color: '#EF4444', emoji: '🌏' },
  africa: { color: '#F59E0B', emoji: '🌍' },
  americas: { color: '#10B981', emoji: '🌎' },
  oceania: { color: '#8B5CF6', emoji: '🏝️' },
  outro: { color: '#6B7280', emoji: '🌐' }
};

const Home = () => {
  const { t } = useLanguage();
  const [mainJourney, setMainJourney] = useState(null);
  const [ambassadorJourneys, setAmbassadorJourneys] = useState(null);
  const [realizedJourneys, setRealizedJourneys] = useState(null);
  const [curatedDreams, setCuratedDreams] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dreamersStats, setDreamersStats] = useState(null);
  
  // Travel planner state
  const [customDestination, setCustomDestination] = useState('');
  const [travelResources, setTravelResources] = useState(null);
  const [expandedSection, setExpandedSection] = useState(null);
  const [loadingResources, setLoadingResources] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        await axios.post(`${API}/seed-journeys`).catch(() => {});
        
        const [mainRes, ambassadorRes, realizedRes, curatedRes, dreamersRes] = await Promise.all([
          axios.get(`${API}/homepage/main-journey`),
          axios.get(`${API}/homepage/ambassador-journeys`),
          axios.get(`${API}/homepage/realized-journeys`),
          axios.get(`${API}/homepage/curated-dreams`),
          axios.get(`${API}/dreamers-stats`)
        ]);
        
        setMainJourney(mainRes.data);
        setAmbassadorJourneys(ambassadorRes.data);
        setRealizedJourneys(realizedRes.data);
        setCuratedDreams(curatedRes.data);
        setDreamersStats(dreamersRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const searchDestination = async () => {
    if (!customDestination.trim()) return;
    setLoadingResources(true);
    setExpandedSection(null);
    
    try {
      const response = await axios.get(`${API}/travel-resources/${encodeURIComponent(customDestination.trim())}`);
      setTravelResources(response.data);
    } catch (error) {
      const destination = customDestination.trim();
      const destEncoded = encodeURIComponent(destination);
      const destPlus = destination.replace(/ /g, '+');
      
      setTravelResources({
        destination: destination,
        map: { title: "Bing Maps", url: `https://www.bing.com/maps?q=${destPlus}` },
        hotels: [
          { name: "Trivago", url: `https://www.trivago.pt/?search=${destPlus}` },
          { name: "TripAdvisor", url: `https://www.tripadvisor.pt/Search?q=${destPlus}` },
          { name: "Kayak", url: `https://www.kayak.pt/hotels` },
          { name: "Airbnb", url: `https://www.airbnb.pt/s/${destEncoded}/homes` },
          { name: "ALL Accor", url: "https://all.accor.com/pt-pt/world/index.shtml" }
        ],
        flights: [
          { name: "TAP", url: "https://www.flytap.com/pt-pt" },
          { name: "Ryanair", url: "https://www.ryanair.com/pt/pt" },
          { name: "EasyJet", url: "https://www.easyjet.com/pt" },
          { name: "Momondo", url: "https://www.momondo.pt" }
        ],
        social: [
          { name: "GetYourGuide", url: `https://www.getyourguide.pt/s/?q=${destPlus}`, description: "Tours e atividades" },
          { name: "Pinterest", url: `https://www.pinterest.pt/search/pins/?q=${destPlus}%20travel`, description: "Inspiração visual" },
          { name: "WikiVoyage", url: `https://pt.wikivoyage.org/wiki/${destEncoded}`, description: "Guia colaborativo" },
          { name: "Reddit", url: `https://www.reddit.com/search/?q=${destPlus}%20travel`, description: "Experiências reais" }
        ]
      });
    } finally {
      setLoadingResources(false);
    }
  };

  const scrollToMain = () => {
    document.getElementById('main-journey')?.scrollIntoView({ behavior: 'smooth' });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAF9]">
        <div className="w-12 h-12 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="home-page">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center dream-mesh">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-64 h-64 bg-[#FFBE98]/20 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#E6F4F1]/40 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        </div>

        <div className="relative max-w-4xl mx-auto px-6 text-center pt-20">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <h1 className="text-5xl md:text-7xl font-bold text-[#2D2A26] tracking-tight mb-6">
              <span className="font-handwritten text-6xl md:text-8xl text-[#FFBE98] block mb-4">4Luis</span>
              {t('hero.tagline')}
            </h1>
          </motion.div>

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl md:text-2xl text-[#6B6661] mb-12 max-w-2xl mx-auto leading-relaxed">
            {t('hero.subtitle')}
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.4 }}>
            <button onClick={scrollToMain} className="btn-primary text-lg" data-testid="discover-btn">
              {t('hero.cta')}
            </button>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }} className="absolute bottom-10 left-1/2 -translate-x-1/2">
            <motion.div animate={{ y: [0, 10, 0] }} transition={{ repeat: Infinity, duration: 2 }}>
              <ArrowDown className="w-6 h-6 text-[#FFBE98]" />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ==================== 1. VIAGEM PRINCIPAL ==================== */}
      <section id="main-journey" className="py-16 md:py-24 bg-white" data-testid="main-journey-section">
        <div className="max-w-6xl mx-auto px-6">
          {mainJourney?.journey ? (
            <>
              {/* Journey Header */}
              <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-12">
                <span className="inline-block px-4 py-2 bg-[#FFBE98]/20 rounded-full text-[#FFBE98] font-medium text-sm mb-4">
                  Viagem Principal
                </span>
                <h2 className="text-4xl md:text-5xl font-bold text-[#2D2A26] mb-4">
                  {mainJourney.journey.name}
                </h2>
                <p className="font-handwritten text-2xl text-[#FFBE98] mb-6">
                  {mainJourney.journey.poetic_name}
                </p>
              </motion.div>

              {/* Live Experience Card */}
              <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                className="relative rounded-3xl overflow-hidden shadow-xl mb-12">
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent z-10" />
                <img src={mainJourney.journey.image_url} alt={mainJourney.journey.name}
                  className="w-full h-[400px] md:h-[500px] object-cover" />
                
                <div className="absolute bottom-0 left-0 right-0 p-8 z-20">
                  <p className="text-white/90 text-lg md:text-xl mb-6 max-w-2xl">
                    {mainJourney.journey.emotional_message}
                  </p>
                  
                  {/* Progress Bar */}
                  {mainJourney.progress && (
                    <div className="mb-6">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-white/80 text-sm">Progresso</span>
                        <div className="flex items-center gap-2">
                          {mainJourney.progress.show_goal_amount && mainJourney.progress.goal_amount ? (
                            <span className="text-white/80 text-sm">
                              €{mainJourney.progress.current_amount?.toLocaleString()} / €{mainJourney.progress.goal_amount?.toLocaleString()}
                            </span>
                          ) : null}
                          <span className="text-white font-bold text-lg">{mainJourney.progress.percentage}%</span>
                        </div>
                      </div>
                      <div className="h-3 bg-white/20 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: `${Math.min(mainJourney.progress.percentage, 100)}%` }}
                          viewport={{ once: true }}
                          transition={{ duration: 1.5, ease: "easeOut" }}
                          className={`h-full rounded-full ${mainJourney.progress.is_funded ? 'bg-green-400' : 'bg-[#FFBE98]'}`}
                        />
                      </div>
                      {mainJourney.progress.is_funded && (
                        <p className="text-green-400 text-sm mt-2 flex items-center gap-2">
                          <Sparkles className="w-4 h-4" /> Objetivo atingido! Ainda podes contribuir.
                        </p>
                      )}
                    </div>
                  )}
                  
                  <Link to={`/journey/${mainJourney.journey.journey_id}`}
                    className="inline-flex items-center gap-2 px-8 py-4 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold hover:bg-[#FFAB7D] transition-colors"
                    data-testid="contribute-main-btn">
                    <Heart className="w-5 h-5" /> Contribuir para este Sonho
                  </Link>
                </div>
              </motion.div>

              {/* Contributions Feed */}
              {mainJourney.contributions?.length > 0 && (
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                  className="bg-[#FAFAF9] rounded-2xl p-6 md:p-8">
                  <h3 className="text-xl font-bold text-[#2D2A26] mb-6 flex items-center gap-2">
                    <Heart className="w-5 h-5 text-[#FFBE98]" /> Últimas Contribuições
                  </h3>
                  <div className="space-y-4">
                    {mainJourney.contributions.slice(0, 5).map((contrib, idx) => (
                      <div key={idx} className="flex items-center gap-4 p-4 bg-white rounded-xl">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${contrib.is_crypto ? 'bg-gradient-to-br from-[#F7931A] to-[#627EEA]' : 'bg-[#E6F4F1]'}`}>
                          {contrib.is_crypto ? (
                            <Bitcoin className="w-6 h-6 text-white" />
                          ) : (
                            <Heart className="w-6 h-6 text-[#FFBE98]" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-[#2D2A26]">
                            {contrib.display_name}
                            {contrib.is_crypto && (
                              <span className="ml-2 text-xs px-2 py-1 bg-gradient-to-r from-[#F7931A]/10 to-[#627EEA]/10 text-[#F7931A] rounded-full">
                                {contrib.crypto_type?.toUpperCase()}
                              </span>
                            )}
                          </p>
                          {contrib.message && (
                            <p className="text-sm text-[#6B6661] italic">"{contrib.message}"</p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-[#2D2A26]">{contrib.amount}€</p>
                        </div>
                      </div>
                    ))}
                  </div>
                  <Link to={`/journey/${mainJourney.journey.journey_id}`}
                    className="block text-center mt-6 text-[#FFBE98] hover:text-[#E6A07C] font-medium">
                    Ver todas as contribuições →
                  </Link>
                </motion.div>
              )}
            </>
          ) : (
            <div className="text-center py-20">
              <p className="text-[#6B6661]">Nenhuma viagem principal ativa de momento.</p>
            </div>
          )}
        </div>
      </section>

      {/* Community Stats */}
      <section className="py-12 bg-gradient-to-r from-[#2D2A26] to-[#4A4640]" data-testid="community-section">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex flex-wrap items-center justify-center gap-12 text-white">
            <div className="text-center">
              <Users className="w-8 h-8 mx-auto mb-2 text-[#FFBE98]" />
              <p className="text-3xl font-bold">{dreamersStats?.total_dreamers || 0}</p>
              <p className="text-white/70">Sonhadores</p>
            </div>
            {dreamersStats?.top_dreamer && (
              <>
                <div className="w-px h-16 bg-white/20" />
                <div className="text-center">
                  <Star className="w-8 h-8 mx-auto mb-2 text-[#F2C94C]" />
                  <p className="text-xl font-bold">{dreamersStats.top_dreamer.name}</p>
                  <p className="text-white/70">Maior Sonhador</p>
                </div>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ==================== 2. PLANEIA A TUA VIAGEM ==================== */}
      <section className="py-16 bg-white" data-testid="plan-trip-section">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Map className="w-6 h-6 text-[#FFBE98]" />
              <h2 className="text-3xl font-bold text-[#2D2A26]">Planeia a Tua Viagem</h2>
            </div>
            <p className="text-[#6B6661] mb-6">Ferramentas úteis para planear a viagem dos teus sonhos</p>
            
            <div className="max-w-md mx-auto flex gap-2">
              <input type="text" value={customDestination} onChange={(e) => setCustomDestination(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchDestination()}
                placeholder="Escreve o teu destino... (ex: Paris, Tóquio)"
                className="flex-1 px-4 py-3 rounded-xl border border-stone-200 bg-white text-[#2D2A26] focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
              />
              <button onClick={searchDestination} disabled={!customDestination.trim() || loadingResources}
                className="px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium hover:bg-[#FFAB7D] transition-colors disabled:opacity-50">
                {loadingResources ? '...' : 'Pesquisar'}
              </button>
            </div>
          </motion.div>

          {travelResources && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
              <p className="text-center text-sm text-[#6B6661] mb-4">
                Recursos para: <span className="font-semibold text-[#2D2A26]">{travelResources.destination}</span>
              </p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <a href={travelResources.map?.url} target="_blank" rel="noopener noreferrer"
                  className="bg-stone-50 rounded-xl p-4 hover:bg-stone-100 transition-colors text-center">
                  <Map className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">{travelResources.map?.title || 'Mapa'}</p>
                </a>

                <div className="bg-stone-50 rounded-xl p-4 cursor-pointer hover:bg-stone-100 transition-colors text-center"
                  onClick={() => setExpandedSection(expandedSection === 'hotels' ? null : 'hotels')}>
                  <Hotel className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">Onde Ficar</p>
                  <p className="text-xs text-[#6B6661]">{travelResources.hotels?.length} opções</p>
                </div>

                <div className="bg-stone-50 rounded-xl p-4 cursor-pointer hover:bg-stone-100 transition-colors text-center"
                  onClick={() => setExpandedSection(expandedSection === 'flights' ? null : 'flights')}>
                  <Plane className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">Voos</p>
                  <p className="text-xs text-[#6B6661]">{travelResources.flights?.length} companhias</p>
                </div>

                <div className="bg-stone-50 rounded-xl p-4 cursor-pointer hover:bg-stone-100 transition-colors text-center"
                  onClick={() => setExpandedSection(expandedSection === 'social' ? null : 'social')}>
                  <Compass className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">Recursos</p>
                  <p className="text-xs text-[#6B6661]">{travelResources.social?.length} sites</p>
                </div>
              </div>

              <AnimatePresence>
                {expandedSection && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {travelResources[expandedSection]?.map((item, idx) => (
                      <a key={idx} href={item.url} target="_blank" rel="noopener noreferrer"
                        className="bg-white border border-stone-200 rounded-lg p-3 hover:border-[#FFBE98] transition-colors text-center">
                        <p className="text-sm font-medium text-[#2D2A26]">{item.name}</p>
                        {item.description && <p className="text-xs text-[#6B6661]">{item.description}</p>}
                      </a>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </section>

      {/* ==================== 3. SONHOS EM FASE DE MATERIALIZAÇÃO ==================== */}
      <section className="py-16 bg-[#FAFAF9]" data-testid="materializing-dreams-section">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-[#E6F4F1] rounded-full text-[#2D2A26] font-medium text-sm mb-4">
              <Sparkles className="w-4 h-4 inline mr-2" />
              Viagens dos Embaixadores
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4">
              Sonhos em Fase de Materialização
            </h2>
            <p className="text-[#6B6661] max-w-xl mx-auto">
              Ajuda outros sonhadores a concretizar as suas viagens de sonho
            </p>
          </motion.div>

          {ambassadorJourneys?.total_count > 0 ? (
            <div className="space-y-10">
              {/* Featured Journeys Section */}
              {ambassadorJourneys.featured?.length > 0 && (
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 bg-gradient-to-br from-[#F2C94C] to-[#FFBE98] rounded-full flex items-center justify-center">
                      <Star className="w-4 h-4 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-[#2D2A26]">Em Destaque</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {ambassadorJourneys.featured.map((journey) => (
                      <Link key={journey.journey_id} to={`/journey/${journey.journey_id}`}
                        className="bg-white rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all group border-2 border-[#FFBE98]/30">
                        <div className="relative h-56 overflow-hidden">
                          <img src={journey.image_url} alt={journey.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                          <div className="absolute top-4 left-4 px-3 py-1 bg-gradient-to-r from-[#F2C94C] to-[#FFBE98] rounded-full text-white text-sm font-medium flex items-center gap-1">
                            <Star className="w-3 h-3" /> Destaque
                          </div>
                          <div className="absolute top-4 right-4 px-3 py-1 bg-white/90 rounded-full text-sm font-medium">
                            {journey.progress_percentage}%
                          </div>
                          <div className="absolute bottom-4 left-4 right-4">
                            <h4 className="text-xl font-bold text-white mb-1">{journey.name}</h4>
                            <p className="text-white/80 text-sm">por {journey.ambassador_name}</p>
                          </div>
                        </div>
                        <div className="p-5">
                          <p className="text-sm text-[#6B6661] mb-4 line-clamp-2">{journey.description}</p>
                          <div className="h-3 bg-stone-100 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] rounded-full transition-all" 
                              style={{ width: `${journey.progress_percentage}%` }} />
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </motion.div>
              )}

              {/* Regular Journeys by Region */}
              {Object.entries(ambassadorJourneys.regions || {}).map(([regionKey, region]) => (
                <motion.div key={regionKey} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">{REGION_CONFIG[regionKey]?.emoji || '🌐'}</span>
                    <h3 className="text-xl font-bold text-[#2D2A26]">{region.name}</h3>
                    <span className="text-sm text-[#6B6661]">({region.journeys.length})</span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {region.journeys.map((journey) => (
                      <Link key={journey.journey_id} to={`/journey/${journey.journey_id}`}
                        className="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow group">
                        <div className="relative h-48 overflow-hidden">
                          <img src={journey.image_url} alt={journey.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                          <div className="absolute top-4 right-4 px-3 py-1 bg-white/90 rounded-full text-sm font-medium">
                            {journey.progress_percentage}%
                          </div>
                        </div>
                        <div className="p-5">
                          <h4 className="font-bold text-[#2D2A26] mb-1">{journey.name}</h4>
                          <p className="text-sm text-[#6B6661] mb-3 line-clamp-2">{journey.description}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-[#6B6661]">por {journey.ambassador_name}</span>
                            <div className="h-2 flex-1 mx-4 bg-stone-100 rounded-full overflow-hidden">
                              <div className="h-full bg-[#FFBE98] rounded-full" style={{ width: `${journey.progress_percentage}%` }} />
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-white rounded-2xl">
              <Globe className="w-16 h-16 text-[#E6F4F1] mx-auto mb-4" />
              <p className="text-[#6B6661] mb-4">Ainda não existem viagens de embaixadores em angariação.</p>
              <p className="text-sm text-[#6B6661]">Torna-te Embaixador para criar a tua viagem!</p>
            </div>
          )}
        </div>
      </section>

      {/* ==================== 4. SONHOS REALIZADOS ==================== */}
      <section className="py-16 bg-white" data-testid="realized-dreams-section">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-green-100 rounded-full text-green-700 font-medium text-sm mb-4">
              <Camera className="w-4 h-4 inline mr-2" />
              Histórias Reais
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4">
              Sonhos Realizados
            </h2>
            <p className="text-[#6B6661] max-w-xl mx-auto">
              Viagens que se tornaram realidade graças à comunidade 4Luis
            </p>
          </motion.div>

          {/* Show curated content if no real journeys */}
          {curatedDreams?.use_curated ? (
            <div>
              <p className="text-center text-sm text-[#FFBE98] mb-8 italic">
                {curatedDreams.message}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {curatedDreams.curated_dreams.map((dream) => (
                  <motion.div key={dream.id} initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
                    className="bg-[#FAFAF9] rounded-2xl overflow-hidden group">
                    <div className="relative h-48 overflow-hidden">
                      <img src={dream.image_url} alt={dream.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                      <div className="absolute bottom-4 left-4 right-4">
                        <p className="text-white font-bold">{dream.name}</p>
                        <p className="text-white/80 text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {dream.country}
                        </p>
                      </div>
                      <span className="absolute top-4 right-4 px-2 py-1 bg-white/20 backdrop-blur text-white text-xs rounded-full">
                        Inspiração
                      </span>
                    </div>
                    <div className="p-4">
                      <p className="text-sm text-[#6B6661] italic">"{dream.story}"</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          ) : realizedJourneys?.total_count > 0 ? (
            <div className="space-y-8">
              {Object.entries(realizedJourneys.countries || {}).map(([country, data]) => (
                <motion.div key={country} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                  <div className="flex items-center gap-3 mb-4">
                    <MapPin className="w-5 h-5 text-green-600" />
                    <h3 className="text-xl font-bold text-[#2D2A26]">{country}</h3>
                    <span className="text-sm text-[#6B6661]">({data.journeys.length} {data.journeys.length === 1 ? 'sonho' : 'sonhos'})</span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {data.journeys.map((journey) => (
                      <div key={journey.journey_id} className="bg-[#FAFAF9] rounded-2xl overflow-hidden group">
                        <div className="relative h-48 overflow-hidden">
                          <img src={journey.image_url} alt={journey.name}
                            className="w-full h-full object-cover" />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                          <div className="absolute bottom-4 left-4 right-4">
                            <p className="text-white font-bold">{journey.name}</p>
                            {journey.ambassador_name && (
                              <p className="text-white/80 text-sm">por {journey.ambassador_name}</p>
                            )}
                          </div>
                          <span className="absolute top-4 right-4 px-2 py-1 bg-green-500 text-white text-xs rounded-full flex items-center gap-1">
                            <Check className="w-3 h-3" /> Realizado
                          </span>
                        </div>
                        {journey.story && (
                          <div className="p-4">
                            <p className="text-sm text-[#6B6661] italic line-clamp-3">"{journey.story}"</p>
                          </div>
                        )}
                        {journey.photos?.length > 0 && (
                          <div className="px-4 pb-4 flex gap-2">
                            {journey.photos.slice(0, 3).map((photo, idx) => (
                              <img key={idx} src={photo} alt="" className="w-12 h-12 rounded-lg object-cover" />
                            ))}
                            {journey.photos.length > 3 && (
                              <div className="w-12 h-12 rounded-lg bg-stone-200 flex items-center justify-center text-sm text-[#6B6661]">
                                +{journey.photos.length - 3}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-[#FAFAF9] rounded-2xl">
              <Camera className="w-16 h-16 text-stone-200 mx-auto mb-4" />
              <p className="text-[#6B6661]">Ainda não existem sonhos realizados.</p>
              <p className="text-sm text-[#6B6661] mt-2">Sê o primeiro a completar uma viagem!</p>
            </div>
          )}
        </div>
      </section>

      {/* Emotional Quote */}
      <section className="py-16 bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/30">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <p className="font-handwritten text-3xl md:text-4xl text-[#6B6661] leading-relaxed">
              "Não é apenas crowdfunding,<br />
              <span className="text-[#FFBE98]">é crowddreaming.</span><br />
              Não é um donativo,<br />
              <span className="text-[#FFBE98]">é um gesto fraternal.</span>"
            </p>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

// Add missing Check icon import at the top
const Check = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

export default Home;
