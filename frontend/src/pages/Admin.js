import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit2, Trash2, Save, X, BarChart3, Settings, CheckCircle, XCircle, Gift, Mail } from 'lucide-react';
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
  const [raffleResult, setRaffleResult] = useState(null);
  const [selectedJourneyForRaffle, setSelectedJourneyForRaffle] = useState('');
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
        const [journeysRes, statsRes, settingsRes, contributionsRes] = await Promise.all([
          axios.get(`${API}/admin/journeys`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/stats`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/settings`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/contributions`, { headers, withCredentials: true })
        ]);
        
        setJourneys(journeysRes.data);
        setStats(statsRes.data);
        setSettings(settingsRes.data);
        setContributions(contributionsRes.data);
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

  const handleDrawRaffle = async () => {
    if (!selectedJourneyForRaffle) {
      alert('Selecione uma viagem para o sorteio');
      return;
    }
    
    if (!window.confirm('Tem certeza que deseja realizar o sorteio? Esta ação é irreversível.')) return;
    
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(`${API}/admin/raffle/${selectedJourneyForRaffle}/draw`, {}, {
        headers,
        withCredentials: true
      });
      setRaffleResult(response.data);
    } catch (error) {
      console.error('Error drawing raffle:', error);
      alert(error.response?.data?.detail || 'Erro ao realizar sorteio');
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
            { id: 'raffle', label: 'Sorteio', icon: null },
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
                <span className="w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
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

          {/* Raffle Tab */}
          {activeTab === 'raffle' && (
            <motion.div
              key="raffle"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
            >
              <div className="flex items-center gap-3 mb-6">
                <Gift className="w-8 h-8 text-[#FFBE98]" />
                <h2 className="text-xl font-bold">Sistema de Sorteio</h2>
              </div>

              <div className="max-w-md mx-auto">
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">Selecionar Viagem</label>
                  <select
                    value={selectedJourneyForRaffle}
                    onChange={(e) => setSelectedJourneyForRaffle(e.target.value)}
                    className="w-full input-warm px-4"
                  >
                    <option value="">Escolha uma viagem...</option>
                    {journeys.map((j) => (
                      <option key={j.journey_id} value={j.journey_id}>
                        {j.name} - €{j.current_amount.toLocaleString()} / €{j.goal_amount.toLocaleString()}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bg-[#E6F4F1]/30 rounded-2xl p-6 mb-6">
                  <h3 className="font-semibold mb-2">Regras do Sorteio</h3>
                  <ul className="text-sm text-[#6B6661] space-y-1">
                    <li>• Voucher de viagem de €5.000 se objetivo atingido</li>
                    <li>• 5% do valor angariado (máx. €2.500) se não atingido</li>
                    <li>• Só participam quem convidou 3+ amigos</li>
                    <li>• Contribuições em crypto = bilhetes em dobro</li>
                  </ul>
                </div>

                <button
                  onClick={handleDrawRaffle}
                  disabled={!selectedJourneyForRaffle}
                  className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
                  data-testid="draw-raffle-btn"
                >
                  <Gift className="w-5 h-5" />
                  Realizar Sorteio
                </button>

                {/* Raffle Result */}
                {raffleResult && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mt-6 p-6 bg-gradient-to-br from-[#F2C94C]/20 to-[#E0C097]/20 rounded-2xl text-center"
                  >
                    <Gift className="w-12 h-12 text-[#F2C94C] mx-auto mb-4" />
                    <h3 className="text-xl font-bold mb-2">Vencedor!</h3>
                    <p className="text-2xl font-bold text-[#2D2A26] mb-1">{raffleResult.winner.name}</p>
                    <p className="text-sm text-[#6B6661] mb-4">{raffleResult.winner.email}</p>
                    <p className="text-sm text-[#6B6661]">Bilhete: {raffleResult.winner.ticket_id}</p>
                    <p className="text-lg font-semibold text-[#FFBE98] mt-4">
                      Prémio: €{raffleResult.prize_amount.toLocaleString()}
                    </p>
                    <p className="text-xs text-[#6B6661] mt-2">
                      De um total de {raffleResult.total_tickets} bilhetes
                    </p>
                  </motion.div>
                )}
              </div>
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
