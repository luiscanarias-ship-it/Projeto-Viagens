import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, Heart, Copy, Check, CreditCard, Smartphone, Bitcoin, ExternalLink,
  Map, Hotel, Plane, MessageCircle, Sparkles, Send, ChevronDown, ChevronUp,
  BookOpen, Compass, Globe, User, AlertCircle, ChevronRight, ArrowRight
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import CheckoutModal from '../components/CheckoutModal';
import ShareMenu, { buildInviteLink } from '../components/ShareMenu';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fixed contribution amounts (v2 - no custom values)
const amounts = [
  { value: 10 },
  { value: 20 },
  { value: 50 },
  { value: 100 },
  { value: 200 },
  { value: 500 },
  { value: 1000 }
];

// Crypto types supported
const cryptoTypes = [
  { id: 'btc', name: 'Bitcoin', symbol: 'BTC', color: '#F7931A' },
  { id: 'eth', name: 'Ethereum', symbol: 'ETH', color: '#627EEA' },
  { id: 'usdt', name: 'Tether', symbol: 'USDT', color: '#26A17B' },
  { id: 'usdc', name: 'USD Coin', symbol: 'USDC', color: '#2775CA' }
];

// Payment methods - CRYPTO FIRST (recommended) - Stripe temporarily disabled
const paymentMethods = [
  { id: 'crypto', name: 'Criptomoedas', icon: Bitcoin, description: 'BTC, ETH, USDT, USDC', type: 'direct', recommended: true },
  { id: 'mbway', name: 'MBWay', icon: Smartphone, description: 'Pagamento móvel Portugal', type: 'direct', recommended: false },
  { id: 'paypal', name: 'PayPal', icon: ExternalLink, description: 'paypal.me/LuisCanarias', type: 'direct', recommended: false },
  { id: 'revolut', name: 'Revolut', icon: ExternalLink, description: '@luis4dreams', type: 'direct', recommended: false },
  { id: 'wise', name: 'Wise', icon: ExternalLink, description: 'Transferência internacional', type: 'direct', recommended: false }
];

// Icon components for social/travel resources
const PinterestIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0C5.373 0 0 5.373 0 12c0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738.098.119.112.224.083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.632-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0z"/>
  </svg>
);

const RedditIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
  </svg>
);

const ViatorIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
  </svg>
);

const JourneyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useLanguage();
  const { user, getAuthHeaders } = useAuth();
  
  const [journey, setJourney] = useState(null);
  const [progress, setProgress] = useState(null);
  const [contributions, setContributions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCheckout, setShowCheckout] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [copied, setCopied] = useState(false);
  const [showStickyBtn, setShowStickyBtn] = useState(false);
  
  // Travel planning state
  const [travelResources, setTravelResources] = useState(null);
  const [expandedSection, setExpandedSection] = useState(null);
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [showAiPlanner, setShowAiPlanner] = useState(false);
  
  const sponsorCode = searchParams.get('sponsor');
  const openPayment = searchParams.get('pay') === 'true';

  // Sticky button on scroll
  useEffect(() => {
    const onScroll = () => setShowStickyBtn(window.scrollY > 400);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [journeyRes, paymentRes, resourcesRes, progressRes, contribRes] = await Promise.all([
          axios.get(`${API}/journeys/${id}`),
          axios.get(`${API}/contributions/payment-info`),
          axios.get(`${API}/journey/${id}/travel-resources`),
          axios.get(`${API}/journeys/${id}/progress`),
          axios.get(`${API}/journeys/${id}/contributions`)
        ]);
        setJourney(journeyRes.data);
        setPaymentInfo(paymentRes.data);
        setTravelResources(resourcesRes.data);
        setProgress(progressRes.data);
        setContributions(contribRes.data.contributions || []);
        
        // Open payment modal if ?pay=true in URL
        if (openPayment) {
          setShowCheckout(true);
        }
      } catch (error) {
        console.error('Error fetching journey:', error);
        navigate('/');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate, openPayment]);

  const handleSupport = () => {
    setShowCheckout(true);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const askAI = async () => {
    if (!aiQuestion.trim()) return;
    
    setAiLoading(true);
    try {
      const response = await axios.post(`${API}/journey/${id}/ai-planner`, {
        question: aiQuestion
      });
      setAiResponse(response.data.response);
    } catch (error) {
      console.error('AI error:', error);
      setAiResponse('Desculpe, ocorreu um erro. Por favor tente novamente.');
    } finally {
      setAiLoading(false);
    }
  };

  const quickQuestions = [
    "Qual o melhor roteiro de 5 dias?",
    "Onde ficar com bom custo-benefício?",
    "Quais os melhores restaurantes locais?",
    "Como me deslocar na cidade?",
    "O que não posso deixar de visitar?"
  ];

  // Use progress from API (can exceed 100%)
  const progressPercent = progress?.percentage || 0;
  const isFunded = progress?.is_funded || false;
  const closingMessage = progress?.closing_message;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!journey) return null;

  return (
    <div className="min-h-screen pt-20" data-testid="journey-detail">
      {/* Sticky Bottom Bar */}
      <AnimatePresence>
        {showStickyBtn && !showCheckout && (
          <motion.div
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-stone-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
            data-testid="sticky-bar"
          >
            <div className="max-w-5xl mx-auto px-4 md:px-6 py-3 flex items-center gap-3 md:gap-5">
              <div className="flex-1 min-w-0 hidden sm:block">
                <p className="text-sm font-bold text-[#2D2A26] truncate">{journey?.name} — <span className="font-handwritten text-[#FFBE98]">{journey?.poetic_name}</span></p>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-1.5 bg-stone-100 rounded-full overflow-hidden max-w-[180px]">
                    <div className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full" style={{ width: `${Math.min(100, progress?.percentage || 0)}%` }} />
                  </div>
                  <span className="text-xs font-semibold text-[#6B6661]">{(progress?.percentage || 0).toFixed(1)}%</span>
                </div>
              </div>
              <button
                onClick={handleSupport}
                className="w-full sm:w-auto py-3 px-6 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-[#FFAB7D] transition-colors"
                data-testid="sticky-contribute-btn"
              >
                <Heart className="w-4 h-4" />
                Contribuir para este sonho
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* Hero Image */}
      <div className="relative h-[50vh] md:h-[60vh]">
        <img
          src={journey.image_url}
          alt={journey.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
        
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          className="absolute top-6 left-6 flex items-center gap-2 text-white/90 hover:text-white transition-colors"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>{t('payment.back')}</span>
        </button>

        {/* Title */}
        <div className="absolute bottom-0 left-0 right-0 p-8 md:p-12">
          <div className="max-w-4xl mx-auto">
            <span className="text-white/80 font-handwritten text-2xl">
              {journey.poetic_name}
            </span>
            <h1 className="text-4xl md:text-6xl font-bold text-white mt-2">
              {journey.name}
            </h1>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 md:px-12 py-12">
        {/* Progress Bar - Always visible, percentage public, goal amount hidden */}
        <div className="bg-white rounded-3xl p-8 shadow-lg -mt-16 relative z-10 mb-8">
          {/* Funded Banner */}
          {isFunded && (
            <div className="bg-gradient-to-r from-[#F2C94C]/20 to-[#FFBE98]/20 rounded-xl p-4 mb-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-[#F2C94C]" />
              <p className="text-[#2D2A26] font-medium">{closingMessage}</p>
            </div>
          )}
          
          <div className="h-4 bg-stone-100 rounded-full overflow-hidden mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(progressPercent, 100)}%` }}
              transition={{ duration: 1.5, ease: 'easeOut' }}
              className={`h-full rounded-full ${isFunded ? 'bg-gradient-to-r from-[#F2C94C] to-[#FFBE98]' : 'progress-bar-warm'}`}
            />
          </div>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <p className={`text-2xl font-bold ${isFunded ? 'text-[#F2C94C]' : 'text-[#FFBE98]'}`}>
              {Math.round(progressPercent)}% angariado
            </p>
            {journey.target_date && (
              <p className="text-sm text-[#6B6661]">
                Data objetivo: {new Date(journey.target_date).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' })}
              </p>
            )}
          </div>
        </div>

          {/* Share this dream - for logged-in users */}
          {user?.anonymous_alias && (
            <div className="flex justify-center -mt-4 mb-8 relative z-10">
              <ShareMenu
                inviteLink={buildInviteLink(user.anonymous_alias)}
                senderName={user?.name}
                buttonLabel="Partilhar este sonho"
                buttonClassName="flex items-center gap-2 py-2.5 px-6 bg-white text-[#2D2A26] rounded-xl text-sm font-semibold hover:bg-stone-50 transition-colors shadow-md border border-stone-100"
              />
            </div>
          )}

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Journey Info */}
          <div className="lg:col-span-2 space-y-8">
            {/* Dream */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-[#E6F4F1]/50 rounded-3xl p-8"
            >
              <h2 className="text-xl font-bold mb-4 text-[#2D2A26]">{t('journey.dream')}</h2>
              <p className="text-[#6B6661] text-lg leading-relaxed font-handwritten text-2xl">
                "{journey.emotional_message}"
              </p>
            </motion.div>

            {/* Impact */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-3xl p-8 border border-stone-100"
            >
              <h2 className="text-xl font-bold mb-4 text-[#2D2A26]">{t('journey.impact')}</h2>
              <p className="text-[#6B6661] leading-relaxed">
                {journey.impact_description}
              </p>
            </motion.div>

            {/* Description */}
            <div className="prose prose-stone max-w-none">
              <p className="text-[#6B6661] leading-relaxed">
                {journey.description}
              </p>
            </div>

            {/* Ambassador Info (if ambassador journey) */}
            {journey.ambassador_info && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="bg-white rounded-2xl p-6 border border-stone-100 shadow-sm"
              >
                <h3 className="text-lg font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                  <User className="w-5 h-5 text-[#FFBE98]" />
                  Sobre o Embaixador
                </h3>
                <a 
                  href={`/ambassador/${journey.ambassador_info.user_id}`}
                  className="flex items-center gap-4 p-3 -m-3 rounded-xl hover:bg-stone-50 transition-colors group"
                  data-testid="ambassador-profile-link"
                >
                  <img 
                    src={journey.ambassador_info.avatar} 
                    alt={journey.ambassador_info.display_name}
                    className="w-14 h-14 rounded-full object-cover border-2 border-[#FFBE98]/30"
                  />
                  <div className="flex-1">
                    <p className="font-bold text-[#2D2A26] group-hover:text-[#FFBE98] transition-colors">
                      {journey.ambassador_info.display_name}
                    </p>
                    {journey.ambassador_info.country && (
                      <p className="text-sm text-[#6B6661] flex items-center gap-1">
                        <Globe className="w-3 h-3" /> {journey.ambassador_info.country}
                      </p>
                    )}
                    <span className="inline-block mt-1 px-2 py-0.5 bg-gradient-to-r from-[#FFBE98]/20 to-[#E6F4F1]/20 rounded-full text-xs font-medium text-[#FFBE98]">
                      Embaixador 4Luis
                    </span>
                  </div>
                  <ChevronRight className="w-5 h-5 text-[#6B6661] group-hover:text-[#FFBE98] transition-colors" />
                </a>
              </motion.div>
            )}

            {/* ==================== TRAVEL PLANNING SECTION ==================== */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-[#FFBE98]/10 to-[#E6F4F1]/30 rounded-3xl p-8 border border-[#FFBE98]/20"
            >
              <h2 className="text-2xl font-bold mb-6 text-[#2D2A26] flex items-center gap-3">
                <Plane className="w-7 h-7 text-[#FFBE98]" />
                Planeia a Tua Viagem para {journey.name}
              </h2>

              {travelResources && (
                <div className="space-y-4">
                  {/* Google Maps */}
                  <div className="bg-white rounded-2xl p-4 shadow-sm">
                    <a 
                      href={travelResources.map.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-4 hover:bg-stone-50 p-2 rounded-xl transition-colors"
                    >
                      <div className="w-12 h-12 bg-[#4285F4]/10 rounded-xl flex items-center justify-center">
                        <Map className="w-6 h-6 text-[#4285F4]" />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-[#2D2A26]">{travelResources.map.title}</p>
                        <p className="text-sm text-[#6B6661]">{travelResources.map.description}</p>
                      </div>
                      <ExternalLink className="w-5 h-5 text-[#6B6661]" />
                    </a>
                  </div>

                  {/* Hotels Section */}
                  <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
                    <button
                      onClick={() => setExpandedSection(expandedSection === 'hotels' ? null : 'hotels')}
                      className="w-full flex items-center gap-4 p-4 hover:bg-stone-50 transition-colors"
                    >
                      <div className="w-12 h-12 bg-[#FFBE98]/20 rounded-xl flex items-center justify-center">
                        <Hotel className="w-6 h-6 text-[#FFBE98]" />
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-semibold text-[#2D2A26]">Onde Ficar</p>
                        <p className="text-sm text-[#6B6661]">Hotéis, apartamentos e alojamentos</p>
                      </div>
                      {expandedSection === 'hotels' ? (
                        <ChevronUp className="w-5 h-5 text-[#6B6661]" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-[#6B6661]" />
                      )}
                    </button>
                    <AnimatePresence>
                      {expandedSection === 'hotels' && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="border-t border-stone-100"
                        >
                          <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-3">
                            {travelResources.hotels.map((hotel, idx) => (
                              <a
                                key={idx}
                                href={hotel.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 p-3 bg-stone-50 rounded-xl hover:bg-stone-100 transition-colors"
                              >
                                <span className="text-sm font-medium text-[#2D2A26]">{hotel.name}</span>
                                <ExternalLink className="w-3 h-3 text-[#6B6661] ml-auto" />
                              </a>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Flights Section */}
                  <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
                    <button
                      onClick={() => setExpandedSection(expandedSection === 'flights' ? null : 'flights')}
                      className="w-full flex items-center gap-4 p-4 hover:bg-stone-50 transition-colors"
                    >
                      <div className="w-12 h-12 bg-[#E6F4F1] rounded-xl flex items-center justify-center">
                        <Plane className="w-6 h-6 text-[#2D2A26]" />
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-semibold text-[#2D2A26]">Voos e Transportes</p>
                        <p className="text-sm text-[#6B6661]">Companhias aéreas e comparadores</p>
                      </div>
                      {expandedSection === 'flights' ? (
                        <ChevronUp className="w-5 h-5 text-[#6B6661]" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-[#6B6661]" />
                      )}
                    </button>
                    <AnimatePresence>
                      {expandedSection === 'flights' && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="border-t border-stone-100"
                        >
                          <div className="p-4 grid grid-cols-2 gap-3">
                            {travelResources.flights.map((flight, idx) => (
                              <a
                                key={idx}
                                href={flight.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 p-3 bg-stone-50 rounded-xl hover:bg-stone-100 transition-colors"
                              >
                                <span className="text-sm font-medium text-[#2D2A26]">{flight.name}</span>
                                <ExternalLink className="w-3 h-3 text-[#6B6661] ml-auto" />
                              </a>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Social Media Section */}
                  <div className="bg-white rounded-2xl overflow-hidden shadow-sm">
                    <button
                      onClick={() => setExpandedSection(expandedSection === 'social' ? null : 'social')}
                      className="w-full flex items-center gap-4 p-4 hover:bg-stone-50 transition-colors"
                    >
                      <div className="w-12 h-12 bg-gradient-to-br from-[#E1306C]/20 to-[#405DE6]/20 rounded-xl flex items-center justify-center">
                        <MessageCircle className="w-6 h-6 text-[#E1306C]" />
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-semibold text-[#2D2A26]">O Que Dizem nas Redes</p>
                        <p className="text-sm text-[#6B6661]">Opiniões, dicas e sugestões</p>
                      </div>
                      {expandedSection === 'social' ? (
                        <ChevronUp className="w-5 h-5 text-[#6B6661]" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-[#6B6661]" />
                      )}
                    </button>
                    <AnimatePresence>
                      {expandedSection === 'social' && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="border-t border-stone-100"
                        >
                          <div className="p-4 space-y-3">
                            {travelResources.social.map((social, idx) => (
                              <a
                                key={idx}
                                href={social.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 p-3 bg-stone-50 rounded-xl hover:bg-stone-100 transition-colors"
                              >
                                <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                                  {social.name === 'GetYourGuide' && <Compass className="w-5 h-5 text-[#FF5533]" />}
                                  {social.name === 'Viator' && <Globe className="w-5 h-5 text-[#00AA6C]" />}
                                  {social.name === 'Pinterest' && <PinterestIcon />}
                                  {social.name === 'WikiVoyage' && <BookOpen className="w-5 h-5 text-[#339966]" />}
                                  {social.name === 'Reddit' && <RedditIcon />}
                                </div>
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-[#2D2A26]">{social.name}</p>
                                  <p className="text-xs text-[#6B6661]">{social.description}</p>
                                </div>
                                <ExternalLink className="w-4 h-4 text-[#6B6661]" />
                              </a>
                            ))}
                            
                            {/* Blogs */}
                            <div className="pt-3 border-t border-stone-100">
                              <p className="text-xs text-[#6B6661] mb-2 font-medium">Blogs de Viagem</p>
                              {travelResources.blogs.map((blog, idx) => (
                                <a
                                  key={idx}
                                  href={blog.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-3 p-3 bg-stone-50 rounded-xl hover:bg-stone-100 transition-colors mb-2"
                                >
                                  <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                                    <BookOpen className="w-5 h-5 text-[#FFBE98]" />
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-sm font-medium text-[#2D2A26]">{blog.name}</p>
                                    <p className="text-xs text-[#6B6661]">{blog.description}</p>
                                  </div>
                                  <ExternalLink className="w-4 h-4 text-[#6B6661]" />
                                </a>
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* AI Planner Section */}
                  <div className="bg-gradient-to-br from-[#FFBE98]/20 to-[#F2C94C]/20 rounded-2xl overflow-hidden border border-[#FFBE98]/30">
                    <button
                      onClick={() => setShowAiPlanner(!showAiPlanner)}
                      className="w-full flex items-center gap-4 p-4 hover:bg-white/30 transition-colors"
                    >
                      <div className="w-12 h-12 bg-gradient-to-br from-[#FFBE98] to-[#F2C94C] rounded-xl flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-white" />
                      </div>
                      <div className="flex-1 text-left">
                        <p className="font-semibold text-[#2D2A26]">A IA Pode Ajudar-te a Planear</p>
                        <p className="text-sm text-[#6B6661]">Roteiros, dicas, restaurantes e muito mais</p>
                      </div>
                      {showAiPlanner ? (
                        <ChevronUp className="w-5 h-5 text-[#6B6661]" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-[#6B6661]" />
                      )}
                    </button>
                    <AnimatePresence>
                      {showAiPlanner && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="border-t border-[#FFBE98]/30"
                        >
                          <div className="p-4 space-y-4">
                            {/* Quick Questions */}
                            <div>
                              <p className="text-xs text-[#6B6661] mb-2">Perguntas frequentes:</p>
                              <div className="flex flex-wrap gap-2">
                                {quickQuestions.map((q, idx) => (
                                  <button
                                    key={idx}
                                    onClick={() => setAiQuestion(q)}
                                    className="text-xs px-3 py-1.5 bg-white rounded-full text-[#2D2A26] hover:bg-[#FFBE98]/20 transition-colors"
                                  >
                                    {q}
                                  </button>
                                ))}
                              </div>
                            </div>

                            {/* Input */}
                            <div className="flex gap-2">
                              <input
                                type="text"
                                value={aiQuestion}
                                onChange={(e) => setAiQuestion(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && askAI()}
                                placeholder={`Pergunta algo sobre ${journey.name}...`}
                                className="flex-1 px-4 py-3 rounded-xl border border-stone-200 bg-white focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent"
                              />
                              <button
                                onClick={askAI}
                                disabled={aiLoading || !aiQuestion.trim()}
                                className="px-4 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium disabled:opacity-50 hover:bg-[#FFAB7D] transition-colors"
                              >
                                {aiLoading ? (
                                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                  <Send className="w-5 h-5" />
                                )}
                              </button>
                            </div>

                            {/* AI Response */}
                            {aiResponse && (
                              <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-white rounded-xl p-4 max-h-96 overflow-y-auto"
                              >
                                <div className="flex items-start gap-3">
                                  <div className="w-8 h-8 bg-gradient-to-br from-[#FFBE98] to-[#F2C94C] rounded-lg flex items-center justify-center flex-shrink-0">
                                    <Sparkles className="w-4 h-4 text-white" />
                                  </div>
                                  <div className="flex-1">
                                    <div className="text-sm text-[#2D2A26] leading-relaxed">
                                      {aiResponse.split('\n').map((line, idx) => (
                                        <p key={idx} className={line.trim() ? 'mb-2' : 'mb-1'}>
                                          {line.trim().startsWith('-') ? (
                                            <span className="flex items-start gap-2">
                                              <span className="text-[#FFBE98] mt-1">•</span>
                                              <span>{line.trim().substring(1).trim()}</span>
                                            </span>
                                          ) : (
                                            line
                                          )}
                                        </p>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </motion.div>
          </div>

          {/* Right Column - Support Card + Contributions Feed */}
          <div className="lg:col-span-1 space-y-6">
            {/* Support Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100 sticky top-28"
            >
              <button
                onClick={handleSupport}
                className="w-full btn-primary flex items-center justify-center gap-2 mb-4"
                data-testid="support-btn"
              >
                <Heart className="w-5 h-5" />
                {t('journey.support_btn')}
              </button>
              
              <div className="bg-gradient-to-r from-[#E6F4F1]/50 to-[#E6F4F1]/30 rounded-2xl p-4">
                <p className="text-sm text-[#2D2A26] flex items-start gap-2">
                  <Heart className="w-5 h-5 text-[#FFBE98] flex-shrink-0 mt-0.5" />
                  <span>A plataforma não retém comissões. O valor integral vai para o sonhador.</span>
                </p>
              </div>
            </motion.div>

            {/* Contributions Feed */}
            {contributions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
              >
                <h3 className="font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                  <Heart className="w-5 h-5 text-[#FFBE98]" />
                  Apoiantes ({contributions.length})
                </h3>
                
                <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                  {contributions.map((contrib, idx) => (
                    <motion.div
                      key={contrib.contribution_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className={`p-4 rounded-xl ${contrib.is_crypto ? 'bg-gradient-to-r from-[#F7931A]/5 to-[#627EEA]/5 border border-[#F7931A]/20' : 'bg-stone-50'}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          contrib.is_crypto 
                            ? 'bg-gradient-to-br from-[#F7931A] to-[#627EEA]' 
                            : 'bg-gradient-to-br from-[#FFBE98] to-[#F2C94C]'
                        }`}>
                          {contrib.is_crypto ? (
                            <Bitcoin className="w-5 h-5 text-white" />
                          ) : (
                            <User className="w-5 h-5 text-white" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-[#2D2A26] truncate flex-1">
                              {contrib.display_name}
                            </p>
                            {contrib.is_crypto && (
                              <span className="text-xs bg-gradient-to-r from-[#F7931A] to-[#627EEA] text-white px-2 py-0.5 rounded-full font-medium uppercase">
                                {contrib.crypto_type || 'Crypto'}
                              </span>
                            )}
                            <span className={`font-bold whitespace-nowrap ${contrib.is_crypto ? 'text-[#F7931A]' : 'text-[#FFBE98]'}`}>
                              €{contrib.amount}
                            </span>
                          </div>
                          {contrib.message && (
                            <p className="text-sm text-[#6B6661] mt-1 italic">
                              "{contrib.message}"
                            </p>
                          )}
                          <p className="text-xs text-[#6B6661]/60 mt-1">
                            {new Date(contrib.created_at).toLocaleDateString('pt-PT', {
                              day: 'numeric',
                              month: 'short'
                            })}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>


      {/* Checkout Modal */}
      <CheckoutModal
        isOpen={showCheckout}
        onClose={() => setShowCheckout(false)}
        journeyName={journey?.name || "China"}
        journeyId={id}
        paymentInfo={paymentInfo}
        getAuthHeaders={getAuthHeaders}
        user={user}
      />
    </div>
  );
};

export default JourneyDetail;

