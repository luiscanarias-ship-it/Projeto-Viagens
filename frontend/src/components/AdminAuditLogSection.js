import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { History, Search, Filter, ChevronDown, User, MapPin, CreditCard, Settings, Shield } from 'lucide-react';
import axios from 'axios';

const ACTION_LABELS = {
  journey_funding_approved: { label: 'Viagem aprovada (financiamento)', icon: MapPin, color: 'bg-green-100 text-green-700' },
  journey_status_changed: { label: 'Estado de viagem alterado', icon: MapPin, color: 'bg-blue-100 text-blue-700' },
  certification_changed: { label: 'Certificação alterada', icon: Shield, color: 'bg-purple-100 text-purple-700' },
  contribution_confirmed: { label: 'Contribuição confirmada', icon: CreditCard, color: 'bg-emerald-100 text-emerald-700' },
  contribution_rejected: { label: 'Contribuição rejeitada', icon: CreditCard, color: 'bg-red-100 text-red-700' },
  user_level_changed: { label: 'Nível de utilizador alterado', icon: User, color: 'bg-amber-100 text-amber-700' },
  user_referrals_changed: { label: 'Referrals corrigidos', icon: User, color: 'bg-amber-100 text-amber-700' },
  subscription_toggled: { label: 'Subscrição alterada', icon: User, color: 'bg-indigo-100 text-indigo-700' },
  settings_updated: { label: 'Configurações atualizadas', icon: Settings, color: 'bg-stone-100 text-stone-600' },
  dream_funded_email_sent: { label: 'Email sonho financiado enviado', icon: MapPin, color: 'bg-teal-100 text-teal-700' },
  new_journey_email_sent: { label: 'Email novo sonho enviado', icon: MapPin, color: 'bg-teal-100 text-teal-700' },
};

const TARGET_TYPE_LABELS = {
  journey: 'Viagem',
  contribution: 'Contribuição',
  user: 'Utilizador',
  settings: 'Configurações',
};

const AdminAuditLogSection = ({ token, API }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState('');
  const [filterTarget, setFilterTarget] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      let url = `${API}/admin/audit-logs?limit=200`;
      if (filterTarget) url += `&target_type=${filterTarget}`;
      const res = await axios.get(url, { headers: { Authorization: `Bearer ${token}` } });
      setLogs(res.data.logs || []);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  }, [API, token, filterTarget]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const filteredLogs = logs.filter(log => {
    if (filterAction && log.action !== filterAction) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const match = (log.target_id || '').toLowerCase().includes(term)
        || (log.admin_id || '').toLowerCase().includes(term)
        || (log.action || '').toLowerCase().includes(term)
        || JSON.stringify(log.metadata || {}).toLowerCase().includes(term);
      if (!match) return false;
    }
    return true;
  });

  const uniqueActions = [...new Set(logs.map(l => l.action))];

  const formatTimestamp = (ts) => {
    if (!ts) return '—';
    const d = new Date(ts);
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return 'Agora mesmo';
    if (diff < 3600) return `${Math.floor(diff / 60)}min atrás`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h atrás`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d atrás`;
    return d.toLocaleDateString('pt-PT', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getActionInfo = (action) => ACTION_LABELS[action] || { label: action, icon: History, color: 'bg-stone-100 text-stone-600' };

  return (
    <motion.div
      key="audit"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="bg-white rounded-3xl p-6 shadow-lg border border-stone-100"
      data-testid="audit-log-section"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <History className="w-8 h-8 text-[#FFBE98]" />
          <div>
            <h2 className="text-xl font-bold text-[#2D2A26]">Registo de Ações</h2>
            <p className="text-sm text-[#6B6661]">{filteredLogs.length} ações registadas</p>
          </div>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${showFilters ? 'bg-[#FFBE98]/20 text-[#FFBE98]' : 'bg-stone-50 text-[#6B6661] hover:bg-stone-100'}`}
          data-testid="audit-toggle-filters"
        >
          <Filter className="w-4 h-4" />
          Filtros
          <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {showFilters && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="mb-6 p-4 bg-stone-50 rounded-2xl space-y-3"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#6B6661] mb-1">Pesquisar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B6661]" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="ID, admin, ação..."
                  className="w-full pl-10 pr-4 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50"
                  data-testid="audit-search-input"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B6661] mb-1">Tipo de ação</label>
              <select
                value={filterAction}
                onChange={(e) => setFilterAction(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50 bg-white"
                data-testid="audit-filter-action"
              >
                <option value="">Todas as ações</option>
                {uniqueActions.map(a => (
                  <option key={a} value={a}>{getActionInfo(a).label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B6661] mb-1">Tipo de alvo</label>
              <select
                value={filterTarget}
                onChange={(e) => setFilterTarget(e.target.value)}
                className="w-full px-4 py-2 rounded-xl border border-stone-200 text-sm focus:outline-none focus:ring-2 focus:ring-[#FFBE98]/50 bg-white"
                data-testid="audit-filter-target"
              >
                <option value="">Todos</option>
                <option value="journey">Viagens</option>
                <option value="contribution">Contribuições</option>
                <option value="user">Utilizadores</option>
                <option value="settings">Configurações</option>
              </select>
            </div>
          </div>
        </motion.div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-[#FFBE98]" />
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="text-center py-16 text-[#6B6661]">
          <History className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="font-medium">Sem ações registadas</p>
          <p className="text-sm mt-1">As ações administrativas aparecerão aqui.</p>
        </div>
      ) : (
        <div className="space-y-2" data-testid="audit-log-list">
          {filteredLogs.map((log, i) => {
            const info = getActionInfo(log.action);
            const Icon = info.icon;
            return (
              <motion.div
                key={log.audit_id || i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: Math.min(i * 0.02, 0.5) }}
                className="flex items-start gap-3 p-3 rounded-xl hover:bg-stone-50 transition-colors group"
                data-testid={`audit-log-entry-${i}`}
              >
                <div className={`flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center ${info.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-[#2D2A26]">{info.label}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-stone-100 text-[#6B6661]">
                      {TARGET_TYPE_LABELS[log.target_type] || log.target_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-[#6B6661]">
                    <span className="font-mono">{(log.target_id || '').substring(0, 24)}</span>
                    <span>por <span className="font-medium">{(log.admin_id || '').substring(0, 16)}</span></span>
                  </div>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {Object.entries(log.metadata).map(([k, v]) => (
                        <span key={k} className="text-xs px-2 py-0.5 rounded-lg bg-stone-50 text-[#6B6661] border border-stone-100">
                          {k}: <span className="font-medium">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0 text-xs text-[#6B6661] text-right whitespace-nowrap">
                  {formatTimestamp(log.timestamp)}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
};

export default AdminAuditLogSection;
