import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Filter, Clock, CheckCircle, AlertCircle, MessageSquare,
  ChevronDown, Send, User, Shield, Loader2, StickyNote, Download,
  HelpCircle, X, ChevronRight, Eye
} from 'lucide-react';
import axios from 'axios';

const STATUS_CONFIG = {
  'Aberto': { color: 'bg-blue-100 text-blue-700', dot: 'bg-blue-500' },
  'Em analise': { color: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' },
  'A aguardar resposta': { color: 'bg-purple-100 text-purple-700', dot: 'bg-purple-500' },
  'Resolvido': { color: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
  'Fechado': { color: 'bg-stone-100 text-stone-500', dot: 'bg-stone-400' },
};

const PRIORITY_CONFIG = {
  'Baixa': { color: 'text-stone-500 bg-stone-50 border-stone-200' },
  'Media': { color: 'text-blue-600 bg-blue-50 border-blue-200' },
  'Alta': { color: 'text-orange-600 bg-orange-50 border-orange-200' },
  'Urgente': { color: 'text-red-600 bg-red-50 border-red-200' },
};

const STATUSES = ['Aberto', 'Em analise', 'A aguardar resposta', 'Resolvido', 'Fechado'];
const PRIORITIES = ['Baixa', 'Media', 'Alta', 'Urgente'];
const TYPES = [
  'Problema tecnico', 'Pagamento', 'Conta e acesso',
  'Convites e referrals', 'Viagens e sonhos',
  'Reclamacao', 'Sugestao', 'Outro'
];

const formatDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

const formatDateShort = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit' });
};

const AdminSupportSection = ({ token, API }) => {
  const headers = { Authorization: `Bearer ${token}` };

  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ total: 0, open_count: 0, today_count: 0, in_analysis: 0, awaiting_reply: 0, urgent_count: 0, types_breakdown: {} });
  const [loading, setLoading] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);

  // Filters
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Detail state
  const [adminReply, setAdminReply] = useState('');
  const [internalNote, setInternalNote] = useState('');
  const [sending, setSending] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const messagesEndRef = useRef(null);

  const QUICK_TEMPLATES = [
    { label: 'Em analise', text: 'Recebemos o teu pedido e estamos a analisar.' },
    { label: 'Pedir detalhes', text: 'Podes enviar mais detalhes ou uma screenshot do problema?' },
    { label: 'Resolvido?', text: 'O problema foi resolvido. Podes confirmar se ja esta tudo a funcionar?' },
    { label: 'Sugestao registada', text: 'Obrigado pelo teu feedback. A tua sugestao foi registada.' },
  ];

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterType) params.append('ticket_type', filterType);
      if (filterPriority) params.append('priority', filterPriority);
      if (searchQuery) params.append('search', searchQuery);
      
      const res = await axios.get(`${API}/admin/support/tickets?${params}`, { headers });
      setTickets(res.data.tickets || []);
      setStats({
        total: res.data.total, open_count: res.data.open_count,
        today_count: res.data.today_count || 0, in_analysis: res.data.in_analysis || 0,
        awaiting_reply: res.data.awaiting_reply || 0, urgent_count: res.data.urgent_count || 0,
        types_breakdown: res.data.types_breakdown || {}
      });
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { fetchTickets(); }, [filterStatus, filterType, filterPriority]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchTickets();
  };

  const openTicket = async (ticketId) => {
    try {
      const res = await axios.get(`${API}/admin/support/tickets/${ticketId}`, { headers });
      setSelectedTicket(res.data);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 200);
    } catch { /* ignore */ }
  };

  const sendReply = async () => {
    if (!adminReply.trim() || !selectedTicket) return;
    setSending(true);
    try {
      await axios.post(`${API}/admin/support/tickets/${selectedTicket.ticket_id}/reply`,
        { message: adminReply }, { headers, 'Content-Type': 'application/json' });
      setAdminReply('');
      await openTicket(selectedTicket.ticket_id);
      await fetchTickets();
    } catch { /* ignore */ }
    setSending(false);
  };

  const updateStatus = async (newStatus) => {
    if (!selectedTicket) return;
    try {
      await axios.put(`${API}/admin/support/tickets/${selectedTicket.ticket_id}/status`,
        { status: newStatus }, { headers });
      await openTicket(selectedTicket.ticket_id);
      await fetchTickets();
    } catch { /* ignore */ }
  };

  const updatePriority = async (newPriority) => {
    if (!selectedTicket) return;
    try {
      await axios.put(`${API}/admin/support/tickets/${selectedTicket.ticket_id}/priority`,
        { priority: newPriority }, { headers });
      await openTicket(selectedTicket.ticket_id);
      await fetchTickets();
    } catch { /* ignore */ }
  };

  const addNote = async () => {
    if (!internalNote.trim() || !selectedTicket) return;
    try {
      await axios.post(`${API}/admin/support/tickets/${selectedTicket.ticket_id}/note`,
        { note: internalNote }, { headers });
      setInternalNote('');
      await openTicket(selectedTicket.ticket_id);
    } catch { /* ignore */ }
  };

  const downloadAttachment = async (attachment) => {
    if (!attachment?.storage_path) return;
    try {
      const res = await axios.get(`${API}/support/files/${attachment.storage_path}`, {
        headers, responseType: 'blob'
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachment.original_filename || 'attachment';
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  // --- TICKET LIST VIEW ---
  if (!selectedTicket) {
    return (
      <div className="space-y-4" data-testid="admin-support-section">
        {/* Quick Stats Dashboard */}
        <div className="grid grid-cols-4 gap-3" data-testid="support-stats-dashboard">
          <div className="bg-white rounded-xl border border-stone-200 p-4">
            <p className="text-xs text-[#6B6661] font-medium">Pedidos hoje</p>
            <p className="text-2xl font-bold text-[#2D2A26] mt-1">{stats.today_count}</p>
          </div>
          <div className="bg-white rounded-xl border border-stone-200 p-4">
            <p className="text-xs text-amber-600 font-medium">Em analise</p>
            <p className="text-2xl font-bold text-amber-700 mt-1">{stats.in_analysis}</p>
          </div>
          <div className="bg-white rounded-xl border border-stone-200 p-4">
            <p className="text-xs text-purple-600 font-medium">A aguardar resposta</p>
            <p className="text-2xl font-bold text-purple-700 mt-1">{stats.awaiting_reply}</p>
          </div>
          <div className="bg-white rounded-xl border border-stone-200 p-4">
            <p className="text-xs text-red-600 font-medium">Urgentes</p>
            <p className="text-2xl font-bold text-red-700 mt-1">{stats.urgent_count}</p>
          </div>
        </div>

        {/* Types Breakdown (last 7 days) */}
        {Object.keys(stats.types_breakdown).length > 0 && (
          <div className="bg-white rounded-xl border border-stone-200 p-4" data-testid="types-breakdown">
            <h4 className="text-xs font-semibold text-[#6B6661] uppercase mb-3">Pedidos por tipo (ultimos 7 dias)</h4>
            <div className="flex flex-wrap gap-3">
              {Object.entries(stats.types_breakdown).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
                <div key={type} className="flex items-center gap-2 px-3 py-1.5 bg-stone-50 rounded-lg">
                  <span className="text-xs text-[#6B6661]">{type}</span>
                  <span className="text-xs font-bold text-[#2D2A26] bg-stone-200 px-1.5 py-0.5 rounded">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Summary + Filters */}
        <div className="flex items-center gap-4 mb-2">
          <div className="bg-blue-50 px-4 py-2 rounded-xl">
            <span className="text-xs text-blue-600 font-semibold">{stats.open_count} Abertos</span>
          </div>
          <div className="bg-stone-50 px-4 py-2 rounded-xl">
            <span className="text-xs text-[#6B6661] font-semibold">{stats.total} Total</span>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 min-w-[200px]">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
              <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                placeholder="Pesquisar por ID, email ou assunto..."
                className="w-full pl-9 pr-4 py-2 border border-stone-200 rounded-xl text-sm focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent"
                data-testid="support-search" />
            </div>
            <button type="submit" className="px-4 py-2 bg-stone-100 rounded-xl text-sm text-[#6B6661] hover:bg-stone-200 transition-colors">
              Pesquisar
            </button>
          </form>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-stone-200 rounded-xl text-sm" data-testid="filter-status">
            <option value="">Todos os estados</option>
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={filterType} onChange={e => setFilterType(e.target.value)}
            className="px-3 py-2 border border-stone-200 rounded-xl text-sm" data-testid="filter-type">
            <option value="">Todos os tipos</option>
            {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select value={filterPriority} onChange={e => setFilterPriority(e.target.value)}
            className="px-3 py-2 border border-stone-200 rounded-xl text-sm" data-testid="filter-priority">
            <option value="">Todas as prioridades</option>
            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        {/* Ticket Table */}
        <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 animate-spin text-[#FFBE98]" />
            </div>
          ) : tickets.length === 0 ? (
            <div className="text-center py-16">
              <HelpCircle className="w-10 h-10 text-stone-300 mx-auto mb-2" />
              <p className="text-[#6B6661] text-sm">Nenhum pedido encontrado</p>
            </div>
          ) : (
            <table className="w-full text-sm" data-testid="support-tickets-table">
              <thead>
                <tr className="border-b border-stone-100 text-left">
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">ID</th>
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">Utilizador</th>
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">Tipo</th>
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">Assunto</th>
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">Estado</th>
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">Prioridade</th>
                  <th className="px-4 py-3 text-xs font-semibold text-stone-500 uppercase">Data</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-50">
                {tickets.map(t => {
                  const sc = STATUS_CONFIG[t.status] || STATUS_CONFIG['Aberto'];
                  const pc = PRIORITY_CONFIG[t.priority] || PRIORITY_CONFIG['Media'];
                  return (
                    <tr key={t.ticket_id} className="hover:bg-stone-50 cursor-pointer transition-colors"
                      onClick={() => openTicket(t.ticket_id)} data-testid={`admin-ticket-${t.ticket_id}`}>
                      <td className="px-4 py-3 font-mono text-xs text-stone-500">{t.ticket_id}</td>
                      <td className="px-4 py-3">
                        <div className="text-xs font-medium text-[#2D2A26]">{t.user_name}</div>
                        <div className="text-xs text-stone-400">{t.user_email}</div>
                      </td>
                      <td className="px-4 py-3 text-xs text-[#6B6661]">{t.ticket_type}</td>
                      <td className="px-4 py-3 text-xs text-[#2D2A26] max-w-[200px] truncate">{t.subject}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${sc.color}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`}></span> {t.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block px-2 py-0.5 rounded-md text-xs font-semibold border ${pc.color}`}>
                          {t.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-stone-400 whitespace-nowrap">{formatDateShort(t.created_at)}</td>
                      <td className="px-4 py-3">
                        <Eye className="w-4 h-4 text-stone-400" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    );
  }

  // --- TICKET DETAIL VIEW (Admin) ---
  const allMessages = [
    { sender: 'user', sender_name: selectedTicket.user_name, message: selectedTicket.description,
      attachment: selectedTicket.attachment, created_at: selectedTicket.created_at, isOriginal: true },
    ...(selectedTicket.messages || [])
  ];
  const sc = STATUS_CONFIG[selectedTicket.status] || STATUS_CONFIG['Aberto'];
  const pc = PRIORITY_CONFIG[selectedTicket.priority] || PRIORITY_CONFIG['Media'];

  return (
    <div className="space-y-4" data-testid="admin-ticket-detail">
      {/* Back */}
      <button onClick={() => setSelectedTicket(null)}
        className="flex items-center gap-2 text-sm text-[#6B6661] hover:text-[#2D2A26] transition-colors"
        data-testid="back-to-list-btn">
        <ChevronRight className="w-4 h-4 rotate-180" /> Voltar a lista
      </button>

      <div className="grid grid-cols-3 gap-4">
        {/* Main conversation */}
        <div className="col-span-2 space-y-4">
          {/* Header */}
          <div className="bg-white rounded-2xl border border-stone-200 p-5">
            <div className="flex items-start justify-between mb-2">
              <div>
                <span className="text-xs font-mono text-stone-400">{selectedTicket.ticket_id}</span>
                <h2 className="text-lg font-bold text-[#2D2A26] mt-0.5">{selectedTicket.subject}</h2>
              </div>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${sc.color}`}>
                {selectedTicket.status}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs text-[#6B6661]">
              <span>{selectedTicket.user_name} ({selectedTicket.user_email})</span>
              <span>|</span>
              <span>{selectedTicket.ticket_type}</span>
              <span>|</span>
              <span>{formatDate(selectedTicket.created_at)}</span>
            </div>
          </div>

          {/* Conversation */}
          <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-stone-100">
              <h3 className="text-sm font-semibold text-[#2D2A26]">Conversa</h3>
            </div>
            <div className="px-5 py-4 space-y-3 max-h-[400px] overflow-y-auto">
              {allMessages.map((msg, i) => {
                const isAdmin = msg.sender === 'admin';
                return (
                  <div key={msg.message_id || `orig-${i}`}
                    className={`flex ${isAdmin ? 'justify-end' : 'justify-start'}`}
                    data-testid={`admin-msg-${i}`}>
                    <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      isAdmin ? 'bg-[#FFBE98]/10 border border-[#FFBE98]/20' : 'bg-stone-50 border border-stone-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        {isAdmin ? <Shield className="w-3 h-3 text-[#FFBE98]" /> : <User className="w-3 h-3 text-stone-500" />}
                        <span className="text-xs font-semibold">{msg.sender_name}</span>
                        <span className="text-xs text-stone-400">{formatDate(msg.created_at)}</span>
                      </div>
                      <p className="text-sm text-[#2D2A26] whitespace-pre-wrap">{msg.message}</p>
                      {msg.attachment && (
                        <button onClick={() => downloadAttachment(msg.attachment)}
                          className="mt-2 inline-flex items-center gap-1.5 px-2 py-1 bg-stone-50 border border-stone-200 rounded-lg text-xs text-[#6B6661] hover:bg-stone-100">
                          <Download className="w-3 h-3" /> {msg.attachment.original_filename}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>

            {/* Admin Reply */}
            <div className="border-t border-stone-100 px-5 py-3">
              {/* Quick Templates */}
              <div className="mb-2 relative">
                <button onClick={() => setShowTemplates(!showTemplates)}
                  className="text-xs text-[#FFBE98] hover:text-[#e0956a] font-semibold transition-colors"
                  data-testid="quick-templates-btn">
                  Inserir resposta rapida
                </button>
                <AnimatePresence>
                  {showTemplates && (
                    <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                      className="absolute left-0 bottom-full mb-1 bg-white border border-stone-200 rounded-xl shadow-lg p-2 z-10 w-[360px]"
                      data-testid="quick-templates-menu">
                      {QUICK_TEMPLATES.map((t, i) => (
                        <button key={i} onClick={() => { setAdminReply(t.text); setShowTemplates(false); }}
                          className="w-full text-left px-3 py-2 text-sm text-[#2D2A26] hover:bg-stone-50 rounded-lg transition-colors"
                          data-testid={`template-${i}`}>
                          <span className="text-xs text-[#FFBE98] font-semibold">{t.label}</span>
                          <p className="text-xs text-[#6B6661] mt-0.5">{t.text}</p>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              <div className="flex items-end gap-2">
                <textarea value={adminReply} onChange={e => setAdminReply(e.target.value)}
                  rows={2} placeholder="Responder ao utilizador..."
                  className="flex-1 px-3 py-2 border border-stone-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent"
                  data-testid="admin-reply-input" />
                <button onClick={sendReply} disabled={!adminReply.trim() || sending}
                  className="p-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl hover:bg-[#f0a878] transition-colors disabled:opacity-40"
                  data-testid="admin-send-reply-btn">
                  {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Actions */}
          <div className="bg-white rounded-2xl border border-stone-200 p-5 space-y-4">
            <h4 className="text-sm font-semibold text-[#2D2A26]">Acoes</h4>

            {/* Status */}
            <div>
              <label className="text-xs font-medium text-[#6B6661] mb-1 block">Estado</label>
              <select value={selectedTicket.status} onChange={e => updateStatus(e.target.value)}
                className="w-full px-3 py-2 border border-stone-200 rounded-xl text-sm"
                data-testid="admin-status-select">
                {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Priority */}
            <div>
              <label className="text-xs font-medium text-[#6B6661] mb-1 block">Prioridade</label>
              <select value={selectedTicket.priority} onChange={e => updatePriority(e.target.value)}
                className="w-full px-3 py-2 border border-stone-200 rounded-xl text-sm"
                data-testid="admin-priority-select">
                {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col gap-2 pt-2">
              {selectedTicket.status !== 'Resolvido' && (
                <button onClick={() => updateStatus('Resolvido')}
                  className="w-full px-4 py-2 bg-green-50 text-green-700 rounded-xl text-sm font-semibold hover:bg-green-100 transition-colors"
                  data-testid="mark-resolved-btn">
                  <CheckCircle className="w-3.5 h-3.5 inline mr-1.5" /> Marcar como resolvido
                </button>
              )}
              {selectedTicket.status !== 'Fechado' && (
                <button onClick={() => updateStatus('Fechado')}
                  className="w-full px-4 py-2 bg-stone-50 text-stone-600 rounded-xl text-sm font-semibold hover:bg-stone-100 transition-colors"
                  data-testid="close-ticket-btn">
                  <X className="w-3.5 h-3.5 inline mr-1.5" /> Fechar pedido
                </button>
              )}
            </div>
          </div>

          {/* Attachment */}
          {selectedTicket.attachment && (
            <div className="bg-white rounded-2xl border border-stone-200 p-5">
              <h4 className="text-sm font-semibold text-[#2D2A26] mb-3">Anexo</h4>
              <button onClick={() => downloadAttachment(selectedTicket.attachment)}
                className="w-full flex items-center gap-2 px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-xs text-[#6B6661] hover:bg-stone-100 transition-colors"
                data-testid="admin-download-attachment">
                <Download className="w-3.5 h-3.5" />
                <span className="truncate">{selectedTicket.attachment.original_filename}</span>
              </button>
            </div>
          )}

          {/* Internal Notes */}
          <div className="bg-white rounded-2xl border border-stone-200 p-5">
            <h4 className="text-sm font-semibold text-[#2D2A26] mb-3 flex items-center gap-1.5">
              <StickyNote className="w-3.5 h-3.5 text-amber-500" /> Notas internas
            </h4>
            <div className="space-y-2 mb-3 max-h-[200px] overflow-y-auto">
              {(selectedTicket.internal_notes || []).length === 0 ? (
                <p className="text-xs text-stone-400 italic">Sem notas internas</p>
              ) : (
                selectedTicket.internal_notes.map((n, i) => (
                  <div key={n.note_id || i} className="p-2.5 bg-amber-50 border border-amber-100 rounded-lg text-xs text-[#2D2A26]"
                    data-testid={`internal-note-${i}`}>
                    <p className="whitespace-pre-wrap">{n.note}</p>
                    <span className="text-stone-400 text-xs mt-1 block">{formatDate(n.created_at)}</span>
                  </div>
                ))
              )}
            </div>
            <div className="flex items-end gap-2">
              <textarea value={internalNote} onChange={e => setInternalNote(e.target.value)}
                rows={2} placeholder="Adicionar nota interna..."
                className="flex-1 px-3 py-2 border border-stone-200 rounded-xl text-xs resize-none focus:ring-2 focus:ring-amber-300 focus:border-transparent"
                data-testid="internal-note-input" />
              <button onClick={addNote} disabled={!internalNote.trim()}
                className="p-2 bg-amber-100 text-amber-700 rounded-xl hover:bg-amber-200 transition-colors disabled:opacity-40"
                data-testid="add-note-btn">
                <StickyNote className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminSupportSection;
