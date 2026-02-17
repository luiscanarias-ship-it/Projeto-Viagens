import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit2, Trash2, Save, X, BarChart3, Settings, CheckCircle, XCircle, Mail, Users, Award, Gift, Crown, TrendingUp, UserPlus, ChevronRight, Star } from 'lucide-react';
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
        const [journeysRes, statsRes, settingsRes, contributionsRes, sponsorsRes, rafflesRes] = await Promise.all([
          axios.get(`${API}/admin/journeys`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/stats`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/settings`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/contributions`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/sponsors-report`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/journeys-ready-for-raffle`, { headers, withCredentials: true })
        ]);
        
        setJourneys(journeysRes.data);
        setStats(statsRes.data);
        setSettings(settingsRes.data);
        setContributions(contributionsRes.data);
        setSponsorsReport(sponsorsRes.data);
        setRafflesReady(rafflesRes.data.ready_journeys || []);
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
            { id: 'contributions', label: 'Contribuições', icon: pendingContributions.length > 0 ? pendingContributions.length : null },
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
