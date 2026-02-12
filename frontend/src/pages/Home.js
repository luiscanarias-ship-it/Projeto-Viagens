import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowDown, Users, Star, Gift, Camera, MapPin } from 'lucide-react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import JourneyCard from '../components/JourneyCard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const { t } = useLanguage();
  const [journeys, setJourneys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dreamersStats, setDreamersStats] = useState(null);
  const [raffleStats, setRaffleStats] = useState(null);
  const [gallery, setGallery] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Seed if needed
        await axios.post(`${API}/seed-journeys`).catch(() => {});
        
        // Fetch all data in parallel
        const [journeysRes, dreamersRes, raffleRes, galleryRes] = await Promise.all([
          axios.get(`${API}/journeys`),
          axios.get(`${API}/dreamers-stats`),
          axios.get(`${API}/raffle-stats`),
          axios.get(`${API}/gallery`)
        ]);
        
        setJourneys(journeysRes.data);
        setDreamersStats(dreamersRes.data);
        setRaffleStats(raffleRes.data);
        setGallery(galleryRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const scrollToJourneys = () => {
    document.getElementById('journeys')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen" data-testid="home-page">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center dream-mesh">
        {/* Decorative elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-64 h-64 bg-[#FFBE98]/20 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#E6F4F1]/40 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        </div>

        <div className="relative max-w-4xl mx-auto px-6 text-center pt-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl font-bold text-[#2D2A26] tracking-tight mb-6">
              <span className="font-handwritten text-6xl md:text-8xl text-[#FFBE98] block mb-4">
                4Luis
              </span>
              {t('hero.tagline')}
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl md:text-2xl text-[#6B6661] mb-12 max-w-2xl mx-auto leading-relaxed"
          >
            {t('hero.subtitle')}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <button
              onClick={scrollToJourneys}
              className="btn-primary text-lg"
              data-testid="discover-btn"
            >
              {t('hero.cta')}
            </button>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="absolute bottom-10 left-1/2 -translate-x-1/2"
          >
            <motion.div
              animate={{ y: [0, 10, 0] }}
              transition={{ repeat: Infinity, duration: 2 }}
            >
              <ArrowDown className="w-6 h-6 text-[#FFBE98]" />
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Community Stats Section - Dreamers & Raffles */}
      <section className="py-16 bg-white border-b border-stone-100" data-testid="community-section">
        <div className="max-w-6xl mx-auto px-6">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <p className="font-handwritten text-2xl md:text-3xl text-[#FFBE98]">
              Cada contributo é um passo de luz.
            </p>
          </motion.div>

          {/* Stats - Only Dreamers (removed Raffles section) */}
          <div className="max-w-2xl mx-auto">
            {/* Dreamers */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-[#E6F4F1]/20 rounded-3xl p-8"
            >
              <div className="flex items-center justify-center gap-8 md:gap-12">
                {/* Total Dreamers */}
                <div className="text-center">
                  <div className="w-16 h-16 bg-[#E6F4F1] rounded-full flex items-center justify-center mx-auto mb-4">
                    <Users className="w-8 h-8 text-[#2D2A26]" />
                  </div>
                  <motion.p 
                    className="text-4xl md:text-5xl font-bold text-[#2D2A26] mb-2"
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ type: "spring", delay: 0.2 }}
                  >
                    {dreamersStats?.total_dreamers || 0}
                  </motion.p>
                  <p className="text-[#6B6661] font-medium">Sonhadores</p>
                </div>

                {/* Divider */}
                {dreamersStats?.top_dreamer && (
                  <div className="w-px h-24 bg-stone-200" />
                )}

                {/* Top Dreamer - Now based on points */}
                {dreamersStats?.top_dreamer && (
                  <div className="text-center">
                    <div className="w-16 h-16 bg-gradient-to-br from-[#F2C94C]/30 to-[#E0C097]/30 rounded-full flex items-center justify-center mx-auto mb-3 border-2 border-[#F2C94C]/40 overflow-hidden">
                      {dreamersStats.top_dreamer.avatar_url ? (
                        <img 
                          src={dreamersStats.top_dreamer.avatar_url} 
                          alt="" 
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <Star className="w-8 h-8 text-[#F2C94C]" />
                      )}
                    </div>
                    <p className="text-sm text-[#6B6661] mb-1">O Maior Sonhador</p>
                    <motion.p 
                      className="text-xl font-bold text-[#2D2A26]"
                      initial={{ scale: 0 }}
                      whileInView={{ scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ type: "spring", delay: 0.3 }}
                    >
                      {dreamersStats.top_dreamer.name}
                    </motion.p>
                    {dreamersStats.top_dreamer.tagline && (
                      <p className="text-sm text-[#FFBE98] mt-1 italic">
                        {dreamersStats.top_dreamer.tagline}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </section>
              className="bg-[#F2C94C]/5 rounded-2xl p-6 flex items-center justify-center"
            >
              <div className="text-center">
                {/* Raffle Stats */}
                <div className="flex items-center justify-center gap-3 mb-2">
                  <Gift className="w-6 h-6 text-[#F2C94C]" />
                  <motion.p 
                    className="text-4xl font-bold text-[#2D2A26]"
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ type: "spring", delay: 0.2 }}
                  >
                    {raffleStats?.total_raffles || 0}
                  </motion.p>
                </div>
                <p className="text-[#6B6661] font-medium text-sm">
                  {raffleStats?.total_raffles === 1 ? 'Viagem Sorteada' : 'Viagens Sorteadas'}
                </p>
                {raffleStats?.total_prize_amount > 0 && (
                  <p className="text-sm font-semibold text-[#F2C94C]">
                    €{raffleStats.total_prize_amount.toLocaleString()} em prémios
                  </p>
                )}

                {/* Winners */}
                {raffleStats?.winners && raffleStats.winners.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-stone-200">
                    <p className="text-xs text-[#6B6661] mb-2">Felizes Contemplados</p>
                    <div className="flex flex-wrap justify-center gap-2">
                      {raffleStats.winners.slice(0, 3).map((winner, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, scale: 0.8 }}
                          whileInView={{ opacity: 1, scale: 1 }}
                          viewport={{ once: true }}
                          transition={{ delay: 0.1 * index }}
                          className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full shadow-sm border border-stone-100"
                        >
                          <div className="w-6 h-6 bg-gradient-to-br from-[#F2C94C]/30 to-[#E0C097]/30 rounded-full flex items-center justify-center overflow-hidden">
                            {winner.avatar_url ? (
                              <img src={winner.avatar_url} alt="" className="w-full h-full object-cover" />
                            ) : (
                              <Star className="w-3 h-3 text-[#F2C94C]" />
                            )}
                          </div>
                          <span className="font-medium text-sm text-[#2D2A26]">{winner.name}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* No raffles yet message */}
                {(!raffleStats || raffleStats.total_raffles === 0) && (
                  <p className="text-xs text-[#6B6661] mt-2 italic">
                    Em breve serão sorteadas viagens de sonho
                  </p>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Journeys Section */}
      <section id="journeys" className="py-20 md:py-32 px-6 md:px-12 bg-[#FAFAF9]" data-testid="journeys-section">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-[#2D2A26] mb-4">
              {t('journeys.title')}
            </h2>
            <p className="text-[#6B6661] text-lg max-w-xl mx-auto">
              {t('journeys.subtitle')}
            </p>
          </motion.div>

          {loading ? (
            <div className="flex justify-center py-20">
              <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {journeys.map((journey, index) => (
                <JourneyCard key={journey.journey_id} journey={journey} index={index} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Trip Gallery Section */}
      {gallery && gallery.length > 0 && (
        <section className="py-16 bg-white" data-testid="gallery-section">
          <div className="max-w-7xl mx-auto px-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-10"
            >
              <div className="flex items-center justify-center gap-2 mb-4">
                <Camera className="w-6 h-6 text-[#FFBE98]" />
                <h2 className="text-3xl font-bold text-[#2D2A26]">
                  Sonhos Realizados
                </h2>
              </div>
              <p className="text-[#6B6661]">
                Fotos das viagens dos nossos felizes sonhadores
              </p>
            </motion.div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {gallery.slice(0, 8).map((photo, index) => (
                <motion.div
                  key={photo.photo_id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="relative group aspect-square rounded-2xl overflow-hidden"
                >
                  <img
                    src={photo.image_url}
                    alt={photo.caption || "Foto de viagem"}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-0 left-0 right-0 p-4">
                      {photo.location && (
                        <p className="text-white text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {photo.location}
                        </p>
                      )}
                      {photo.caption && (
                        <p className="text-white/80 text-xs mt-1">{photo.caption}</p>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Emotional Quote Section */}
      <section className="py-16 bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/30">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <p className="font-handwritten text-3xl md:text-4xl text-[#6B6661] leading-relaxed">
              "Não é apenas crowdfunding,
              <br />
              <span className="text-[#FFBE98]">  é crowddreaming.</span>
              <br />
              Não é um donativo,
              <br />
              <span className="text-[#FFBE98]">é um gesto fraternal.</span>"
            </p>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default Home;
