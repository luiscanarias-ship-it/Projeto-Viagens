import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Heart, Lock, Eye, EyeOff, Check, ArrowLeft } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const match = confirm.length === 0 || password === confirm;
  const valid = password.length >= 8 && match && confirm.length > 0;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!valid) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao repor palavra-passe');
      }
      setDone(true);
    } catch (err) {
      // Handle both API errors and network errors
      const errorMsg = err.message || 'Erro ao repor palavra-passe';
      setError(errorMsg.includes('body stream') ? 'Link inválido ou já utilizado.' : errorMsg);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center dream-mesh px-6">
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100 max-w-sm w-full text-center">
          <p className="text-sm text-red-500 mb-3">Link inválido.</p>
          <Link to="/login" className="text-sm text-[#FFBE98] font-medium hover:underline">Voltar ao login</Link>
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <div className="min-h-screen flex items-center justify-center dream-mesh px-6">
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
          className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100 max-w-sm w-full text-center">
          <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <Check className="w-6 h-6 text-green-600" />
          </div>
          <p className="text-base font-bold text-[#2D2A26] mb-1">Palavra-passe atualizada!</p>
          <p className="text-sm text-[#6B6661] mb-4">Já podes entrar com a nova palavra-passe.</p>
          <button onClick={() => navigate('/login')}
            className="w-full btn-primary" data-testid="back-to-login-btn">
            Ir para o login
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center dream-mesh px-6" data-testid="reset-password-page">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <Link to="/" className="flex items-center justify-center gap-2 mb-6">
          <Heart className="w-7 h-7 text-[#FFBE98] fill-[#FFBE98]" />
          <span className="text-xl font-bold text-[#2D2A26]">4Luis</span>
        </Link>
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100">
          <h1 className="text-lg font-bold text-center mb-1">Nova palavra-passe</h1>
          <p className="text-xs text-[#6B6661] text-center mb-5">Escolhe uma palavra-passe segura</p>

          <form onSubmit={handleSubmit} className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#FFBE98]" />Palavra-passe
              </label>
              <div className="relative">
                <input type={showPw ? 'text' : 'password'} value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  className="w-full px-3.5 py-2.5 pr-10 input-warm text-sm" required
                  data-testid="new-password-input" />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6B6661] hover:text-[#2D2A26] p-0.5" tabIndex={-1}>
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-[#FFBE98]" />Confirmar
              </label>
              <input type="password" value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="Repete a palavra-passe"
                className={`w-full px-3.5 py-2.5 input-warm text-sm ${confirm.length > 0 && !match ? 'border-red-300' : ''}`}
                required data-testid="confirm-new-password-input" />
              {confirm.length > 0 && !match && (
                <p className="text-[11px] text-red-400 mt-1">As palavras-passe não coincidem</p>
              )}
            </div>

            {error && <p className="text-red-500 text-xs text-center" data-testid="reset-error">{error}</p>}

            <button type="submit" disabled={!valid || loading}
              className="w-full btn-primary disabled:opacity-50 text-sm" data-testid="reset-submit-btn">
              {loading ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" /> : 'Guardar nova palavra-passe'}
            </button>
          </form>

          <div className="mt-4 text-center">
            <Link to="/login" className="text-xs text-[#6B6661] hover:text-[#FFBE98] inline-flex items-center gap-1">
              <ArrowLeft className="w-3 h-3" />Voltar ao login
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ResetPassword;
