import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HelpCircle, Plus, Clock, CheckCircle, AlertCircle, MessageSquare,
  ChevronRight, Search, ArrowLeft, Upload, Send, Paperclip, X, Loader2
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_CONFIG = {
  'Aberto': { color: 'bg-blue-100 text-blue-700', icon: AlertCircle },
  'Em analise': { color: 'bg-amber-100 text-amber-700', icon: Clock },
  'A aguardar resposta': { color: 'bg-purple-100 text-purple-700', icon: MessageSquare },
  'Resolvido': { color: 'bg-green-100 text-green-700', icon: CheckCircle },
  'Fechado': { color: 'bg-stone-100 text-stone-500', icon: CheckCircle },
};

const TYPE_LABELS = {
  'Problema tecnico': 'Problema tecnico',
  'Pagamento': 'Pagamento',
  'Conta e acesso': 'Conta e acesso',
  'Convites e referrals': 'Convites e referrals',
  'Viagens e sonhos': 'Viagens e sonhos',
  'Reclamacao': 'Reclamacao',
  'Sugestao': 'Sugestao',
  'Outro': 'Outro',
};

const StatusBadge = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG['Aberto'];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${config.color}`} data-testid={`status-badge-${status}`}>
      <Icon className="w-3 h-3" /> {status}
    </span>
  );
};

const SupportDashboard = () => {
  const { user, getAuthHeaders } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const res = await axios.get(`${API}/support/tickets`, { headers: getAuthHeaders(), withCredentials: true });
        setTickets(res.data.tickets || []);
      } catch { /* ignore */ }
      setLoading(false);
    };
    fetchTickets();
  }, [getAuthHeaders]);

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const openCount = tickets.filter(t => ['Aberto', 'Em analise', 'A aguardar resposta'].includes(t.status)).length;

  return (
    <div className="space-y-6" data-testid="support-dashboard">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#2D2A26] flex items-center gap-2">
            <HelpCircle className="w-6 h-6 text-[#FFBE98]" />
            Ajuda e Suporte
            {openCount > 0 && (
              <span className="ml-1 px-2.5 py-0.5 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full" data-testid="open-tickets-count">
                {openCount} {openCount === 1 ? 'aberto' : 'abertos'}
              </span>
            )}
          </h2>
          <p className="text-[#6B6661] text-sm mt-1">
            Precisas de ajuda? Abre um pedido e a nossa equipa ira responder-te o mais rapidamente possivel.
          </p>
        </div>
        <button
          onClick={() => navigate('/support/new')}
          className="flex items-center gap-2 px-5 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-semibold text-sm hover:bg-[#f0a878] transition-colors"
          data-testid="new-ticket-btn"
        >
          <Plus className="w-4 h-4" /> Abrir novo pedido
        </button>
      </div>

      {/* Ticket List */}
      <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-stone-100">
          <h3 className="font-semibold text-[#2D2A26]">Os meus pedidos</h3>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-[#FFBE98]" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-16 px-6">
            <HelpCircle className="w-12 h-12 text-stone-300 mx-auto mb-3" />
            <p className="text-[#6B6661]">Ainda nao tens pedidos de suporte.</p>
            <p className="text-sm text-stone-400 mt-1">Quando abrires um pedido, aparecera aqui.</p>
          </div>
        ) : (
          <div className="divide-y divide-stone-100">
            {tickets.map((ticket, i) => (
              <motion.div
                key={ticket.ticket_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
                className="px-6 py-4 flex items-center gap-4 hover:bg-stone-50 transition-colors cursor-pointer"
                onClick={() => navigate(`/support/${ticket.ticket_id}`)}
                data-testid={`ticket-row-${ticket.ticket_id}`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-stone-400">{ticket.ticket_id}</span>
                    <span className="text-xs text-stone-400">|</span>
                    <span className="text-xs text-[#6B6661]">{TYPE_LABELS[ticket.ticket_type] || ticket.ticket_type}</span>
                  </div>
                  <p className="text-sm font-medium text-[#2D2A26] truncate">{ticket.subject}</p>
                </div>
                <StatusBadge status={ticket.status} />
                <span className="text-xs text-stone-400 whitespace-nowrap">{formatDate(ticket.created_at)}</span>
                <ChevronRight className="w-4 h-4 text-stone-300 flex-shrink-0" />
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SupportDashboard;
