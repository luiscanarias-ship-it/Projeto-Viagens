import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Crown, Star, Sparkles, Users, Copy, Check, Share2, 
  Wallet, TrendingUp, MapPin, Heart, User, Camera, 
  Eye, EyeOff, Save, ExternalLink
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user, loading: authLoading, getAuthHeaders, checkAuth } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);
  
  const [dashboardData, setDashboardData] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copiedLink, setCopiedLink] = useState(false);
  const [startingCheckout, setStartingCheckout] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const passedUser = location.state?.user;

  // Check for subscription success/cancel from URL
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const subStatus = params.get('sub');
    if (subStatus === 'success') {
      window.history.replaceState({}, '', '/dashboard');
      checkAuth();
    } else if (subStatus === 'cancel') {
      window.history.replaceState({}, '', '/dashboard');
    }
  }, [location.search, checkAuth]);

  useEffect(() => {
    if (!authLoading && !user && !passedUser) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const headers = getAuthHeaders();
        const [statsRes, profileRes] = await Promise.all([
          axios.get(`${API}/dashboard/user-stats`, { headers, withCredentials: true }),
          axios.get(`${API}/profile`, { headers, withCredentials: true })
        ]);
        
        setDashboardData(statsRes.data);
        setProfile(profileRes.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (user || passedUser) {
      fetchData();
    }
  }, [user, authLoading, passedUser, navigate, getAuthHeaders]);

  const startSubscriptionCheckout = async () => {
    setStartingCheckout(true);
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/subscription/create-checkout`, {}, { 
        headers, 
        withCredentials: true 
      });
      
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      }
    } catch (error) {
      console.error('Error starting checkout:', error);
      alert(error.response?.data?.detail || 'Erro ao iniciar pagamento');
      setStartingCheckout(false);
    }
  };

  const createSponsorLink = async (journeyId) => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/sponsor-links/create`, 
        { journey_id: journeyId },
        { headers, withCredentials: true }
      );
      // Refresh dashboard data
      const statsRes = await axios.get(`${API}/dashboard/user-stats`, { headers, withCredentials: true });
      setDashboardData(statsRes.data);
      return response.data;
    } catch (error) {
      console.error('Error creating sponsor link:', error);
    }
  };

  const copyLink = (linkId, journeyId) => {
    const fullUrl = `${window.location.origin}/journey/${journeyId}?sponsor=${linkId}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const shareLink = async (linkId, journeyId) => {
    const fullUrl = `${window.location.origin}/journey/${journeyId}?sponsor=${linkId}`;
    const shareData = {
      title: '4Luis - Apoiar Viagem dos Sonhos',
      text: 'Junta-te a mim para apoiar esta viagem incrível!',
      url: fullUrl
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.log('Share cancelled');
      }
    } else {
      copyLink(linkId, journeyId);
    }
  };

  const saveProfile = async () => {
    setSavingProfile(true);
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/profile`, profile, { headers, withCredentials: true });
      await checkAuth();
      alert('Perfil guardado com sucesso!');
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('Erro ao guardar perfil');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleAvatarUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Por favor selecione uma imagem válida');
      return;
    }

    if (file.size > 500 * 1024) {
      alert('A imagem é muito grande. Máximo 500KB.');
      return;
    }

    setUploadingAvatar(true);
    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Image = reader.result;
        
        try {
          const headers = getAuthHeaders();
          const response = await axios.post(`${API}/profile/avatar`, 
            { image: base64Image },
            { headers, withCredentials: true }
          );
          
          setProfile({ ...profile, avatar: response.data.avatar });
          await checkAuth();
        } catch (error) {
          console.error('Error uploading avatar:', error);
          alert(error.response?.data?.detail || 'Erro ao carregar avatar');
        } finally {
          setUploadingAvatar(false);
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error reading file:', error);
      setUploadingAvatar(false);
    }
  };

  const regenerateAnonymousIdentity = async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/profile/generate-anonymous`, {}, { 
        headers, 
        withCredentials: true 
      });
      
      setProfile({
        ...profile,
        anonymous_alias: response.data.anonymous_alias,
        anonymous_avatar: response.data.anonymous_avatar
      });
    } catch (error) {
      console.error('Error regenerating anonymous identity:', error);
    }
  };

  const currentUser = user || passedUser;

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <p className="text-[#6B6661]">Erro ao carregar dados</p>
      </div>
    );
  }

  const { user: userData, contributions, invites, main_journey, main_sponsor_link } = dashboardData;
  const level = userData?.level || 'curioso';
  const subscriptionActive = userData?.subscription_active || false;
  const validReferrals = userData?.valid_referrals_count || 0;
  const isPremium = level === 'premium';
  const isSonhador = subscriptionActive && level === 'sonhador';
  const isCurioso = !subscriptionActive || level === 'curioso';

  // Progress calculation
  const progressPercent = Math.min((validReferrals / 3) * 100, 100);
  const referralsNeeded = Math.max(3 - validReferrals, 0);

  // Get or create sponsor link for main journey
  const sponsorLinkId = main_sponsor_link?.link_id;
  const sponsorLinkUrl = sponsorLinkId && main_journey 
    ? `${window.location.origin}/journey/${main_journey.journey_id}?sponsor=${sponsorLinkId}`
    : null;

  return (
    <div className="min-h-screen pt-28 pb-12 px-4 md:px-8" data-testid="dashboard-page">
      <div className="max-w-4xl mx-auto space-y-6">
        
        {/* BLOCO 1 — Estado Atual */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-3xl"
        >
          {isPremium ? (
            <div className="bg-gradient-to-br from-[#F2C94C] via-[#FFBE98] to-[#F2C94C] p-6 md:p-8">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                  <Crown className="w-9 h-9 text-white" />
                </div>
                <div>
                  <p className="text-white/80 text-sm font-medium">Estado</p>
                  <h2 className="text-2xl md:text-3xl font-bold text-white">Premium</h2>
                  <p className="text-white/70 text-sm mt-1">Acesso completo a todos os benefícios</p>
                </div>
              </div>
            </div>
          ) : isSonhador ? (
            <div className="bg-gradient-to-br from-[#FFBE98] to-[#E0C097] p-6 md:p-8">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-white/25 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                  <Star className="w-9 h-9 text-white" />
                </div>
                <div>
                  <p className="text-white/80 text-sm font-medium">Estado</p>
                  <h2 className="text-2xl md:text-3xl font-bold text-white">Sonhador ativo</h2>
                  <p className="text-white/70 text-sm mt-1">Subscrição ativa</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-gradient-to-br from-[#2D2A26] to-[#4A4640] p-6 md:p-8">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-[#FFBE98]/20 rounded-2xl flex items-center justify-center">
                    <Sparkles className="w-9 h-9 text-[#FFBE98]" />
                  </div>
                  <div>
                    <p className="text-white/60 text-sm font-medium">Estado</p>
                    <h2 className="text-2xl md:text-3xl font-bold text-white">Curioso</h2>
                    <p className="text-white/50 text-sm mt-1">Ainda não és sonhador</p>
                  </div>
                </div>
                <button
                  onClick={startSubscriptionCheckout}
                  disabled={startingCheckout}
                  className="px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold hover:bg-[#FFAB7D] transition-all disabled:opacity-50 flex items-center gap-2 shadow-lg"
                  data-testid="subscribe-btn"
                >
                  {startingCheckout ? (
                    <>
                      <div className="w-5 h-5 border-2 border-[#2D2A26] border-t-transparent rounded-full animate-spin" />
                      A processar...
                    </>
                  ) : (
                    <>
                      <Star className="w-5 h-5" />
                      Tornar-me Sonhador
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </motion.div>

        {/* BLOCO 2 — Progresso para Premium */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-3xl p-6 md:p-8 shadow-lg border border-stone-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-[#F2C94C]/20 to-[#FFBE98]/20 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-[#F2C94C]" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#2D2A26]">Progresso para Premium</h3>
              <p className="text-sm text-[#6B6661]">Motor principal de progressão</p>
            </div>
          </div>

          {isPremium ? (
            <div className="text-center py-6">
              <div className="w-20 h-20 bg-gradient-to-br from-[#F2C94C] to-[#FFBE98] rounded-full flex items-center justify-center mx-auto mb-4">
                <Crown className="w-10 h-10 text-white" />
              </div>
              <h4 className="text-xl font-bold text-[#2D2A26] mb-2">Premium Desbloqueado!</h4>
              <p className="text-[#6B6661]">
                Continua a convidar e a apoiar para manter vantagens e acesso prioritário.
              </p>
            </div>
          ) : (
            <>
              {/* Progress Stats */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-[#FFBE98]" />
                  <span className="font-semibold text-[#2D2A26]">Convites válidos:</span>
                </div>
                <span className="text-2xl font-bold text-[#F2C94C]">{validReferrals} / 3</span>
              </div>

              {/* Progress Bar */}
              <div className="relative h-4 bg-stone-100 rounded-full overflow-hidden mb-4">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${progressPercent}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full"
                />
                {/* Progress indicators */}
                <div className="absolute inset-0 flex justify-between px-1">
                  {[1, 2, 3].map((num) => (
                    <div
                      key={num}
                      className={`w-3 h-3 rounded-full my-0.5 ${
                        validReferrals >= num ? 'bg-white' : 'bg-stone-300'
                      }`}
                    />
                  ))}
                </div>
              </div>

              {/* Status Message */}
              {isCurioso ? (
                <div className="p-4 bg-[#FFF8F0] rounded-xl border border-[#FFBE98]/30">
                  <p className="text-sm text-[#2D2A26]">
                    <strong className="text-[#FFBE98]">Ativa a subscrição</strong> para que os teus convites contem e possas desbloquear Premium.
                  </p>
                </div>
              ) : referralsNeeded > 0 ? (
                <p className="text-center text-[#6B6661]">
                  Faltam <span className="font-bold text-[#F2C94C]">{referralsNeeded}</span> para desbloquear Premium
                </p>
              ) : (
                <p className="text-center text-green-600 font-medium">
                  Já tens 3 referrals! O Premium será ativado automaticamente.
                </p>
              )}
            </>
          )}
        </motion.div>

        {/* BLOCO 3 — Convites */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-3xl p-6 md:p-8 shadow-lg border border-stone-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-[#E6F4F1] rounded-xl flex items-center justify-center">
              <Share2 className="w-6 h-6 text-[#2D2A26]" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#2D2A26]">Convites</h3>
              <p className="text-sm text-[#6B6661]">Partilha e acompanha o teu impacto</p>
            </div>
          </div>

          {/* Sponsor Link */}
          {main_journey && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-[#6B6661] mb-2">
                O teu link de convite:
              </label>
              
              {sponsorLinkId ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    readOnly
                    value={sponsorLinkUrl}
                    className="flex-1 px-4 py-3 bg-stone-50 border border-stone-200 rounded-xl text-sm text-[#2D2A26] truncate"
                    data-testid="sponsor-link-input"
                  />
                  <button
                    onClick={() => copyLink(sponsorLinkId, main_journey.journey_id)}
                    className={`px-4 py-3 rounded-xl font-medium transition-all flex items-center gap-2 ${
                      copiedLink 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-[#FFBE98] text-[#2D2A26] hover:bg-[#FFAB7D]'
                    }`}
                    data-testid="copy-link-btn"
                  >
                    {copiedLink ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                    {copiedLink ? 'Copiado!' : 'Copiar'}
                  </button>
                  <button
                    onClick={() => shareLink(sponsorLinkId, main_journey.journey_id)}
                    className="px-4 py-3 bg-[#2D2A26] text-white rounded-xl font-medium hover:bg-[#4A4640] transition-all flex items-center gap-2"
                    data-testid="share-link-btn"
                  >
                    <Share2 className="w-5 h-5" />
                    <span className="hidden sm:inline">Partilhar</span>
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => createSponsorLink(main_journey.journey_id)}
                  className="w-full px-4 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium hover:bg-[#FFAB7D] transition-all flex items-center justify-center gap-2"
                  data-testid="create-sponsor-link-btn"
                >
                  <Share2 className="w-5 h-5" />
                  Gerar link de convite
                </button>
              )}
            </div>
          )}

          {/* Invite Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-stone-50 rounded-xl">
              <p className="text-2xl font-bold text-[#2D2A26]">{invites?.total_invited || 0}</p>
              <p className="text-xs text-[#6B6661] mt-1">Pessoas convidadas</p>
            </div>
            <div className="text-center p-4 bg-stone-50 rounded-xl">
              <p className="text-2xl font-bold text-[#F2C94C]">{invites?.total_contributed_by_invites || 0}</p>
              <p className="text-xs text-[#6B6661] mt-1">Quantas contribuíram</p>
            </div>
            <div className="text-center p-4 bg-stone-50 rounded-xl">
              <p className="text-2xl font-bold text-[#FFBE98]">€{invites?.impact_amount?.toFixed(0) || 0}</p>
              <p className="text-xs text-[#6B6661] mt-1">Impacto gerado</p>
            </div>
          </div>
        </motion.div>

        {/* BLOCO 4 — Contribuições Pessoais */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-3xl p-6 md:p-8 shadow-lg border border-stone-100"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-[#FFBE98]/20 rounded-xl flex items-center justify-center">
              <Wallet className="w-6 h-6 text-[#FFBE98]" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-[#2D2A26]">Contribuições Pessoais</h3>
              <p className="text-sm text-[#6B6661]">O teu apoio direto</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gradient-to-br from-[#FFBE98]/10 to-[#F2C94C]/10 rounded-xl border border-[#FFBE98]/20">
              <p className="text-2xl font-bold text-[#2D2A26]">€{contributions?.total_amount?.toFixed(0) || 0}</p>
              <p className="text-xs text-[#6B6661] mt-1">Total contribuído</p>
            </div>
            <div className="text-center p-4 bg-stone-50 rounded-xl">
              <p className="text-2xl font-bold text-[#2D2A26]">{contributions?.total_count || 0}</p>
              <p className="text-xs text-[#6B6661] mt-1">Nº contribuições</p>
            </div>
            <div className="text-center p-4 bg-stone-50 rounded-xl">
              <p className="text-sm font-medium text-[#2D2A26]">
                {contributions?.last_contribution 
                  ? new Date(contributions.last_contribution.created_at).toLocaleDateString('pt-PT')
                  : '—'}
              </p>
              <p className="text-xs text-[#6B6661] mt-1">Última contribuição</p>
            </div>
          </div>
        </motion.div>

        {/* BLOCO 5 — Atividade da Viagem Principal */}
        {main_journey && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-3xl overflow-hidden shadow-lg border border-stone-100"
          >
            {/* Journey Image Header */}
            <div className="relative h-40 md:h-48">
              <img 
                src={main_journey.image_url} 
                alt={main_journey.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-4 left-6 right-6">
                <div className="flex items-center gap-2 text-white/80 text-sm mb-1">
                  <MapPin className="w-4 h-4" />
                  <span>Viagem em destaque</span>
                </div>
                <h3 className="text-xl md:text-2xl font-bold text-white">{main_journey.name}</h3>
              </div>
            </div>

            <div className="p-6">
              {/* Progress */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-[#6B6661]">Progresso</span>
                  <span className="font-bold text-[#2D2A26]">
                    {Math.min(Math.round((main_journey.current_amount / main_journey.goal_amount) * 100), 100)}%
                  </span>
                </div>
                <div className="h-3 bg-stone-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min((main_journey.current_amount / main_journey.goal_amount) * 100, 100)}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full"
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <p className="text-xs text-[#6B6661]">Valor atual</p>
                  <p className="text-lg font-bold text-[#2D2A26]">€{main_journey.current_amount?.toFixed(0) || 0}</p>
                </div>
                {main_journey.target_date && (
                  <div className="text-right">
                    <p className="text-xs text-[#6B6661]">Data objetivo</p>
                    <p className="text-lg font-bold text-[#2D2A26]">
                      {new Date(main_journey.target_date).toLocaleDateString('pt-PT', { month: 'short', year: 'numeric' })}
                    </p>
                  </div>
                )}
              </div>

              {/* CTA Button */}
              <button
                onClick={() => navigate(`/journey/${main_journey.journey_id}`)}
                className="w-full py-4 bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] text-[#2D2A26] rounded-xl font-bold hover:shadow-lg transition-all flex items-center justify-center gap-2"
                data-testid="support-journey-btn"
              >
                <Heart className="w-5 h-5" />
                Apoiar viagem
              </button>
            </div>
          </motion.div>
        )}

        {/* Profile Section (Collapsed by Default) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white rounded-3xl shadow-lg border border-stone-100 overflow-hidden"
        >
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="w-full p-6 flex items-center justify-between hover:bg-stone-50 transition-colors"
            data-testid="toggle-profile-btn"
          >
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-stone-100 rounded-xl flex items-center justify-center overflow-hidden">
                {profile?.avatar || profile?.picture ? (
                  <img src={profile.avatar || profile.picture} alt="" className="w-full h-full object-cover" />
                ) : (
                  <User className="w-6 h-6 text-[#6B6661]" />
                )}
              </div>
              <div className="text-left">
                <h3 className="font-bold text-[#2D2A26]">{currentUser?.name}</h3>
                <p className="text-sm text-[#6B6661]">Ver e editar perfil</p>
              </div>
            </div>
            <ExternalLink className={`w-5 h-5 text-[#6B6661] transition-transform ${showProfile ? 'rotate-180' : ''}`} />
          </button>

          {showProfile && profile && (
            <div className="px-6 pb-6 border-t border-stone-100">
              <div className="pt-6 space-y-6">
                {/* Avatar Upload */}
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-20 h-20 bg-stone-100 rounded-full flex items-center justify-center overflow-hidden">
                      {profile.avatar || profile.picture ? (
                        <img src={profile.avatar || profile.picture} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <User className="w-10 h-10 text-[#6B6661]" />
                      )}
                    </div>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingAvatar}
                      className="absolute -bottom-1 -right-1 w-8 h-8 bg-[#FFBE98] rounded-full flex items-center justify-center shadow-lg hover:bg-[#FFAB7D] transition-colors disabled:opacity-50"
                      data-testid="avatar-upload-btn"
                    >
                      {uploadingAvatar ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Camera className="w-4 h-4 text-white" />
                      )}
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      className="hidden"
                    />
                  </div>
                  <div>
                    <p className="font-medium text-[#2D2A26]">{profile.name}</p>
                    <p className="text-sm text-[#6B6661]">{profile.email}</p>
                  </div>
                </div>

                {/* Name Input */}
                <div>
                  <label className="block text-sm font-medium mb-2 text-[#2D2A26]">Nome</label>
                  <input
                    type="text"
                    value={profile.name || ''}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full px-4 py-3 bg-stone-50 border border-stone-200 rounded-xl"
                    data-testid="profile-name"
                  />
                </div>

                {/* Privacy Toggle */}
                <div className="p-4 bg-stone-50 rounded-xl">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {profile.use_real_name ? (
                        <Eye className="w-5 h-5 text-[#2D2A26]" />
                      ) : (
                        <EyeOff className="w-5 h-5 text-[#6B6661]" />
                      )}
                      <div>
                        <p className="font-medium text-[#2D2A26]">Mostrar nome real</p>
                        <p className="text-xs text-[#6B6661]">
                          {profile.use_real_name 
                            ? 'Visível publicamente'
                            : 'Identidade anónima ativa'
                          }
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => setProfile({ ...profile, use_real_name: !profile.use_real_name })}
                      className={`w-14 h-8 rounded-full transition-colors ${
                        profile.use_real_name ? 'bg-[#FFBE98]' : 'bg-stone-300'
                      }`}
                      data-testid="privacy-toggle"
                    >
                      <div className={`w-6 h-6 bg-white rounded-full shadow transition-transform ${
                        profile.use_real_name ? 'translate-x-7' : 'translate-x-1'
                      }`} />
                    </button>
                  </div>
                </div>

                {/* Anonymous Identity Preview */}
                {!profile.use_real_name && (
                  <div className="p-4 bg-[#E6F4F1]/50 rounded-xl border border-[#E6F4F1]">
                    <p className="text-sm font-medium text-[#2D2A26] mb-3">Identidade anónima:</p>
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full overflow-hidden bg-white">
                        {profile.anonymous_avatar ? (
                          <img src={profile.anonymous_avatar} alt="Avatar anónimo" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-stone-200">
                            <User className="w-6 h-6 text-stone-400" />
                          </div>
                        )}
                      </div>
                      <p className="font-medium text-[#2D2A26]">
                        {profile.anonymous_alias || 'A gerar...'}
                      </p>
                    </div>
                    <button
                      onClick={regenerateAnonymousIdentity}
                      className="mt-3 text-xs text-[#FFBE98] hover:text-[#FFAB7D] transition-colors"
                    >
                      Gerar nova identidade
                    </button>
                  </div>
                )}

                {/* Save Button */}
                <button
                  onClick={saveProfile}
                  disabled={savingProfile}
                  className="w-full py-3 bg-[#2D2A26] text-white rounded-xl font-medium hover:bg-[#4A4640] transition-all flex items-center justify-center gap-2"
                  data-testid="save-profile-btn"
                >
                  {savingProfile ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Save className="w-5 h-5" />
                  )}
                  Guardar Perfil
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default Dashboard;
