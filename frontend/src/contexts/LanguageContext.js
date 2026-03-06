import React, { createContext, useContext, useState, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Default Portuguese texts
const defaultTexts = {
  // Header
  "nav.home": "Início",
  "nav.journeys": "Viagens",
  "nav.login": "Entrar",
  "nav.dashboard": "Meu Painel",
  "nav.admin": "Administração",
  "nav.logout": "Sair",
  
  // Hero
  "hero.tagline": "Aqui, cada gesto ilumina um caminho.",
  "hero.subtitle": "A plataforma de CrowdDreaming para quem acredita que os sonhos se podem concretizar.",
  "hero.cta": "Descobrir Viagens",
  
  // Journeys
  "journeys.title": "Viagens de Sonho",
  "journeys.subtitle": "Cada viagem é uma história à espera de ser vivida",
  "journeys.support": "Apoiar",
  "journeys.progress": "angariado",
  "journeys.goal": "objetivo",
  
  // Journey Detail
  "journey.dream": "O Sonho",
  "journey.impact": "O Impacto",
  "journey.support_btn": "Apoiar esta Viagem",
  "journey.crypto_bonus": "Utilize Criptomoedas para duplicar as suas possibilidades de ganhar uma viagem de sonho.",
  "journey.testimonials": "Mensagens de Apoio",
  
  // Payment
  "payment.title": "Escolha como apoiar",
  "payment.amount": "Escolha o montante",
  "payment.method": "Método de pagamento",
  "payment.card": "Cartão (Stripe)",
  "payment.mbway": "MBWay",
  "payment.paypal": "PayPal",
  "payment.wise": "Wise",
  "payment.crypto": "Criptomoeda (USDT)",
  "payment.crypto_warning": "Use a mesma rede de depósito (TRC20) para que as criptomoedas não se percam.",
  "payment.tickets": "bilhetes",
  "payment.tickets_bonus": "Pagar com crypto = bilhetes em dobro!",
  "payment.continue": "Continuar",
  "payment.back": "Voltar",
  
  // User Data
  "user.name": "Nome",
  "user.surname": "Sobrenome",
  "user.email": "Email",
  "user.email_confirm": "Confirmar Email",
  "user.submit": "Confirmar Contribuição",
  
  // Success
  "success.title": "Obrigado!",
  "success.message": "Obrigado por soprares as velas deste sonho.",
  "success.tickets": "Recebeu {count} bilhetes para o sorteio.",
  "success.share": "Partilhar com amigos",
  "success.sponsor_note": "Atenção: só tem direito aos bilhetes de participação no sorteio depois de convidar pelo menos 3 amigos a apoiar esta angariação.",
  
  // Dashboard
  "dashboard.title": "Meu Painel",
  "dashboard.tickets": "Meus Bilhetes",
  "dashboard.contributions": "Minhas Contribuições",
  "dashboard.sponsor_links": "Links de Sponsor",
  "dashboard.create_link": "Criar Link",
  "dashboard.copy_link": "Copiar Link",
  "dashboard.referrals": "Referências",
  
  // Admin
  "admin.title": "Administração",
  "admin.journeys": "Gerir Viagens",
  "admin.create": "Criar Nova Viagem",
  "admin.edit": "Editar",
  "admin.delete": "Eliminar",
  "admin.save": "Guardar",
  "admin.stats": "Estatísticas",
  
  // Auth
  "auth.login": "Entrar",
  "auth.register": "Registar",
  "auth.email": "Email",
  "auth.password": "Password",
  "auth.google": "Continuar com Google",
  "auth.or": "ou",
  "auth.no_account": "Não tem conta?",
  "auth.has_account": "Já tem conta?",
  
  // Footer
  "footer.tagline": "Cada contributo é um passo de luz.",
  "footer.privacy": "Privacidade",
  "footer.terms": "Termos",
  "footer.translation_note": "Tradução automática por IA. Podem existir pequenas imprecisões.",
  
  // Languages
  "lang.pt": "Português",
  "lang.en": "English",
  "lang.es": "Español",
  "lang.fr": "Français",
  "lang.de": "Deutsch",
  "lang.it": "Italiano"
};

const LanguageContext = createContext(null);

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(localStorage.getItem('language') || 'pt');
  const [texts, setTexts] = useState(defaultTexts);
  const [isTranslating, setIsTranslating] = useState(false);
  const [cache, setCache] = useState({});

  const translateTexts = useCallback(async (targetLang) => {
    if (targetLang === 'pt') {
      setTexts(defaultTexts);
      return;
    }

    // Use cached translation if available
    if (cache[targetLang]) {
      setTexts(cache[targetLang]);
      toast.info('Tradução automática por IA. Podem existir pequenas imprecisões.', {
        duration: 4000,
        icon: '🌐',
      });
      return;
    }

    setIsTranslating(true);
    try {
      const response = await axios.post(`${API}/translate`, {
        texts: defaultTexts,
        target_language: targetLang === 'en' ? 'English' : 
                         targetLang === 'es' ? 'Spanish' :
                         targetLang === 'fr' ? 'French' :
                         targetLang === 'de' ? 'German' :
                         targetLang === 'it' ? 'Italian' : 'English'
      });
      
      if (response.data.translations) {
        setTexts(response.data.translations);
        setCache(prev => ({ ...prev, [targetLang]: response.data.translations }));
        toast.info('Tradução automática por IA. Podem existir pequenas imprecisões.', {
          duration: 5000,
          icon: '🌐',
        });
      }
    } catch (error) {
      console.error('Translation error:', error);
      toast.error('Erro na tradução. A mostrar textos originais.');
    } finally {
      setIsTranslating(false);
    }
  }, [cache]);

  // Save language preference to user account
  const saveLanguageToAccount = useCallback(async (lang) => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      await axios.patch(`${API}/users/preferred-language`, 
        { language: lang },
        { headers: { Authorization: `Bearer ${token}` } }
      );
    } catch (e) {
      // Silent fail - localStorage still works as fallback
    }
  }, []);

  const changeLanguage = useCallback(async (newLang) => {
    setLanguage(newLang);
    localStorage.setItem('language', newLang);
    saveLanguageToAccount(newLang);
    await translateTexts(newLang);
  }, [translateTexts, saveLanguageToAccount]);

  // Sync language from user's account preference (called after login)
  const syncFromUser = useCallback(async (preferredLang) => {
    if (!preferredLang || preferredLang === language) return;
    setLanguage(preferredLang);
    localStorage.setItem('language', preferredLang);
    await translateTexts(preferredLang);
  }, [language, translateTexts]);

  const t = useCallback((key) => {
    return texts[key] || defaultTexts[key] || key;
  }, [texts]);

  return (
    <LanguageContext.Provider value={{
      language,
      changeLanguage,
      syncFromUser,
      t,
      isTranslating,
      texts
    }}>
      {children}
    </LanguageContext.Provider>
  );
};
