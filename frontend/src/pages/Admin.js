import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit2, Trash2, Save, X, BarChart3, Settings, CheckCircle, XCircle, Mail, Users, Award, Gift, Crown, TrendingUp, UserPlus, ChevronRight, Star, FileText, Clock, MapPin, Target, Calendar, Eye } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Admin = () => {
  const { user, loading: authLoading, getAuthHeaders } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('journeys');
  const [journeys, setJourneys] = useState([]);
  const [contributions, setContributions] = useState([]);
  const [stats, setStats] = useState(null);
  const [settings, setSettings] = useState({ contact_email: '', contact_message: '' });
  const [loading, setLoading] = useState(true);
  const [editingJourney, setEditingJourney] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [sponsorsReport, setSponsorsReport] = useState(null);
  const [rafflesReady, setRafflesReady] = useState([]);
  const [selectedRaffleJourney, setSelectedRaffleJourney] = useState(null);
  const [raffleParticipants, setRaffleParticipants] = useState(null);
  const [drawingRaffle, setDrawingRaffle] = useState(false);
  // Users Dashboard State
  const [usersDashboard, setUsersDashboard] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetail, setUserDetail] = useState(null);
  const [updatingUser, setUpdatingUser] = useState(false);
  // Users table filters
  const [userSearch, setUserSearch] = useState('');
  const [userLevelFilter, setUserLevelFilter] = useState('all');
  const [userSubscriptionFilter, setUserSubscriptionFilter] = useState('all');
  const [userSortBy, setUserSortBy] = useState('referrals');
  const [userSortOrder, setUserSortOrder] = useState('desc');
  // Visibility state
  const [visibilityJourneys, setVisibilityJourneys] = useState([]);
  const [loadingVisibility, setLoadingVisibility] = useState(false);
  // Candidaturas state
  const [ambassadorApplications, setAmbassadorApplications] = useState(null);
  const [loadingApplications, setLoadingApplications] = useState(false);
  const [applicationStatusFilter, setApplicationStatusFilter] = useState('candidatura');
  const [formData, setFormData] = useState({
    name: '',
    poetic_name: '',
    description: '',
    emotional_message: '',
    impact_description: '',
    image_url: '',
    goal_amount: 5000,
    target_date: ''
  });

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      try {
        const headers = getAuthHeaders();
        const [journeysRes, statsRes, settingsRes, contributionsRes, sponsorsRes, rafflesRes, usersRes, applicationsRes] = await Promise.all([
          axios.get(`${API}/admin/journeys`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/stats`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/settings`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/contributions`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/sponsors-report`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/journeys-ready-for-raffle`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/users/dashboard`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/ambassador-journeys?status=candidatura`, { headers, withCredentials: true }).catch(() => ({ data: { journeys: [] } }))
        ]);
        
        setJourneys(journeysRes.data);
        setStats(statsRes.data);
        setSettings(settingsRes.data);
        setContributions(contributionsRes.data);
        setSponsorsReport(sponsorsRes.data);
        setRafflesReady(rafflesRes.data.ready_journeys || []);
        setUsersDashboard(usersRes.data);
        // Store pending applications count
        if (applicationsRes.data?.journeys?.length > 0) {
          setAmbassadorApplications(applicationsRes.data);
        }
      } catch (error) {
        console.error('Error fetching admin data:', error);
      } finally {
        setLoading(false);
      }
    };

    if (user?.is_admin) {
      fetchData();
    }
  }, [user, authLoading, navigate, getAuthHeaders]);

  const handleCreate = async () => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/admin/journeys`, formData, { 
        headers, 
        withCredentials: true 
      });
      setJourneys([...journeys, response.data]);
      setShowCreateForm(false);
      setFormData({
        name: '',
        poetic_name: '',
        description: '',
        emotional_message: '',
        impact_description: '',
        image_url: '',
        goal_amount: 5000,
        target_date: ''
      });
    } catch (error) {
      console.error('Error creating journey:', error);
      alert('Erro ao criar viagem');
    }
  };

  const handleUpdate = async (journeyId) => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.put(`${API}/admin/journeys/${journeyId}`, editingJourney, {
        headers,
        withCredentials: true
      });
      setJourneys(journeys.map(j => j.journey_id === journeyId ? response.data : j));
      setEditingJourney(null);
    } catch (error) {
      console.error('Error updating journey:', error);
      alert('Erro ao atualizar viagem');
    }
  };

  const handleDelete = async (journeyId) => {
    if (!window.confirm('Tem certeza que deseja eliminar esta viagem?')) return;
    
    try {
      const headers = getAuthHeaders();
      await axios.delete(`${API}/admin/journeys/${journeyId}`, { 
        headers, 
        withCredentials: true 
      });
      setJourneys(journeys.filter(j => j.journey_id !== journeyId));
    } catch (error) {
      console.error('Error deleting journey:', error);
      alert('Erro ao eliminar viagem');
    }
  };

  const handleSaveSettings = async () => {
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/admin/settings`, settings, {
        headers,
        withCredentials: true
      });
      alert('Configurações guardadas com sucesso!');
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Erro ao guardar configurações');
    }
  };

  const handleConfirmContribution = async (contributionId) => {
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/admin/contributions/${contributionId}/confirm`, {}, {
        headers,
        withCredentials: true
      });
      setContributions(contributions.map(c => 
        c.contribution_id === contributionId ? { ...c, status: 'completed' } : c
      ));
    } catch (error) {
      console.error('Error confirming contribution:', error);
      alert('Erro ao confirmar contribuição');
    }
  };

  const handleRejectContribution = async (contributionId) => {
    if (!window.confirm('Tem certeza que deseja rejeitar esta contribuição?')) return;
    
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/admin/contributions/${contributionId}/reject`, {}, {
        headers,
        withCredentials: true
      });
      setContributions(contributions.map(c => 
        c.contribution_id === contributionId ? { ...c, status: 'rejected' } : c
      ));
    } catch (error) {
      console.error('Error rejecting contribution:', error);
      alert('Erro ao rejeitar contribuição');
    }
  };

  const loadRaffleParticipants = async (journeyId) => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/raffle/${journeyId}`, { 
        headers, 
        withCredentials: true 
      });
      setRaffleParticipants(response.data);
      setSelectedRaffleJourney(journeyId);
    } catch (error) {
      console.error('Error loading raffle participants:', error);
      alert('Erro ao carregar participantes');
    }
  };

  const performRaffleDraw = async (journeyId) => {
    if (!window.confirm('Tem certeza que deseja realizar o sorteio? Esta ação não pode ser desfeita.')) return;
    
    setDrawingRaffle(true);
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/admin/raffle/${journeyId}/draw`, {}, { 
        headers, 
        withCredentials: true 
      });
      
      alert(`🎉 Sorteio realizado com sucesso!\n\nVencedor: ${response.data.winner.name}\nEmail: ${response.data.winner.email}\nTotal de entradas: ${response.data.total_entries}`);
      
      // Reload raffle data
      const rafflesRes = await axios.get(`${API}/admin/journeys-ready-for-raffle`, { headers, withCredentials: true });
      setRafflesReady(rafflesRes.data.ready_journeys || []);
      
      // Reload participants for the current journey
      if (selectedRaffleJourney === journeyId) {
        await loadRaffleParticipants(journeyId);
      }
    } catch (error) {
      console.error('Error performing raffle:', error);
      alert(error.response?.data?.detail || 'Erro ao realizar sorteio');
    } finally {
      setDrawingRaffle(false);
    }
  };

  // User management functions
  const loadUserDetail = async (userId) => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/users/${userId}/detail`, { headers, withCredentials: true });
      setUserDetail(response.data);
      setSelectedUser(userId);
    } catch (error) {
      console.error('Error loading user detail:', error);
      alert('Erro ao carregar detalhes do utilizador');
    }
  };

  const toggleSubscription = async (userId) => {
    setUpdatingUser(true);
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/admin/users/${userId}/subscription`, {}, { headers, withCredentials: true });
      // Reload dashboard
      const usersRes = await axios.get(`${API}/admin/users/dashboard`, { headers, withCredentials: true });
      setUsersDashboard(usersRes.data);
      if (selectedUser === userId) {
        await loadUserDetail(userId);
      }
    } catch (error) {
      console.error('Error toggling subscription:', error);
      alert('Erro ao atualizar subscrição');
    } finally {
      setUpdatingUser(false);
    }
  };

  const updateUserLevel = async (userId, newLevel) => {
    setUpdatingUser(true);
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/admin/users/${userId}/level`, { level: newLevel }, { headers, withCredentials: true });
      // Reload dashboard
      const usersRes = await axios.get(`${API}/admin/users/dashboard`, { headers, withCredentials: true });
      setUsersDashboard(usersRes.data);
      if (selectedUser === userId) {
        await loadUserDetail(userId);
      }
    } catch (error) {
      console.error('Error updating level:', error);
      alert('Erro ao atualizar nível');
    } finally {
      setUpdatingUser(false);
    }
  };

  const updateUserReferrals = async (userId, newCount) => {
    setUpdatingUser(true);
    try {
      const headers = getAuthHeaders();
      await axios.put(`${API}/admin/users/${userId}/referrals`, { valid_referrals_count: newCount }, { headers, withCredentials: true });
      // Reload dashboard
      const usersRes = await axios.get(`${API}/admin/users/dashboard`, { headers, withCredentials: true });
      setUsersDashboard(usersRes.data);
      if (selectedUser === userId) {
        await loadUserDetail(userId);
      }
    } catch (error) {
      console.error('Error updating referrals:', error);
      alert('Erro ao atualizar referrals');
    } finally {
      setUpdatingUser(false);
    }
  };

  const getLevelBadge = (level) => {
    const badges = {
      curioso: { bg: 'bg-stone-100', text: 'text-stone-600', label: 'Curioso' },
      sonhador: { bg: 'bg-[#FFBE98]/20', text: 'text-[#FFBE98]', label: 'Sonhador' },
      premium: { bg: 'bg-[#F2C94C]/20', text: 'text-[#F2C94C]', label: 'Premium' }
    };
    const badge = badges[level] || badges.curioso;
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badge.bg} ${badge.text}`}>
        {badge.label}
      </span>
    );
  };

  // Filter and sort users
  const getFilteredUsers = () => {
    if (!usersDashboard?.users) return [];
    
    let filtered = usersDashboard.users.filter(u => !u.is_admin);
    
    // Search filter
    if (userSearch) {
      const search = userSearch.toLowerCase();
      filtered = filtered.filter(u => 
        u.name?.toLowerCase().includes(search) || 
        u.email?.toLowerCase().includes(search)
      );
    }
    
    // Level filter
    if (userLevelFilter !== 'all') {
      filtered = filtered.filter(u => u.level === userLevelFilter);
    }
    
    // Subscription filter
    if (userSubscriptionFilter !== 'all') {
      filtered = filtered.filter(u => 
        userSubscriptionFilter === 'active' ? u.subscription_active : !u.subscription_active
      );
    }
    
    // Sort
    filtered.sort((a, b) => {
      let aVal, bVal;
      switch (userSortBy) {
        case 'referrals':
          aVal = a.valid_referrals_count || 0;
          bVal = b.valid_referrals_count || 0;
          break;
        case 'contributions':
          aVal = a.contributions_total || 0;
          bVal = b.contributions_total || 0;
          break;
        case 'impact':
          aVal = a.sponsor_impact_value || 0;
          bVal = b.sponsor_impact_value || 0;
          break;
        case 'date':
          aVal = a.registered_at || '';
          bVal = b.registered_at || '';
          break;
        case 'name':
          aVal = a.name?.toLowerCase() || '';
          bVal = b.name?.toLowerCase() || '';
          break;
        default:
          aVal = a.valid_referrals_count || 0;
          bVal = b.valid_referrals_count || 0;
      }
      if (userSortOrder === 'desc') {
        return bVal > aVal ? 1 : -1;
      }
      return aVal > bVal ? 1 : -1;
    });
    
    return filtered;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return '-';
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const pendingContributions = contributions.filter(c => c.status === 'pending_confirmation');

  return (
    <div className="min-h-screen pt-28 pb-12 px-6 md:px-12" data-testid="admin-page">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-[#2D2A26] mb-2">
            {t('admin.title')}
          </h1>
          <p className="text-[#6B6661]">
            Gerir viagens, contribuições e configurações
          </p>
        </motion.div>

        {/* Stats */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"
          >
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100">
              <BarChart3 className="w-8 h-8 text-[#FFBE98] mb-2" />
              <p className="text-3xl font-bold text-[#2D2A26]">
                €{stats.total_amount_raised.toLocaleString()}
              </p>
              <p className="text-sm text-[#6B6661]">Total Angariado</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100">
              <p className="text-3xl font-bold text-[#2D2A26]">{stats.total_contributions}</p>
              <p className="text-sm text-[#6B6661]">Contribuições</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100">
              <p className="text-3xl font-bold text-[#2D2A26]">{stats.total_users}</p>
              <p className="text-sm text-[#6B6661]">Utilizadores</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100">
              <p className="text-3xl font-bold text-[#2D2A26]">{stats.total_journeys}</p>
              <p className="text-sm text-[#6B6661]">Viagens</p>
            </div>
            <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100 relative">
              {pendingContributions.length > 0 && (
                <span className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                  {pendingContributions.length}
                </span>
              )}
              <p className="text-3xl font-bold text-[#2D2A26]">{pendingContributions.length}</p>
              <p className="text-sm text-[#6B6661]">Pendentes</p>
            </div>
          </motion.div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {[
            { id: 'journeys', label: 'Viagens', icon: null },
            { id: 'candidaturas', label: 'Candidaturas', icon: ambassadorApplications?.by_status?.candidatura?.length || null },
            { id: 'visibility', label: 'Visibilidade', icon: null },
            { id: 'contributions', label: 'Contribuições', icon: pendingContributions.length > 0 ? pendingContributions.length : null },
            { id: 'users', label: 'Utilizadores', icon: usersDashboard?.metrics?.premium_users || null },
            { id: 'raffles', label: 'Sorteios', icon: rafflesReady?.length || null },
            { id: 'sponsors', label: 'Sponsors', icon: sponsorsReport?.total_qualified_sponsors || null },
            { id: 'settings', label: 'Configurações', icon: null }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 rounded-xl font-medium transition-all whitespace-nowrap flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'bg-[#FFBE98] text-[#2D2A26]'
                  : 'bg-white border border-stone-200 text-[#6B6661] hover:bg-stone-50'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              {tab.label}
              {tab.icon && (
                <span className="w-5 h-5 bg-[#FFBE98] text-[#2D2A26] text-xs rounded-full flex items-center justify-center">
                  {tab.icon}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {/* Journeys Tab */}
          {activeTab === 'journeys' && (
            <motion.div
              key="journeys"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold">{t('admin.journeys')}</h2>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="btn-primary text-sm px-4 py-2 flex items-center gap-2"
                  data-testid="create-journey-btn"
                >
                  <Plus className="w-4 h-4" />
                  {t('admin.create')}
                </button>
              </div>

              {/* Create Form */}
              {showCreateForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mb-6 p-6 bg-stone-50 rounded-2xl"
                >
                  <h3 className="font-semibold mb-4">Nova Viagem</h3>
                  <div className="grid md:grid-cols-2 gap-4">
                    <input
                      type="text"
                      placeholder="Nome"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input-warm px-4"
                      data-testid="input-name"
                    />
                    <input
                      type="text"
                      placeholder="Nome Poético"
                      value={formData.poetic_name}
                      onChange={(e) => setFormData({ ...formData, poetic_name: e.target.value })}
                      className="input-warm px-4"
                    />
                    <input
                      type="text"
                      placeholder="Mensagem Emocional"
                      value={formData.emotional_message}
                      onChange={(e) => setFormData({ ...formData, emotional_message: e.target.value })}
                      className="input-warm px-4"
                    />
                    <input
                      type="text"
                      placeholder="Descrição do Impacto"
                      value={formData.impact_description}
                      onChange={(e) => setFormData({ ...formData, impact_description: e.target.value })}
                      className="input-warm px-4"
                    />
                    <input
                      type="url"
                      placeholder="URL da Imagem"
                      value={formData.image_url}
                      onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                      className="input-warm px-4"
                    />
                    <input
                      type="number"
                      placeholder="Objetivo (€)"
                      value={formData.goal_amount}
                      onChange={(e) => setFormData({ ...formData, goal_amount: parseFloat(e.target.value) })}
                      className="input-warm px-4"
                    />
                    <div>
                      <label className="block text-xs text-[#6B6661] mb-1">Data Objetivo</label>
                      <input
                        type="date"
                        value={formData.target_date}
                        onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                        className="input-warm px-4 w-full"
                        data-testid="input-target-date"
                      />
                    </div>
                    <textarea
                      placeholder="Descrição"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="input-warm px-4 py-3 md:col-span-2 h-24 resize-none"
                    />
                  </div>
                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={handleCreate}
                      className="btn-primary text-sm px-4 py-2 flex items-center gap-2"
                    >
                      <Save className="w-4 h-4" />
                      {t('admin.save')}
                    </button>
                    <button
                      onClick={() => setShowCreateForm(false)}
                      className="btn-secondary text-sm px-4 py-2"
                    >
                      Cancelar
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Journeys List */}
              <div className="space-y-4">
                {journeys.map((journey) => (
                  <div
                    key={journey.journey_id}
                    className="p-4 border border-stone-100 rounded-2xl"
                  >
                    {editingJourney?.journey_id === journey.journey_id ? (
                      <div className="space-y-3">
                        <div className="grid md:grid-cols-2 gap-3">
                          <input
                            type="text"
                            value={editingJourney.name}
                            onChange={(e) => setEditingJourney({ ...editingJourney, name: e.target.value })}
                            className="input-warm px-3 text-sm"
                          />
                          <input
                            type="text"
                            value={editingJourney.poetic_name}
                            onChange={(e) => setEditingJourney({ ...editingJourney, poetic_name: e.target.value })}
                            className="input-warm px-3 text-sm"
                          />
                          <input
                            type="number"
                            value={editingJourney.goal_amount}
                            onChange={(e) => setEditingJourney({ ...editingJourney, goal_amount: parseFloat(e.target.value) })}
                            className="input-warm px-3 text-sm"
                          />
                          <div>
                            <label className="block text-xs text-[#6B6661] mb-1">Data Objetivo</label>
                            <input
                              type="date"
                              value={editingJourney.target_date || ''}
                              onChange={(e) => setEditingJourney({ ...editingJourney, target_date: e.target.value })}
                              className="input-warm px-3 text-sm w-full"
                            />
                          </div>
                          <select
                            value={editingJourney.is_active}
                            onChange={(e) => setEditingJourney({ ...editingJourney, is_active: e.target.value === 'true' })}
                            className="input-warm px-3 text-sm"
                          >
                            <option value="true">Ativa</option>
                            <option value="false">Inativa</option>
                          </select>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdate(journey.journey_id)}
                            className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                          >
                            <Save className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setEditingJourney(null)}
                            className="p-2 bg-stone-100 text-stone-600 rounded-lg hover:bg-stone-200"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <img
                            src={journey.image_url}
                            alt={journey.name}
                            className="w-16 h-16 rounded-xl object-cover"
                          />
                          <div>
                            <h3 className="font-semibold">{journey.name}</h3>
                            <p className="text-sm text-[#6B6661]">{journey.poetic_name}</p>
                            <p className="text-xs text-[#6B6661]">
                              €{journey.current_amount.toLocaleString()} / €{journey.goal_amount.toLocaleString()}
                              {journey.target_date && (
                                <span className="ml-2 text-[#FFBE98]">
                                  • Objetivo: {new Date(journey.target_date).toLocaleDateString('pt-PT')}
                                </span>
                              )}
                              {!journey.is_active && (
                                <span className="ml-2 bg-red-100 text-red-600 px-2 py-0.5 rounded">Inativa</span>
                              )}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setEditingJourney(journey)}
                            className="p-2 hover:bg-stone-100 rounded-lg transition-colors"
                          >
                            <Edit2 className="w-4 h-4 text-[#6B6661]" />
                          </button>
                          <button
                            onClick={() => handleDelete(journey.journey_id)}
                            className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Candidaturas Tab */}
          {activeTab === 'candidaturas' && (
            <motion.div
              key="candidaturas"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <FileText className="w-5 h-5 text-[#FFBE98]" />
                    Candidaturas de Embaixadores
                  </h2>
                  <p className="text-sm text-[#6B6661] mt-1">Aprovar ou rejeitar candidaturas de viagens de embaixadores</p>
                </div>
                <div className="flex gap-2">
                  <select
                    value={applicationStatusFilter}
                    onChange={(e) => setApplicationStatusFilter(e.target.value)}
                    className="px-3 py-2 border border-stone-200 rounded-xl text-sm"
                  >
                    <option value="">Todos os estados</option>
                    <option value="candidatura">Pendentes</option>
                    <option value="aprovada">Aprovadas</option>
                    <option value="ativa">Ativas</option>
                    <option value="financiada">Financiadas</option>
                    <option value="realizada">Realizadas</option>
                    <option value="encerrada">Encerradas</option>
                  </select>
                  <button
                    onClick={async () => {
                      setLoadingApplications(true);
                      try {
                        const status = applicationStatusFilter ? `?status=${applicationStatusFilter}` : '';
                        const res = await axios.get(`${API}/admin/ambassador-journeys${status}`, { headers: getAuthHeaders() });
                        setAmbassadorApplications(res.data);
                      } catch (e) {
                        console.error(e);
                      }
                      setLoadingApplications(false);
                    }}
                    className="px-4 py-2 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-medium hover:bg-[#FFAB7D] transition-colors"
                  >
                    Carregar
                  </button>
                </div>
              </div>

              {loadingApplications && (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
                </div>
              )}

              {!loadingApplications && !ambassadorApplications && (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-stone-200 mx-auto mb-4" />
                  <p className="text-[#6B6661] mb-4">Clica em "Carregar" para ver as candidaturas</p>
                </div>
              )}

              {ambassadorApplications && (
                <div className="space-y-6">
                  {/* Summary by Status */}
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
                    {Object.entries(ambassadorApplications.by_status || {}).map(([status, items]) => (
                      <div 
                        key={status}
                        onClick={() => setApplicationStatusFilter(status)}
                        className={`p-3 rounded-xl border cursor-pointer transition-all ${
                          applicationStatusFilter === status 
                            ? 'border-[#FFBE98] bg-[#FFBE98]/10' 
                            : 'border-stone-100 hover:border-stone-200'
                        }`}
                      >
                        <p className="text-2xl font-bold text-[#2D2A26]">{items.length}</p>
                        <p className="text-xs text-[#6B6661] capitalize">{status}</p>
                      </div>
                    ))}
                  </div>

                  {/* Applications List */}
                  {ambassadorApplications.journeys?.length === 0 ? (
                    <p className="text-center text-[#6B6661] py-8">Nenhuma candidatura encontrada com este filtro.</p>
                  ) : (
                    <div className="space-y-4">
                      {ambassadorApplications.journeys?.map((application) => (
                        <div 
                          key={application.journey_id}
                          className={`p-5 border rounded-2xl transition-all ${
                            application.status === 'candidatura' 
                              ? 'border-[#F2C94C] bg-[#F2C94C]/5' 
                              : application.status === 'aprovada' 
                              ? 'border-blue-200 bg-blue-50/50'
                              : application.status === 'ativa'
                              ? 'border-green-200 bg-green-50/50'
                              : 'border-stone-100'
                          }`}
                        >
                          <div className="flex items-start gap-4">
                            {/* Image */}
                            <img 
                              src={application.image_url || 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=200'} 
                              alt={application.name} 
                              className="w-24 h-24 rounded-xl object-cover flex-shrink-0"
                            />
                            
                            {/* Content */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <h3 className="font-bold text-[#2D2A26] truncate">{application.name}</h3>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                  application.status === 'candidatura' ? 'bg-[#F2C94C]/20 text-[#F2C94C]' :
                                  application.status === 'aprovada' ? 'bg-blue-100 text-blue-600' :
                                  application.status === 'ativa' ? 'bg-green-100 text-green-600' :
                                  application.status === 'financiada' ? 'bg-purple-100 text-purple-600' :
                                  application.status === 'realizada' ? 'bg-[#FFBE98]/20 text-[#FFBE98]' :
                                  'bg-stone-100 text-stone-600'
                                }`}>
                                  {application.status}
                                </span>
                              </div>
                              
                              <p className="text-sm text-[#6B6661] mb-3 line-clamp-2">{application.description}</p>
                              
                              <div className="flex flex-wrap gap-4 text-xs text-[#6B6661]">
                                <span className="flex items-center gap-1">
                                  <Users className="w-3 h-3" />
                                  {application.ambassador_name}
                                </span>
                                <span className="flex items-center gap-1">
                                  <MapPin className="w-3 h-3" />
                                  {application.country || application.region || 'N/A'}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Target className="w-3 h-3" />
                                  €{application.goal_amount?.toLocaleString()}
                                </span>
                                {application.target_date && (
                                  <span className="flex items-center gap-1">
                                    <Calendar className="w-3 h-3" />
                                    {new Date(application.target_date).toLocaleDateString('pt-PT')}
                                  </span>
                                )}
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {new Date(application.created_at).toLocaleDateString('pt-PT')}
                                </span>
                              </div>

                              {/* Application Message */}
                              {application.application_message && (
                                <div className="mt-3 p-3 bg-stone-50 rounded-lg">
                                  <p className="text-xs text-[#6B6661] font-medium mb-1">Mensagem do embaixador:</p>
                                  <p className="text-sm text-[#2D2A26] italic">"{application.application_message}"</p>
                                </div>
                              )}
                            </div>

                            {/* Actions */}
                            <div className="flex flex-col gap-2 flex-shrink-0">
                              {application.status === 'candidatura' && (
                                <>
                                  <button
                                    onClick={async () => {
                                      try {
                                        await axios.put(
                                          `${API}/admin/ambassador-journeys/${application.journey_id}/status`,
                                          { status: 'aprovada' },
                                          { headers: getAuthHeaders() }
                                        );
                                        setAmbassadorApplications(prev => ({
                                          ...prev,
                                          journeys: prev.journeys.map(j => 
                                            j.journey_id === application.journey_id 
                                              ? {...j, status: 'aprovada'} 
                                              : j
                                          ),
                                          by_status: {
                                            ...prev.by_status,
                                            candidatura: prev.by_status.candidatura.filter(j => j.journey_id !== application.journey_id),
                                            aprovada: [...(prev.by_status.aprovada || []), {...application, status: 'aprovada'}]
                                          }
                                        }));
                                      } catch (e) {
                                        console.error(e);
                                        alert('Erro ao aprovar candidatura');
                                      }
                                    }}
                                    className="px-4 py-2 bg-green-100 text-green-600 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors flex items-center gap-1"
                                    data-testid={`approve-${application.journey_id}`}
                                  >
                                    <CheckCircle className="w-4 h-4" />
                                    Aprovar
                                  </button>
                                  <button
                                    onClick={async () => {
                                      if (!window.confirm('Tem certeza que deseja rejeitar esta candidatura?')) return;
                                      try {
                                        await axios.put(
                                          `${API}/admin/ambassador-journeys/${application.journey_id}/status`,
                                          { status: 'encerrada', admin_notes: 'Candidatura rejeitada pelo admin' },
                                          { headers: getAuthHeaders() }
                                        );
                                        setAmbassadorApplications(prev => ({
                                          ...prev,
                                          journeys: prev.journeys.map(j => 
                                            j.journey_id === application.journey_id 
                                              ? {...j, status: 'encerrada'} 
                                              : j
                                          ),
                                          by_status: {
                                            ...prev.by_status,
                                            candidatura: prev.by_status.candidatura.filter(j => j.journey_id !== application.journey_id),
                                            encerrada: [...(prev.by_status.encerrada || []), {...application, status: 'encerrada'}]
                                          }
                                        }));
                                      } catch (e) {
                                        console.error(e);
                                        alert('Erro ao rejeitar candidatura');
                                      }
                                    }}
                                    className="px-4 py-2 bg-red-100 text-red-600 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors flex items-center gap-1"
                                  >
                                    <XCircle className="w-4 h-4" />
                                    Rejeitar
                                  </button>
                                </>
                              )}
                              
                              {application.status === 'aprovada' && (
                                <button
                                  onClick={async () => {
                                    try {
                                      await axios.put(
                                        `${API}/admin/ambassador-journeys/${application.journey_id}/status`,
                                        { status: 'ativa' },
                                        { headers: getAuthHeaders() }
                                      );
                                      setAmbassadorApplications(prev => ({
                                        ...prev,
                                        journeys: prev.journeys.map(j => 
                                          j.journey_id === application.journey_id 
                                            ? {...j, status: 'ativa'} 
                                            : j
                                        ),
                                        by_status: {
                                          ...prev.by_status,
                                          aprovada: prev.by_status.aprovada.filter(j => j.journey_id !== application.journey_id),
                                          ativa: [...(prev.by_status.ativa || []), {...application, status: 'ativa'}]
                                        }
                                      }));
                                    } catch (e) {
                                      console.error(e);
                                      alert('Erro ao ativar viagem');
                                    }
                                  }}
                                  className="px-4 py-2 bg-blue-100 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-200 transition-colors flex items-center gap-1"
                                  data-testid={`activate-${application.journey_id}`}
                                >
                                  <Eye className="w-4 h-4" />
                                  Ativar
                                </button>
                              )}

                              {application.status === 'ativa' && (
                                <div className="text-center">
                                  <div className="text-xs text-[#6B6661] mb-1">Progresso</div>
                                  <div className="text-lg font-bold text-[#2D2A26]">
                                    {((application.current_amount / application.goal_amount) * 100).toFixed(0)}%
                                  </div>
                                  <div className="text-xs text-[#6B6661]">
                                    €{application.current_amount?.toLocaleString()} / €{application.goal_amount?.toLocaleString()}
                                  </div>
                                </div>
                              )}

                              {application.status === 'financiada' && (
                                <button
                                  onClick={async () => {
                                    try {
                                      await axios.put(
                                        `${API}/admin/ambassador-journeys/${application.journey_id}/status`,
                                        { status: 'realizada' },
                                        { headers: getAuthHeaders() }
                                      );
                                      setAmbassadorApplications(prev => ({
                                        ...prev,
                                        journeys: prev.journeys.map(j => 
                                          j.journey_id === application.journey_id 
                                            ? {...j, status: 'realizada'} 
                                            : j
                                        )
                                      }));
                                    } catch (e) {
                                      console.error(e);
                                      alert('Erro ao marcar como realizada');
                                    }
                                  }}
                                  className="px-4 py-2 bg-[#FFBE98] text-white rounded-lg text-sm font-medium hover:bg-[#E6A07C] transition-colors flex items-center gap-1"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                  Marcar Realizada
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* Visibility Tab */}
          {activeTab === 'visibility' && (
            <motion.div
              key="visibility"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <Star className="w-5 h-5 text-[#FFBE98]" />
                    Gestão de Visibilidade
                  </h2>
                  <p className="text-sm text-[#6B6661] mt-1">Destaque viagens e ajuste a sua visibilidade na plataforma</p>
                </div>
                <button
                  onClick={async () => {
                    setLoadingVisibility(true);
                    try {
                      await axios.post(`${API}/admin/recalculate-all-visibility`, {}, { headers: getAuthHeaders() });
                      const res = await axios.get(`${API}/admin/journeys-visibility?status=ativa`, { headers: getAuthHeaders() });
                      setVisibilityJourneys(res.data.journeys || []);
                    } catch (e) {
                      console.error(e);
                    }
                    setLoadingVisibility(false);
                  }}
                  className="px-4 py-2 bg-stone-100 hover:bg-stone-200 rounded-xl text-sm font-medium transition-colors"
                >
                  Recalcular Scores
                </button>
              </div>

              {/* Load visibility data on first view */}
              {visibilityJourneys.length === 0 && !loadingVisibility && (
                <div className="text-center py-12">
                  <Star className="w-12 h-12 text-stone-200 mx-auto mb-4" />
                  <p className="text-[#6B6661] mb-4">Carrega as viagens para gerir visibilidade</p>
                  <button
                    onClick={async () => {
                      setLoadingVisibility(true);
                      try {
                        const res = await axios.get(`${API}/admin/journeys-visibility?status=ativa`, { headers: getAuthHeaders() });
                        setVisibilityJourneys(res.data.journeys || []);
                      } catch (e) {
                        console.error(e);
                      }
                      setLoadingVisibility(false);
                    }}
                    className="px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium hover:bg-[#FFAB7D] transition-colors"
                  >
                    Carregar Viagens
                  </button>
                </div>
              )}

              {loadingVisibility && (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
                </div>
              )}

              {visibilityJourneys.length > 0 && (
                <div className="space-y-4">
                  {/* Legend */}
                  <div className="bg-stone-50 rounded-xl p-4 mb-6">
                    <p className="text-sm text-[#6B6661] mb-2"><strong>Critérios de Score:</strong></p>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs text-[#6B6661]">
                      <span>• Progresso (30%)</span>
                      <span>• Atividade recente (25%)</span>
                      <span>• Nº contribuições (20%)</span>
                      <span>• Impacto social (15%)</span>
                      <span>• Novidade (10%)</span>
                    </div>
                  </div>

                  {visibilityJourneys.map((journey) => (
                    <div key={journey.journey_id} className={`p-4 border rounded-xl transition-all ${journey.is_featured ? 'border-[#FFBE98] bg-[#FFBE98]/5' : 'border-stone-200'}`}>
                      <div className="flex items-start gap-4">
                        <img src={journey.image_url} alt={journey.name} className="w-20 h-20 rounded-lg object-cover" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-bold text-[#2D2A26] truncate">{journey.name}</h3>
                            {journey.is_featured && (
                              <span className="px-2 py-0.5 bg-[#FFBE98] text-white text-xs rounded-full flex items-center gap-1">
                                <Star className="w-3 h-3" /> Destaque
                              </span>
                            )}
                            {journey.hide_from_listings && (
                              <span className="px-2 py-0.5 bg-red-100 text-red-600 text-xs rounded-full">Oculta</span>
                            )}
                          </div>
                          <p className="text-sm text-[#6B6661] mb-2">por {journey.ambassador_name} • {journey.country || 'N/A'}</p>
                          
                          <div className="flex items-center gap-4 text-xs text-[#6B6661]">
                            <span>Score: <strong className="text-[#FFBE98]">{journey.calculated_score?.toFixed(1) || journey.visibility_score?.toFixed(1) || '0'}</strong></span>
                            <span>Boost: <strong className={journey.visibility_boost > 0 ? 'text-green-600' : journey.visibility_boost < 0 ? 'text-red-600' : ''}>{journey.visibility_boost || 0}</strong></span>
                            <span>Progresso: {((journey.current_amount / journey.goal_amount) * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        
                        <div className="flex flex-col gap-2">
                          {/* Feature/Unfeature */}
                          <button
                            onClick={async () => {
                              try {
                                await axios.post(`${API}/admin/journeys/${journey.journey_id}/update-visibility`, 
                                  { is_featured: !journey.is_featured },
                                  { headers: getAuthHeaders() }
                                );
                                setVisibilityJourneys(prev => prev.map(j => 
                                  j.journey_id === journey.journey_id ? {...j, is_featured: !j.is_featured} : j
                                ));
                              } catch (e) {
                                console.error(e);
                              }
                            }}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              journey.is_featured 
                                ? 'bg-[#FFBE98] text-white hover:bg-[#E6A07C]' 
                                : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'
                            }`}
                          >
                            {journey.is_featured ? '★ Remover Destaque' : '☆ Destacar'}
                          </button>
                          
                          {/* Boost controls */}
                          <div className="flex items-center gap-1">
                            <button
                              onClick={async () => {
                                const newBoost = Math.max(-100, (journey.visibility_boost || 0) - 10);
                                try {
                                  await axios.post(`${API}/admin/journeys/${journey.journey_id}/update-visibility`, 
                                    { visibility_boost: newBoost },
                                    { headers: getAuthHeaders() }
                                  );
                                  setVisibilityJourneys(prev => prev.map(j => 
                                    j.journey_id === journey.journey_id ? {...j, visibility_boost: newBoost} : j
                                  ));
                                } catch (e) {
                                  console.error(e);
                                }
                              }}
                              className="px-2 py-1 bg-red-50 text-red-600 rounded text-xs hover:bg-red-100"
                            >
                              -10
                            </button>
                            <span className="text-xs w-8 text-center">{journey.visibility_boost || 0}</span>
                            <button
                              onClick={async () => {
                                const newBoost = Math.min(100, (journey.visibility_boost || 0) + 10);
                                try {
                                  await axios.post(`${API}/admin/journeys/${journey.journey_id}/update-visibility`, 
                                    { visibility_boost: newBoost },
                                    { headers: getAuthHeaders() }
                                  );
                                  setVisibilityJourneys(prev => prev.map(j => 
                                    j.journey_id === journey.journey_id ? {...j, visibility_boost: newBoost} : j
                                  ));
                                } catch (e) {
                                  console.error(e);
                                }
                              }}
                              className="px-2 py-1 bg-green-50 text-green-600 rounded text-xs hover:bg-green-100"
                            >
                              +10
                            </button>
                          </div>
                          
                          {/* Hide toggle */}
                          <button
                            onClick={async () => {
                              try {
                                await axios.post(`${API}/admin/journeys/${journey.journey_id}/update-visibility`, 
                                  { hide_from_listings: !journey.hide_from_listings },
                                  { headers: getAuthHeaders() }
                                );
                                setVisibilityJourneys(prev => prev.map(j => 
                                  j.journey_id === journey.journey_id ? {...j, hide_from_listings: !j.hide_from_listings} : j
                                ));
                              } catch (e) {
                                console.error(e);
                              }
                            }}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                              journey.hide_from_listings 
                                ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                                : 'bg-stone-100 text-[#6B6661] hover:bg-stone-200'
                            }`}
                          >
                            {journey.hide_from_listings ? 'Mostrar' : 'Ocultar'}
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Contributions Tab */}
          {activeTab === 'contributions' && (
            <motion.div
              key="contributions"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <h2 className="text-xl font-bold mb-6">Gestão de Contribuições</h2>
              
              {contributions.length === 0 ? (
                <p className="text-center text-[#6B6661] py-8">Nenhuma contribuição registada.</p>
              ) : (
                <div className="space-y-3">
                  {contributions.map((contrib) => (
                    <div
                      key={contrib.contribution_id}
                      className={`p-4 rounded-2xl border ${
                        contrib.status === 'pending_confirmation' 
                          ? 'border-[#F2C94C] bg-[#F2C94C]/5' 
                          : contrib.status === 'completed'
                          ? 'border-green-200 bg-green-50/50'
                          : 'border-stone-100'
                      }`}
                    >
                      <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold">€{contrib.amount}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              contrib.status === 'pending_confirmation' ? 'bg-[#F2C94C]/20 text-[#F2C94C]' :
                              contrib.status === 'completed' ? 'bg-green-100 text-green-600' :
                              contrib.status === 'rejected' ? 'bg-red-100 text-red-600' :
                              'bg-stone-100 text-stone-600'
                            }`}>
                              {contrib.status === 'pending_confirmation' ? 'Pendente' :
                               contrib.status === 'completed' ? 'Confirmada' :
                               contrib.status === 'rejected' ? 'Rejeitada' : contrib.status}
                            </span>
                            {contrib.is_crypto && (
                              <span className="text-xs bg-[#F2C94C] text-white px-2 py-0.5 rounded-full">
                                Crypto
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-[#6B6661]">
                            {contrib.user_name} • {contrib.user_email}
                          </p>
                          <p className="text-xs text-[#6B6661]">
                            {contrib.journey_name} • {contrib.payment_method} • {new Date(contrib.created_at).toLocaleDateString('pt-PT')}
                          </p>
                        </div>
                        
                        {contrib.status === 'pending_confirmation' && (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleConfirmContribution(contrib.contribution_id)}
                              className="p-2 bg-green-100 text-green-600 rounded-lg hover:bg-green-200 flex items-center gap-1"
                              data-testid={`confirm-${contrib.contribution_id}`}
                            >
                              <CheckCircle className="w-4 h-4" />
                              <span className="text-sm">Confirmar</span>
                            </button>
                            <button
                              onClick={() => handleRejectContribution(contrib.contribution_id)}
                              className="p-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 flex items-center gap-1"
                            >
                              <XCircle className="w-4 h-4" />
                              <span className="text-sm">Rejeitar</span>
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && usersDashboard && (
            <motion.div
              key="users"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              {/* Platform Momentum Score */}
              <div className="bg-gradient-to-r from-[#2D2A26] to-[#4A4640] rounded-2xl p-6 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm opacity-80 mb-1">Platform Momentum Score</h3>
                    <p className="text-4xl font-bold">{usersDashboard.metrics.momentum_score}</p>
                    <p className="text-xs opacity-60 mt-1">novos registos + sonhadores + contribuições + referrals (7 dias)</p>
                  </div>
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-xl font-bold">{usersDashboard.metrics.weekly_signups}</p>
                      <p className="text-xs opacity-60">Novos</p>
                    </div>
                    <div>
                      <p className="text-xl font-bold">{usersDashboard.metrics.weekly_sonhadores}</p>
                      <p className="text-xs opacity-60">Sonhadores</p>
                    </div>
                    <div>
                      <p className="text-xl font-bold">{usersDashboard.metrics.weekly_contributions}</p>
                      <p className="text-xs opacity-60">Contrib.</p>
                    </div>
                    <div>
                      <p className="text-xl font-bold">{usersDashboard.metrics.valid_referrals_total}</p>
                      <p className="text-xs opacity-60">Referrals</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* 3 Questions Section */}
              <div className="grid md:grid-cols-3 gap-4">
                {/* Q1: A plataforma está a crescer? */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    A crescer?
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Novos utilizadores</span>
                      <span className="font-bold text-[#2D2A26]">+{usersDashboard.metrics.weekly_signups} <span className="text-xs text-[#6B6661]">/ 7d</span></span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Novos sonhadores</span>
                      <span className="font-bold text-[#FFBE98]">+{usersDashboard.metrics.weekly_sonhadores} <span className="text-xs text-[#6B6661]">/ 7d</span></span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Novos premium</span>
                      <span className="font-bold text-[#F2C94C]">+{usersDashboard.metrics.weekly_premium} <span className="text-xs text-[#6B6661]">/ 7d</span></span>
                    </div>
                    <div className="pt-3 border-t border-stone-100">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-[#6B6661]">Total utilizadores</span>
                        <span className="font-bold">{usersDashboard.metrics.total_users}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Q2: Está a gerar impacto real? */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-[#FFBE98]" />
                    Impacto real?
                  </h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Total financiado</span>
                      <span className="font-bold text-[#2D2A26]">€{usersDashboard.metrics.total_contributions_value.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Nº contribuições</span>
                      <span className="font-bold">{usersDashboard.metrics.total_contributions_count}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Média por contrib.</span>
                      <span className="font-bold">€{usersDashboard.metrics.average_contribution_value}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-[#6B6661]">Gerado via sponsors</span>
                      <span className="font-bold text-[#FFBE98]">€{usersDashboard.metrics.total_sponsor_impact?.toLocaleString() || 0}</span>
                    </div>
                    <div className="pt-3 border-t border-stone-100">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-[#6B6661]">Viagens financiadas</span>
                        <span className="font-bold text-green-500">{usersDashboard.metrics.journeys_funded} / {usersDashboard.metrics.journeys_active + usersDashboard.metrics.journeys_funded}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Q3: Quem está a puxar a comunidade? */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                    <Users className="w-5 h-5 text-purple-500" />
                    Quem puxa?
                  </h3>
                  <div className="space-y-2">
                    <p className="text-xs text-[#6B6661] mb-2">Top Sponsors</p>
                    {usersDashboard.top_sponsors.length > 0 ? (
                      usersDashboard.top_sponsors.slice(0, 3).map((s, i) => (
                        <div key={s.user_id} className="flex justify-between items-center text-sm">
                          <span className="flex items-center gap-1">
                            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${i === 0 ? 'bg-[#F2C94C] text-white' : 'bg-stone-200'}`}>{i+1}</span>
                            {s.name}
                          </span>
                          <span className="font-bold text-[#FFBE98]">€{s.impact_value}</span>
                        </div>
                      ))
                    ) : <p className="text-xs text-[#6B6661]">Sem sponsors ainda</p>}
                    <p className="text-xs text-[#6B6661] mt-3 mb-2">Top Contribuidores</p>
                    {usersDashboard.top_contributors?.length > 0 ? (
                      usersDashboard.top_contributors.slice(0, 3).map((c, i) => (
                        <div key={c.user_id} className="flex justify-between items-center text-sm">
                          <span className="flex items-center gap-1">
                            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${i === 0 ? 'bg-green-500 text-white' : 'bg-stone-200'}`}>{i+1}</span>
                            {c.name}
                          </span>
                          <span className="font-bold text-green-600">€{c.total_contributed}</span>
                        </div>
                      ))
                    ) : <p className="text-xs text-[#6B6661]">Sem contribuidores ainda</p>}
                  </div>
                </div>
              </div>

              {/* Charts Row - Evolução temporal */}
              <div className="grid md:grid-cols-4 gap-4">
                {/* Evolução utilizadores */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-3 text-sm">Evolução Utilizadores</h3>
                  <div className="flex items-end gap-1 h-20">
                    {(usersDashboard.charts?.signups_by_month || []).slice(-6).map((item, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center">
                        <div 
                          className="w-full bg-[#FFBE98] rounded-t transition-all"
                          style={{ height: `${Math.max(8, (item.count / Math.max(...(usersDashboard.charts?.signups_by_month || []).map(i => i.count), 1)) * 60)}px` }}
                        />
                        <span className="text-[7px] text-[#6B6661] mt-1">{item.month?.slice(5)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evolução financeira */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-3 text-sm">Evolução Financeira (€)</h3>
                  <div className="flex items-end gap-1 h-20">
                    {(usersDashboard.charts?.contributions_by_month || []).slice(-6).map((item, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center">
                        <div 
                          className="w-full bg-green-400 rounded-t transition-all"
                          style={{ height: `${Math.max(8, (item.amount / Math.max(...(usersDashboard.charts?.contributions_by_month || []).map(i => i.amount), 1)) * 60)}px` }}
                        />
                        <span className="text-[7px] text-[#6B6661] mt-1">€{item.amount}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Evolução referrals */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-3 text-sm">Evolução Referrals</h3>
                  <div className="flex items-end gap-1 h-20">
                    {(usersDashboard.charts?.referrals_by_month || []).slice(-6).map((item, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center">
                        <div 
                          className="w-full bg-purple-400 rounded-t transition-all"
                          style={{ height: `${Math.max(8, (item.count / Math.max(...(usersDashboard.charts?.referrals_by_month || []).map(i => i.count), 1)) * 60)}px` }}
                        />
                        <span className="text-[7px] text-[#6B6661] mt-1">{item.month?.slice(5)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Distribuição níveis */}
                <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                  <h3 className="font-bold text-[#2D2A26] mb-3 text-sm">Distribuição Níveis</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-stone-100 rounded-full overflow-hidden">
                        <div className="h-full bg-stone-400 rounded-full" style={{ width: `${(usersDashboard.level_distribution.curioso / usersDashboard.metrics.total_users * 100) || 0}%` }} />
                      </div>
                      <span className="text-xs text-[#6B6661]">{usersDashboard.level_distribution.curioso} Curioso</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-stone-100 rounded-full overflow-hidden">
                        <div className="h-full bg-[#FFBE98] rounded-full" style={{ width: `${(usersDashboard.level_distribution.sonhador / usersDashboard.metrics.total_users * 100) || 0}%` }} />
                      </div>
                      <span className="text-xs text-[#FFBE98]">{usersDashboard.level_distribution.sonhador} Sonhador</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-stone-100 rounded-full overflow-hidden">
                        <div className="h-full bg-[#F2C94C] rounded-full" style={{ width: `${(usersDashboard.level_distribution.premium / usersDashboard.metrics.total_users * 100) || 0}%` }} />
                      </div>
                      <span className="text-xs text-[#F2C94C]">{usersDashboard.level_distribution.premium} Premium</span>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-stone-100 text-xs">
                    <div className="flex justify-between">
                      <span className="text-[#6B6661]">Ativos (30d)</span>
                      <span className="font-medium">{usersDashboard.metrics.active_users}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Users Table */}
              <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                  <h3 className="font-bold text-[#2D2A26]">Lista de Utilizadores ({getFilteredUsers().length})</h3>
                  
                  {/* Filters */}
                  <div className="flex flex-wrap gap-2">
                    <input
                      type="text"
                      placeholder="Pesquisar..."
                      value={userSearch}
                      onChange={(e) => setUserSearch(e.target.value)}
                      className="px-3 py-1.5 border border-stone-200 rounded-lg text-sm w-40"
                    />
                    <select
                      value={userLevelFilter}
                      onChange={(e) => setUserLevelFilter(e.target.value)}
                      className="px-3 py-1.5 border border-stone-200 rounded-lg text-sm"
                    >
                      <option value="all">Todos níveis</option>
                      <option value="curioso">Curioso</option>
                      <option value="sonhador">Sonhador</option>
                      <option value="premium">Premium</option>
                    </select>
                    <select
                      value={userSubscriptionFilter}
                      onChange={(e) => setUserSubscriptionFilter(e.target.value)}
                      className="px-3 py-1.5 border border-stone-200 rounded-lg text-sm"
                    >
                      <option value="all">Subscrição</option>
                      <option value="active">Ativa</option>
                      <option value="inactive">Inativa</option>
                    </select>
                    <select
                      value={userSortBy}
                      onChange={(e) => setUserSortBy(e.target.value)}
                      className="px-3 py-1.5 border border-stone-200 rounded-lg text-sm"
                    >
                      <option value="referrals">Ordenar: Referrals</option>
                      <option value="contributions">Ordenar: Contribuições</option>
                      <option value="impact">Ordenar: Impacto</option>
                      <option value="date">Ordenar: Data</option>
                      <option value="name">Ordenar: Nome</option>
                    </select>
                    <button
                      onClick={() => setUserSortOrder(userSortOrder === 'desc' ? 'asc' : 'desc')}
                      className="px-3 py-1.5 border border-stone-200 rounded-lg text-sm hover:bg-stone-50"
                    >
                      {userSortOrder === 'desc' ? '↓' : '↑'}
                    </button>
                  </div>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-stone-100">
                        <th className="text-left py-3 px-2 text-[#6B6661] font-medium">Utilizador</th>
                        <th className="text-left py-3 px-2 text-[#6B6661] font-medium">Nível</th>
                        <th className="text-center py-3 px-2 text-[#6B6661] font-medium">Subs.</th>
                        <th className="text-center py-3 px-2 text-[#6B6661] font-medium">Referrals</th>
                        <th className="text-right py-3 px-2 text-[#6B6661] font-medium">Contribuições</th>
                        <th className="text-right py-3 px-2 text-[#6B6661] font-medium">Impacto</th>
                        <th className="text-center py-3 px-2 text-[#6B6661] font-medium">Membro desde</th>
                        <th className="text-center py-3 px-2 text-[#6B6661] font-medium">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getFilteredUsers().map(u => (
                        <tr key={u.user_id} className="border-b border-stone-50 hover:bg-stone-50 transition-colors">
                          <td className="py-3 px-2">
                            <div className="flex items-center gap-2">
                              {u.avatar ? (
                                <img src={u.avatar} alt="" className="w-8 h-8 rounded-full object-cover" />
                              ) : (
                                <div className="w-8 h-8 rounded-full bg-stone-200 flex items-center justify-center text-stone-500 text-xs font-medium">
                                  {u.name?.charAt(0)?.toUpperCase() || '?'}
                                </div>
                              )}
                              <div>
                                <p className="font-medium text-[#2D2A26]">{u.name}</p>
                                <p className="text-xs text-[#6B6661]">{u.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-2">{getLevelBadge(u.level)}</td>
                          <td className="py-3 px-2 text-center">
                            <button
                              onClick={() => toggleSubscription(u.user_id)}
                              disabled={updatingUser}
                              className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
                                u.subscription_active 
                                  ? 'bg-green-100 text-green-600 hover:bg-green-200' 
                                  : 'bg-stone-100 text-stone-400 hover:bg-stone-200'
                              }`}
                              title={u.subscription_active ? 'Desativar' : 'Ativar'}
                            >
                              {u.subscription_active ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                            </button>
                          </td>
                          <td className="py-3 px-2 text-center">
                            <span className="font-medium">{u.valid_referrals_count}</span>
                            <span className="text-[#6B6661]">/{u.referrals_made}</span>
                          </td>
                          <td className="py-3 px-2 text-right">
                            <span className="font-medium">€{u.contributions_total.toLocaleString()}</span>
                            <span className="text-[#6B6661] text-xs ml-1">({u.contributions_count})</span>
                          </td>
                          <td className="py-3 px-2 text-right">
                            <span className={`font-medium ${u.sponsor_impact_value > 0 ? 'text-[#FFBE98]' : 'text-[#6B6661]'}`}>
                              €{u.sponsor_impact_value.toLocaleString()}
                            </span>
                          </td>
                          <td className="py-3 px-2 text-center text-xs text-[#6B6661]">
                            {formatDate(u.registered_at)}
                          </td>
                          <td className="py-3 px-2 text-center">
                            <button
                              onClick={() => loadUserDetail(u.user_id)}
                              className="p-2 hover:bg-stone-100 rounded-lg transition-colors"
                              title="Ver detalhes"
                            >
                              <ChevronRight className="w-4 h-4 text-[#6B6661]" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* User Detail Modal */}
              {userDetail && selectedUser && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                  onClick={() => { setSelectedUser(null); setUserDetail(null); }}
                >
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
                    onClick={e => e.stopPropagation()}
                  >
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h3 className="text-xl font-bold text-[#2D2A26]">{userDetail.user.name}</h3>
                        <p className="text-sm text-[#6B6661]">{userDetail.user.email}</p>
                      </div>
                      <button
                        onClick={() => { setSelectedUser(null); setUserDetail(null); }}
                        className="p-2 hover:bg-stone-100 rounded-full"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    {/* User Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="bg-stone-50 rounded-xl p-4 text-center">
                        <p className="text-2xl font-bold text-[#2D2A26]">€{userDetail.contributions_total.toLocaleString()}</p>
                        <p className="text-xs text-[#6B6661]">Contribuições</p>
                      </div>
                      <div className="bg-stone-50 rounded-xl p-4 text-center">
                        <p className="text-2xl font-bold text-[#FFBE98]">{userDetail.user.valid_referrals_count || 0}</p>
                        <p className="text-xs text-[#6B6661]">Referrals Válidos</p>
                      </div>
                      <div className="bg-stone-50 rounded-xl p-4 text-center">
                        <p className="text-2xl font-bold text-[#F2C94C]">€{userDetail.sponsor_impact_value.toLocaleString()}</p>
                        <p className="text-xs text-[#6B6661]">Impacto</p>
                      </div>
                    </div>

                    {/* Admin Actions */}
                    <div className="space-y-4 mb-6">
                      <div className="flex items-center justify-between p-4 bg-stone-50 rounded-xl">
                        <div>
                          <p className="font-medium">Nível</p>
                          <p className="text-sm text-[#6B6661]">Atual: {getLevelBadge(userDetail.user.level)}</p>
                        </div>
                        <select
                          value={userDetail.user.level || 'curioso'}
                          onChange={(e) => updateUserLevel(userDetail.user.user_id, e.target.value)}
                          disabled={updatingUser}
                          className="px-4 py-2 border border-stone-200 rounded-xl bg-white"
                        >
                          <option value="curioso">Curioso</option>
                          <option value="sonhador">Sonhador</option>
                          <option value="premium">Premium</option>
                        </select>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-stone-50 rounded-xl">
                        <div>
                          <p className="font-medium">Subscrição</p>
                          <p className="text-sm text-[#6B6661]">{userDetail.user.subscription_active ? 'Ativa' : 'Inativa'}</p>
                        </div>
                        <button
                          onClick={() => toggleSubscription(userDetail.user.user_id)}
                          disabled={updatingUser}
                          className={`px-4 py-2 rounded-xl font-medium transition-colors ${
                            userDetail.user.subscription_active
                              ? 'bg-red-100 text-red-600 hover:bg-red-200'
                              : 'bg-green-100 text-green-600 hover:bg-green-200'
                          }`}
                        >
                          {userDetail.user.subscription_active ? 'Desativar' : 'Ativar'}
                        </button>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-stone-50 rounded-xl">
                        <div>
                          <p className="font-medium">Referrals Válidos</p>
                          <p className="text-sm text-[#6B6661]">Corrigir manualmente</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            min="0"
                            defaultValue={userDetail.user.valid_referrals_count || 0}
                            className="w-20 px-3 py-2 border border-stone-200 rounded-xl text-center"
                            onBlur={(e) => {
                              const newVal = parseInt(e.target.value);
                              if (newVal !== userDetail.user.valid_referrals_count) {
                                updateUserReferrals(userDetail.user.user_id, newVal);
                              }
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Sponsor Info */}
                    {userDetail.sponsor_info && (
                      <div className="mb-6">
                        <h4 className="font-medium mb-2">Convidado por</h4>
                        <div className="p-3 bg-stone-50 rounded-xl">
                          <p className="font-medium">{userDetail.sponsor_info.name}</p>
                          <p className="text-sm text-[#6B6661]">{userDetail.sponsor_info.email}</p>
                        </div>
                      </div>
                    )}

                    {/* Invited Users */}
                    {userDetail.invited_users.length > 0 && (
                      <div>
                        <h4 className="font-medium mb-2">Utilizadores Convidados ({userDetail.invited_users.length})</h4>
                        <div className="space-y-2 max-h-40 overflow-y-auto">
                          {userDetail.invited_users.map(inv => (
                            <div key={inv.user_id} className="flex items-center justify-between p-2 bg-stone-50 rounded-lg">
                              <div>
                                <p className="font-medium text-sm">{inv.name}</p>
                                <p className="text-xs text-[#6B6661]">{inv.email}</p>
                              </div>
                              <p className="text-sm font-medium text-[#FFBE98]">€{inv.contributions_total?.toLocaleString() || 0}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                </motion.div>
              )}
            </motion.div>
          )}

          {/* Raffles Tab */}
          {activeTab === 'raffles' && (
            <motion.div
              key="raffles"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <Gift className="w-8 h-8 text-[#FFBE98]" />
                <div>
                  <h2 className="text-xl font-bold">Sorteios</h2>
                  <p className="text-sm text-[#6B6661]">
                    Viagens que atingiram o objetivo de financiamento
                  </p>
                </div>
              </div>

              {rafflesReady.length > 0 ? (
                <div className="space-y-4">
                  {/* List of journeys ready for raffle */}
                  <div className="grid gap-4">
                    {rafflesReady.map((journey) => (
                      <div
                        key={journey.journey_id}
                        className={`p-4 rounded-xl border ${
                          journey.raffle_done 
                            ? 'border-green-200 bg-green-50' 
                            : 'border-[#FFBE98] bg-[#FFBE98]/10'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h3 className="font-bold text-[#2D2A26]">{journey.name}</h3>
                            <p className="text-sm text-[#6B6661]">
                              €{journey.current_amount.toLocaleString()} / €{journey.goal_amount.toLocaleString()} angariados
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium">
                              {journey.participant_count} participantes
                            </p>
                            {journey.raffle_done ? (
                              <span className="text-xs bg-green-500 text-white px-2 py-1 rounded-full">
                                Sorteado
                              </span>
                            ) : (
                              <span className="text-xs bg-[#FFBE98] text-[#2D2A26] px-2 py-1 rounded-full">
                                Pronto
                              </span>
                            )}
                          </div>
                        </div>

                        {journey.raffle_done && journey.raffle_result && (
                          <div className="bg-white rounded-lg p-3 mt-2">
                            <p className="text-sm font-medium text-green-600">
                              🎉 Vencedor: {journey.raffle_result.winner_name}
                            </p>
                            <p className="text-xs text-[#6B6661]">
                              {journey.raffle_result.winner_email}
                            </p>
                          </div>
                        )}

                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() => loadRaffleParticipants(journey.journey_id)}
                            className="flex-1 px-4 py-2 bg-white border border-stone-200 rounded-xl text-sm font-medium hover:bg-stone-50 transition-colors"
                          >
                            Ver Participantes
                          </button>
                          {!journey.raffle_done && (
                            <button
                              onClick={() => performRaffleDraw(journey.journey_id)}
                              disabled={drawingRaffle || journey.participant_count === 0}
                              className="flex-1 px-4 py-2 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-medium hover:bg-[#FFAB7D] transition-colors disabled:opacity-50"
                            >
                              {drawingRaffle ? 'A sortear...' : 'Realizar Sorteio'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Participants Modal/Section */}
                  {raffleParticipants && selectedRaffleJourney && (
                    <div className="mt-6 p-4 bg-stone-50 rounded-xl">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-bold">
                          Participantes - {rafflesReady.find(j => j.journey_id === selectedRaffleJourney)?.name}
                        </h3>
                        <button
                          onClick={() => { setRaffleParticipants(null); setSelectedRaffleJourney(null); }}
                          className="text-[#6B6661] hover:text-[#2D2A26]"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                      
                      {raffleParticipants.raffle_done && raffleParticipants.raffle_result && (
                        <div className="bg-green-100 rounded-lg p-3 mb-4">
                          <p className="text-sm font-medium text-green-700">
                            ✅ Sorteio já realizado - Vencedor: {raffleParticipants.raffle_result.winner_name}
                          </p>
                        </div>
                      )}

                      <div className="text-sm text-[#6B6661] mb-3">
                        {raffleParticipants.total_participants} participantes | {raffleParticipants.total_points} pontos totais
                      </div>
                      
                      <div className="max-h-64 overflow-y-auto space-y-2">
                        {raffleParticipants.participants?.map((participant, idx) => (
                          <div 
                            key={participant.user_id}
                            className={`p-3 rounded-lg bg-white flex items-center justify-between ${
                              raffleParticipants.raffle_result?.winner_user_id === participant.user_id 
                                ? 'border-2 border-green-500' 
                                : ''
                            }`}
                          >
                            <div className="flex items-center gap-2">
                              {idx === 0 && <Award className="w-4 h-4 text-[#F2C94C]" />}
                              {raffleParticipants.raffle_result?.winner_user_id === participant.user_id && (
                                <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">Vencedor</span>
                              )}
                              <div>
                                <p className="font-medium">{participant.user_name}</p>
                                <p className="text-xs text-[#6B6661]">{participant.user_email}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="font-bold text-[#FFBE98]">{participant.total_points} pontos</p>
                              <p className="text-xs text-[#6B6661]">{participant.entries.length} entradas</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-[#6B6661]">
                  <Gift className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Nenhuma viagem atingiu o objetivo de financiamento ainda.</p>
                  <p className="text-sm mt-2">
                    Os sorteios ficam disponíveis quando uma viagem atinge 100% do objetivo.
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {/* Sponsors Tab */}
          {activeTab === 'sponsors' && (
            <motion.div
              key="sponsors"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <Users className="w-8 h-8 text-[#FFBE98]" />
                <div>
                  <h2 className="text-xl font-bold">Sponsors Qualificados</h2>
                  <p className="text-sm text-[#6B6661]">
                    Utilizadores que convidaram 3+ amigos e estão a ganhar pontos
                  </p>
                </div>
              </div>

              {sponsorsReport && sponsorsReport.sponsors?.length > 0 ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-[#E6F4F1]/30 rounded-xl p-4 text-center">
                      <p className="text-3xl font-bold text-[#2D2A26]">
                        {sponsorsReport.total_qualified_sponsors}
                      </p>
                      <p className="text-sm text-[#6B6661]">Sponsors Qualificados</p>
                    </div>
                    <div className="bg-[#FFBE98]/10 rounded-xl p-4 text-center">
                      <p className="text-3xl font-bold text-[#2D2A26]">
                        {sponsorsReport.sponsors.reduce((acc, s) => acc + s.total_points, 0)}
                      </p>
                      <p className="text-sm text-[#6B6661]">Total de Pontos</p>
                    </div>
                  </div>

                  {/* Sponsors List */}
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {sponsorsReport.sponsors.map((sponsor, idx) => (
                      <div
                        key={sponsor.user_id}
                        className={`p-4 rounded-xl border ${
                          idx === 0 ? 'border-[#F2C94C] bg-[#F2C94C]/5' : 'border-stone-200 bg-stone-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            {idx === 0 && <Award className="w-5 h-5 text-[#F2C94C]" />}
                            <div>
                              <p className="font-semibold text-[#2D2A26]">
                                {sponsor.user_name}
                                {sponsor.alias && <span className="text-sm text-[#6B6661] ml-2">({sponsor.alias})</span>}
                              </p>
                              <p className="text-xs text-[#6B6661]">{sponsor.user_email}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-[#FFBE98]">{sponsor.total_points} pontos</p>
                            <p className="text-xs text-[#6B6661]">{sponsor.successful_referrals} referências</p>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs text-[#6B6661]">
                          <span>Viagem: {sponsor.journey_name}</span>
                          <span>{sponsor.registration_numbers.length} números de registo</span>
                        </div>
                        {sponsor.registration_numbers.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {sponsor.registration_numbers.slice(0, 5).map(num => (
                              <span key={num} className="text-xs bg-white px-2 py-0.5 rounded font-mono">
                                {num}
                              </span>
                            ))}
                            {sponsor.registration_numbers.length > 5 && (
                              <span className="text-xs text-[#6B6661]">
                                +{sponsor.registration_numbers.length - 5} mais
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-[#6B6661]">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Ainda não há sponsors qualificados.</p>
                  <p className="text-sm mt-2">
                    Os utilizadores precisam de convidar pelo menos 3 amigos para se qualificarem.
                  </p>
                </div>
              )}
            </motion.div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <motion.div
              key="settings"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <Settings className="w-8 h-8 text-[#FFBE98]" />
                <h2 className="text-xl font-bold">Configurações do Site</h2>
              </div>

              <div className="max-w-md space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    <Mail className="w-4 h-4 inline mr-2" />
                    Email de Contacto
                  </label>
                  <input
                    type="email"
                    value={settings.contact_email || ''}
                    onChange={(e) => setSettings({ ...settings, contact_email: e.target.value })}
                    placeholder="contacto@4luis.com"
                    className="w-full input-warm px-4"
                    data-testid="contact-email-input"
                  />
                  <p className="text-xs text-[#6B6661] mt-1">
                    Este email será mostrado na secção "Entre em Contacto"
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Mensagem de Contacto</label>
                  <textarea
                    value={settings.contact_message || ''}
                    onChange={(e) => setSettings({ ...settings, contact_message: e.target.value })}
                    placeholder="Tem alguma questão? Entre em contacto connosco."
                    className="w-full input-warm px-4 py-3 h-24 resize-none"
                  />
                </div>

                <button
                  onClick={handleSaveSettings}
                  className="btn-primary flex items-center gap-2"
                  data-testid="save-settings-btn"
                >
                  <Save className="w-5 h-5" />
                  Guardar Configurações
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default Admin;
