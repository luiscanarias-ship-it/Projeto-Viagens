import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Edit2, Trash2, Save, X, BarChart3 } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Admin = () => {
  const { user, loading: authLoading, getAuthHeaders } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  
  const [journeys, setJourneys] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingJourney, setEditingJourney] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    poetic_name: '',
    description: '',
    emotional_message: '',
    impact_description: '',
    image_url: '',
    goal_amount: 5000
  });

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      try {
        const headers = getAuthHeaders();
        const [journeysRes, statsRes] = await Promise.all([
          axios.get(`${API}/admin/journeys`, { headers, withCredentials: true }),
          axios.get(`${API}/admin/stats`, { headers, withCredentials: true })
        ]);
        
        setJourneys(journeysRes.data);
        setStats(statsRes.data);
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
        goal_amount: 5000
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

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center pt-20">
        <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-28 pb-12 px-6 md:px-12" data-testid="admin-page">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-4xl font-bold text-[#2D2A26] mb-2">
            {t('admin.title')}
          </h1>
          <p className="text-[#6B6661]">
            Gerir viagens e ver estatísticas
          </p>
        </motion.div>

        {/* Stats */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
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
          </motion.div>
        )}

        {/* Journeys Management */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
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
                  data-testid="input-poetic-name"
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
                  data-testid="save-journey-btn"
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
                        data-testid={`edit-${journey.journey_id}`}
                      >
                        <Edit2 className="w-4 h-4 text-[#6B6661]" />
                      </button>
                      <button
                        onClick={() => handleDelete(journey.journey_id)}
                        className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                        data-testid={`delete-${journey.journey_id}`}
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
      </div>
    </div>
  );
};

export default Admin;
