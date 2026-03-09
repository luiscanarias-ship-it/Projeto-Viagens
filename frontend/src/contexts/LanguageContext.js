import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
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
  
  // Main Journey
  "home.main_journey": "Viagem Principal",
  "home.progress": "Progresso",
  "home.goal_reached": "Objetivo atingido! Ainda podes contribuir.",
  "home.contribute_dream": "Contribuir para este Sonho",
  "home.latest_contributions": "Últimas Contribuições",
  "home.view_all_contributions": "Ver todas as contribuições",
  "home.no_main_journey": "Nenhuma viagem principal ativa de momento.",
  "home.funded": "financiado",
  
  // Community Stats
  "home.dreamers": "Sonhadores",
  "home.top_dreamer": "Maior Sonhador",
  
  // Social Proof & How it Works
  "home.social_proof": "sonhadores já ajudaram esta plataforma",
  "home.how_it_works": "Como funciona o Crowddreaming",
  "home.step1_title": "Apoia um sonho",
  "home.step1_desc": "Apoia a viagem principal e ajuda a concretizar um sonho",
  "home.step2_title": "Convida 3 amigos a contribuirem",
  "home.step2_desc": "Partilha o sonho com os teus amigos e torna-te embaixador da 4Luis",
  "home.step3_title": "Embaixador: financia a tua viagem",
  "home.step3_desc": "Angaria apoio para realizares a tua viagem de sonho",
  "home.support_dream": "Apoiar este sonho",
  
  // Plan Your Trip
  "home.plan_trip": "Planeia a Tua Viagem",
  "home.plan_trip_desc": "Ferramentas úteis para planear a viagem dos teus sonhos",
  "home.plan_trip_intro": "Descobre quanto pode custar a tua viagem e encontra as melhores opções de voos, alojamento e experiências.",
  "home.plan_placeholder": "Escreve o teu destino... (ex: Paris, Tóquio)",
  "home.search": "Pesquisar",
  "home.resources_for": "Recursos para:",
  "home.map": "Mapa",
  "home.where_to_stay": "Onde Ficar",
  "home.options": "opções",
  "home.flights": "Voos",
  "home.airlines": "companhias",
  "home.resources": "Recursos",
  "home.sites": "sites",
  
  // Ambassador Journeys
  "home.ambassador_journeys": "Viagens dos Embaixadores",
  "home.materializing_dreams": "Sonhos em Fase de Materialização",
  "home.help_dreamers": "Ajuda outros sonhadores a concretizar as suas viagens de sonho",
  "home.featured": "Em Destaque",
  "home.highlight": "Destaque",
  "home.by": "por",
  "home.no_ambassador_journeys": "Ainda não existem viagens de embaixadores em angariação.",
  "home.become_ambassador": "Torna-te Embaixador para criar a tua viagem!",
  
  // Realized Dreams
  "home.real_stories": "Histórias Reais",
  "home.realized_dreams": "Sonhos Realizados",
  "home.realized_desc": "Viagens que se tornaram realidade graças à comunidade 4Luis",
  "home.inspiration": "Inspiração",
  "home.dream_singular": "sonho",
  "home.dream_plural": "sonhos",
  "home.realized": "Realizado",
  "home.no_realized": "Ainda não existem sonhos realizados.",
  "home.be_first": "Sê o primeiro a completar uma viagem!",
  
  // Emotional Quote
  "home.quote1": "Todos os sonhos começam com um primeiro passo.",
  "home.quote2": "Ajuda alguém a viajar hoje.",
  "home.quote3": "E amanhã pode ser a tua vez.",

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

  // Translate on mount if language is not Portuguese
  const initialTranslated = useRef(false);
  useEffect(() => {
    if (!initialTranslated.current && language !== 'pt') {
      initialTranslated.current = true;
      translateTexts(language);
    }
  }, [language, translateTexts]);

  const langNameMap = { en: 'English', es: 'Spanish', fr: 'French', de: 'German', it: 'Italian' };

  // Translate arbitrary dynamic texts (DB content)
  const translateDynamic = useCallback(async (textsObj) => {
    if (language === 'pt' || !textsObj || Object.keys(textsObj).length === 0) return textsObj;
    try {
      const response = await axios.post(`${API}/translate`, {
        texts: textsObj,
        target_language: langNameMap[language] || 'English'
      });
      return response.data.translations || textsObj;
    } catch {
      return textsObj;
    }
  }, [language]);

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
      translateDynamic,
      t,
      isTranslating,
      texts
    }}>
      {children}
    </LanguageContext.Provider>
  );
};
