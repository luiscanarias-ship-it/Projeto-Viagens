import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Edit2, Trash2, Save, X, BarChart3, Settings, CheckCircle, XCircle, Mail, Users, Award, Gift, Crown, TrendingUp, UserPlus, ChevronRight, Star, FileText, Clock, MapPin, Target, Calendar, Eye, EyeOff, MessageSquare, AlertCircle, ExternalLink, History, Search, Heart, Sparkles, BookOpen, Wallet, ArrowUpRight, Banknote } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import JourneyEditForm from '../components/JourneyEditForm';
import EmailPreviewModal from '../components/EmailPreviewModal';
import AdminSupportSection from '../components/AdminSupportSection';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Admin = () => {
  const { user, loading: authLoading, getAuthHeaders, token } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('analytics');
  const [journeys, setJourneys] = useState([]);
  const [contributions, setContributions] = useState([]);
  const [contributionSearch, setContributionSearch] = useState('');
  const [searchingContribution, setSearchingContribution] = useState(false);
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
  // Email announce state
  const [showAnnounceSelect, setShowAnnounceSelect] = useState(false);
  const [emailPreview, setEmailPreview] = useState(null); // { previewUrl, sendUrl, title }
  // Candidaturas state
  const [ambassadorApplications, setAmbassadorApplications] = useState(null);
  const [openSupportCount, setOpenSupportCount] = useState(0);
  const [loadingApplications, setLoadingApplications] = useState(false);
  const [applicationStatusFilter, setApplicationStatusFilter] = useState('candidatura');
  // Candidatura detail modal state
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [applicationDetails, setApplicationDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  // Adjustment request state
  const [showAdjustmentModal, setShowAdjustmentModal] = useState(false);
  const [adjustmentRequest, setAdjustmentRequest] = useState('');
  const [adjustmentJourneyId, setAdjustmentJourneyId] = useState(null);
  const [generatingDescs, setGeneratingDescs] = useState(false);
  const [journeyFilter, setJourneyFilter] = useState('todas');
  // Payouts state
  const [payoutsData, setPayoutsData] = useState({ payouts: [], summary: { total: 0, pending: 0, processing: 0, completed: 0, total_pending_amount: 0, total_paid_amount: 0 } });
  const [payoutStatusFilter, setPayoutStatusFilter] = useState('all');
  const [editingPayout, setEditingPayout] = useState(null);
  const [payoutForm, setPayoutForm] = useState({ payment_method: '', payment_reference: '', admin_notes: '' });
  // Platform Revenue state
  const [platformRevenue, setPlatformRevenue] = useState(null);
  const [loadingPlatformRevenue, setLoadingPlatformRevenue] = useState(false);

  // Autosave: restore create form data from localStorage or server
  const CREATE_AUTOSAVE_KEY = 'autosave_journey_create';
  const defaultFormData = { name: '', poetic_name: '', description: '', emotional_message: '', impact_description: '', image_url: '', goal_amount: 5000, target_date: '' };
  const [formData, setFormData] = useState(defaultFormData);
  const [createFormAutosaved, setCreateFormAutosaved] = useState(false);
  const [createDraftLoaded, setCreateDraftLoaded] = useState(false);
  const createAutosaveTimer = useRef(null);
  const createServerTimer = useRef(null);

  // Load create draft from server or localStorage on mount
  useEffect(() => {
    if (createDraftLoaded || !token) return;
    setCreateDraftLoaded(true);
    const loadCreateDraft = async () => {
      // Try server first
      try {
        const res = await axios.get(`${API}/admin/drafts/journey_create/new`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.data?.data) {
          setFormData(prev => ({ ...defaultFormData, ...res.data.data }));
          return;
        }
      } catch { /* 404 */ }
      // Fallback to localStorage
      try {
        const raw = localStorage.getItem(CREATE_AUTOSAVE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed._autosave_ts && Date.now() - parsed._autosave_ts < 86400000) {
            const { _autosave_ts, ...data } = parsed;
            setFormData({ ...defaultFormData, ...data });
          } else {
            localStorage.removeItem(CREATE_AUTOSAVE_KEY);
          }
        }
      } catch { /* ignore */ }
    };
    loadCreateDraft();
  }, [token, createDraftLoaded]);

  // Autosave create form on changes (local + server)
  const isCreateFormDirty = JSON.stringify(formData) !== JSON.stringify(defaultFormData);
  useEffect(() => {
    if (!isCreateFormDirty || !showCreateForm) return;
    if (createAutosaveTimer.current) clearTimeout(createAutosaveTimer.current);
    createAutosaveTimer.current = setTimeout(() => {
      try {
        localStorage.setItem(CREATE_AUTOSAVE_KEY, JSON.stringify({ ...formData, _autosave_ts: Date.now() }));
      } catch { /* ignore */ }
      // Sync to server
      if (createServerTimer.current) clearTimeout(createServerTimer.current);
      createServerTimer.current = setTimeout(async () => {
        try {
          await axios.put(`${API}/admin/drafts/journey_create/new`,
            { data: formData },
            { headers: { Authorization: `Bearer ${token}` } }
          );
          setCreateFormAutosaved(true);
          setTimeout(() => setCreateFormAutosaved(false), 3000);
        } catch {
          setCreateFormAutosaved(true);
          setTimeout(() => setCreateFormAutosaved(false), 3000);
        }
      }, 500);
    }, 2000);
    return () => {
      if (createAutosaveTimer.current) clearTimeout(createAutosaveTimer.current);
      if (createServerTimer.current) clearTimeout(createServerTimer.current);
    };
  }, [formData, isCreateFormDirty, showCreateForm, token]);

  const clearCreateAutosave = useCallback(async () => {
    localStorage.removeItem(CREATE_AUTOSAVE_KEY);
    try {
      await axios.delete(`${API}/admin/drafts/journey_create/new`, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch { /* ignore */ }
  }, [token]);

  useEffect(() => {
    if (!authLoading && (!user || !user.is_admin)) {
      navigate('/');
      return;
    }

    const fetchData = async () => {
      try {
        const headers = getAuthHeaders();
        const [journeysRes, statsRes, settingsRes, contributionsRes, sponsorsRes, rafflesRes, usersRes, applicationsRes, supportRes, payoutsRes, platformRevenueRes] = await Promise.all([
          axios.get(`${API}/admin/journeys`, { headers, withCredentials: true }).catch(e => ({ data: [] })),
          axios.get(`${API}/admin/stats`, { headers, withCredentials: true }).catch(e => ({ data: {} })),
          axios.get(`${API}/admin/settings`, { headers, withCredentials: true }).catch(e => ({ data: {} })),
          axios.get(`${API}/admin/contributions`, { headers, withCredentials: true }).catch(e => ({ data: [] })),
          axios.get(`${API}/admin/sponsors-report`, { headers, withCredentials: true }).catch(e => ({ data: {} })),
          axios.get(`${API}/admin/journeys-ready-for-raffle`, { headers, withCredentials: true }).catch(e => ({ data: { ready_journeys: [] } })),
          axios.get(`${API}/admin/users/dashboard`, { headers, withCredentials: true }).catch(e => ({ data: null })),
          axios.get(`${API}/admin/ambassador-journeys?status=candidatura`, { headers, withCredentials: true }).catch(() => ({ data: { journeys: [] } })),
          axios.get(`${API}/admin/support/tickets?status=Aberto`, { headers, withCredentials: true }).catch(() => ({ data: { open_count: 0 } })),
          axios.get(`${API}/admin/payouts`, { headers, withCredentials: true }).catch(() => ({ data: { payouts: [], summary: {} } })),
          axios.get(`${API}/admin/platform-revenue`, { headers, withCredentials: true }).catch(() => ({ data: null }))
        ]);
        
        // Validate data before setting state
        setJourneys(Array.isArray(journeysRes.data) ? journeysRes.data : []);
        setStats(typeof statsRes.data === 'object' && !Array.isArray(statsRes.data) ? statsRes.data : {});
        setSettings(typeof settingsRes.data === 'object' && !Array.isArray(settingsRes.data) ? settingsRes.data : {});
        setContributions(Array.isArray(contributionsRes.data) ? contributionsRes.data : []);
        setSponsorsReport(typeof sponsorsRes.data === 'object' ? sponsorsRes.data : {});
        setRafflesReady(rafflesRes.data?.ready_journeys || []);
        setUsersDashboard(usersRes.data);
        // Store pending applications count
        if (applicationsRes.data?.journeys?.length > 0) {
          setAmbassadorApplications(applicationsRes.data);
        }
        setOpenSupportCount(supportRes.data?.open_count || 0);
        if (payoutsRes.data?.payouts) {
          setPayoutsData(payoutsRes.data);
        }
        // Platform revenue data
        if (platformRevenueRes?.data) {
          setPlatformRevenue(platformRevenueRes.data);
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
      clearCreateAutosave();
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

  const handleToggleSuspend = async (journey) => {
    const newActive = !journey.is_active;
    const action = newActive ? 'reativar' : 'suspender';
    if (!window.confirm(`Queres ${action} a viagem "${journey.name}"?`)) return;
    try {
      const headers = getAuthHeaders();
      const response = await axios.put(`${API}/admin/journeys/${journey.journey_id}`, 
        { ...journey, is_active: newActive }, { headers, withCredentials: true });
      setJourneys(journeys.map(j => j.journey_id === journey.journey_id ? response.data : j));
    } catch (error) {
      alert('Erro ao alterar estado da viagem');
    }
  };

  const handleSetMainTrip = async (journey) => {
    if (!window.confirm(`Definir "${journey.name}" como viagem principal?`)) return;
    try {
      const headers = getAuthHeaders();
      // First unset all as main
      for (const j of journeys.filter(j => j.is_main_trip)) {
        await axios.put(`${API}/admin/journeys/${j.journey_id}`, { ...j, is_main_trip: false }, { headers, withCredentials: true });
      }
      // Set the selected one as main
      const response = await axios.put(`${API}/admin/journeys/${journey.journey_id}`, 
        { ...journey, is_main_trip: true }, { headers, withCredentials: true });
      setJourneys(journeys.map(j => {
        if (j.journey_id === journey.journey_id) return response.data;
        return { ...j, is_main_trip: false };
      }));
    } catch (error) {
      alert('Erro ao definir viagem principal');
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

  const handleSearchContribution = async () => {
    if (!contributionSearch.trim()) {
      // If empty search, reload all contributions
      try {
        const headers = getAuthHeaders();
        const response = await axios.get(`${API}/admin/contributions`, { headers, withCredentials: true });
        setContributions(Array.isArray(response.data) ? response.data : []);
      } catch (error) {
        console.error('Error loading contributions:', error);
        setContributions([]);
      }
      return;
    }
    
    setSearchingContribution(true);
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/contributions/search?ref=${encodeURIComponent(contributionSearch.trim())}`, {
        headers,
        withCredentials: true
      });
      setContributions(Array.isArray(response.data?.contributions) ? response.data.contributions : []);
    } catch (error) {
      console.error('Error searching contribution:', error);
      alert('Erro ao pesquisar contribuição');
      setContributions([]);
    } finally {
      setSearchingContribution(false);
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

  // Load full application details with ambassador history
  const loadApplicationDetails = async (journeyId) => {
    setLoadingDetails(true);
    try {
      const headers = getAuthHeaders();
      const response = await axios.get(`${API}/admin/ambassador-journeys/${journeyId}/details`, { headers, withCredentials: true });
      setApplicationDetails(response.data);
      setSelectedApplication(journeyId);
    } catch (error) {
      console.error('Error loading application details:', error);
      alert('Erro ao carregar detalhes da candidatura');
    } finally {
      setLoadingDetails(false);
    }
  };

  // Close application details modal
  const closeApplicationDetails = () => {
    setSelectedApplication(null);
    setApplicationDetails(null);
  };

  // Approve application (auto-activates by default)
  const approveApplication = async (journeyId, autoActivate = true) => {
    try {
      const headers = getAuthHeaders();
      const response = await axios.put(
        `${API}/admin/ambassador-journeys/${journeyId}/status`,
        { status: 'aprovada', auto_activate: autoActivate },
        { headers, withCredentials: true }
      );
      
      const newStatus = response.data.new_status;
      alert(response.data.is_now_live 
        ? `✅ Viagem aprovada e ativada! Já está visível em "Sonhos em Materialização". ${response.data.email_sent ? 'Email enviado ao embaixador.' : ''}`
        : '✅ Candidatura aprovada!'
      );
      
      // Reload applications list
      const status = applicationStatusFilter ? `?status=${applicationStatusFilter}` : '';
      const res = await axios.get(`${API}/admin/ambassador-journeys${status}`, { headers });
      setAmbassadorApplications(res.data);
      closeApplicationDetails();
    } catch (error) {
      console.error('Error approving application:', error);
      alert('Erro ao aprovar candidatura');
    }
  };

  // Reject application
  const rejectApplication = async (journeyId, reason) => {
    if (!window.confirm('Tem certeza que deseja rejeitar esta candidatura?')) return;
    
    try {
      const headers = getAuthHeaders();
      await axios.put(
        `${API}/admin/ambassador-journeys/${journeyId}/status`,
        { status: 'encerrada', admin_notes: reason || 'Candidatura rejeitada pelo admin' },
        { headers, withCredentials: true }
      );
      
      alert('Candidatura rejeitada');
      
      // Reload applications list
      const status = applicationStatusFilter ? `?status=${applicationStatusFilter}` : '';
      const res = await axios.get(`${API}/admin/ambassador-journeys${status}`, { headers });
      setAmbassadorApplications(res.data);
      closeApplicationDetails();
    } catch (error) {
      console.error('Error rejecting application:', error);
      alert('Erro ao rejeitar candidatura');
    }
  };

  // Request adjustments
  const requestAdjustments = async () => {
    if (!adjustmentRequest.trim()) {
      alert('Por favor escreve o que precisa de ser ajustado');
      return;
    }
    
    try {
      const headers = getAuthHeaders();
      await axios.put(
        `${API}/admin/ambassador-journeys/${adjustmentJourneyId}/status`,
        { status: 'ajustes_pedidos', adjustment_request: adjustmentRequest },
        { headers, withCredentials: true }
      );
      
      alert('✅ Pedido de ajustes enviado ao embaixador');
      
      // Reload applications list
      const status = applicationStatusFilter ? `?status=${applicationStatusFilter}` : '';
      const res = await axios.get(`${API}/admin/ambassador-journeys${status}`, { headers });
      setAmbassadorApplications(res.data);
      
      // Reset state
      setShowAdjustmentModal(false);
      setAdjustmentRequest('');
      setAdjustmentJourneyId(null);
      closeApplicationDetails();
    } catch (error) {
      console.error('Error requesting adjustments:', error);
      alert('Erro ao pedir ajustes');
    }
  };

  // Open adjustment modal
  const openAdjustmentModal = (journeyId) => {
    setAdjustmentJourneyId(journeyId);
    setAdjustmentRequest('');
    setShowAdjustmentModal(true);
  };

  const getLevelBadge = (level) => {
    const badges = {
      sonhador: { bg: 'bg-[#FFBE98]/20', text: 'text-[#FFBE98]', label: 'Sonhador' },
      verificado: { bg: 'bg-[#5BB5A2]/20', text: 'text-[#5BB5A2]', label: 'Verificado' },
      embaixador: { bg: 'bg-[#F2C94C]/20', text: 'text-[#F2C94C]', label: 'Embaixador' }
    };
    const badge = badges[level] || badges.sonhador;
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
        <div className="flex flex-wrap gap-1.5 mb-6">
          {[
            { id: 'analytics', label: 'Analytics', icon: null },
            { id: 'revenue', label: 'Receita', icon: platformRevenue?.summary?.total_tips > 0 ? '€' : null },
            { id: 'journeys', label: 'Viagens', icon: null },
            { id: 'candidaturas', label: 'Candidaturas', icon: ambassadorApplications?.by_status?.candidatura?.length || null },
            { id: 'visibility', label: 'Visibilidade', icon: null },
            { id: 'contributions', label: 'Contribuições', icon: pendingContributions.length > 0 ? pendingContributions.length : null },
            { id: 'payouts', label: 'Payouts', icon: payoutsData.summary.pending > 0 ? payoutsData.summary.pending : null },
            { id: 'users', label: 'Utilizadores', icon: usersDashboard?.metrics?.premium_users || null },
            { id: 'raffles', label: 'Sorteios', icon: rafflesReady?.length || null },
            { id: 'sponsors', label: 'Sponsors', icon: sponsorsReport?.total_qualified_sponsors || null },
            { id: 'support', label: 'Suporte', icon: openSupportCount > 0 ? openSupportCount : null },
            { id: 'settings', label: 'Configurações', icon: null }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'bg-[#FFBE98] text-[#2D2A26]'
                  : 'bg-white border border-stone-200 text-[#6B6661] hover:bg-stone-50'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              {tab.label}
              {tab.icon && (
                <span className="w-4 h-4 bg-[#FFBE98] text-[#2D2A26] text-[10px] rounded-full flex items-center justify-center">
                  {tab.icon}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <AnalyticsDashboard token={token} />
            </motion.div>
          )}

          {/* Revenue Tab - Platform Monetization */}
          {activeTab === 'revenue' && (
            <motion.div
              key="revenue"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
              data-testid="revenue-tab"
            >
              <div className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100">
                <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                  <Banknote className="w-5 h-5 text-[#FFBE98]" />
                  Receita da Plataforma
                </h2>

                {platformRevenue ? (
                  <>
                    {/* Summary Cards */}
                    <div className="grid md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-2xl p-4 border border-emerald-200">
                        <p className="text-2xl font-bold text-emerald-700" data-testid="total-platform-revenue">
                          €{platformRevenue.summary.total_platform_revenue || 0}
                        </p>
                        <p className="text-sm text-emerald-600">Receita Total da Plataforma</p>
                      </div>
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-4 border border-purple-200">
                        <p className="text-2xl font-bold text-purple-700" data-testid="total-tips">
                          €{platformRevenue.summary.total_tips || 0}
                        </p>
                        <p className="text-sm text-purple-600">Total em Contribuições</p>
                        <p className="text-xs text-purple-500 mt-1">{platformRevenue.summary.tip_contributions || 0} contribuições</p>
                      </div>
                      <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-4 border border-blue-200">
                        <p className="text-2xl font-bold text-blue-700" data-testid="platform-campaign-revenue">
                          €{platformRevenue.summary.total_platform_campaign_revenue || 0}
                        </p>
                        <p className="text-sm text-blue-600">Campanhas da Plataforma</p>
                        <p className="text-xs text-blue-500 mt-1">{platformRevenue.summary.platform_campaign_contributions || 0} contribuições</p>
                      </div>
                      <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-2xl p-4 border border-amber-200">
                        <p className="text-2xl font-bold text-amber-700" data-testid="tip-conversion-rate">
                          {platformRevenue.summary.tip_conversion_rate || 0}%
                        </p>
                        <p className="text-sm text-amber-600">Taxa de Conversão</p>
                        <p className="text-xs text-amber-500 mt-1">Utilizadores que contribuem</p>
                      </div>
                    </div>

                    {/* Ambassador Stats */}
                    <div className="bg-stone-50 rounded-2xl p-4 mb-6">
                      <h3 className="font-semibold text-[#2D2A26] mb-3 flex items-center gap-2">
                        <Award className="w-4 h-4 text-[#FFBE98]" />
                        Apoio aos Embaixadores
                      </h3>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-lg font-bold text-[#2D2A26]">€{platformRevenue.summary.ambassador_support_total || 0}</p>
                          <p className="text-xs text-[#6B6661]">Total enviado para embaixadores</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold text-[#2D2A26]">{platformRevenue.summary.ambassador_contributions_count || 0}</p>
                          <p className="text-xs text-[#6B6661]">Contribuições em campanhas de embaixadores</p>
                        </div>
                      </div>
                      <p className="text-xs text-[#6B6661] mt-2 italic">
                        100% do apoio vai para os embaixadores. A plataforma só recebe as contribuições voluntárias.
                      </p>
                    </div>

                    {/* Tip Breakdown */}
                    {platformRevenue.tip_breakdown && platformRevenue.tip_breakdown.length > 0 && (
                      <div className="mb-6">
                        <h3 className="font-semibold text-[#2D2A26] mb-3 flex items-center gap-2">
                          <TrendingUp className="w-4 h-4 text-[#FFBE98]" />
                          Distribuição das Contribuições
                        </h3>
                        <div className="grid md:grid-cols-3 gap-3">
                          {platformRevenue.tip_breakdown.map((tip, idx) => (
                            <div key={idx} className="bg-white border border-stone-200 rounded-xl p-3">
                              <div className="flex justify-between items-center">
                                <span className="font-bold text-[#2D2A26]">€{tip.amount}</span>
                                <span className="text-xs bg-stone-100 px-2 py-0.5 rounded-full text-[#6B6661]">
                                  {tip.count} vezes
                                </span>
                              </div>
                              <p className="text-xs text-[#6B6661] mt-1">Total: €{tip.total}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recent Tips */}
                    {platformRevenue.recent_tips && platformRevenue.recent_tips.length > 0 && (
                      <div>
                        <h3 className="font-semibold text-[#2D2A26] mb-3 flex items-center gap-2">
                          <Heart className="w-4 h-4 text-[#FFBE98]" />
                          Contribuições Recentes
                        </h3>
                        <div className="space-y-2">
                          {platformRevenue.recent_tips.slice(0, 5).map((tip, idx) => (
                            <div key={idx} className="flex justify-between items-center py-2 border-b border-stone-100 last:border-0">
                              <div>
                                <p className="text-sm font-medium text-[#2D2A26]">
                                  €{tip.tip_amount} contribuição
                                </p>
                                <p className="text-xs text-[#6B6661]">
                                  Apoio: €{tip.support_amount || tip.amount - tip.tip_amount}
                                </p>
                              </div>
                              <span className="text-xs text-[#6B6661]">
                                {new Date(tip.created_at).toLocaleDateString('pt-PT')}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-12">
                    <Banknote className="w-12 h-12 text-stone-300 mx-auto mb-3" />
                    <p className="text-[#6B6661]">A carregar dados de receita...</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}
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
                <div className="flex items-center gap-2 relative">
                  <button
                    onClick={() => setEmailPreview({
                      previewUrl: '/admin/emails/preview/weekly-summary',
                      sendUrl: '/admin/emails/weekly-summary',
                      title: 'Preview: Resumo Semanal'
                    })}
                    className="px-3 py-2 bg-stone-100 text-[#2D2A26] rounded-xl font-medium text-xs hover:bg-stone-200 transition-colors flex items-center gap-1.5"
                    data-testid="send-weekly-summary-btn"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    Resumo Semanal
                  </button>
                  <div className="relative">
                    <button
                      onClick={() => setShowAnnounceSelect(!showAnnounceSelect)}
                      className="px-3 py-2 bg-blue-100 text-blue-700 rounded-xl font-medium text-xs hover:bg-blue-200 transition-colors flex items-center gap-1.5"
                      data-testid="announce-dream-btn"
                    >
                      <Heart className="w-3.5 h-3.5" />
                      Anunciar Novo Sonho
                    </button>
                    {showAnnounceSelect && (
                      <div className="absolute right-0 top-full mt-2 bg-white border border-stone-200 rounded-xl shadow-xl p-3 z-50 w-72" data-testid="announce-select-dropdown">
                        <p className="text-xs font-semibold text-[#6B6661] mb-2">Seleciona a viagem a anunciar:</p>
                        <div className="space-y-1 max-h-48 overflow-y-auto">
                          {journeys.filter(j => j.is_active && !j.announcement_email_sent).map(j => (
                            <button key={j.journey_id}
                              onClick={() => {
                                setShowAnnounceSelect(false);
                                setEmailPreview({
                                  previewUrl: `/admin/emails/preview/new-journey/${j.journey_id}`,
                                  sendUrl: `/admin/emails/new-journey/${j.journey_id}`,
                                  title: `Preview: Anunciar "${j.name}"`
                                });
                              }}
                              className="w-full text-left px-3 py-2 rounded-lg hover:bg-stone-50 transition-colors flex items-center gap-2 text-sm"
                              data-testid={`announce-journey-${j.journey_id}`}
                            >
                              <span className="font-semibold text-[#2D2A26]">{j.name}</span>
                              {j.is_main_trip && <Star className="w-3 h-3 text-[#F2C94C] fill-[#F2C94C]" />}
                            </button>
                          ))}
                          {journeys.filter(j => j.is_active && !j.announcement_email_sent).length === 0 && (
                            <p className="text-xs text-[#6B6661] py-2">Nenhuma viagem ativa por anunciar</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setShowCreateForm(true)}
                    className="btn-primary text-sm px-4 py-2 flex items-center gap-2"
                    data-testid="create-journey-btn"
                  >
                    <Plus className="w-4 h-4" />
                    {t('admin.create')}
                  </button>
                </div>
              </div>

              {/* Create Form */}
              {showCreateForm && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mb-6 p-6 bg-stone-50 rounded-2xl"
                >
                  <h3 className="font-semibold mb-4 flex items-center gap-3">
                    Nova Viagem
                    {createFormAutosaved && (
                      <span className="text-xs text-green-600 font-normal flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" /> Rascunho guardado
                      </span>
                    )}
                  </h3>
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
                      onClick={() => { clearCreateAutosave(); setShowCreateForm(false); setFormData(defaultFormData); }}
                      className="btn-secondary text-sm px-4 py-2"
                    >
                      Cancelar
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Journeys List */}
              <div className="space-y-3">
                {/* Status Filters */}
                <div className="flex gap-2 flex-wrap" data-testid="journey-filters">
                  {[
                    { id: 'todas', label: 'Todas', count: journeys.length },
                    { id: 'candidatura', label: 'Candidaturas', color: 'bg-amber-100 text-amber-700' },
                    { id: 'ativa', label: 'Ativas', color: 'bg-green-100 text-green-700' },
                    { id: 'financiada', label: 'Financiadas', color: 'bg-blue-100 text-blue-700' },
                    { id: 'realizada', label: 'Realizadas', color: 'bg-purple-100 text-purple-700' },
                    { id: 'encerrada', label: 'Encerradas', color: 'bg-stone-100 text-stone-500' }
                  ].map(f => {
                    const count = f.id === 'todas' ? journeys.length : journeys.filter(j => (j.status || 'ativa') === f.id).length;
                    return (
                      <button
                        key={f.id}
                        onClick={() => setJourneyFilter(f.id)}
                        data-testid={`filter-${f.id}`}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                          journeyFilter === f.id
                            ? 'bg-[#FFBE98] text-[#2D2A26] shadow-sm'
                            : 'bg-stone-50 text-[#6B6661] hover:bg-stone-100'
                        }`}
                      >
                        {f.label}
                        <span className={`w-5 h-5 text-[10px] rounded-full flex items-center justify-center ${
                          journeyFilter === f.id ? 'bg-white/40 text-[#2D2A26]' : 'bg-stone-200 text-[#6B6661]'
                        }`}>{count}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Table Header */}
                <div className="grid grid-cols-[1fr_100px_120px_130px_60px] gap-3 px-4 py-2 text-xs font-semibold text-[#6B6661] uppercase tracking-wider border-b border-stone-100">
                  <span>Viagem</span>
                  <span>Estado</span>
                  <span>Progresso</span>
                  <span>Owner</span>
                  <span></span>
                </div>

                {journeys
                  .filter(j => journeyFilter === 'todas' || (j.status || 'ativa') === journeyFilter)
                  .map((journey) => (
                  <div
                    key={journey.journey_id}
                    className="border border-stone-100 rounded-2xl overflow-hidden"
                  >
                    {editingJourney?.journey_id === journey.journey_id ? (
                      <JourneyEditForm
                        journey={editingJourney}
                        onSave={async (updatedForm) => {
                          try {
                            const headers = getAuthHeaders();
                            const response = await axios.put(`${API}/admin/journeys/${journey.journey_id}`, updatedForm, { headers, withCredentials: true });
                            setJourneys(journeys.map(j => j.journey_id === journey.journey_id ? response.data : j));
                            setEditingJourney(null);
                          } catch (error) {
                            console.error('Error updating journey:', error);
                            alert('Erro ao atualizar viagem');
                          }
                        }}
                        onCancel={() => setEditingJourney(null)}
                        getAuthHeaders={getAuthHeaders}
                        token={token}
                        onEmailPreview={(preview) => setEmailPreview(preview)}
                      />
                    ) : (
                      <div className="grid grid-cols-[1fr_100px_120px_130px_60px] gap-3 items-center p-4" data-testid={`journey-row-${journey.journey_id}`}>
                        <div className="flex items-center gap-3 min-w-0">
                          <img
                            src={journey.image_url}
                            alt={journey.name}
                            className="w-10 h-10 rounded-lg object-cover flex-shrink-0"
                          />
                          <div className="min-w-0">
                            <h3 className="font-semibold text-sm text-[#2D2A26] truncate">{journey.name}</h3>
                            <p className="text-xs text-[#6B6661] truncate">{journey.poetic_name}</p>
                          </div>
                        </div>
                        <div>
                          {(() => {
                            const s = journey.status || 'ativa';
                            const styles = {
                              candidatura: 'bg-amber-100 text-amber-700',
                              ativa: 'bg-green-100 text-green-700',
                              financiada: 'bg-blue-100 text-blue-700',
                              realizada: 'bg-purple-100 text-purple-700',
                              encerrada: 'bg-stone-100 text-stone-500'
                            };
                            return (
                              <span className={`text-xs font-semibold px-2 py-1 rounded-lg ${styles[s] || styles.ativa}`} data-testid={`status-${journey.journey_id}`}>
                                {s.charAt(0).toUpperCase() + s.slice(1)}
                              </span>
                            );
                          })()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 h-1.5 bg-stone-100 rounded-full overflow-hidden max-w-[70px]">
                              <div
                                className="h-full bg-gradient-to-r from-[#FFBE98] to-[#F2C94C] rounded-full"
                                style={{ width: `${Math.min(100, journey.goal_amount > 0 ? (journey.current_amount / journey.goal_amount) * 100 : 0)}%` }}
                              />
                            </div>
                            <span className="text-xs font-bold text-[#2D2A26]">
                              {journey.goal_amount > 0 ? Math.round((journey.current_amount / journey.goal_amount) * 100) : 0}%
                            </span>
                          </div>
                        </div>
                        <div className="text-xs text-[#6B6661] truncate">
                          {journey.is_ambassador_journey ? (journey.ambassador_name || 'Embaixador') : 'Admin'}
                        </div>
                        <div className="flex gap-1">
                          {journey.is_main_trip && (
                            <span className="px-1.5 py-0.5 bg-[#F2C94C]/20 text-[#D4A017] rounded text-[10px] font-bold" data-testid={`main-badge-${journey.journey_id}`}>
                              Principal
                            </span>
                          )}
                          {journey.funding_status === 'pending_validation' && (
                            <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded text-[10px] font-bold animate-pulse" data-testid={`pending-badge-${journey.journey_id}`}>
                              Aguarda validação
                            </span>
                          )}
                          {journey.funding_status === 'completed' && (
                            <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-bold" data-testid={`completed-badge-${journey.journey_id}`}>
                              100% Financiado
                            </span>
                          )}
                          {!journey.is_active && !journey.funding_status && (
                            <span className="px-1.5 py-0.5 bg-red-100 text-red-600 rounded text-[10px] font-bold" data-testid={`suspended-badge-${journey.journey_id}`}>
                              Suspensa
                            </span>
                          )}
                        </div>
                        <div className="flex gap-1">
                          {journey.funding_status === 'pending_validation' && (
                            <button
                              onClick={async () => {
                                if (!window.confirm(`Aprovar financiamento de "${journey.name}"? Isto ativa a celebração.`)) return;
                                try {
                                  await axios.post(`${API}/admin/journey/${journey.journey_id}/approve-funding`, {}, { headers: getAuthHeaders() });
                                  alert('Financiamento aprovado! Celebração ativada.');
                                  fetchData();
                                } catch (e) {
                                  alert('Erro: ' + (e.response?.data?.detail || e.message));
                                }
                              }}
                              className="px-2 py-1 bg-green-500 text-white rounded-lg text-[10px] font-bold hover:bg-green-600 transition-colors flex items-center gap-1"
                              title="Aprovar financiamento"
                              data-testid={`approve-funding-btn-${journey.journey_id}`}
                            >
                              <CheckCircle className="w-3 h-3" /> Aprovar
                            </button>
                          )}
                          <button
                            onClick={() => handleSetMainTrip(journey)}
                            className={`p-1.5 rounded-lg transition-colors ${journey.is_main_trip ? 'bg-[#F2C94C]/20' : 'hover:bg-stone-100'}`}
                            title={journey.is_main_trip ? 'Viagem principal' : 'Definir como principal'}
                            data-testid={`set-main-btn-${journey.journey_id}`}
                          >
                            <Star className={`w-3.5 h-3.5 ${journey.is_main_trip ? 'text-[#F2C94C] fill-[#F2C94C]' : 'text-[#6B6661]'}`} />
                          </button>
                          <button
                            onClick={() => handleToggleSuspend(journey)}
                            className="p-1.5 hover:bg-stone-100 rounded-lg transition-colors"
                            title={journey.is_active ? 'Suspender viagem' : 'Reativar viagem'}
                            data-testid={`suspend-btn-${journey.journey_id}`}
                          >
                            {journey.is_active ? (
                              <EyeOff className="w-3.5 h-3.5 text-[#6B6661]" />
                            ) : (
                              <Eye className="w-3.5 h-3.5 text-green-600" />
                            )}
                          </button>
                          <button
                            onClick={() => setEditingJourney(journey)}
                            className="p-1.5 hover:bg-stone-100 rounded-lg transition-colors"
                            title="Editar viagem"
                            data-testid={`edit-btn-${journey.journey_id}`}
                          >
                            <Edit2 className="w-3.5 h-3.5 text-[#6B6661]" />
                          </button>
                          <button
                            onClick={() => handleDelete(journey.journey_id)}
                            className="p-1.5 hover:bg-red-50 rounded-lg transition-colors"
                            title="Eliminar viagem"
                            data-testid={`delete-btn-${journey.journey_id}`}
                          >
                            <Trash2 className="w-3.5 h-3.5 text-red-500" />
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
                              : application.status === 'ajustes_pedidos'
                              ? 'border-orange-300 bg-orange-50/50'
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
                              className="w-24 h-24 rounded-xl object-cover flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
                              onClick={() => loadApplicationDetails(application.journey_id)}
                            />
                            
                            {/* Content */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <h3 
                                  className="font-bold text-[#2D2A26] truncate cursor-pointer hover:text-[#FFBE98] transition-colors"
                                  onClick={() => loadApplicationDetails(application.journey_id)}
                                >
                                  {application.name}
                                </h3>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                  application.status === 'candidatura' ? 'bg-[#F2C94C]/20 text-[#F2C94C]' :
                                  application.status === 'ajustes_pedidos' ? 'bg-orange-100 text-orange-600' :
                                  application.status === 'aprovada' ? 'bg-blue-100 text-blue-600' :
                                  application.status === 'ativa' ? 'bg-green-100 text-green-600' :
                                  application.status === 'financiada' ? 'bg-purple-100 text-purple-600' :
                                  application.status === 'realizada' ? 'bg-[#FFBE98]/20 text-[#FFBE98]' :
                                  'bg-stone-100 text-stone-600'
                                }`}>
                                  {application.status === 'ajustes_pedidos' ? 'Ajustes Pedidos' : application.status}
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

                              {/* Application Message Preview */}
                              {application.application_message && (
                                <div className="mt-3 p-3 bg-stone-50 rounded-lg">
                                  <p className="text-xs text-[#6B6661] font-medium mb-1">Mensagem do embaixador:</p>
                                  <p className="text-sm text-[#2D2A26] italic line-clamp-2">"{application.application_message}"</p>
                                </div>
                              )}
                              
                              {/* Adjustment Request Warning */}
                              {application.status === 'ajustes_pedidos' && application.adjustment_request && (
                                <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                                  <p className="text-xs text-orange-600 font-medium mb-1 flex items-center gap-1">
                                    <AlertCircle className="w-3 h-3" />
                                    Ajustes pedidos:
                                  </p>
                                  <p className="text-sm text-orange-700">{application.adjustment_request}</p>
                                </div>
                              )}
                            </div>

                            {/* Actions */}
                            <div className="flex flex-col gap-2 flex-shrink-0">
                              {/* View Details button - Always visible */}
                              <button
                                onClick={() => loadApplicationDetails(application.journey_id)}
                                className="px-4 py-2 bg-stone-100 text-[#6B6661] rounded-lg text-sm font-medium hover:bg-stone-200 transition-colors flex items-center gap-1"
                                data-testid={`details-${application.journey_id}`}
                              >
                                <Eye className="w-4 h-4" />
                                Ver Detalhes
                              </button>
                              
                              {(application.status === 'candidatura' || application.status === 'ajustes_pedidos') && (
                                <>
                                  <button
                                    onClick={() => approveApplication(application.journey_id)}
                                    className="px-4 py-2 bg-green-100 text-green-600 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors flex items-center gap-1"
                                    data-testid={`approve-${application.journey_id}`}
                                  >
                                    <CheckCircle className="w-4 h-4" />
                                    Aprovar e Ativar
                                  </button>
                                  <button
                                    onClick={() => openAdjustmentModal(application.journey_id)}
                                    className="px-4 py-2 bg-orange-100 text-orange-600 rounded-lg text-sm font-medium hover:bg-orange-200 transition-colors flex items-center gap-1"
                                  >
                                    <MessageSquare className="w-4 h-4" />
                                    Pedir Ajustes
                                  </button>
                                  <button
                                    onClick={() => rejectApplication(application.journey_id)}
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
                                      const headers = getAuthHeaders();
                                      await axios.put(
                                        `${API}/admin/ambassador-journeys/${application.journey_id}/status`,
                                        { status: 'ativa' },
                                        { headers }
                                      );
                                      // Reload
                                      const status = applicationStatusFilter ? `?status=${applicationStatusFilter}` : '';
                                      const res = await axios.get(`${API}/admin/ambassador-journeys${status}`, { headers });
                                      setAmbassadorApplications(res.data);
                                    } catch (e) {
                                      console.error(e);
                                      alert('Erro ao ativar viagem');
                                    }
                                  }}
                                  className="px-4 py-2 bg-blue-100 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-200 transition-colors flex items-center gap-1"
                                  data-testid={`activate-${application.journey_id}`}
                                >
                                  <Eye className="w-4 h-4" />
                                  Ativar Viagem
                                </button>
                              )}

                              {application.status === 'ativa' && (
                                <div className="text-center p-2 bg-green-50 rounded-lg">
                                  <div className="text-xs text-green-600 mb-1">Progresso</div>
                                  <div className="text-lg font-bold text-green-700">
                                    {((application.current_amount / application.goal_amount) * 100).toFixed(0)}%
                                  </div>
                                  <div className="text-xs text-green-600">
                                    €{application.current_amount?.toLocaleString()} / €{application.goal_amount?.toLocaleString()}
                                  </div>
                                </div>
                              )}

                              {application.status === 'financiada' && (
                                <button
                                  onClick={async () => {
                                    try {
                                      const headers = getAuthHeaders();
                                      await axios.put(
                                        `${API}/admin/ambassador-journeys/${application.journey_id}/status`,
                                        { status: 'realizada' },
                                        { headers }
                                      );
                                      // Reload
                                      const status = applicationStatusFilter ? `?status=${applicationStatusFilter}` : '';
                                      const res = await axios.get(`${API}/admin/ambassador-journeys${status}`, { headers });
                                      setAmbassadorApplications(res.data);
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
              
              {/* Search by Payment Reference */}
              <div className="mb-6">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={contributionSearch}
                      onChange={(e) => setContributionSearch(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearchContribution()}
                      placeholder="Pesquisar por código de referência (ex: CN-1234)"
                      className="w-full px-4 py-3 border border-stone-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50"
                    />
                    {contributionSearch && (
                      <button
                        onClick={() => {
                          setContributionSearch('');
                          handleSearchContribution();
                        }}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B6661] hover:text-[#2D2A26]"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                  <button
                    onClick={handleSearchContribution}
                    disabled={searchingContribution}
                    className="px-6 py-3 bg-[#2D2A26] text-white rounded-xl hover:bg-[#4A4640] transition-all flex items-center gap-2"
                  >
                    {searchingContribution ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <Search className="w-4 h-4" />
                        Pesquisar
                      </>
                    )}
                  </button>
                </div>
                <p className="text-xs text-[#6B6661] mt-2">
                  💡 Os utilizadores recebem um código de referência (CN-XXXX) para incluir na descrição do pagamento.
                </p>
              </div>
              
              {contributions.length === 0 ? (
                <p className="text-center text-[#6B6661] py-8">
                  {contributionSearch ? 'Nenhuma contribuição encontrada com esse código.' : 'Nenhuma contribuição registada.'}
                </p>
              ) : (
                <div className="space-y-3">
                  {contributions.map((contrib) => (
                    <div
                      key={contrib.contribution_id}
                      className={`p-4 rounded-2xl border ${
                        contrib.status === 'pending' || contrib.status === 'pending_confirmation'
                          ? 'border-[#F2C94C] bg-[#F2C94C]/5' 
                          : contrib.status === 'completed'
                          ? 'border-green-200 bg-green-50/50'
                          : 'border-stone-100'
                      }`}
                    >
                      <div className="flex items-center justify-between flex-wrap gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <span className="font-semibold">€{contrib.amount}</span>
                            {/* Payment Reference Badge */}
                            {contrib.payment_reference && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-[#FFBE98]/20 text-[#FFBE98] font-mono font-bold">
                                {contrib.payment_reference}
                              </span>
                            )}
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              contrib.status === 'pending' || contrib.status === 'pending_confirmation' ? 'bg-[#F2C94C]/20 text-[#F2C94C]' :
                              contrib.status === 'completed' ? 'bg-green-100 text-green-600' :
                              contrib.status === 'rejected' ? 'bg-red-100 text-red-600' :
                              'bg-stone-100 text-stone-600'
                            }`}>
                              {contrib.status === 'pending' || contrib.status === 'pending_confirmation' ? 'Pendente' :
                               contrib.status === 'completed' ? 'Confirmada' :
                               contrib.status === 'rejected' ? 'Rejeitada' : contrib.status}
                            </span>
                            {contrib.crypto_type && (
                              <span className="text-xs bg-[#F2C94C] text-white px-2 py-0.5 rounded-full">
                                {contrib.crypto_type.toUpperCase()}
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-[#6B6661]">
                            {contrib.user_name || contrib.contributor_name || 'Anónimo'} • {contrib.user_email || contrib.contributor_email || ''}
                          </p>
                          <p className="text-xs text-[#6B6661]">
                            {contrib.journey_name} • {contrib.payment_method} • {new Date(contrib.created_at).toLocaleDateString('pt-PT')}
                          </p>
                        </div>
                        
                        {(contrib.status === 'pending' || contrib.status === 'pending_confirmation') && (
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
                          value={userDetail.user.level || 'sonhador'}
                          onChange={(e) => updateUserLevel(userDetail.user.user_id, e.target.value)}
                          disabled={updatingUser}
                          className="px-4 py-2 border border-stone-200 rounded-xl bg-white"
                        >
                          <option value="sonhador">Sonhador</option>
                          <option value="verificado">Sonhador Verificado</option>
                          <option value="embaixador">Embaixador</option>
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

          {/* Payouts Tab */}
          {activeTab === 'payouts' && (
            <motion.div
              key="payouts"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <h2 className="text-xl font-bold mb-6" data-testid="payouts-title">Pagamentos a Embaixadores</h2>
              
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                  <p className="text-xs text-amber-700 font-medium">Pendentes</p>
                  <p className="text-2xl font-bold text-amber-800" data-testid="payouts-pending-count">{payoutsData.summary.pending}</p>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                  <p className="text-xs text-blue-700 font-medium">Em processamento</p>
                  <p className="text-2xl font-bold text-blue-800" data-testid="payouts-processing-count">{payoutsData.summary.processing}</p>
                </div>
                <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
                  <p className="text-xs text-emerald-700 font-medium">Concluídos</p>
                  <p className="text-2xl font-bold text-emerald-800" data-testid="payouts-completed-count">{payoutsData.summary.completed}</p>
                </div>
                <div className="bg-stone-50 border border-stone-200 rounded-xl p-4">
                  <p className="text-xs text-[#6B6661] font-medium">Por pagar</p>
                  <p className="text-2xl font-bold text-[#2D2A26]" data-testid="payouts-pending-amount">{payoutsData.summary.total_pending_amount?.toFixed(0) || 0}</p>
                </div>
              </div>

              {/* Filter */}
              <div className="flex gap-2 mb-4">
                {['all', 'pending', 'processing', 'completed'].map(s => (
                  <button
                    key={s}
                    onClick={() => setPayoutStatusFilter(s)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${payoutStatusFilter === s ? 'bg-[#2D2A26] text-white' : 'bg-white border border-stone-200 text-[#6B6661] hover:bg-stone-50'}`}
                    data-testid={`payout-filter-${s}`}
                  >
                    {s === 'all' ? 'Todos' : s === 'pending' ? 'Pendentes' : s === 'processing' ? 'Em processamento' : 'Concluídos'}
                  </button>
                ))}
              </div>

              {/* Payouts list */}
              {payoutsData.payouts.length === 0 ? (
                <div className="bg-white border border-stone-200 rounded-xl p-8 text-center">
                  <Wallet className="w-10 h-10 text-stone-300 mx-auto mb-3" />
                  <p className="text-sm text-[#6B6661]">Nenhum payout registado ainda.</p>
                  <p className="text-xs text-stone-400 mt-1">Os payouts são criados automaticamente quando uma viagem de embaixador atinge 100% de financiamento.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {payoutsData.payouts
                    .filter(p => payoutStatusFilter === 'all' || p.status === payoutStatusFilter)
                    .map(payout => (
                    <div key={payout.payout_id} className="bg-white border border-stone-200 rounded-xl p-4" data-testid={`payout-card-${payout.payout_id}`}>
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-sm text-[#2D2A26]">{payout.journey_name}</h3>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                              payout.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                              payout.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                              'bg-emerald-100 text-emerald-700'
                            }`} data-testid={`payout-status-${payout.payout_id}`}>
                              {payout.status === 'pending' ? 'Pendente' : payout.status === 'processing' ? 'Em processamento' : 'Concluído'}
                            </span>
                          </div>
                          <p className="text-xs text-[#6B6661] mt-1">
                            Embaixador: <strong>{payout.ambassador_name}</strong>
                          </p>
                          <p className="text-xs text-stone-400 mt-0.5">
                            Criado: {new Date(payout.created_at).toLocaleDateString('pt-PT')}
                            {payout.completed_at && ` | Pago: ${new Date(payout.completed_at).toLocaleDateString('pt-PT')}`}
                          </p>
                          {payout.payment_method && (
                            <p className="text-xs text-[#6B6661] mt-1">Método: {payout.payment_method} {payout.payment_reference && `| Ref: ${payout.payment_reference}`}</p>
                          )}
                          {payout.admin_notes && (
                            <p className="text-xs text-stone-400 mt-0.5 italic">Notas: {payout.admin_notes}</p>
                          )}
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-lg font-bold text-[#2D2A26]">{payout.amount?.toFixed(0)}</p>
                          <p className="text-[10px] text-[#6B6661]">objetivo: {payout.goal_amount?.toFixed(0)}</p>
                        </div>
                      </div>
                      
                      {/* Actions */}
                      {payout.status !== 'completed' && (
                        <div className="mt-3 pt-3 border-t border-stone-100">
                          {editingPayout === payout.payout_id ? (
                            <div className="space-y-2">
                              <div className="grid grid-cols-2 gap-2">
                                <input
                                  type="text"
                                  placeholder="Método (ex: IBAN, PayPal)"
                                  value={payoutForm.payment_method}
                                  onChange={e => setPayoutForm({...payoutForm, payment_method: e.target.value})}
                                  className="px-2 py-1.5 border border-stone-200 rounded-lg text-xs"
                                  data-testid={`payout-method-input-${payout.payout_id}`}
                                />
                                <input
                                  type="text"
                                  placeholder="Referência"
                                  value={payoutForm.payment_reference}
                                  onChange={e => setPayoutForm({...payoutForm, payment_reference: e.target.value})}
                                  className="px-2 py-1.5 border border-stone-200 rounded-lg text-xs"
                                  data-testid={`payout-ref-input-${payout.payout_id}`}
                                />
                              </div>
                              <input
                                type="text"
                                placeholder="Notas (opcional)"
                                value={payoutForm.admin_notes}
                                onChange={e => setPayoutForm({...payoutForm, admin_notes: e.target.value})}
                                className="w-full px-2 py-1.5 border border-stone-200 rounded-lg text-xs"
                                data-testid={`payout-notes-input-${payout.payout_id}`}
                              />
                              <div className="flex gap-2">
                                {payout.status === 'pending' && (
                                  <button
                                    onClick={async () => {
                                      try {
                                        await axios.put(`${API}/admin/payouts/${payout.payout_id}/status`, {
                                          status: 'processing',
                                          ...payoutForm
                                        }, { headers: getAuthHeaders() });
                                        const res = await axios.get(`${API}/admin/payouts`, { headers: getAuthHeaders() });
                                        setPayoutsData(res.data);
                                        setEditingPayout(null);
                                      } catch (e) { alert(e.response?.data?.detail || 'Erro'); }
                                    }}
                                    className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700"
                                    data-testid={`payout-mark-processing-${payout.payout_id}`}
                                  >
                                    <ArrowUpRight className="w-3 h-3 inline mr-1" /> Marcar em processamento
                                  </button>
                                )}
                                <button
                                  onClick={async () => {
                                    if (!window.confirm('Marcar payout como concluído? Isto notifica o embaixador.')) return;
                                    try {
                                      await axios.put(`${API}/admin/payouts/${payout.payout_id}/status`, {
                                        status: 'completed',
                                        ...payoutForm
                                      }, { headers: getAuthHeaders() });
                                      const res = await axios.get(`${API}/admin/payouts`, { headers: getAuthHeaders() });
                                      setPayoutsData(res.data);
                                      setEditingPayout(null);
                                    } catch (e) { alert(e.response?.data?.detail || 'Erro'); }
                                  }}
                                  className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700"
                                  data-testid={`payout-mark-completed-${payout.payout_id}`}
                                >
                                  <CheckCircle className="w-3 h-3 inline mr-1" /> Concluir payout
                                </button>
                                <button
                                  onClick={() => setEditingPayout(null)}
                                  className="px-3 py-1.5 bg-stone-100 text-[#6B6661] rounded-lg text-xs font-medium hover:bg-stone-200"
                                >
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          ) : (
                            <button
                              onClick={() => {
                                setEditingPayout(payout.payout_id);
                                setPayoutForm({
                                  payment_method: payout.payment_method || '',
                                  payment_reference: payout.payment_reference || '',
                                  admin_notes: payout.admin_notes || ''
                                });
                              }}
                              className="px-3 py-1.5 bg-[#FFBE98] text-[#2D2A26] rounded-lg text-xs font-medium hover:bg-[#FFB080]"
                              data-testid={`payout-edit-btn-${payout.payout_id}`}
                            >
                              <Banknote className="w-3 h-3 inline mr-1" /> Processar pagamento
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {/* Support Tab */}
          {activeTab === 'support' && (
            <motion.div
              key="support"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <h2 className="text-xl font-bold mb-6">Pedidos de Suporte</h2>
              <AdminSupportSection token={token} API={API} />
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

        {/* Application Details Modal */}
        <AnimatePresence>
          {selectedApplication && applicationDetails && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
              onClick={closeApplicationDetails}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                {/* Header */}
                <div className="sticky top-0 bg-white border-b border-stone-100 p-6 flex items-start justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-[#2D2A26]">{applicationDetails.journey?.name}</h2>
                    <p className="text-[#6B6661]">Candidatura de {applicationDetails.ambassador?.name}</p>
                  </div>
                  <button
                    onClick={closeApplicationDetails}
                    className="p-2 hover:bg-stone-100 rounded-full transition-colors"
                  >
                    <X className="w-6 h-6 text-[#6B6661]" />
                  </button>
                </div>

                <div className="p-6 space-y-6">
                  {/* Journey Details */}
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <img 
                        src={applicationDetails.journey?.image_url || 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400'} 
                        alt={applicationDetails.journey?.name}
                        className="w-full h-48 object-cover rounded-xl"
                      />
                    </div>
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-sm font-medium text-[#6B6661] mb-1">Descrição</h3>
                        <p className="text-[#2D2A26]">{applicationDetails.journey?.description}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h3 className="text-sm font-medium text-[#6B6661] mb-1">Objetivo</h3>
                          <p className="text-xl font-bold text-[#FFBE98]">€{applicationDetails.journey?.goal_amount?.toLocaleString()}</p>
                        </div>
                        <div>
                          <h3 className="text-sm font-medium text-[#6B6661] mb-1">Destino</h3>
                          <p className="text-[#2D2A26]">{applicationDetails.journey?.country || applicationDetails.journey?.region || 'N/A'}</p>
                        </div>
                        {applicationDetails.journey?.target_date && (
                          <div>
                            <h3 className="text-sm font-medium text-[#6B6661] mb-1">Data Prevista</h3>
                            <p className="text-[#2D2A26]">{new Date(applicationDetails.journey?.target_date).toLocaleDateString('pt-PT')}</p>
                          </div>
                        )}
                        <div>
                          <h3 className="text-sm font-medium text-[#6B6661] mb-1">Estado</h3>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            applicationDetails.journey?.status === 'candidatura' ? 'bg-[#F2C94C]/20 text-[#F2C94C]' :
                            applicationDetails.journey?.status === 'ajustes_pedidos' ? 'bg-orange-100 text-orange-600' :
                            applicationDetails.journey?.status === 'aprovada' ? 'bg-blue-100 text-blue-600' :
                            applicationDetails.journey?.status === 'ativa' ? 'bg-green-100 text-green-600' :
                            'bg-stone-100 text-stone-600'
                          }`}>
                            {applicationDetails.journey?.status === 'ajustes_pedidos' ? 'Ajustes Pedidos' : applicationDetails.journey?.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Application Message */}
                  {applicationDetails.journey?.application_message && (
                    <div className="bg-stone-50 rounded-xl p-4">
                      <h3 className="text-sm font-medium text-[#6B6661] mb-2 flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" />
                        Mensagem do Embaixador
                      </h3>
                      <p className="text-[#2D2A26] italic">"{applicationDetails.journey?.application_message}"</p>
                    </div>
                  )}

                  {/* Ambassador Profile */}
                  <div className="border border-stone-100 rounded-xl p-5">
                    <h3 className="text-lg font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                      <Users className="w-5 h-5 text-[#FFBE98]" />
                      Perfil do Embaixador
                    </h3>
                    <div className="flex items-start gap-4">
                      {applicationDetails.ambassador?.avatar ? (
                        <img src={applicationDetails.ambassador.avatar} alt="" className="w-16 h-16 rounded-full object-cover" />
                      ) : (
                        <div className="w-16 h-16 rounded-full bg-[#FFBE98]/20 flex items-center justify-center text-[#FFBE98] text-xl font-bold">
                          {applicationDetails.ambassador?.name?.charAt(0)?.toUpperCase() || '?'}
                        </div>
                      )}
                      <div className="flex-1">
                        <h4 className="font-bold text-[#2D2A26]">{applicationDetails.ambassador?.name}</h4>
                        <p className="text-sm text-[#6B6661]">{applicationDetails.ambassador?.email}</p>
                        <p className="text-xs text-[#6B6661] mt-1">
                          Membro desde {applicationDetails.ambassador?.registered_at ? new Date(applicationDetails.ambassador.registered_at).toLocaleDateString('pt-PT') : 'N/A'}
                        </p>
                        <div className="flex gap-4 mt-3">
                          <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
                            applicationDetails.ambassador?.level === 'embaixador' ? 'bg-[#FFBE98]/20 text-[#FFBE98]' :
                            applicationDetails.ambassador?.level === 'sonhador' ? 'bg-blue-100 text-blue-600' :
                            'bg-stone-100 text-stone-600'
                          }`}>
                            {applicationDetails.ambassador?.level || 'curioso'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Ambassador History */}
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Contributions History */}
                    <div className="border border-stone-100 rounded-xl p-5">
                      <h3 className="text-sm font-bold text-[#2D2A26] mb-3 flex items-center gap-2">
                        <History className="w-4 h-4 text-green-500" />
                        Histórico de Contribuições
                      </h3>
                      <div className="text-center mb-4 p-3 bg-green-50 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">€{applicationDetails.ambassador_history?.total_contributed?.toLocaleString() || 0}</p>
                        <p className="text-xs text-green-600">Total contribuído</p>
                      </div>
                      {applicationDetails.ambassador_history?.contributions?.length > 0 ? (
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {applicationDetails.ambassador_history.contributions.slice(0, 5).map((c, i) => (
                            <div key={i} className="flex justify-between items-center text-sm p-2 bg-stone-50 rounded-lg">
                              <span className="text-[#6B6661]">{new Date(c.created_at).toLocaleDateString('pt-PT')}</span>
                              <span className="font-medium text-green-600">€{c.amount}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-[#6B6661] text-center">Sem contribuições registadas</p>
                      )}
                    </div>

                    {/* Referrals History */}
                    <div className="border border-stone-100 rounded-xl p-5">
                      <h3 className="text-sm font-bold text-[#2D2A26] mb-3 flex items-center gap-2">
                        <UserPlus className="w-4 h-4 text-purple-500" />
                        Referrals (Convites)
                      </h3>
                      <div className="text-center mb-4 p-3 bg-purple-50 rounded-lg">
                        <p className="text-2xl font-bold text-purple-600">{applicationDetails.ambassador_history?.valid_referrals_count || 0}</p>
                        <p className="text-xs text-purple-600">Referrals válidos</p>
                      </div>
                      {applicationDetails.ambassador_history?.referrals?.length > 0 ? (
                        <div className="space-y-2 max-h-32 overflow-y-auto">
                          {applicationDetails.ambassador_history.referrals.slice(0, 5).map((r, i) => (
                            <div key={i} className="flex justify-between items-center text-sm p-2 bg-stone-50 rounded-lg">
                              <span className="text-[#2D2A26]">{r.name}</span>
                              <span className={`text-xs px-2 py-0.5 rounded-full ${r.has_contributed ? 'bg-green-100 text-green-600' : 'bg-stone-200 text-stone-600'}`}>
                                {r.has_contributed ? 'Contribuiu' : 'Pendente'}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-[#6B6661] text-center">Sem convites registados</p>
                      )}
                    </div>
                  </div>

                  {/* Other Journeys */}
                  {applicationDetails.ambassador_history?.journeys_created?.length > 0 && (
                    <div className="border border-stone-100 rounded-xl p-5">
                      <h3 className="text-sm font-bold text-[#2D2A26] mb-3">Outras Viagens deste Embaixador</h3>
                      <div className="space-y-2">
                        {applicationDetails.ambassador_history.journeys_created.map((j, i) => (
                          <div key={i} className="flex justify-between items-center text-sm p-2 bg-stone-50 rounded-lg">
                            <span className="text-[#2D2A26]">{j.name}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              j.status === 'ativa' ? 'bg-green-100 text-green-600' :
                              j.status === 'financiada' ? 'bg-purple-100 text-purple-600' :
                              j.status === 'realizada' ? 'bg-[#FFBE98]/20 text-[#FFBE98]' :
                              'bg-stone-200 text-stone-600'
                            }`}>
                              {j.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {(applicationDetails.journey?.status === 'candidatura' || applicationDetails.journey?.status === 'ajustes_pedidos') && (
                    <div className="flex gap-3 pt-4 border-t border-stone-100">
                      <button
                        onClick={() => approveApplication(applicationDetails.journey?.journey_id)}
                        className="flex-1 px-6 py-3 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
                      >
                        <CheckCircle className="w-5 h-5" />
                        Aprovar e Ativar Viagem
                      </button>
                      <button
                        onClick={() => openAdjustmentModal(applicationDetails.journey?.journey_id)}
                        className="px-6 py-3 bg-orange-100 text-orange-600 rounded-xl font-medium hover:bg-orange-200 transition-colors flex items-center gap-2"
                      >
                        <MessageSquare className="w-5 h-5" />
                        Pedir Ajustes
                      </button>
                      <button
                        onClick={() => rejectApplication(applicationDetails.journey?.journey_id)}
                        className="px-6 py-3 bg-red-100 text-red-600 rounded-xl font-medium hover:bg-red-200 transition-colors flex items-center gap-2"
                      >
                        <XCircle className="w-5 h-5" />
                        Rejeitar
                      </button>
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading Details Overlay */}
        {loadingDetails && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
            <div className="bg-white rounded-2xl p-8">
              <div className="w-8 h-8 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-[#6B6661]">A carregar detalhes...</p>
            </div>
          </div>
        )}

        {/* Adjustment Request Modal */}
        <AnimatePresence>
          {showAdjustmentModal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
              onClick={() => setShowAdjustmentModal(false)}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-white rounded-2xl w-full max-w-lg p-6"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 className="text-xl font-bold text-[#2D2A26] mb-2 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-orange-500" />
                  Pedir Ajustes ao Embaixador
                </h3>
                <p className="text-sm text-[#6B6661] mb-4">
                  Descreve o que precisa de ser alterado ou melhorado na candidatura. O embaixador receberá um email com estas instruções.
                </p>
                <textarea
                  value={adjustmentRequest}
                  onChange={(e) => setAdjustmentRequest(e.target.value)}
                  placeholder="Ex: Por favor adiciona mais detalhes sobre o itinerário da viagem e uma imagem mais representativa do destino..."
                  className="w-full h-32 p-4 border border-stone-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50"
                />
                <div className="flex gap-3 mt-4">
                  <button
                    onClick={() => setShowAdjustmentModal(false)}
                    className="flex-1 px-4 py-3 bg-stone-100 text-[#6B6661] rounded-xl font-medium hover:bg-stone-200 transition-colors"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={requestAdjustments}
                    className="flex-1 px-4 py-3 bg-orange-500 text-white rounded-xl font-medium hover:bg-orange-600 transition-colors"
                  >
                    Enviar Pedido
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Email Preview Modal */}
        {emailPreview && (
          <EmailPreviewModal
            previewUrl={emailPreview.previewUrl}
            sendUrl={emailPreview.sendUrl}
            title={emailPreview.title}
            token={token}
            onClose={() => setEmailPreview(null)}
            onSent={async (data) => {
              alert(`Email enviado com sucesso para ${data.sent || data.recipient_count || '?'} destinatarios!`);
              // Reload journeys list
              try {
                const headers = getAuthHeaders();
                const response = await axios.get(`${API}/admin/journeys`, { headers, withCredentials: true });
                setJourneys(Array.isArray(response.data) ? response.data : []);
              } catch (e) {
                console.error('Error reloading journeys:', e);
              }
            }}
          />
        )}
      </div>
    </div>
  );
};

export default Admin;
