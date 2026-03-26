import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Heart, Eye, EyeOff, Check, X, ShieldCheck } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

const API = process.env.REACT_APP_BACKEND_URL;

const getPasswordStrength = (password) => {
  if (!password) return { level: 0, label: '', color: '' };
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 1) return { level: 1, label: 'Fraca', color: 'bg-red-400' };
  if (score <= 3) return { level: 2, label: 'Média', color: 'bg-amber-400' };
  return { level: 3, label: 'Forte', color: 'bg-green-500' };
};

const Login = () => {
  const { login, register, loginWithGoogle } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  useEffect(() => { window.scrollTo(0, 0); }, []);

  const [isRegister, setIsRegister] = useState(false);
  const [isForgot, setIsForgot] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forgotSuccess, setForgotSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [formData, setFormData] = useState({
    email: '', password: '', confirmPassword: '', name: '', surname: ''
  });
  const [acceptedPrivacy, setAcceptedPrivacy] = useState(false);

  const strength = useMemo(() => getPasswordStrength(formData.password), [formData.password]);
  const passwordTooShort = formData.password.length > 0 && formData.password.length < 8;
  const passwordsMatch = formData.confirmPassword.length === 0 || formData.password === formData.confirmPassword;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (isRegister) {
      if (formData.password.length < 8) { setError('A senha deve ter pelo menos 8 caracteres.'); setLoading(false); return; }
      if (formData.password !== formData.confirmPassword) { setError('As senhas não coincidem.'); setLoading(false); return; }
    }

    try {
      if (isRegister) {
        await register(formData.email, formData.password, formData.name, formData.surname);
        const inviteAlias = localStorage.getItem('invite_alias');
        navigate(inviteAlias ? '/onboarding/invite' : '/onboarding');
      } else {
        const userData = await login(formData.email, formData.password);
        navigate(userData?.is_admin ? '/admin' : '/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao autenticar');
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: formData.email })
      });
      if (res.ok) setForgotSuccess(true);
    } catch {
      setForgotSuccess(true); // Don't reveal errors
    } finally {
      setLoading(false);
    }
  };

  const update = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  const switchMode = (mode) => {
    setIsRegister(mode === 'register');
    setIsForgot(mode === 'forgot');
    setForgotSuccess(false);
    setError('');
    setAcceptedPrivacy(false);
  };

  // ── Forgot Password View ──
  if (isForgot) {
    return (
      <div className="min-h-screen flex items-center justify-center dream-mesh px-6" data-testid="login-page">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
          <Link to="/" className="flex items-center justify-center gap-2 mb-5">
            <Heart className="w-7 h-7 text-[#FFBE98] fill-[#FFBE98]" />
            <span className="text-xl font-bold text-[#2D2A26]">4Luis</span>
          </Link>
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-stone-100">
            {forgotSuccess ? (
              <div className="text-center py-2">
                <div className="w-10 h-10 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Check className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-sm font-bold text-[#2D2A26] mb-1">Email enviado!</p>
                <p className="text-xs text-[#6B6661] mb-4" data-testid="forgot-success-msg">
                  Se este email existir, vais receber instruções para repor a tua palavra-passe.
                </p>
                <button onClick={() => switchMode('login')}
                  className="text-xs text-[#FFBE98] font-medium hover:underline" data-testid="back-to-login-link">
                  Voltar ao login
                </button>
              </div>
            ) : (
              <>
                <h1 className="text-lg font-bold text-center mb-1">Recuperar palavra-passe</h1>
                <p className="text-xs text-[#6B6661] text-center mb-4">Insere o teu email e enviamos instruções</p>
                <form onSubmit={handleForgot} className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium mb-1.5 flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-[#FFBE98]" />{t('auth.email')}
                    </label>
                    <input type="email" value={formData.email}
                      onChange={(e) => update('email', e.target.value)}
                      placeholder="o-teu-email@exemplo.com"
                      className="w-full px-3.5 py-2.5 input-warm text-sm" required
                      data-testid="email-input" />
                  </div>
                  {error && <p className="text-red-500 text-xs text-center">{error}</p>}
                  <button type="submit" disabled={loading}
                    className="w-full btn-primary disabled:opacity-50 text-sm" data-testid="forgot-submit-btn">
                    {loading ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" /> : 'Enviar instruções'}
                  </button>
                </form>
                <p className="text-center text-xs text-[#6B6661] mt-4">
                  <button onClick={() => switchMode('login')}
                    className="text-[#FFBE98] font-medium hover:underline" data-testid="back-to-login-link">
                    Voltar ao login
                  </button>
                </p>
              </>
            )}
          </div>
        </motion.div>
      </div>
    );
  }

  // ── Login / Register View ──
  return (
    <div className="min-h-screen flex items-center justify-center dream-mesh px-6 py-8" data-testid="login-page">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        {/* Logo — compact */}
        <Link to="/" className="flex items-center justify-center gap-2 mb-4">
          <Heart className="w-7 h-7 text-[#FFBE98] fill-[#FFBE98]" />
          <span className="text-xl font-bold text-[#2D2A26]">4Luis</span>
        </Link>

        <div className="bg-white rounded-2xl p-5 shadow-lg border border-stone-100">
          <h1 className="text-lg font-bold text-center mb-1" data-testid="auth-title">
            {isRegister ? t('auth.register') : t('auth.login')}
          </h1>
          {!isRegister && (
            <p className="text-[10px] text-[#6B6661] text-center mb-4">
              Entra para continuar a apoiar viagens e desbloquear a tua
            </p>
          )}
          {isRegister && <div className="mb-4" />}

          {/* Google Login */}
          <button onClick={() => loginWithGoogle()}
            className="w-full flex items-center justify-center gap-2.5 py-2.5 px-4 rounded-xl border-2 border-stone-200 hover:border-stone-300 transition-colors mb-4 text-sm"
            data-testid="google-login-btn">
            <svg className="w-4.5 h-4.5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            <span className="font-medium text-sm">{t('auth.google')}</span>
          </button>

          {/* Divider — compact */}
          <div className="relative mb-4">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-stone-200"></div></div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 bg-white text-[#6B6661]">{t('auth.or')}</span>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            {isRegister && (
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium mb-1 flex items-center gap-1">
                    <User className="w-3 h-3 text-[#FFBE98]" />{t('user.name')}
                  </label>
                  <input type="text" value={formData.name}
                    onChange={(e) => update('name', e.target.value)}
                    placeholder="Nome" className="w-full px-3 py-2 input-warm text-sm"
                    required data-testid="name-input" />
                </div>
                <div>
                  <label className="block text-xs font-medium mb-1 flex items-center gap-1">
                    <User className="w-3 h-3 text-[#E0C097]" />{t('user.surname')}
                  </label>
                  <input type="text" value={formData.surname}
                    onChange={(e) => update('surname', e.target.value)}
                    placeholder="Apelido" className="w-full px-3 py-2 input-warm text-sm"
                    data-testid="surname-input" />
                </div>
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-xs font-medium mb-1 flex items-center gap-1">
                <Mail className="w-3 h-3 text-[#FFBE98]" />{t('auth.email')}
              </label>
              <input type="email" value={formData.email}
                onChange={(e) => update('email', e.target.value)}
                placeholder="o-teu-email@exemplo.com"
                className="w-full px-3 py-2 input-warm text-sm" required
                data-testid="email-input" />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-medium mb-1 flex items-center gap-1">
                <Lock className="w-3 h-3 text-[#FFBE98]" />{t('auth.password')}
              </label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} value={formData.password}
                  onChange={(e) => update('password', e.target.value)}
                  placeholder={isRegister ? 'Mínimo 8 caracteres' : ''}
                  className="w-full px-3 py-2 pr-10 input-warm text-sm" required
                  data-testid="password-input" />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6B6661] hover:text-[#2D2A26] p-0.5" tabIndex={-1}
                  data-testid="toggle-password-visibility">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Forgot password link (login only) */}
              {!isRegister && (
                <div className="mt-1 text-right">
                  <button type="button" onClick={() => switchMode('forgot')}
                    className="text-[10px] text-[#FFBE98] hover:underline font-medium"
                    data-testid="forgot-password-link">
                    Esqueceste-te da palavra-passe?
                  </button>
                </div>
              )}

              {/* Strength indicator (register only) */}
              {isRegister && formData.password.length > 0 && (
                <div className="mt-1.5 space-y-1">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 flex gap-1">
                      {[1, 2, 3].map(i => (
                        <div key={i}
                          className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                            i <= strength.level ? strength.color : 'bg-stone-200'
                          }`} />
                      ))}
                    </div>
                    <span className={`text-[10px] font-medium ${
                      strength.level === 1 ? 'text-red-500' : strength.level === 2 ? 'text-amber-500' : 'text-green-600'
                    }`} data-testid="password-strength-label">{strength.label}</span>
                  </div>
                  {passwordTooShort && (
                    <p className="text-[10px] text-red-400 flex items-center gap-1" data-testid="password-too-short">
                      <X className="w-2.5 h-2.5" /> Mínimo 8 caracteres
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Confirm Password (register only) */}
            {isRegister && (
              <div>
                <label className="block text-xs font-medium mb-1 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-[#FFBE98]" />Confirmar senha
                </label>
                <div className="relative">
                  <input type={showConfirm ? 'text' : 'password'} value={formData.confirmPassword}
                    onChange={(e) => update('confirmPassword', e.target.value)}
                    placeholder="Repete a tua senha"
                    className={`w-full px-3 py-2 pr-10 input-warm text-sm ${
                      formData.confirmPassword.length > 0 && !passwordsMatch ? 'border-red-300' :
                      formData.confirmPassword.length > 0 && passwordsMatch ? 'border-green-300' : ''
                    }`} required data-testid="confirm-password-input" />
                  <button type="button" onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#6B6661] hover:text-[#2D2A26] p-0.5" tabIndex={-1}
                    data-testid="toggle-confirm-visibility">
                    {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {formData.confirmPassword.length > 0 && (
                  <p className={`text-[10px] mt-1 flex items-center gap-1 ${
                    passwordsMatch ? 'text-green-600' : 'text-red-400'
                  }`} data-testid="password-match-feedback">
                    {passwordsMatch
                      ? <><Check className="w-2.5 h-2.5" /> As senhas coincidem</>
                      : <><X className="w-2.5 h-2.5" /> As senhas não coincidem</>}
                  </p>
                )}
              </div>
            )}

            {/* Privacy consent (register only) */}
            {isRegister && (
              <label className="flex items-start gap-2 cursor-pointer" data-testid="privacy-consent-label">
                <input type="checkbox" checked={acceptedPrivacy}
                  onChange={(e) => setAcceptedPrivacy(e.target.checked)}
                  className="mt-0.5 w-3.5 h-3.5 rounded border-stone-300 text-[#FFBE98] focus:ring-[#FFBE98]"
                  data-testid="privacy-consent-checkbox" />
                <span className="text-[10px] text-[#6B6661] leading-relaxed">
                  Li e aceito a{' '}
                  <a href="/privacy" target="_blank" className="text-[#FFBE98] font-medium hover:underline">
                    Política de Privacidade
                  </a>
                </span>
              </label>
            )}

            {error && <p className="text-red-500 text-xs text-center" data-testid="error-message">{error}</p>}

            <button type="submit"
              disabled={loading || (isRegister && (passwordTooShort || !passwordsMatch || !acceptedPrivacy))}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              data-testid="submit-btn">
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto" />
              ) : (
                isRegister ? t('auth.register') : t('auth.login')
              )}
            </button>
          </form>

          <p className="text-center text-xs text-[#6B6661] mt-4">
            {isRegister ? t('auth.has_account') : t('auth.no_account')}{' '}
            <button onClick={() => switchMode(isRegister ? 'login' : 'register')}
              className="text-[#FFBE98] font-medium hover:underline" data-testid="toggle-auth-btn">
              {isRegister ? t('auth.login') : t('auth.register')}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
