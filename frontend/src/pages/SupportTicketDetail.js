import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Send, Paperclip, Upload, X, Loader2, User, Shield,
  Clock, CheckCircle, AlertCircle, MessageSquare, HelpCircle, Download
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

const StatusBadge = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG['Aberto'];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${config.color}`}>
      <Icon className="w-3 h-3" /> {status}
    </span>
  );
};

const AttachmentView = ({ attachment, token }) => {
  const [blobUrl, setBlobUrl] = useState(null);

  useEffect(() => {
    if (!attachment?.storage_path) return;
    const isImage = attachment.content_type?.startsWith('image/');
    if (isImage) {
      axios.get(`${API}/support/files/${attachment.storage_path}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      }).then(res => {
        setBlobUrl(URL.createObjectURL(res.data));
      }).catch(() => {});
    }
    return () => { if (blobUrl) URL.revokeObjectURL(blobUrl); };
  }, [attachment, token]);

  if (!attachment) return null;
  const isImage = attachment.content_type?.startsWith('image/');

  const handleDownload = async () => {
    try {
      const res = await axios.get(`${API}/support/files/${attachment.storage_path}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob'
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = attachment.original_filename || 'attachment';
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* ignore */ }
  };

  return (
    <div className="mt-2">
      {isImage && blobUrl ? (
        <img src={blobUrl} alt="Anexo" className="max-w-[280px] max-h-[200px] rounded-lg border border-stone-200 cursor-pointer hover:opacity-90 transition-opacity"
          onClick={handleDownload} data-testid="attachment-image" />
      ) : (
        <button onClick={handleDownload}
          className="inline-flex items-center gap-2 px-3 py-1.5 bg-stone-50 border border-stone-200 rounded-lg text-xs text-[#6B6661] hover:bg-stone-100 transition-colors"
          data-testid="attachment-download">
          <Download className="w-3.5 h-3.5" /> {attachment.original_filename || 'Descarregar anexo'}
        </button>
      )}
    </div>
  );
};

const formatDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

const SupportTicketDetail = () => {
  const { ticketId } = useParams();
  const { user, getAuthHeaders, token } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState('');
  const [replyAttachment, setReplyAttachment] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [sending, setSending] = useState(false);

  const hasLoadedOnce = useRef(false);

  const fetchTicket = async () => {
    try {
      const res = await axios.get(`${API}/support/tickets/${ticketId}`, {
        headers: getAuthHeaders(), withCredentials: true
      });
      setTicket(res.data);
      if (!hasLoadedOnce.current) {
        hasLoadedOnce.current = true;
        setTimeout(() => window.scrollTo(0, 0), 50);
      }
    } catch {
      navigate('/dashboard');
    }
    setLoading(false);
  };

  useEffect(() => {
    window.scrollTo(0, 0);
    hasLoadedOnce.current = false;
    fetchTicket();
  }, [ticketId]);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowed = ['image/png', 'image/jpeg', 'image/webp', 'application/pdf'];
    if (!allowed.includes(file.type) || file.size > 5 * 1024 * 1024) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(`${API}/support/upload`, formData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });
      setReplyAttachment({ ...res.data, display_name: file.name });
    } catch { /* ignore */ }
    setUploading(false);
  };

  const handleSendReply = async () => {
    if (!reply.trim()) return;
    setSending(true);
    try {
      const payload = { message: reply };
      if (replyAttachment) {
        payload.attachment = {
          storage_path: replyAttachment.storage_path,
          original_filename: replyAttachment.original_filename,
          content_type: replyAttachment.content_type,
          size: replyAttachment.size
        };
      }
      await axios.post(`${API}/support/tickets/${ticketId}/reply`, payload, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        withCredentials: true
      });
      setReply('');
      setReplyAttachment(null);
      await fetchTicket();
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch { /* ignore */ }
    setSending(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FAFAF9] pt-24 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#FFBE98]" />
      </div>
    );
  }

  if (!ticket) return null;

  const allMessages = [
    { sender: 'user', sender_name: ticket.user_name, message: ticket.description,
      attachment: ticket.attachment, created_at: ticket.created_at, isOriginal: true },
    ...(ticket.messages || [])
  ];

  const isClosed = ticket.status === 'Fechado';

  return (
    <div className="min-h-screen bg-[#FAFAF9] pt-24 pb-16 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Back */}
        <button onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-sm text-[#6B6661] hover:text-[#2D2A26] mb-4 transition-colors"
          data-testid="back-btn">
          <ArrowLeft className="w-4 h-4" /> Voltar ao dashboard
        </button>

        {/* Ticket Header */}
        <div className="bg-white rounded-2xl border border-stone-200 p-6 mb-4" data-testid="ticket-header">
          <div className="flex items-start justify-between mb-3">
            <div>
              <span className="text-xs font-mono text-stone-400">{ticket.ticket_id}</span>
              <h1 className="text-lg font-bold text-[#2D2A26] mt-1">{ticket.subject}</h1>
            </div>
            <StatusBadge status={ticket.status} />
          </div>
          <div className="flex items-center gap-4 text-xs text-[#6B6661]">
            <span>Tipo: {ticket.ticket_type}</span>
            <span>Criado: {formatDate(ticket.created_at)}</span>
            {ticket.updated_at !== ticket.created_at && (
              <span>Atualizado: {formatDate(ticket.updated_at)}</span>
            )}
          </div>
        </div>

        {/* Conversation */}
        <div className="bg-white rounded-2xl border border-stone-200 overflow-hidden" data-testid="conversation">
          <div className="px-6 py-4 border-b border-stone-100">
            <h3 className="text-sm font-semibold text-[#2D2A26]">Conversa</h3>
          </div>

          <div className="px-6 py-4 space-y-4 max-h-[500px] overflow-y-auto">
            {allMessages.map((msg, i) => {
              const isAdmin = msg.sender === 'admin';
              return (
                <motion.div key={msg.message_id || `orig-${i}`}
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`flex ${isAdmin ? 'justify-start' : 'justify-end'}`}
                  data-testid={`message-${i}`}>
                  <div className={`max-w-[80%] ${isAdmin ? 'order-1' : 'order-1'}`}>
                    <div className={`rounded-2xl px-4 py-3 ${
                      isAdmin
                        ? 'bg-[#FFBE98]/10 border border-[#FFBE98]/20'
                        : 'bg-stone-100 border border-stone-200'
                    }`}>
                      <div className="flex items-center gap-2 mb-1.5">
                        {isAdmin ? (
                          <Shield className="w-3.5 h-3.5 text-[#FFBE98]" />
                        ) : (
                          <User className="w-3.5 h-3.5 text-[#6B6661]" />
                        )}
                        <span className="text-xs font-semibold text-[#2D2A26]">
                          {msg.sender_name || (isAdmin ? 'Equipa 4Luis' : 'Tu')}
                        </span>
                        <span className="text-xs text-stone-400">{formatDate(msg.created_at)}</span>
                      </div>
                      <p className="text-sm text-[#2D2A26] whitespace-pre-wrap leading-relaxed">{msg.message}</p>
                      {msg.attachment && <AttachmentView attachment={msg.attachment} token={token} />}
                    </div>
                    {msg.isOriginal && (
                      <span className="text-xs text-stone-400 mt-1 block px-1">Pedido original</span>
                    )}
                  </div>
                </motion.div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Reply Input */}
          {!isClosed ? (
            <div className="border-t border-stone-100 px-6 py-4" data-testid="reply-section">
              {replyAttachment && (
                <div className="flex items-center gap-2 mb-3 p-2 bg-stone-50 rounded-lg">
                  <Paperclip className="w-3.5 h-3.5 text-[#FFBE98]" />
                  <span className="text-xs text-[#2D2A26] flex-1 truncate">{replyAttachment.display_name}</span>
                  <button onClick={() => setReplyAttachment(null)} className="text-stone-400 hover:text-red-500">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <div className="flex items-end gap-3">
                <div className="flex-1">
                  <textarea value={reply} onChange={e => setReply(e.target.value)}
                    rows={2} placeholder="Escreve a tua resposta..."
                    className="w-full px-4 py-2.5 border border-stone-200 rounded-xl text-sm resize-none focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent"
                    data-testid="reply-input" />
                </div>
                <div className="flex items-center gap-2 pb-0.5">
                  <label className="p-2.5 text-stone-400 hover:text-[#FFBE98] cursor-pointer transition-colors rounded-lg hover:bg-stone-50">
                    {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Paperclip className="w-4 h-4" />}
                    <input type="file" className="hidden" accept=".png,.jpg,.jpeg,.webp,.pdf"
                      onChange={handleFileUpload} disabled={uploading} />
                  </label>
                  <button onClick={handleSendReply} disabled={!reply.trim() || sending}
                    className="p-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl hover:bg-[#f0a878] transition-colors disabled:opacity-40"
                    data-testid="send-reply-btn">
                    {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="border-t border-stone-100 px-6 py-4 text-center text-sm text-stone-400">
              Este pedido foi fechado. Se precisares de mais ajuda, abre um novo pedido.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SupportTicketDetail;
