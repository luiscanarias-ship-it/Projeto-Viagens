import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Crown, Star, Users, Copy, Check, Share2, 
  Wallet, TrendingUp, MapPin, Heart, User, Camera, 
  Eye, EyeOff, Save, ExternalLink, Award, CheckCircle, Plane
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import JourneyApplicationModal from '../components/JourneyApplicationModal';
import ShareMenu, { buildInviteLink } from '../components/ShareMenu';
import SupportDashboard from '../components/SupportDashboard';
import AmbassadorValidations from '../components/AmbassadorValidations';

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
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [myJourneys, setMyJourneys] = useState([]);

  const passedUser = location.state?.user;

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
        
        // Fetch ambassador journeys if user is ambassador
        if (profileRes.data?.level === 'embaixador') {
          try {
            const journeysRes = await axios.get(`${API}/ambassador/my-journeys`, { headers, withCredentials: true });
            setMyJourneys(journeysRes.data.journeys || []);
          } catch (e) {
            console.log('No ambassador journeys');
          }
        }
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
  const level = userData?.level || 'sonhador';
  const contributedToMainTrip = userData?.contributed_to_main_trip || false;
  const validReferrals = userData?.valid_referrals_count || 0;
  const isEmbaixador = level === 'embaixador';
  const isSonhador = level === 'sonhador';

  // Progress calculation for Embaixador
  // Requirements: contributed_to_main_trip + 3 valid referrals
  const hasContribution = contributedToMainTrip || contributions?.total_count > 0;
  const referralsProgress = Math.min(validReferrals, 3);
  const referralsNeeded = Math.max(3 - validReferrals, 0);
  const progressPercent = (referralsProgress / 3) * 100;

  // Get or create sponsor link for main journey
  const sponsorLinkId = main_sponsor_link?.link_id;
  const sponsorLinkUrl = sponsorLinkId && main_journey 
    ? `${window.location.origin}/journey/${main_journey.journey_id}?sponsor=${sponsorLinkId}`
    : null;

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 md:px-8" data-testid="dashboard-page">
      <div className="max-w-4xl mx-auto space-y-5">
        
        {/* AMBASSADOR ACTION CARD — Layout horizontal, glassmorphism */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative rounded-3xl overflow-hidden border border-white/20 shadow-xl"
          style={{ background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)' }}
          data-testid="invite-section"
        >
          {/* Glassmorphism overlay */}
          <div className="absolute inset-0 backdrop-blur-sm bg-white/40" />
          
          <div className="relative z-10 p-5 md:p-6">
            {isEmbaixador ? (
              /* ── EMBAIXADOR VIEW ── */
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-[#F2C94C] to-[#FFBE98] rounded-2xl flex items-center justify-center shadow-md">
                    <Crown className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-[#2D2A26]">Embaixador</h2>
                    <p className="text-xs text-[#6B6661]">Podes candidatar-te a abrir viagem própria</p>
                  </div>
                </div>
                {myJourneys.some(j => ['candidatura', 'aprovada', 'ativa'].includes(j.status)) ? (
                  <div className="space-y-2 mb-4">
                    {myJourneys.filter(j => ['candidatura', 'aprovada', 'ativa'].includes(j.status)).map(j => (
                      <div key={j.journey_id} className="flex items-center gap-3 p-3 bg-white/70 rounded-xl border border-stone-200/50">
                        <Plane className="w-4 h-4 text-[#004D40]" />
                        <div className="flex-1">
                          <p className="font-medium text-sm text-[#2D2A26]">{j.name}</p>
                          <p className="text-xs text-[#6B6661]">
                            Estado: <span className={`font-medium ${
                              j.status === 'ativa' ? 'text-green-600' : j.status === 'aprovada' ? 'text-blue-600' : 'text-amber-600'
                            }`}>{j.status}</span>
                          </p>
                        </div>
                        {j.status === 'ativa' && (
                          <a href={`/journey/${j.journey_id}`} className="text-[#004D40] text-sm font-semibold">Ver →</a>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <button
                    onClick={() => setShowApplicationModal(true)}
                    className="w-full py-3 bg-[#004D40] text-white rounded-xl font-bold hover:bg-[#00695C] hover:scale-[1.02] transition-all shadow-md flex items-center justify-center gap-2 mb-4"
                    data-testid="open-application-btn"
                  >
                    <Plane className="w-5 h-5" />
                    Candidatar-me a Abrir Viagem
                  </button>
                )}
                {dashboardData?.user_alias && (
                  <ShareMenu
                    inviteLink={buildInviteLink(dashboardData.user_alias)}
                    senderName={user?.name}
                    buttonLabel="Convidar amigos"
                    buttonClassName="w-full flex items-center justify-center gap-2 py-3 bg-[#004D40]/10 text-[#004D40] rounded-xl text-sm font-semibold hover:bg-[#004D40]/20 transition-all border border-[#004D40]/20"
                  />
                )}
              </div>
            ) : (
              /* ── SONHADOR VIEW — Horizontal Split ── */
              <div className="flex flex-col md:flex-row md:items-center gap-5">
                {/* Lado Esquerdo — Indicador visual circular */}
                <div className="flex items-center gap-4 md:w-auto">
                  <div className="relative w-20 h-20 flex-shrink-0">
                    {/* Background circle */}
                    <svg className="w-20 h-20 -rotate-90" viewBox="0 0 72 72">
                      <circle cx="36" cy="36" r="30" fill="none" stroke="#e5e7eb" strokeWidth="5" />
                      <circle cx="36" cy="36" r="30" fill="none" stroke="#004D40" strokeWidth="5"
                        strokeLinecap="round"
                        strokeDasharray={`${(validReferrals / 3) * 188.5} 188.5`}
                        className="transition-all duration-1000"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-xl font-bold text-[#2D2A26]">{validReferrals}</span>
                      <span className="text-[9px] text-[#6B6661] font-medium -mt-0.5">de 3</span>
                    </div>
                  </div>
                  <div className="md:hidden">
                    <h2 className="text-base font-bold text-[#2D2A26]">Nível Sonhador</h2>
                    <p className="text-xs text-[#6B6661] mt-0.5">
                      {referralsNeeded > 0 
                        ? `Falta${referralsNeeded > 1 ? 'm' : ''} ${referralsNeeded} amigo${referralsNeeded > 1 ? 's' : ''}`
                        : 'Requisitos cumpridos!'}
                    </p>
                  </div>
                </div>

                {/* Lado Direito — Info + CTA */}
                <div className="flex-1">
                  <div className="hidden md:block mb-3">
                    <h2 className="text-base font-bold text-[#2D2A26]">Nível Sonhador</h2>
                  </div>
                  <p className="text-sm text-[#2D2A26] leading-relaxed mb-1">
                    <span className="font-semibold">Desbloqueia a tua própria viagem.</span>
                  </p>
                  <p className="text-xs text-[#6B6661] mb-4">
                    {referralsNeeded > 0 
                      ? `Faltam apenas ${referralsNeeded} amigo${referralsNeeded > 1 ? 's' : ''} para te tornares Embaixador.`
                      : hasContribution 
                        ? 'Parabéns! Cumpres todos os requisitos!' 
                        : 'Contribui para a viagem principal para completar os requisitos.'}
                  </p>

                  {/* Requisitos inline */}
                  <div className="flex items-center gap-2 mb-4">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium ${
                      hasContribution ? 'bg-[#004D40]/10 text-[#004D40]' : 'bg-stone-100 text-[#6B6661]'
                    }`}>
                      {hasContribution ? <CheckCircle className="w-3 h-3" /> : <Heart className="w-3 h-3" />}
                      {hasContribution ? 'Contribuição feita' : 'Contribuir'}
                    </span>
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-medium ${
                      validReferrals >= 3 ? 'bg-[#004D40]/10 text-[#004D40]' : 'bg-stone-100 text-[#6B6661]'
                    }`}>
                      {validReferrals >= 3 ? <CheckCircle className="w-3 h-3" /> : <Users className="w-3 h-3" />}
                      {validReferrals}/3 amigos convidaram
                    </span>
                  </div>

                  {/* CTA Principal — Azul Petróleo */}
                  {dashboardData?.user_alias && (
                    <ShareMenu
                      inviteLink={buildInviteLink(dashboardData.user_alias)}
                      senderName={user?.name}
                      buttonLabel="Convidar amigos"
                      buttonClassName="w-full flex items-center justify-center gap-2 py-3.5 bg-[#004D40] text-white rounded-xl text-base font-bold hover:bg-[#00695C] hover:scale-[1.02] transition-all shadow-lg"
                    />
                  )}
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* AMBASSADOR VALIDATIONS — Pending payments to confirm */}
        {isEmbaixador && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-white rounded-3xl p-6 md:p-8 shadow-lg border border-stone-100"
          >
            <AmbassadorValidations token={localStorage.getItem('token')} />
          </motion.div>
        )}

        {/* BLOCO 3 — Impacto dos Convites (compacto) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-3xl p-5 shadow-lg border border-stone-100"
        >
          <h3 className="text-sm font-bold text-[#2D2A26] mb-3 flex items-center gap-2">
            <Share2 className="w-4 h-4 text-[#FFBE98]" /> O teu impacto
          </h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center p-3 bg-stone-50 rounded-xl">
              <p className="text-xl font-bold text-[#2D2A26]">{invites?.total_invited || 0}</p>
              <p className="text-[10px] text-[#6B6661]">Convidados</p>
            </div>
            <div className="text-center p-3 bg-stone-50 rounded-xl">
              <p className="text-xl font-bold text-[#F2C94C]">{invites?.total_contributed_by_invites || 0}</p>
              <p className="text-[10px] text-[#6B6661]">Contribuíram</p>
            </div>
            <div className="text-center p-3 bg-stone-50 rounded-xl">
              <p className="text-xl font-bold text-[#FFBE98]">€{invites?.impact_amount?.toFixed(0) || 0}</p>
              <p className="text-[10px] text-[#6B6661]">Impacto</p>
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
      
      {/* Support Section */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
        className="mt-8">
        <SupportDashboard />
      </motion.div>
      
      {/* Journey Application Modal */}
      <JourneyApplicationModal
        isOpen={showApplicationModal}
        onClose={() => setShowApplicationModal(false)}
        onSuccess={(data) => {
          // Refresh journeys list
          setMyJourneys(prev => [data.journey, ...prev]);
          alert('Candidatura submetida com sucesso! Vamos analisá-la em breve.');
        }}
        authHeaders={getAuthHeaders()}
      />
    </div>
  );
};

export default Dashboard;
