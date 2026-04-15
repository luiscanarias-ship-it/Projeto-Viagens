import React, { useState, useEffect, useCallback } from 'react';
import { Check, X, Clock, Image, AlertCircle } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AmbassadorValidations = ({ token }) => {
  const [data, setData] = useState({ pending: [], pending_count: 0, recently_validated: [] });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [notes, setNotes] = useState({});
  const [showProof, setShowProof] = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchPending = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/ambassador/pending-validations`, { headers });
      setData(res.data);
    } catch (e) {
      console.error('Error fetching validations:', e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchPending(); }, [fetchPending]);

  const handleAction = async (contributionId, action) => {
    setActionLoading(contributionId);
    try {
      await axios.put(`${API}/contributions/${contributionId}/ambassador-validate`, {
        action,
        notes: notes[contributionId] || ''
      }, { headers });
      fetchPending();
    } catch (e) {
      alert(e.response?.data?.detail || 'Erro ao processar');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return <p className="text-sm text-[#6B6661] py-4">A carregar...</p>;

  return (
    <div className="space-y-4" data-testid="ambassador-validations">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-[#2D2A26] flex items-center gap-2">
          <Clock className="w-4 h-4 text-[#FFBE98]" />
          Pagamentos por confirmar
        </h3>
        {data.pending_count > 0 && (
          <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-0.5 rounded-full">
            {data.pending_count}
          </span>
        )}
      </div>

      {data.pending.length === 0 ? (
        <div className="text-center py-6 bg-stone-50 rounded-xl">
          <Check className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
          <p className="text-sm text-[#6B6661]">Sem pagamentos pendentes</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.pending.map(c => (
            <div key={c.contribution_id} className="bg-white border border-stone-200 rounded-xl p-4 space-y-3" data-testid={`validation-${c.contribution_id}`}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-lg font-bold text-[#2D2A26]">
                    {c.support_amount || c.amount}€
                  </p>
                  <p className="text-xs text-[#6B6661]">
                    {c.payment_method === 'crypto' ? `Crypto (${c.crypto_type || 'BTC'})` : c.payment_method === 'mbway' ? 'MBWay' : c.payment_method}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-[#6B6661]">{c.contributor_name || 'Anónimo'}</p>
                  <p className="text-[10px] text-[#6B6661]/70">{new Date(c.created_at).toLocaleDateString('pt-PT')}</p>
                </div>
              </div>

              {c.payment_reference && (
                <p className="text-xs text-[#6B6661] bg-stone-50 rounded-lg px-2 py-1">
                  Ref: <strong>{c.payment_reference}</strong>
                </p>
              )}

              {c.proof_image_url && (
                <button
                  onClick={() => setShowProof(showProof === c.contribution_id ? null : c.contribution_id)}
                  className="text-xs text-blue-600 flex items-center gap-1 hover:underline"
                >
                  <Image className="w-3 h-3" />
                  {showProof === c.contribution_id ? 'Esconder comprovativo' : 'Ver comprovativo'}
                </button>
              )}

              {showProof === c.contribution_id && c.proof_image_url && (
                <img src={c.proof_image_url} alt="Comprovativo" className="w-full max-h-48 object-contain rounded-lg border border-stone-200" />
              )}

              <input
                type="text"
                placeholder="Notas (opcional)"
                value={notes[c.contribution_id] || ''}
                onChange={e => setNotes(prev => ({ ...prev, [c.contribution_id]: e.target.value }))}
                className="w-full px-3 py-1.5 border border-stone-200 rounded-lg text-xs text-[#2D2A26] focus:outline-none focus:border-[#FFBE98]"
                data-testid={`notes-${c.contribution_id}`}
              />

              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(c.contribution_id, 'confirm')}
                  disabled={actionLoading === c.contribution_id}
                  className="flex-1 py-2 bg-emerald-600 text-white rounded-lg text-xs font-semibold hover:bg-emerald-700 transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
                  data-testid={`confirm-${c.contribution_id}`}
                >
                  <Check className="w-3.5 h-3.5" />
                  Confirmar pagamento
                </button>
                <button
                  onClick={() => handleAction(c.contribution_id, 'reject')}
                  disabled={actionLoading === c.contribution_id}
                  className="flex-shrink-0 px-4 py-2 bg-red-50 text-red-600 rounded-lg text-xs font-medium hover:bg-red-100 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  data-testid={`reject-${c.contribution_id}`}
                >
                  <AlertCircle className="w-3.5 h-3.5" />
                  Não recebi
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Recently validated */}
      {data.recently_validated.length > 0 && (
        <div className="pt-2">
          <p className="text-xs font-semibold text-[#6B6661] mb-2">Recentemente validados</p>
          <div className="space-y-1.5">
            {data.recently_validated.map(c => (
              <div key={c.contribution_id} className="flex items-center justify-between py-1.5 px-3 bg-stone-50 rounded-lg">
                <div className="flex items-center gap-2">
                  {c.status === 'confirmed' ? (
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                  ) : (
                    <X className="w-3.5 h-3.5 text-red-500" />
                  )}
                  <span className="text-xs text-[#2D2A26] font-medium">{c.support_amount || c.amount}€</span>
                </div>
                <span className="text-[10px] text-[#6B6661]">
                  {c.validated_at ? new Date(c.validated_at).toLocaleDateString('pt-PT') : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AmbassadorValidations;
