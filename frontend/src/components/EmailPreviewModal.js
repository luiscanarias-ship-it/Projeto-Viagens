import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Loader2, Users, Mail } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EmailPreviewModal = ({ previewUrl, sendUrl, sendMethod, token, onClose, onSent, title }) => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        const res = await axios.get(`${API}${previewUrl}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setPreview(res.data);
      } catch (err) {
        setError('Erro ao carregar preview do email');
      } finally {
        setLoading(false);
      }
    };
    fetchPreview();
  }, [previewUrl, token]);

  const handleSend = async () => {
    setSending(true);
    try {
      const res = await axios.post(`${API}${sendUrl}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (onSent) onSent(res.data);
      onClose();
    } catch (err) {
      setError('Erro ao enviar email: ' + (err.response?.data?.detail || err.message));
      setSending(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
        onClick={onClose}
        data-testid="email-preview-modal"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95 }}
          onClick={e => e.stopPropagation()}
          className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200 bg-stone-50 flex-shrink-0">
            <div>
              <h3 className="font-bold text-lg text-[#2D2A26]">{title || 'Preview do Email'}</h3>
              {preview && (
                <p className="text-xs text-[#6B6661] mt-0.5">
                  Assunto: <strong>{preview.subject}</strong>
                </p>
              )}
            </div>
            <button onClick={onClose} className="p-2 hover:bg-stone-200 rounded-lg transition-colors" data-testid="email-preview-close">
              <X className="w-5 h-5 text-[#6B6661]" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto">
            {loading && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-[#FFBE98] animate-spin" />
              </div>
            )}
            {error && !preview && (
              <div className="p-6 text-center text-red-500">{error}</div>
            )}
            {preview && (
              <div className="p-4">
                <div
                  className="border border-stone-200 rounded-xl overflow-hidden"
                  dangerouslySetInnerHTML={{ __html: preview.html }}
                  data-testid="email-preview-content"
                />
              </div>
            )}
          </div>

          {/* Footer */}
          {preview && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-stone-200 bg-stone-50 flex-shrink-0">
              <div className="flex items-center gap-2 text-sm text-[#6B6661]">
                <Users className="w-4 h-4" />
                <span>Sera enviado para <strong className="text-[#2D2A26]">{preview.recipient_count}</strong> destinatarios</span>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={onClose} className="px-5 py-2.5 text-[#6B6661] hover:bg-stone-200 rounded-xl transition-colors"
                  data-testid="email-preview-cancel">
                  Cancelar
                </button>
                <button onClick={handleSend} disabled={sending}
                  className="px-5 py-2.5 bg-[#2D2A26] text-white rounded-xl hover:bg-[#4A4640] transition-colors flex items-center gap-2 disabled:opacity-50"
                  data-testid="email-preview-send">
                  {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  {sending ? 'A enviar...' : 'Confirmar e Enviar'}
                </button>
              </div>
              {error && <p className="text-red-500 text-xs mt-2">{error}</p>}
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default EmailPreviewModal;
