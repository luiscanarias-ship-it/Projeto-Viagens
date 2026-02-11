import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowDown, Users, Star, Mail } from 'lucide-react';
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
  const [siteSettings, setSiteSettings] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Seed if needed
        await axios.post(`${API}/seed-journeys`).catch(() => {});
        
        // Fetch all data in parallel
        const [journeysRes, dreamersRes, settingsRes] = await Promise.all([
          axios.get(`${API}/journeys`),
          axios.get(`${API}/dreamers-stats`),
          axios.get(`${API}/settings`)
        ]);
        
        setJourneys(journeysRes.data);
        setDreamersStats(dreamersRes.data);
        setSiteSettings(settingsRes.data);
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

      {/* Dreamers Counter Section */}
      {dreamersStats && (
        <section className="py-12 bg-white border-b border-stone-100" data-testid="dreamers-section">
          <div className="max-w-5xl mx-auto px-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              {/* Total Dreamers */}
              <div className="text-center p-6 rounded-2xl bg-[#E6F4F1]/30">
                <div className="w-14 h-14 bg-[#E6F4F1] rounded-full flex items-center justify-center mx-auto mb-4">
                  <Users className="w-7 h-7 text-[#2D2A26]" />
                </div>
                <motion.p 
                  className="text-4xl font-bold text-[#2D2A26] mb-1"
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ type: "spring", delay: 0.2 }}
                >
                  {dreamersStats.total_dreamers || 0}
                </motion.p>
                <p className="text-[#6B6661] font-medium">Sonhadores</p>
              </div>

              {/* Total Contributions */}
              <div className="text-center p-6 rounded-2xl bg-[#FFBE98]/10">
                <div className="w-14 h-14 bg-[#FFBE98]/30 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">💝</span>
                </div>
                <motion.p 
                  className="text-4xl font-bold text-[#2D2A26] mb-1"
                  initial={{ scale: 0 }}
                  whileInView={{ scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ type: "spring", delay: 0.3 }}
                >
                  {dreamersStats.total_contributions || 0}
                </motion.p>
                <p className="text-[#6B6661] font-medium">Gestos Fraternais</p>
              </div>

              {/* Top Dreamer */}
              {dreamersStats.top_dreamer && (
                <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-[#F2C94C]/20 to-[#E0C097]/20 border-2 border-[#F2C94C]/30">
                  <div className="w-14 h-14 bg-[#F2C94C]/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Star className="w-7 h-7 text-[#F2C94C] fill-[#F2C94C]" />
                  </div>
                  <p className="text-sm text-[#6B6661] mb-1">Maior Sonhador</p>
                  <motion.p 
                    className="text-2xl font-bold text-[#2D2A26] mb-1"
                    initial={{ scale: 0 }}
                    whileInView={{ scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ type: "spring", delay: 0.4 }}
                  >
                    {dreamersStats.top_dreamer.name}
                  </motion.p>
                  <p className="text-sm text-[#6B6661]">
                    {dreamersStats.top_dreamer.contribution_count} contribuições
                  </p>
                </div>
              )}
            </motion.div>
          </div>
        </section>
      )}

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

      {/* Emotional Section */}
      <section className="py-20 bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/30">
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

      {/* Contact Section */}
      {siteSettings && (
        <section id="contact" className="py-20 bg-white" data-testid="contact-section">
          <div className="max-w-2xl mx-auto px-6 text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <div className="w-16 h-16 bg-[#FFBE98]/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Mail className="w-8 h-8 text-[#FFBE98]" />
              </div>
              
              <h2 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4">
                Entre em Contacto
              </h2>
              
              <p className="text-[#6B6661] text-lg mb-8 max-w-md mx-auto">
                {siteSettings.contact_message || "Tem alguma questão? Entre em contacto connosco."}
              </p>
              
              <a
                href={`mailto:${siteSettings.contact_email}`}
                className="btn-primary inline-flex items-center gap-3 text-lg"
                data-testid="contact-email-btn"
              >
                <Mail className="w-5 h-5" />
                {siteSettings.contact_email}
              </a>
            </motion.div>
          </div>
        </section>
      )}
    </div>
  );
};

export default Home;
