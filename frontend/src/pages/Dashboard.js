import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Ticket, Link as LinkIcon, Copy, Check, Plus, User, Eye, EyeOff, Save, Camera } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const { user, loading: authLoading, getAuthHeaders, checkAuth } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);
  
  const [activeTab, setActiveTab] = useState('tickets');
  const [tickets, setTickets] = useState([]);
  const [sponsorLinks, setSponsorLinks] = useState([]);
  const [journeys, setJourneys] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copiedLink, setCopiedLink] = useState(null);
  const [selectedJourney, setSelectedJourney] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  const passedUser = location.state?.user;

  useEffect(() => {
    if (!authLoading && !user && !passedUser) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const headers = getAuthHeaders();
        const [ticketsRes, linksRes, journeysRes, profileRes] = await Promise.all([
          axios.get(`${API}/tickets/my-tickets`, { headers, withCredentials: true }),
          axios.get(`${API}/sponsor-links/my-links`, { headers, withCredentials: true }),
          axios.get(`${API}/journeys`),
          axios.get(`${API}/profile`, { headers, withCredentials: true })
        ]);
        
        setTickets(ticketsRes.data);
        setSponsorLinks(linksRes.data);
        setJourneys(journeysRes.data);
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

  const createSponsorLink = async () => {
    if (!selectedJourney) return;
    
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/sponsor-links/create`, 
        { journey_id: selectedJourney },
        { headers, withCredentials: true }
      );
      setSponsorLinks([...sponsorLinks, response.data]);
      setSelectedJourney('');
    } catch (error) {
      console.error('Error creating sponsor link:', error);
    }
  };

  const copyLink = (linkId) => {
    const fullUrl = `${window.location.origin}/journey/${sponsorLinks.find(l => l.link_id === linkId)?.journey_id}?sponsor=${linkId}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedLink(linkId);
    setTimeout(() => setCopiedLink(null), 2000);
  };

  const saveProfile = async () => {
    setSavingProfile(true);
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/profile`, profile, { headers, withCredentials: true });
      await checkAuth(); // Refresh auth context
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

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Por favor selecione uma imagem válida');
      return;
    }

    // Validate file size (max 500KB)
    if (file.size > 500 * 1024) {
      alert('A imagem é muito grande. Máximo 500KB.');
      return;
    }

    setUploadingAvatar(true);
    try {
      // Convert to base64
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
          alert('Avatar atualizado com sucesso!');
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
      alert('Erro ao processar imagem');
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

  return (
    <div className="min-h-screen pt-28 pb-12 px-6 md:px-12" data-testid="dashboard-page">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-[#2D2A26] mb-2">
            {t('dashboard.title')}
          </h1>
          <p className="text-[#6B6661]">
            Olá, {currentUser?.name}! Bem-vindo de volta.
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: 'tickets', label: 'Meus Bilhetes' },
            { id: 'sponsor', label: 'Links de Sponsor' },
            { id: 'profile', label: 'Meu Perfil' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-xl font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-[#FFBE98] text-[#2D2A26]'
                  : 'bg-white border border-stone-200 text-[#6B6661] hover:bg-stone-50'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {/* Tickets Tab */}
          {activeTab === 'tickets' && (
            <motion.div
              key="tickets"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-[#E6F4F1] rounded-xl flex items-center justify-center">
                  <Ticket className="w-6 h-6 text-[#2D2A26]" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">{t('dashboard.tickets')}</h2>
                  <p className="text-sm text-[#6B6661]">{tickets.length} bilhetes</p>
                </div>
              </div>

              {tickets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-[#6B6661] mb-4">Ainda não tem bilhetes.</p>
                  <p className="text-sm text-[#6B6661]">
                    <strong>Importante:</strong> Convida 3 amigos a apoiar uma viagem e ganha automaticamente 
                    bilhetes para o sorteio do voucher da tua viagem de sonho! Para isso envia-lhes o teu link de Sponsor.
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {tickets.map((ticket) => (
                    <div
                      key={ticket.ticket_id}
                      className="flex items-center justify-between p-3 bg-stone-50 rounded-xl"
                    >
                      <span className="font-mono text-sm font-medium">{ticket.ticket_id}</span>
                      <span className="text-xs text-[#6B6661]">
                        {journeys.find(j => j.journey_id === ticket.journey_id)?.name}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Sponsor Links Tab */}
          {activeTab === 'sponsor' && (
            <motion.div
              key="sponsor"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-[#FFBE98]/20 rounded-xl flex items-center justify-center">
                  <LinkIcon className="w-6 h-6 text-[#FFBE98]" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">{t('dashboard.sponsor_links')}</h2>
                  <p className="text-sm text-[#6B6661]">Partilhe e ganhe bilhetes</p>
                </div>
              </div>

              {/* Create New Link */}
              <div className="flex gap-2 mb-4">
                <select
                  value={selectedJourney}
                  onChange={(e) => setSelectedJourney(e.target.value)}
                  className="flex-1 px-4 py-2 rounded-xl border border-stone-200 bg-white text-sm"
                  data-testid="journey-select"
                >
                  <option value="">Selecionar viagem...</option>
                  {journeys.map((j) => (
                    <option key={j.journey_id} value={j.journey_id}>
                      {j.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={createSponsorLink}
                  disabled={!selectedJourney}
                  className="px-4 py-2 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium disabled:opacity-50 transition-all hover:bg-[#FFAB7D]"
                  data-testid="create-link-btn"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>

              {sponsorLinks.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-[#6B6661]">Crie um link de sponsor para começar.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sponsorLinks.map((link) => {
                    const journey = journeys.find(j => j.journey_id === link.journey_id);
                    return (
                      <div key={link.link_id} className="p-4 bg-stone-50 rounded-xl">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{journey?.name}</span>
                          <span className="text-xs bg-[#E6F4F1] px-2 py-1 rounded-full">
                            {link.successful_referrals}/3 referências
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            readOnly
                            value={`${window.location.origin}/journey/${link.journey_id}?sponsor=${link.link_id}`}
                            className="flex-1 text-xs bg-white px-3 py-2 rounded-lg border border-stone-200 truncate"
                          />
                          <button
                            onClick={() => copyLink(link.link_id)}
                            className="p-2 hover:bg-white rounded-lg transition-colors"
                          >
                            {copiedLink === link.link_id ? (
                              <Check className="w-4 h-4 text-green-500" />
                            ) : (
                              <Copy className="w-4 h-4 text-[#6B6661]" />
                            )}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="mt-4 p-4 bg-[#F2C94C]/10 rounded-xl space-y-3">
                <p className="text-sm text-[#2D2A26]">
                  A tua contribuição também ajuda a financiar a tua viagem de sonho. Pede aos teus amigos 
                  para contribuírem para este projeto. Assim que o objetivo de angariação for conseguido, 
                  e se pelo menos 3 dos teus amigos tiverem contribuído, ficarás habilitado ao sorteio de 
                  um voucher de viagem por isso quantos mais amigos conseguires convidar melhor.
                </p>
                <p className="text-sm text-[#2D2A26]">
                  <strong>Nota:</strong> Se o objetivo de financiamento for atingido o valor do voucher 
                  será de 5.000€, se o objetivo não for atingido o valor do voucher será de 5% do valor 
                  angariado com o máximo de 2.500€.
                </p>
              </div>
            </motion.div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && profile && (
            <motion.div
              key="profile"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-[#E6F4F1] rounded-xl flex items-center justify-center">
                  <User className="w-6 h-6 text-[#2D2A26]" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">Meu Perfil</h2>
                  <p className="text-sm text-[#6B6661]">Configurações de conta e privacidade</p>
                </div>
              </div>

              <div className="max-w-md space-y-6">
                {/* Avatar */}
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
                      data-testid="avatar-input"
                    />
                  </div>
                  <div>
                    <p className="font-medium">{profile.name}</p>
                    <p className="text-sm text-[#6B6661]">{profile.email}</p>
                    <p className="text-xs text-[#FFBE98] mt-1">Clique no ícone para alterar foto</p>
                  </div>
                </div>

                {/* Name */}
                <div>
                  <label className="block text-sm font-medium mb-2">Nome</label>
                  <input
                    type="text"
                    value={profile.name || ''}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full input-warm px-4"
                    data-testid="profile-name"
                  />
                </div>

                {/* Alias */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Alias (Nome público alternativo)
                  </label>
                  <input
                    type="text"
                    value={profile.alias || ''}
                    onChange={(e) => setProfile({ ...profile, alias: e.target.value })}
                    placeholder="Ex: Sonhador Misterioso"
                    className="w-full input-warm px-4"
                    data-testid="profile-alias"
                  />
                  <p className="text-xs text-[#6B6661] mt-1">
                    Este nome será mostrado publicamente se preferir manter o anonimato.
                  </p>
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
                        <p className="font-medium">Mostrar nome real publicamente</p>
                        <p className="text-xs text-[#6B6661]">
                          {profile.use_real_name 
                            ? 'O seu primeiro nome será visível (ex: rankings)'
                            : 'Será mostrada a sua identidade anónima gerada automaticamente'
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

                {/* Anonymous Identity Preview - shown when anonymous mode is on */}
                {!profile.use_real_name && (
                  <div className="p-4 bg-[#E6F4F1]/50 rounded-xl border border-[#E6F4F1]">
                    <p className="text-sm font-medium text-[#2D2A26] mb-3">A sua identidade anónima:</p>
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
                      <div>
                        <p className="font-medium text-[#2D2A26]">
                          {profile.anonymous_alias || 'A gerar...'}
                        </p>
                        <p className="text-xs text-[#6B6661]">
                          Este nome e avatar serão mostrados publicamente
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={regenerateAnonymousIdentity}
                      className="mt-3 text-xs text-[#FFBE98] hover:text-[#FFAB7D] transition-colors"
                      data-testid="regenerate-identity-btn"
                    >
                      Gerar nova identidade anónima
                    </button>
                  </div>
                )}

                {/* Save Button */}
                <button
                  onClick={saveProfile}
                  disabled={savingProfile}
                  className="btn-primary flex items-center gap-2"
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Dashboard;
