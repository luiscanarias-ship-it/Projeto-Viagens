import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft, Heart, Copy, Check, CreditCard, Smartphone, Bitcoin, ExternalLink,
  Sparkles, ChevronRight, User, AlertCircle, Flag, ShieldCheck, Globe, Clock
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useAuth } from '../contexts/AuthContext';
import CheckoutModal from '../components/CheckoutModal';
import SuccessStoryBanner from '../components/SuccessStoryBanner';
import ShareMenu, { buildInviteLink } from '../components/ShareMenu';
import StoryChapter from '../components/StoryChapter';
import MilestoneProgress from '../components/MilestoneProgress';
import TestimonialsSection from '../components/TestimonialsSection';
import MilestoneCelebration from '../components/MilestoneCelebration';
import ShareButton from '../components/ShareButton';
import SEO from '../components/SEO';
import { CelebrationBanner, FundedBadge, PendingBadge } from '../components/CelebrationBanner';

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

const TrustBadge = ({ level, memberSince }) => {
  const config = {
    sonhador: {
      label: 'Sonhador 4Luis',
      gradient: 'from-[#FFBE98]/20 to-[#FFD4B8]/20',
      textColor: 'text-[#E6A07C]',
      borderColor: 'border-[#FFBE98]/30',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3c.5 0 9 2 9 9s-8.5 9-9 9-9-2-9-9 8.5-9 9-9z" fill="currentColor" opacity="0.15"/>
          <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.4"/>
        </svg>
      )
    },
    verificado: {
      label: 'Sonhador Verificado',
      gradient: 'from-[#5BB5A2]/15 to-[#E6F4F1]/30',
      textColor: 'text-[#5BB5A2]',
      borderColor: 'border-[#5BB5A2]/30',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.15"/>
          <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      )
    },
    embaixador: {
      label: 'Embaixador 4Luis',
      gradient: 'from-[#F2C94C]/15 to-[#FFBE98]/15',
      textColor: 'text-[#D4A017]',
      borderColor: 'border-[#F2C94C]/40',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor" opacity="0.85">
          <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 16.8l-6.2 4.5 2.4-7.4L2 9.4h7.6z"/>
        </svg>
      )
    }
  };

  const c = config[level] || config.sonhador;
  const formattedDate = memberSince
    ? new Date(memberSince).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : null;

  return (
    <div className="space-y-1.5" data-testid="trust-badge">
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${c.gradient} ${c.textColor} border ${c.borderColor}`}>
        {c.icon}
        {c.label}
      </span>
      {formattedDate && (
        <p className="text-[10px] text-[#6B6661]/60" data-testid="member-since">
          Membro da 4Luis desde {formattedDate}
        </p>
      )}
    </div>
  );
};

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
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [showExitIntent, setShowExitIntent] = useState(false);
  const [trustIndicators, setTrustIndicators] = useState(null);
  const exitIntentShown = useRef(false);
  const supportBtnRef = useRef(null);
  
  const sponsorCode = searchParams.get('sponsor');
  const openPayment = searchParams.get('pay') === 'true';

  // Track sidebar visibility
  useEffect(() => {
    if (!supportBtnRef.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => setSidebarVisible(entry.isIntersecting),
      { threshold: 0 }
    );
    observer.observe(supportBtnRef.current);
    return () => observer.disconnect();
  }, [loading]);

  // Track scroll position
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 500);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Show sticky only when scrolled past sidebar area AND sidebar is not visible
  const showSticky = scrolled && !sidebarVisible && !showCheckout;

  // Exit intent detection
  useEffect(() => {
    const handleMouseLeave = (e) => {
      if (e.clientY <= 0 && !exitIntentShown.current && !showCheckout) {
        exitIntentShown.current = true;
        setShowExitIntent(true);
      }
    };
    const inactivityTimer = setTimeout(() => {
      if (!exitIntentShown.current && !showCheckout) {
        exitIntentShown.current = true;
        setShowExitIntent(true);
      }
    }, 30000);
    document.addEventListener('mouseleave', handleMouseLeave);
    return () => {
      document.removeEventListener('mouseleave', handleMouseLeave);
      clearTimeout(inactivityTimer);
    };
  }, [showCheckout]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [journeyRes, paymentRes, progressRes, contribRes] = await Promise.all([
          axios.get(`${API}/journeys/${id}`),
          axios.get(`${API}/contributions/payment-info`),
          axios.get(`${API}/journeys/${id}/progress`),
          axios.get(`${API}/journeys/${id}/contributions`)
        ]);
        setJourney(journeyRes.data);
        setPaymentInfo(paymentRes.data);
        setProgress(progressRes.data);
        setContributions(contribRes.data.contributions || []);
        
        // Fetch trust indicators for ambassador journeys
        if (journeyRes.data?.ambassador_info?.user_id) {
          axios.get(`${API}/ambassador/${journeyRes.data.ambassador_info.user_id}/trust-indicators`)
            .then(res => setTrustIndicators(res.data))
            .catch(() => {});
        }
        
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

  // Use progress from API (can exceed 100%)
  const progressPercent = progress?.percentage || 0;
  const isFunded = progress?.is_funded || false;
  const fundingStatus = progress?.funding_status || 'active';
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
      <SEO 
        title={journey?.name}
        description={journey?.poetic_name || journey?.description}
        image={journey?.image_url}
        url={window.location.href}
      />
      {/* Sticky Bottom Bar */}
      <AnimatePresence>
        {showSticky && (
          <motion.div
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            className="fixed bottom-10 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-stone-200 shadow-[0_-4px_20px_rgba(0,0,0,0.08)]"
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
                Ajudar a realizar este sonho
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
        {/* Success Story Banner */}
        <SuccessStoryBanner
          journey={journey}
          progress={progress}
          contributions={contributions}
          user={user}
        />

        {/* Story Chapter */}
        <div className="mb-4 -mt-8 relative z-10 max-w-2xl mx-auto">
          <StoryChapter
            percentage={progressPercent}
            customChapters={journey.story_chapters}
          />
        </div>

        {/* Progress Bar - Always visible, percentage public, goal amount hidden */}
        <div className="bg-white rounded-3xl p-8 shadow-lg -mt-16 relative z-10 mb-8">
          {/* Celebration / Pending Validation Banner */}
          {fundingStatus === 'completed' && (
            <div className="mb-6">
              <CelebrationBanner journeyName={journey.poetic_name || journey.name} variant="completed" />
            </div>
          )}
          {fundingStatus === 'pending_validation' && (
            <div className="mb-6">
              <CelebrationBanner variant="pending_validation" />
            </div>
          )}
          {isFunded && fundingStatus === 'active' && (
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
            <p className={`text-2xl font-bold ${fundingStatus === 'completed' ? 'text-[#F2C94C]' : isFunded ? 'text-[#F2C94C]' : 'text-[#FFBE98]'}`}>
              {Math.round(progressPercent)}% angariado
            </p>
            {fundingStatus === 'completed' && <FundedBadge />}
            {fundingStatus === 'pending_validation' && <PendingBadge />}
            {journey.target_date && (
              <p className="text-sm text-[#6B6661]">
                Data objetivo: {new Date(journey.target_date).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' })}
              </p>
            )}
          </div>
          
          {/* Social context — handled by MilestoneProgress */}

          <MilestoneProgress progressPercentage={progressPercent} contributorCount={progress?.contributor_count} />
        </div>

        {/* Milestone Celebration Banner */}
        <div className="max-w-4xl mx-auto px-4 md:px-8">
          <MilestoneCelebration journey={journey} customChapters={journey?.story_chapters} />
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
                data-testid="dreamer-info-section"
              >
                <h3 className="text-lg font-bold text-[#2D2A26] mb-1 flex items-center gap-2">
                  <User className="w-5 h-5 text-[#FFBE98]" />
                  Sonho de {journey.ambassador_info.display_name}
                </h3>
                <div className="mb-4">
                  <TrustBadge
                    level={journey.ambassador_info.level}
                    memberSince={journey.ambassador_info.member_since}
                  />
                  {journey.ambassador_info.certification_label && (
                    <span className={`inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      journey.ambassador_info.certification_level === 'confiavel' 
                        ? 'bg-emerald-100 text-emerald-700'
                        : journey.ambassador_info.certification_level === 'verificado'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-[#FFBE98]/20 text-[#2D2A26]'
                    }`} data-testid="certification-badge" title="Este embaixador foi validado pela 4Luis">
                      <ShieldCheck className="w-3 h-3" />
                      {journey.ambassador_info.certification_label}
                    </span>
                  )}
                  {/* Trust indicators */}
                  {trustIndicators && trustIndicators.confirmed_count > 0 && (
                    <div className="flex items-center gap-3 mt-2 flex-wrap" data-testid="trust-indicators">
                      <span className="text-[10px] text-[#6B6661] flex items-center gap-1">
                        <Check className="w-3 h-3 text-emerald-500" />
                        {trustIndicators.confirmed_count} pagamentos confirmados
                      </span>
                      {trustIndicators.confirmation_rate > 0 && (
                        <span className="text-[10px] text-emerald-600 font-medium">
                          {trustIndicators.confirmation_rate}% taxa de confirmação
                        </span>
                      )}
                      {trustIndicators.avg_confirmation_label && (
                        <span className="text-[10px] text-blue-600 font-medium flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Confirmação em {trustIndicators.avg_confirmation_label}
                        </span>
                      )}
                    </div>
                  )}
                </div>
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
                  </div>
                  <ChevronRight className="w-5 h-5 text-[#6B6661] group-hover:text-[#FFBE98] transition-colors" />
                </a>
              </motion.div>
            )}

            {/* AI Travel Planner CTA */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-[#FFBE98]/10 to-[#E6F4F1]/30 rounded-3xl overflow-hidden border border-[#FFBE98]/20"
              data-testid="ai-planner-cta"
            >
              <div className="p-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-[#FFBE98] to-[#F2C94C] rounded-xl flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-xl font-bold text-[#2D2A26]">Planeie esta viagem com IA</h2>
                </div>
                <p className="text-[#6B6661] mb-6">
                  Receba um guia completo para {journey.name} — roteiro dia a dia, checklist, dicas locais e muito mais, gerado em segundos.
                </p>
                <Link
                  to={`/travel-planner?destination=${encodeURIComponent(journey.name)}`}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-full font-bold hover:bg-[#FFAB7D] transition-all hover:scale-105 shadow-sm"
                  data-testid="ai-planner-cta-btn"
                >
                  <Sparkles className="w-4 h-4" />
                  Gerar plano de viagem
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </motion.div>
          </div>

          {/* Right Column - Support Card + Contributions Feed */}
          <div ref={supportBtnRef} className="lg:col-span-1 space-y-6">
            {/* Support Card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100 sticky top-28"
            >
              <button
                onClick={handleSupport}
                className="w-full btn-primary flex items-center justify-center gap-2 mb-3"
                data-testid="support-btn"
              >
                <Heart className="w-5 h-5" />
                {journey.is_main_trip && isFunded ? 'Faz parte deste momento' : t('journey.support_btn')}
              </button>
              
              <ShareButton 
                url={window.location.href}
                text={`Ajuda o sonho "${journey?.name}" a tornar-se realidade na 4Luis!`}
                className="w-full justify-center mb-4"
              />
              
              <div className="bg-gradient-to-r from-[#E6F4F1]/50 to-[#E6F4F1]/30 rounded-2xl p-4">
                <p className="text-sm text-[#2D2A26] flex items-start gap-2">
                  <Heart className="w-5 h-5 text-[#FFBE98] flex-shrink-0 mt-0.5" />
                  <span>A plataforma não retém comissões. O valor integral vai para o sonhador.</span>
                </p>
              </div>

              <div className="mt-3 px-1" data-testid="journey-disclaimer">
                <p className="text-[10px] leading-relaxed text-[#6B6661]/70">
                  As contribuições feitas na plataforma 4Luis são voluntárias e destinam-se a apoiar sonhos de viagem. A 4Luis funciona como uma plataforma de CrowdDreaming que liga sonhadores e apoiantes. Dependendo do método de pagamento escolhido, os valores podem ser enviados diretamente ao sonhador responsável pela viagem. A 4Luis não garante a realização das viagens nem assume responsabilidade pela utilização dos fundos.
                </p>
              </div>
            </motion.div>

            {/* Testimonials (compact) */}
            <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 }}
              className="bg-white/60 backdrop-blur-sm rounded-3xl p-5 shadow-sm border border-stone-100">
              <h4 className="text-xs font-semibold text-[#6B6661] uppercase mb-3">Sonhadores dizem</h4>
              <TestimonialsSection variant="compact" />
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

      {/* Report Problem - Discrete */}
      <div className="max-w-6xl mx-auto px-6 md:px-12 pb-8 flex justify-end">
        <a
          href={`mailto:suporte@4luis.com?subject=Reportar problema — ${journey?.name || 'Viagem'}&body=Olá equipa 4Luis,%0A%0AGostaria de reportar um problema com a viagem "${journey?.name || ''}".%0A%0ADescrição do problema:%0A`}
          className="inline-flex items-center gap-1.5 text-xs text-[#6B6661]/50 hover:text-[#6B6661] transition-colors"
          data-testid="report-problem-btn"
        >
          <Flag className="w-3 h-3" />
          Reportar problema
        </a>
      </div>


      {/* Checkout Modal */}
      <CheckoutModal
        isOpen={showCheckout}
        onClose={() => setShowCheckout(false)}
        journeyName={journey?.name || "China"}
        journeyId={id}
        journeyData={journey}
        trustIndicators={trustIndicators}
        contributionDescriptions={journey?.contribution_descriptions}
        paymentInfo={paymentInfo}
        getAuthHeaders={getAuthHeaders}
        user={user}
        progressData={progress}
      />

      {/* Exit Intent Modal */}
      <AnimatePresence>
        {showExitIntent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setShowExitIntent(false)}
            data-testid="exit-intent-overlay"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-2xl"
              data-testid="exit-intent-modal"
            >
              <p className="text-sm text-[#FFBE98] font-semibold mb-3">Antes de partires...</p>
              <p className="text-[#6B6661] leading-relaxed mb-2">
                O sonho da viagem pela <strong className="text-[#2D2A26]">{journey?.name}</strong> já começou.
              </p>
              <p className="text-[#2D2A26] font-semibold mb-1">Não fiques fora deste sonho.</p>
              <p className="font-handwritten text-xl text-[#FFBE98] mb-6">Sonha connosco.</p>
              <button
                onClick={() => { setShowExitIntent(false); setShowCheckout(true); }}
                className="w-full py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-[#FFAB7D] transition-colors"
                data-testid="exit-intent-contribute-btn"
              >
                <Heart className="w-4 h-4" /> Ajudar a realizar este sonho
              </button>
              <button
                onClick={() => setShowExitIntent(false)}
                className="mt-3 text-sm text-[#6B6661] hover:text-[#2D2A26] transition-colors"
              >
                Talvez mais tarde
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default JourneyDetail;

