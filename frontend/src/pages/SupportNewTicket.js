import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, Send, Upload, X, Loader2, Paperclip, CheckCircle, HelpCircle
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TICKET_TYPES = [
  'Problema tecnico', 'Pagamento', 'Conta e acesso',
  'Convites e referrals', 'Viagens e sonhos',
  'Reclamacao', 'Sugestao', 'Outro'
];

const SupportNewTicket = () => {
  const { user, getAuthHeaders, token } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    ticket_type: '',
    subject: '',
    description: ''
  });
  const [attachment, setAttachment] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(null);
  const [errors, setErrors] = useState({});

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowed = ['image/png', 'image/jpeg', 'image/webp', 'application/pdf'];
    if (!allowed.includes(file.type)) {
      setErrors(prev => ({ ...prev, file: 'Tipo nao suportado. Use png, jpg, webp ou pdf.' }));
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setErrors(prev => ({ ...prev, file: 'Ficheiro excede 5MB.' }));
      return;
    }

    setUploading(true);
    setErrors(prev => { const n = { ...prev }; delete n.file; return n; });

    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await axios.post(`${API}/support/upload`, formData, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      });
      setAttachment({
        ...res.data,
        display_name: file.name
      });
    } catch (err) {
      setErrors(prev => ({ ...prev, file: 'Erro ao enviar ficheiro.' }));
    }
    setUploading(false);
  };

  const validate = () => {
    const e = {};
    if (!form.ticket_type) e.ticket_type = 'Selecione um tipo';
    if (!form.subject.trim()) e.subject = 'Assunto e obrigatorio';
    if (!form.description.trim()) e.description = 'Descricao e obrigatoria';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    try {
      const payload = { ...form };
      if (attachment) {
        payload.attachment = {
          storage_path: attachment.storage_path,
          original_filename: attachment.original_filename,
          content_type: attachment.content_type,
          size: attachment.size
        };
      }
      const res = await axios.post(`${API}/support/tickets`, payload, {
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        withCredentials: true
      });
      setSubmitted(res.data);
    } catch (err) {
      setErrors({ submit: err.response?.data?.detail || 'Erro ao criar pedido' });
    }
    setSubmitting(false);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#FAFAF9] pt-24 pb-16 px-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="max-w-lg mx-auto text-center" data-testid="ticket-success">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-[#2D2A26] mb-2">Pedido enviado com sucesso!</h2>
          <p className="text-[#6B6661] mb-2">
            Referencia: <span className="font-mono font-semibold">{submitted.ticket_id}</span>
          </p>
          <p className="text-sm text-[#6B6661] leading-relaxed mb-8">
            A nossa equipa ja esta a analisar.<br />
            Normalmente respondemos em poucas horas.<br /><br />
            Receberas tambem um email com a referencia do pedido.
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate(`/support/${submitted.ticket_id}`)}
              className="px-6 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-semibold text-sm hover:bg-[#f0a878] transition-colors"
              data-testid="view-ticket-btn">
              Ver pedido
            </button>
            <button onClick={() => navigate('/dashboard')}
              className="px-6 py-2.5 border border-stone-200 text-[#6B6661] rounded-xl font-semibold text-sm hover:bg-stone-50 transition-colors">
              Voltar ao dashboard
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAFAF9] pt-24 pb-16 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Back */}
        <button onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-sm text-[#6B6661] hover:text-[#2D2A26] mb-6 transition-colors"
          data-testid="back-to-dashboard-btn">
          <ArrowLeft className="w-4 h-4" /> Voltar ao dashboard
        </button>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden" data-testid="new-ticket-form">
          {/* Header */}
          <div className="px-8 py-6 border-b border-stone-100">
            <h1 className="text-xl font-bold text-[#2D2A26] flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-[#FFBE98]" />
              Abrir novo pedido de suporte
            </h1>
            <p className="text-sm text-[#6B6661] mt-1">Preenche o formulario e a nossa equipa ira ajudar-te.</p>
          </div>

          <div className="px-8 py-6 space-y-5">
            {/* Name & Email (auto) */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[#2D2A26] mb-1.5">Nome</label>
                <input type="text" value={user?.name || ''} disabled
                  className="w-full px-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-sm text-[#6B6661]"
                  data-testid="input-name" />
              </div>
              <div>
                <label className="block text-sm font-medium text-[#2D2A26] mb-1.5">Email</label>
                <input type="email" value={user?.email || ''} disabled
                  className="w-full px-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-sm text-[#6B6661]"
                  data-testid="input-email" />
              </div>
            </div>

            {/* Type */}
            <div>
              <label className="block text-sm font-medium text-[#2D2A26] mb-1.5">Tipo de pedido *</label>
              <select value={form.ticket_type}
                onChange={e => { setForm(p => ({ ...p, ticket_type: e.target.value })); setErrors(p => { const n = { ...p }; delete n.ticket_type; return n; }); }}
                className={`w-full px-4 py-2.5 border rounded-xl text-sm ${errors.ticket_type ? 'border-red-300' : 'border-stone-200'} focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent`}
                data-testid="select-type">
                <option value="">Selecionar tipo...</option>
                {TICKET_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              {errors.ticket_type && <p className="text-xs text-red-500 mt-1">{errors.ticket_type}</p>}
            </div>

            {/* Subject */}
            <div>
              <label className="block text-sm font-medium text-[#2D2A26] mb-1.5">Assunto *</label>
              <input type="text" value={form.subject} placeholder="Descreve brevemente o teu pedido"
                onChange={e => { setForm(p => ({ ...p, subject: e.target.value })); setErrors(p => { const n = { ...p }; delete n.subject; return n; }); }}
                className={`w-full px-4 py-2.5 border rounded-xl text-sm ${errors.subject ? 'border-red-300' : 'border-stone-200'} focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent`}
                data-testid="input-subject" />
              {errors.subject && <p className="text-xs text-red-500 mt-1">{errors.subject}</p>}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-[#2D2A26] mb-1.5">Descricao *</label>
              <textarea value={form.description} rows={5} placeholder={"Explica-nos o que aconteceu.\nSe possivel, indica o passo onde ocorreu o problema (por exemplo pagamento, convite, dashboard, etc.).\n\nTambem podes anexar uma screenshot para nos ajudar a compreender melhor."}
                onChange={e => { setForm(p => ({ ...p, description: e.target.value })); setErrors(p => { const n = { ...p }; delete n.description; return n; }); }}
                className={`w-full px-4 py-2.5 border rounded-xl text-sm resize-none ${errors.description ? 'border-red-300' : 'border-stone-200'} focus:ring-2 focus:ring-[#FFBE98] focus:border-transparent`}
                data-testid="input-description" />
              {errors.description && <p className="text-xs text-red-500 mt-1">{errors.description}</p>}
            </div>

            {/* Attachment */}
            <div>
              <label className="block text-sm font-medium text-[#2D2A26] mb-1.5">Anexo (opcional)</label>
              {attachment ? (
                <div className="flex items-center gap-3 p-3 bg-stone-50 border border-stone-200 rounded-xl">
                  <Paperclip className="w-4 h-4 text-[#FFBE98]" />
                  <span className="text-sm text-[#2D2A26] flex-1 truncate">{attachment.display_name}</span>
                  <button onClick={() => setAttachment(null)} className="text-stone-400 hover:text-red-500 transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <label className="flex items-center gap-3 p-4 border-2 border-dashed border-stone-200 rounded-xl cursor-pointer hover:border-[#FFBE98] hover:bg-[#FFBE98]/5 transition-colors"
                  data-testid="upload-area">
                  {uploading ? (
                    <Loader2 className="w-5 h-5 animate-spin text-[#FFBE98]" />
                  ) : (
                    <Upload className="w-5 h-5 text-stone-400" />
                  )}
                  <span className="text-sm text-[#6B6661]">
                    {uploading ? 'A enviar...' : 'Clica para adicionar screenshot ou ficheiro (png, jpg, webp, pdf — max 5MB)'}
                  </span>
                  <input type="file" className="hidden" accept=".png,.jpg,.jpeg,.webp,.pdf"
                    onChange={handleFileUpload} disabled={uploading} data-testid="file-input" />
                </label>
              )}
              {errors.file && <p className="text-xs text-red-500 mt-1">{errors.file}</p>}
            </div>

            {errors.submit && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">{errors.submit}</div>
            )}
          </div>

          {/* Footer */}
          <div className="px-8 py-4 border-t border-stone-100 bg-stone-50 flex justify-end">
            <button onClick={handleSubmit} disabled={submitting}
              className="flex items-center gap-2 px-6 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-semibold text-sm hover:bg-[#f0a878] transition-colors disabled:opacity-50"
              data-testid="submit-ticket-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {submitting ? 'A enviar...' : 'Enviar pedido'}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default SupportNewTicket;
