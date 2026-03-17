import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { 
  ArrowDown, Users, Star, MapPin, Map, Hotel, Plane, 
  Sparkles, ChevronDown, ExternalLink, Compass, Globe, 
  Heart, Bitcoin, Clock, Camera, ChevronRight, Play, CheckCircle
} from 'lucide-react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import CheckoutModal from '../components/CheckoutModal';
import TestimonialsSection from '../components/TestimonialsSection';
import StoryChapter from '../components/StoryChapter';
import MilestoneProgress from '../components/MilestoneProgress';
import MilestoneCelebration from '../components/MilestoneCelebration';

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
  const { t, language, translateDynamic } = useLanguage();
  const { user, getAuthHeaders } = useAuth();
  const [mainJourney, setMainJourney] = useState(null);
  const [ambassadorJourneys, setAmbassadorJourneys] = useState(null);
  const [realizedJourneys, setRealizedJourneys] = useState(null);
  const [curatedDreams, setCuratedDreams] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dreamersStats, setDreamersStats] = useState(null);
  const [platformStats, setPlatformStats] = useState(null);
  const [showCheckout, setShowCheckout] = useState(false);
  const [showStickyBar, setShowStickyBar] = useState(false);
  
  // Translated dynamic content from DB
  const [dynTexts, setDynTexts] = useState({});
  const lastTransLang = useRef('pt');
  
  // Travel planner state
  const [customDestination, setCustomDestination] = useState('');
  const [travelResources, setTravelResources] = useState(null);
  const [expandedSection, setExpandedSection] = useState(null);
  const [loadingResources, setLoadingResources] = useState(false);

  // Scroll to section if coming from another page with ?scrollTo=
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const scrollTo = params.get('scrollTo');
    if (scrollTo) {
      setTimeout(() => {
        document.getElementById(scrollTo)?.scrollIntoView({ behavior: 'smooth' });
        window.history.replaceState({}, '', '/');
      }, 500);
    }
  }, []);

  // Sticky bar scroll listener
  useEffect(() => {
    const handleScroll = () => setShowStickyBar(window.scrollY > 600);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        await axios.post(`${API}/seed-journeys`).catch(() => {});
        
        const [mainRes, ambassadorRes, realizedRes, curatedRes, dreamersRes, platformRes] = await Promise.all([
          axios.get(`${API}/homepage/main-journey`),
          axios.get(`${API}/homepage/ambassador-journeys`),
          axios.get(`${API}/homepage/realized-journeys`),
          axios.get(`${API}/homepage/curated-dreams`),
          axios.get(`${API}/dreamers-stats`),
          axios.get(`${API}/platform/stats`).catch(() => ({ data: null }))
        ]);
        
        setMainJourney(mainRes.data);
        setAmbassadorJourneys(ambassadorRes.data);
        setRealizedJourneys(realizedRes.data);
        setCuratedDreams(curatedRes.data);
        setDreamersStats(dreamersRes.data);
        setPlatformStats(platformRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Translate dynamic DB content when language or data changes
  const translateContent = useCallback(async () => {
    if (language === 'pt') {
      setDynTexts({});
      lastTransLang.current = 'pt';
      return;
    }
    if (language === lastTransLang.current) return;
    
    const toTranslate = {};
    if (mainJourney?.journey) {
      const j = mainJourney.journey;
      if (j.poetic_name) toTranslate['main.poetic'] = j.poetic_name;
      if (j.emotional_message) toTranslate['main.emotional'] = j.emotional_message;
    }
    if (curatedDreams?.message) toTranslate['curated.message'] = curatedDreams.message;
    if (curatedDreams?.curated_dreams) {
      curatedDreams.curated_dreams.forEach((dream, i) => {
        if (dream.name) toTranslate[`curated.${i}.name`] = dream.name;
        if (dream.country) toTranslate[`curated.${i}.country`] = dream.country;
        if (dream.story) toTranslate[`curated.${i}.story`] = dream.story;
      });
    }
    
    if (Object.keys(toTranslate).length === 0) return;
    const translated = await translateDynamic(toTranslate);
    if (translated) {
      setDynTexts(translated);
      lastTransLang.current = language;
    }
  }, [language, mainJourney, curatedDreams, translateDynamic]);

  useEffect(() => {
    if (!loading) translateContent();
  }, [loading, language, translateContent]);

  // Helper to get dynamic translated text
  const d = useCallback((key, fallback) => dynTexts[key] || fallback, [dynTexts]);

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
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1 }}
            className="text-sm md:text-base text-[#6B6661]/70 italic mb-6" data-testid="opening-question">
            E se os sonhos pudessem ser financiados por todos?
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}>
            <h1 className="tracking-tight mb-6">
              <span className="font-handwritten text-6xl md:text-8xl text-[#FFBE98] block mb-4">4Luis</span>
              <span className="font-handwritten text-4xl md:text-6xl text-[#FFBE98] whitespace-nowrap" style={{ fontWeight: 700 }}>{t('hero.tagline')}</span>
            </h1>
          </motion.div>

          <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl md:text-2xl text-[#6B6661] mb-12 max-w-2xl mx-auto leading-relaxed">
            A plataforma de <span className="font-bold text-[#FFBE98]">CrowdDreaming</span> para quem acredita que os sonhos se podem concretizar.
          </motion.p>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.4 }}>
            <button onClick={scrollToMain} className="btn-primary text-lg" data-testid="discover-btn">
              {t('hero.cta')}
            </button>
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}
            className="mt-8 flex flex-col sm:flex-row items-center gap-3 sm:gap-6" data-testid="trust-signals">
            {['Pagamentos diretos ao sonhador', 'Sem comissões da plataforma', 'Clube de sonhadores'].map((text) => (
              <span key={text} className="flex items-center gap-1.5 text-sm text-[#6B6661]">
                <CheckCircle className="w-4 h-4 text-[#FFBE98]" />
                {text}
              </span>
            ))}
          </motion.div>

          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }} className="absolute bottom-10 left-1/2 -translate-x-1/2">
            <motion.div animate={{ y: [0, 10, 0] }} transition={{ repeat: Infinity, duration: 2 }}>
              <ArrowDown className="w-6 h-6 text-[#FFBE98]" />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ==================== COMO FUNCIONA + PROVA SOCIAL ==================== */}
      <section className="py-16 bg-[#FAFAF9]" data-testid="how-it-works-section">
        <div className="max-w-5xl mx-auto px-6">
          {/* How it Works */}
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-center mb-10">
            <h2 className="text-3xl font-bold text-[#2D2A26]">Como funciona o <span className="text-[#FFBE98]">CrowdDreaming</span></h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-stone-100 text-center">
              <div className="w-14 h-14 bg-[#FFBE98]/15 rounded-full flex items-center justify-center mx-auto mb-4">
                <Heart className="w-7 h-7 text-[#FFBE98]" />
              </div>
              <div className="w-8 h-8 bg-[#2D2A26] rounded-full flex items-center justify-center mx-auto mb-3 text-white text-sm font-bold">1</div>
              <p className="text-base font-semibold text-[#2D2A26]">{t('home.step1_title')}</p>
              <p className="text-sm text-[#6B6661] mt-2">{t('home.step1_desc')}</p>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-stone-100 text-center">
              <div className="w-14 h-14 bg-[#E6F4F1] rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-7 h-7 text-[#2D2A26]" />
              </div>
              <div className="w-8 h-8 bg-[#2D2A26] rounded-full flex items-center justify-center mx-auto mb-3 text-white text-sm font-bold">2</div>
              <p className="text-base font-semibold text-[#2D2A26]">{t('home.step2_title')}</p>
              <p className="text-sm text-[#6B6661] mt-2">{t('home.step2_desc')}</p>
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.3 }}
              className="bg-white rounded-2xl p-6 shadow-sm border border-stone-100 text-center">
              <div className="w-14 h-14 bg-[#F2C94C]/15 rounded-full flex items-center justify-center mx-auto mb-4">
                <Star className="w-7 h-7 text-[#F2C94C]" />
              </div>
              <div className="w-8 h-8 bg-[#2D2A26] rounded-full flex items-center justify-center mx-auto mb-3 text-white text-sm font-bold">3</div>
              <p className="text-base font-semibold text-[#2D2A26]">{t('home.step3_title')}</p>
              <p className="text-sm text-[#6B6661] mt-2">{t('home.step3_desc')}</p>
            </motion.div>
          </div>

          {/* CTA Button - direct to main journey checkout */}
          {mainJourney?.journey && (
            <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.4 }}
              className="text-center mt-10">
              <Link to={`/journey/${mainJourney.journey.journey_id}?pay=true`}
                className="inline-flex items-center gap-2 px-8 py-3.5 bg-[#2D2A26] text-white rounded-xl font-semibold hover:bg-[#4A4640] transition-colors text-base"
                data-testid="howit-works-cta"
              >
                <Heart className="w-5 h-5" />
                {t('home.support_dream')}
              </Link>
            </motion.div>
          )}
        </div>
      </section>

      {/* ==================== 1. VIAGEM PRINCIPAL ==================== */}
      <section id="main-journey" className="relative scroll-mt-16" data-testid="main-journey-section">
        {mainJourney?.journey ? (
          <>
            {/* Immersive Hero Card */}
            <div className="relative min-h-[60vh] flex items-end overflow-hidden">
              <img src={mainJourney.journey.image_url} alt={mainJourney.journey.name}
                className="absolute inset-0 w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-black/10" />
              
              <div className="relative z-10 w-full max-w-5xl mx-auto px-6 pb-8 pt-10">
                <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                  <div className="flex justify-center mb-4">
                    <Link to={`/journey/${mainJourney.journey.journey_id}`}
                      className="group relative inline-flex items-center gap-3 px-8 py-3.5 rounded-full font-bold text-lg text-white border-2 border-[#FFBE98]/60 hover:border-[#FFBE98] transition-all duration-500 overflow-hidden shadow-[0_0_25px_rgba(255,190,152,0.3)] hover:shadow-[0_0_40px_rgba(255,190,152,0.5)] hover:scale-105"
                      data-testid="main-journey-label"
                    >
                      <span className="absolute inset-0 bg-gradient-to-r from-[#FFBE98]/30 via-[#F2C94C]/20 to-[#FFBE98]/30 backdrop-blur-md" />
                      <span className="absolute inset-0 bg-gradient-to-r from-[#FFBE98]/40 via-transparent to-[#F2C94C]/40 animate-pulse" style={{ animationDuration: '2s' }} />
                      <span className="absolute -inset-1 bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full opacity-20 blur-lg group-hover:opacity-40 transition-opacity duration-500" />
                      <Sparkles className="w-5 h-5 text-[#FFBE98] relative z-10 group-hover:rotate-12 group-hover:scale-110 transition-all duration-300 drop-shadow-[0_0_6px_rgba(255,190,152,0.8)]" />
                      <span className="relative z-10 tracking-wider uppercase text-shadow">{t('home.main_journey')}</span>
                      <span className="relative z-10 w-2 h-2 rounded-full bg-[#FFBE98] animate-pulse shadow-[0_0_8px_rgba(255,190,152,0.8)]" />
                    </Link>
                  </div>
                  
                  <h2 className="text-5xl md:text-7xl font-bold text-white mb-2">
                    {mainJourney.journey.name}
                  </h2>
                  <p className="font-handwritten text-3xl md:text-4xl text-[#FFBE98] mb-4">
                    {d('main.poetic', mainJourney.journey.poetic_name)}
                  </p>

                  <div className="flex flex-col md:flex-row gap-6 md:items-start">
                    {/* Left: Chapter + Progress */}
                    <div className="flex-1">
                      <div className="max-w-lg mb-5">
                        <StoryChapter
                          percentage={mainJourney.progress?.percentage || 0}
                          customChapters={mainJourney.journey.story_chapters}
                          variant="dark"
                        />
                      </div>

                      {mainJourney.progress && (
                        <div className="max-w-md">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-white/70 text-sm">{t('home.progress')}</span>
                            <span className="text-white font-bold text-lg">{mainJourney.progress.percentage}% <span className="text-white/60 text-sm font-normal">{t('home.funded')}</span></span>
                          </div>
                          <div className="h-2.5 bg-white/15 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              whileInView={{ width: `${Math.min(mainJourney.progress.percentage, 100)}%` }}
                              viewport={{ once: true }}
                              transition={{ duration: 1.5, ease: "easeOut" }}
                              className={`h-full rounded-full ${mainJourney.progress.is_funded ? 'bg-green-400' : 'bg-gradient-to-r from-[#FFBE98] to-[#F2C94C]'}`}
                            />
                          </div>
                          {mainJourney.progress.is_funded && (
                            <p className="text-green-400 text-sm mt-2 flex items-center gap-2">
                              <Sparkles className="w-4 h-4" /> {t('home.goal_reached')}
                            </p>
                          )}
                          {!mainJourney.progress.is_funded && (
                            <MilestoneProgress progressPercentage={mainJourney.progress.percentage} variant="dark" />
                          )}
                        </div>
                      )}
                    </div>

                    {/* Right: CTA aligned with chapter */}
                    <div className="md:w-72 flex flex-col items-start md:items-center justify-start md:pt-4">
                      <p className="text-white/70 text-sm italic mb-4 text-center" data-testid="micro-question">
                        Queres ajudar este sonho a dar o próximo passo?
                      </p>
                      <button
                        onClick={() => setShowCheckout(true)}
                        className="inline-flex items-center gap-2 px-8 py-4 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-lg hover:bg-[#FFAB7D] transition-colors"
                        data-testid="contribute-main-btn">
                        <Heart className="w-5 h-5" /> {t('home.contribute_dream')}
                      </button>
                      {mainJourney.contributor_count > 0 && (
                        <p className="text-white/50 text-xs mt-3 text-center" data-testid="social-proof-line">
                          <Sparkles className="w-3 h-3 inline mr-1 opacity-70" />
                          Mais de {mainJourney.contributor_count} sonhadores já contribuíram para este sonho
                        </p>
                      )}
                    </div>
                  </div>
                </motion.div>
              </div>
            </div>

            {/* Milestone Celebration Banner */}
            <div className="max-w-5xl mx-auto px-6 pt-8">
              <MilestoneCelebration journey={mainJourney.journey} customChapters={mainJourney.journey?.story_chapters} />
            </div>

            {/* Contributions Feed */}
            {mainJourney.contributions?.length > 0 && (
              <div className="bg-white py-12">
                <div className="max-w-6xl mx-auto px-6">
                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                  className="bg-[#FAFAF9] rounded-2xl p-6 md:p-8">
                  <h3 className="text-xl font-bold text-[#2D2A26] mb-6 flex items-center gap-2">
                    <Heart className="w-5 h-5 text-[#FFBE98]" /> {t('home.latest_contributions')}
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
                    {t('home.view_all_contributions')} →
                  </Link>
                </motion.div>
                </div>
              </div>
            )}
            </>
          ) : (
            <div className="text-center py-20">
              <p className="text-[#6B6661]">{t('home.no_main_journey')}</p>
            </div>
          )}
      </section>

      {/* ==================== 2. PLANEIA A TUA VIAGEM ==================== */}
      <section className="py-16 bg-white" data-testid="plan-trip-section">
        <div className="max-w-5xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Map className="w-6 h-6 text-[#FFBE98]" />
              <h2 className="text-3xl font-bold text-[#2D2A26]">{t('home.plan_trip')}</h2>
            </div>
            <p className="text-[#6B6661] mb-2">{t('home.plan_trip_intro')}</p>
            <p className="text-sm text-[#6B6661]/70 mb-6">{t('home.plan_trip_desc')}</p>
            
            <div className="max-w-md mx-auto flex gap-2">
              <input type="text" value={customDestination} onChange={(e) => setCustomDestination(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchDestination()}
                placeholder={t('home.plan_placeholder')}
                className="flex-1 px-4 py-3 rounded-xl border border-stone-200 bg-white text-[#2D2A26] focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
              />
              <button onClick={searchDestination} disabled={!customDestination.trim() || loadingResources}
                className="px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium hover:bg-[#FFAB7D] transition-colors disabled:opacity-50">
                {loadingResources ? '...' : t('home.search')}
              </button>
            </div>
          </motion.div>

          {travelResources && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
              <p className="text-center text-sm text-[#6B6661] mb-4">
                {t('home.resources_for')} <span className="font-semibold text-[#2D2A26]">{travelResources.destination}</span>
              </p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <a href={travelResources.map?.url} target="_blank" rel="noopener noreferrer"
                  className="bg-stone-50 rounded-xl p-4 hover:bg-stone-100 transition-colors text-center">
                  <Map className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">{travelResources.map?.title || t('home.map')}</p>
                </a>

                <div className="bg-stone-50 rounded-xl p-4 cursor-pointer hover:bg-stone-100 transition-colors text-center"
                  onClick={() => setExpandedSection(expandedSection === 'hotels' ? null : 'hotels')}>
                  <Hotel className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">{t('home.where_to_stay')}</p>
                  <p className="text-xs text-[#6B6661]">{travelResources.hotels?.length} {t('home.options')}</p>
                </div>

                <div className="bg-stone-50 rounded-xl p-4 cursor-pointer hover:bg-stone-100 transition-colors text-center"
                  onClick={() => setExpandedSection(expandedSection === 'flights' ? null : 'flights')}>
                  <Plane className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">{t('home.flights')}</p>
                  <p className="text-xs text-[#6B6661]">{travelResources.flights?.length} {t('home.airlines')}</p>
                </div>

                <div className="bg-stone-50 rounded-xl p-4 cursor-pointer hover:bg-stone-100 transition-colors text-center"
                  onClick={() => setExpandedSection(expandedSection === 'social' ? null : 'social')}>
                  <Compass className="w-6 h-6 text-[#FFBE98] mx-auto mb-2" />
                  <p className="text-sm font-medium text-[#2D2A26]">{t('home.resources')}</p>
                  <p className="text-xs text-[#6B6661]">{travelResources.social?.length} {t('home.sites')}</p>
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
      <section id="journeys" className="py-16 bg-[#FAFAF9]" data-testid="materializing-dreams-section">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-[#E6F4F1] rounded-full text-[#2D2A26] font-medium text-sm mb-4">
              <Sparkles className="w-4 h-4 inline mr-2" />
              {t('home.ambassador_journeys')}
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4">
              {t('home.materializing_dreams')}
            </h2>
            <p className="text-[#6B6661] max-w-xl mx-auto">
              {t('home.help_dreamers')}
            </p>
          </motion.div>

          {(() => {
            const allJourneys = [
              ...(ambassadorJourneys?.featured || []),
              ...Object.values(ambassadorJourneys?.regions || {}).flatMap(r => r.journeys || [])
            ];
            const displayJourneys = allJourneys.slice(0, 4);

            if (displayJourneys.length === 0) {
              return (
                <div className="text-center py-16 bg-white rounded-2xl">
                  <Globe className="w-16 h-16 text-[#E6F4F1] mx-auto mb-4" />
                  <p className="text-[#6B6661] mb-4">{t('home.no_ambassador_journeys')}</p>
                  <p className="text-sm text-[#6B6661]">{t('home.become_ambassador')}</p>
                </div>
              );
            }

            return (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                  {displayJourneys.map((journey, idx) => {
                    const pct = journey.progress_percentage || 0;
                    return (
                      <motion.div
                        key={journey.journey_id}
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: idx * 0.1 }}
                      >
                        <Link
                          to={`/journey/${journey.journey_id}`}
                          className="block bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 group h-full"
                          data-testid={`dream-card-${journey.journey_id}`}
                        >
                          {/* Image */}
                          <div className="relative h-48 overflow-hidden">
                            <img
                              src={journey.image_url}
                              alt={journey.name}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                            <div className="absolute bottom-3 left-4 right-4">
                              <h4 className="text-lg font-bold text-white leading-tight">{journey.name}</h4>
                            </div>
                          </div>

                          {/* Content */}
                          <div className="p-4">
                            <p className="text-sm text-[#6B6661] mb-3 font-medium">
                              Sonho de <span className="text-[#2D2A26] font-semibold">{journey.ambassador_name}</span>
                            </p>

                            {/* Progress Bar */}
                            <div className="mb-2">
                              <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] rounded-full transition-all duration-700"
                                  style={{ width: `${Math.min(pct, 100)}%` }}
                                />
                              </div>
                            </div>

                            <div className="flex items-center justify-between">
                              <span className="text-sm font-bold text-[#FFBE98]">{Math.round(pct)}% financiado</span>
                              <span className="text-xs text-[#FFBE98] font-semibold group-hover:translate-x-1 transition-transform flex items-center gap-1">
                                Descobre <ChevronRight className="w-3 h-3" />
                              </span>
                            </div>
                          </div>
                        </Link>
                      </motion.div>
                    );
                  })}
                </div>

                {allJourneys.length > 4 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    className="text-center mt-10"
                  >
                    <Link
                      to="/journeys"
                      className="inline-flex items-center gap-2 px-8 py-3 bg-white border-2 border-[#FFBE98]/40 text-[#2D2A26] rounded-xl font-semibold hover:bg-[#FFBE98]/10 hover:border-[#FFBE98] transition-all"
                      data-testid="explore-more-dreams-btn"
                    >
                      <Compass className="w-5 h-5 text-[#FFBE98]" />
                      Explorar mais sonhos
                    </Link>
                  </motion.div>
                )}
              </>
            );
          })()}
        </div>
      </section>

      {/* ==================== 4. SONHOS REALIZADOS ==================== */}
      <section className="py-16 bg-white" data-testid="realized-dreams-section">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-12">
            <span className="inline-block px-4 py-2 bg-green-100 rounded-full text-green-700 font-medium text-sm mb-4">
              <Camera className="w-4 h-4 inline mr-2" />
              {t('home.real_stories')}
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4">
              {t('home.realized_dreams')}
            </h2>
            <p className="text-[#6B6661] max-w-xl mx-auto">
              {t('home.realized_desc')}
            </p>
          </motion.div>

          {/* Show curated content if no real journeys */}
          {curatedDreams?.use_curated ? (
            <div>
              <p className="text-center text-sm text-[#FFBE98] mb-8 italic">
                {d('curated.message', curatedDreams.message)}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {curatedDreams.curated_dreams.map((dream, idx) => (
                  <motion.div key={dream.id} initial={{ opacity: 0, scale: 0.95 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
                    className="bg-[#FAFAF9] rounded-2xl overflow-hidden group">
                    <div className="relative h-48 overflow-hidden">
                      <img src={dream.image_url} alt={dream.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                      <div className="absolute bottom-4 left-4 right-4">
                        <p className="text-white font-bold">{d(`curated.${idx}.name`, dream.name)}</p>
                        <p className="text-white/80 text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {d(`curated.${idx}.country`, dream.country)}
                        </p>
                      </div>
                      <span className="absolute top-4 right-4 px-2 py-1 bg-white/20 backdrop-blur text-white text-xs rounded-full">
                        {t('home.inspiration')}
                      </span>
                    </div>
                    <div className="p-4">
                      <p className="text-sm text-[#6B6661] italic">"{d(`curated.${idx}.story`, dream.story)}"</p>
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
                    <span className="text-sm text-[#6B6661]">({data.journeys.length} {data.journeys.length === 1 ? t('home.dream_singular') : t('home.dream_plural')})</span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {data.journeys.map((journey) => (
                      <Link to={`/journey/${journey.journey_id}`} key={journey.journey_id} className="bg-[#FAFAF9] rounded-2xl overflow-hidden group hover:shadow-lg transition-all duration-300 cursor-pointer">
                        <div className="relative h-48 overflow-hidden">
                          <img src={journey.image_url} alt={journey.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                          <div className="absolute bottom-4 left-4 right-4">
                            <p className="text-white font-bold">{journey.name}</p>
                            {journey.ambassador_name && (
                            <p className="text-white/80 text-sm">{t('home.by')} {journey.ambassador_name}</p>
                            )}
                          </div>
                          <span className="absolute top-4 right-4 px-2 py-1 bg-green-500 text-white text-xs rounded-full flex items-center gap-1">
                            <Check className="w-3 h-3" /> {t('home.realized')}
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
                      </Link>
                    ))}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 bg-[#FAFAF9] rounded-2xl">
              <Camera className="w-16 h-16 text-stone-200 mx-auto mb-4" />
              <p className="text-[#6B6661]">{t('home.no_realized')}</p>
              <p className="text-sm text-[#6B6661] mt-2">{t('home.be_first')}</p>
            </div>
          )}
        </div>
      </section>

      {/* Testimonials */}
      <TestimonialsSection />

      {/* About 4Luis - lightweight block */}
      <section className="py-10 bg-white" data-testid="about-block">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h3 className="text-lg font-bold text-[#2D2A26] mb-3">Sobre a 4Luis</h3>
          <p className="text-sm text-[#6B6661] leading-relaxed mb-4">
            A 4Luis nasceu de uma ideia simples:<br />
            E se fosse possível criar uma comunidade<br />
            onde as pessoas ajudam outras a realizar os seus sonhos?
          </p>
          <Link to="/about" className="text-sm text-[#FFBE98] hover:text-[#E6A07C] font-medium transition-colors" data-testid="about-link">
            Saber mais →
          </Link>
        </div>
      </section>

      {/* Emotional Quote */}
      <section className="py-16 bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/30">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
            <p className="font-handwritten text-3xl md:text-4xl text-[#6B6661] leading-relaxed">
              "{t('home.quote1')}<br /><br />
              <span className="text-[#FFBE98]">{t('home.quote2')}</span><br />
              {t('home.quote3')}"
            </p>
          </motion.div>
        </div>
      </section>

      {/* Sticky Contribution Bar */}
      <AnimatePresence>
        {showStickyBar && mainJourney?.journey && !showCheckout && (
          <motion.div
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-stone-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
            data-testid="home-sticky-bar"
          >
            <div className="max-w-5xl mx-auto px-4 md:px-6 py-3 flex items-center gap-3 md:gap-5">
              <div className="flex-1 min-w-0 hidden sm:block">
                <p className="text-sm font-bold text-[#2D2A26] truncate">
                  {mainJourney.journey.name} — <span className="font-handwritten text-[#FFBE98]">{d('main.poetic', mainJourney.journey.poetic_name)}</span>
                </p>
                <div className="flex items-center gap-3 mt-1">
                  {mainJourney.progress && (
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden w-[140px]">
                        <div className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full" style={{ width: `${Math.min(100, mainJourney.progress.percentage)}%` }} />
                      </div>
                      <span className="text-xs font-semibold text-[#6B6661]">{mainJourney.progress.percentage}%</span>
                    </div>
                  )}
                  {dreamersStats?.total_dreamers > 0 && (
                    <span className="hidden md:flex items-center gap-1.5 text-xs text-[#6B6661]" data-testid="sticky-dreamers-count">
                      <Users className="w-3 h-3 text-[#FFBE98]" />
                      <span className="font-semibold text-[#2D2A26]">{dreamersStats.total_dreamers}</span> sonhadores
                    </span>
                  )}
                </div>
              </div>
              <div className="flex-1 flex justify-center sm:justify-end sm:pr-[180px]">
                <button
                  onClick={() => setShowCheckout(true)}
                  className="w-full sm:w-auto py-3 px-6 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#FFAB7D] transition-colors"
                  data-testid="home-sticky-contribute-btn"
                >
                  <Heart className="w-4 h-4" />
                  {t('home.contribute_dream')}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Checkout Modal */}
      {mainJourney?.journey && (
        <CheckoutModal
          isOpen={showCheckout}
          onClose={() => setShowCheckout(false)}
          journeyName={mainJourney.journey.name}
          journeyId={mainJourney.journey.journey_id}
          contributionDescriptions={mainJourney.journey.contribution_descriptions}
          getAuthHeaders={getAuthHeaders}
          user={user}
        />
      )}
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
