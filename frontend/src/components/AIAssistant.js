import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Send, Loader2, ArrowRight, DollarSign, Star, Calendar, CloudSun, RotateCcw, ExternalLink, Hotel, Ticket } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const QUICK_ACTIONS = [
  { id: 'cheaper', label: 'Tornar mais barato', icon: DollarSign, message: 'Sugere formas de tornar esta viagem mais economica, mantendo as experiencias essenciais.' },
  { id: 'experiences', label: 'Experiencias unicas', icon: Star, message: 'Sugere experiencias unicas e autenticas que nao estejam no roteiro atual.' },
  { id: 'days', label: 'Melhorar distribuicao dos dias', icon: Calendar, message: 'Analisa a distribuicao das atividades por dia e sugere melhorias para evitar dias muito cheios ou vazios.' },
  { id: 'weather', label: 'Ajustar ao clima', icon: CloudSun, message: 'Ajusta o roteiro considerando o clima previsto para as datas da viagem.' },
];

const AIAssistant = ({ plan, token, onApplyRefinement, affiliateLinks, onTrackAffiliate }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading || !plan) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API}/ai/assistant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          plan,
          message: text,
          history: messages.slice(-6)
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Erro no assistente');
      }

      const data = await res.json();
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        suggestions: data.suggestions,
        canApply: data.can_apply,
        applyPrompt: data.apply_prompt
      }]);
    } catch (e) {
      setError(e.message || 'Erro ao contactar o assistente');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = (applyPrompt) => {
    if (onApplyRefinement && applyPrompt) {
      onApplyRefinement(applyPrompt);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setError('');
  };

  return (
    <div className="bg-white rounded-xl border border-[#FFBE98]/20 overflow-hidden" data-testid="ai-assistant">
      {/* Header */}
      <div className="bg-gradient-to-r from-[#FFBE98]/10 to-violet-50/30 px-4 py-3 flex items-center justify-between border-b border-stone-100">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-violet-600" />
          </div>
          <div>
            <p className="text-xs font-bold text-[#2D2A26]">Assistente pessoal</p>
            <p className="text-[9px] text-[#6B6661]">Melhora o teu roteiro com IA</p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleReset}
            className="text-[10px] text-[#6B6661] hover:text-[#2D2A26] flex items-center gap-1 transition-colors"
            data-testid="assistant-reset"
          >
            <RotateCcw className="w-3 h-3" />
            Nova conversa
          </button>
        )}
      </div>

      {/* Quick actions — show when no messages */}
      {messages.length === 0 && (
        <div className="p-4 space-y-2" data-testid="assistant-quick-actions">
          <p className="text-[10px] font-semibold text-[#6B6661] uppercase tracking-wider">O que queres melhorar?</p>
          <div className="grid grid-cols-2 gap-1.5">
            {QUICK_ACTIONS.map(action => (
              <button
                key={action.id}
                onClick={() => sendMessage(action.message)}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-2.5 bg-stone-50 hover:bg-[#FFBE98]/10 border border-stone-100 hover:border-[#FFBE98]/30 rounded-lg transition-all text-left group"
                data-testid={`assistant-action-${action.id}`}
              >
                <action.icon className="w-3.5 h-3.5 text-[#6B6661] group-hover:text-[#FFBE98] shrink-0 transition-colors" />
                <span className="text-[11px] font-medium text-[#2D2A26]">{action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.length > 0 && (
        <div className="max-h-[320px] overflow-y-auto px-4 py-3 space-y-3" data-testid="assistant-messages">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className={msg.role === 'user' ? 'flex justify-end' : ''}
            >
              {msg.role === 'user' ? (
                <div className="bg-[#FFBE98]/15 text-[#2D2A26] px-3 py-2 rounded-xl rounded-br-sm max-w-[85%]">
                  <p className="text-xs">{msg.content}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {/* Response summary */}
                  <div className="flex items-start gap-2">
                    <div className="w-5 h-5 bg-violet-100 rounded-md flex items-center justify-center shrink-0 mt-0.5">
                      <Sparkles className="w-3 h-3 text-violet-600" />
                    </div>
                    <p className="text-xs font-medium text-[#2D2A26]">{msg.content}</p>
                  </div>

                  {/* Suggestions as bullets */}
                  {msg.suggestions?.length > 0 && (
                    <div className="ml-7 space-y-1.5">
                      {msg.suggestions.map((s, j) => (
                        <div key={j} className="flex items-start gap-1.5">
                          <ArrowRight className="w-3 h-3 text-[#FFBE98] shrink-0 mt-0.5" />
                          <p className="text-[11px] text-[#6B6661] leading-relaxed">{s}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Apply button */}
                  {msg.canApply && msg.applyPrompt && (
                    <div className="ml-7 pt-1">
                      <button
                        onClick={() => handleApply(msg.applyPrompt)}
                        className="flex items-center gap-1.5 text-[10px] font-semibold text-violet-600 bg-violet-50 hover:bg-violet-100 px-3 py-1.5 rounded-lg transition-colors"
                        data-testid="assistant-apply-btn"
                      >
                        <Sparkles className="w-3 h-3" />
                        Aplicar ao roteiro
                      </button>
                    </div>
                  )}

                  {/* Contextual affiliate CTA based on conversation intent */}
                  {msg.role === 'assistant' && affiliateLinks && (
                    <div className="ml-7 pt-1.5 flex flex-wrap gap-1.5" data-testid="assistant-affiliate-ctas">
                      {(msg.content?.toLowerCase().includes('hotel') || msg.content?.toLowerCase().includes('alojamento')) && affiliateLinks.booking?.url && (
                        <a href={affiliateLinks.booking.url} target="_blank" rel="noopener noreferrer"
                          onClick={() => onTrackAffiliate?.('booking')}
                          className="inline-flex items-center gap-1 text-[9px] font-semibold text-[#FFBE98] bg-[#FFBE98]/8 hover:bg-[#FFBE98]/15 border border-[#FFBE98]/15 px-2.5 py-1 rounded-lg transition-colors"
                          data-testid="assistant-cta-booking">
                          <Hotel className="w-3 h-3" />Ver hoteis alternativos<ExternalLink className="w-2.5 h-2.5 opacity-60" />
                        </a>
                      )}
                      {(msg.content?.toLowerCase().includes('bilhete') || msg.content?.toLowerCase().includes('experiencia') || msg.content?.toLowerCase().includes('atividade') || msg.content?.toLowerCase().includes('fila')) && affiliateLinks.getyourguide?.url && (
                        <a href={affiliateLinks.getyourguide.url} target="_blank" rel="noopener noreferrer"
                          onClick={() => onTrackAffiliate?.('getyourguide')}
                          className="inline-flex items-center gap-1 text-[9px] font-semibold text-[#FFBE98] bg-[#FFBE98]/8 hover:bg-[#FFBE98]/15 border border-[#FFBE98]/15 px-2.5 py-1 rounded-lg transition-colors"
                          data-testid="assistant-cta-getyourguide">
                          <Ticket className="w-3 h-3" />Ver opcoes<ExternalLink className="w-2.5 h-2.5 opacity-60" />
                        </a>
                      )}
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          ))}

          {/* Loading */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-xs text-[#6B6661]"
            >
              <Loader2 className="w-3.5 h-3.5 animate-spin text-violet-500" />
              <span>A analisar o teu plano...</span>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-4 pb-2"
          >
            <p className="text-[11px] text-red-500 bg-red-50 px-3 py-1.5 rounded-lg" data-testid="assistant-error">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input */}
      {messages.length > 0 && (
        <div className="px-4 py-3 border-t border-stone-100">
          <form
            onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
            className="flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Pergunta sobre o teu roteiro..."
              disabled={loading}
              className="flex-1 text-xs bg-stone-50 border border-stone-200 rounded-lg px-3 py-2 focus:outline-none focus:border-[#FFBE98] transition-colors placeholder:text-stone-400"
              data-testid="assistant-input"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="w-8 h-8 bg-[#FFBE98] hover:bg-[#E6A07C] disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg flex items-center justify-center transition-colors"
              data-testid="assistant-send"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Quick follow-ups */}
          <div className="flex flex-wrap gap-1 mt-2">
            {QUICK_ACTIONS.filter(a => !messages.some(m => m.role === 'user' && m.content === a.message)).slice(0, 2).map(action => (
              <button
                key={action.id}
                onClick={() => sendMessage(action.message)}
                disabled={loading}
                className="text-[9px] text-[#6B6661] bg-stone-50 hover:bg-[#FFBE98]/10 border border-stone-100 px-2 py-1 rounded-md transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAssistant;
