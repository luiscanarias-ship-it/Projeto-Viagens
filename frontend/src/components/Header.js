import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Menu, X, User, LogOut, Settings, Heart, Mail } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import NotificationBell from './NotificationBell';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const languages = [
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' }
];

const Header = () => {
  const { user, logout } = useAuth();
  const { language, changeLanguage, t, isTranslating } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [contactEmail, setContactEmail] = useState('contacto@4luis.com');
  const [activeSection, setActiveSection] = useState(null);

  useEffect(() => {
    if (location.pathname !== '/') setActiveSection(null);
  }, [location.pathname]);

  const isActive = (key) => {
    if (key === 'journeys') return location.pathname === '/' && activeSection === 'journeys';
    if (key === '/') return location.pathname === '/' && activeSection !== 'journeys';
    if (key === '/plan-trip') return location.pathname.startsWith('/plan-trip') || location.pathname.startsWith('/travel-planner');
    return location.pathname.startsWith(key);
  };

  const activeStyle = 'text-[#FFBE98] after:absolute after:bottom-[-4px] after:left-0 after:right-0 after:h-[2px] after:bg-[#FFBE98] after:rounded-full';

  const navLinkClass = (key) =>
    `transition-colors text-sm font-medium whitespace-nowrap relative ${
      isActive(key) ? activeStyle : 'text-[#2D2A26] hover:text-[#FFBE98]'
    }`;

  const mobileNavClass = (key) =>
    `block py-3 font-medium w-full text-left ${
      isActive(key)
        ? 'text-[#FFBE98] border-l-2 border-[#FFBE98] pl-3'
        : 'text-[#2D2A26]'
    }`;

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await axios.get(`${API}/settings`);
        if (response.data.contact_email) {
          setContactEmail(response.data.contact_email);
        }
      } catch (error) {
        // Use default email
      }
    };
    fetchSettings();
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const currentLang = languages.find(l => l.code === language) || languages[0];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass" data-testid="header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-12">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <motion.div 
              whileHover={{ scale: 1.05 }}
              className="flex items-center gap-2"
            >
              <Heart className="w-8 h-8 text-[#FFBE98] fill-[#FFBE98]" />
              <span className="text-2xl font-bold text-[#2D2A26] tracking-tight">4Luis</span>
            </motion.div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-5">
            <Link 
              to="/" 
              onClick={() => setActiveSection(null)}
              className={navLinkClass('/')}
              data-testid="nav-home"
            >
              {t('nav.home')}
            </Link>
            <Link 
              to="/" 
              onClick={(e) => {
                e.preventDefault();
                setActiveSection('journeys');
                if (window.location.pathname === '/') {
                  document.getElementById('journeys')?.scrollIntoView({ behavior: 'smooth' });
                } else {
                  navigate('/?scrollTo=journeys');
                }
              }}
              className={navLinkClass('journeys')}
              data-testid="nav-journeys"
            >
              Explorar Viagens
            </Link>
            <Link 
              to="/" 
              onClick={(e) => {
                e.preventDefault();
                if (window.location.pathname === '/') {
                  document.getElementById('main-journey')?.scrollIntoView({ behavior: 'smooth' });
                } else {
                  navigate('/');
                }
              }}
              className="px-5 py-2 bg-[#FFBE98] text-white hover:bg-[#E6A07C] transition-colors font-bold rounded-full text-sm shadow-sm whitespace-nowrap"
              data-testid="nav-main-journey"
            >
              Viagem Principal
            </Link>
            <Link 
              to="/plan-trip" 
              className={navLinkClass('/plan-trip')}
              data-testid="nav-plan-trip"
            >
              Planear Viagem
            </Link>
            
            {user && (
              <Link 
                to="/dashboard" 
                className={navLinkClass('/dashboard')}
                data-testid="nav-dashboard"
              >
                {t('nav.dashboard')}
              </Link>
            )}
            
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
            {/* Language Selector */}
            <div className="relative">
              <button
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-full hover:bg-stone-100 transition-colors"
                data-testid="language-selector"
              >
                <Globe className="w-5 h-5 text-[#6B6661]" />
                <span className="hidden sm:inline text-sm">{currentLang.flag}</span>
                {isTranslating && (
                  <span className="w-2 h-2 rounded-full bg-[#FFBE98] animate-pulse-soft" />
                )}
              </button>
              
              <AnimatePresence>
                {langMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute right-0 mt-2 w-48 bg-white rounded-2xl shadow-xl border border-stone-100 overflow-hidden"
                  >
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => {
                          changeLanguage(lang.code);
                          setLangMenuOpen(false);
                        }}
                        className={`w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-stone-50 transition-colors ${
                          language === lang.code ? 'bg-[#E6F4F1]' : ''
                        }`}
                        data-testid={`lang-${lang.code}`}
                      >
                        <span>{lang.flag}</span>
                        <span className="text-sm">{lang.name}</span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Notification Bell */}
            {user && <NotificationBell />}

            {/* User Menu / Login */}
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#E6F4F1] hover:bg-[#d0e8e3] transition-colors"
                  data-testid="user-menu-btn"
                >
                  {user.picture ? (
                    <img src={user.picture} alt="" className="w-6 h-6 rounded-full" />
                  ) : (
                    <User className="w-5 h-5 text-[#2D2A26]" />
                  )}
                  <span className="hidden sm:inline text-sm font-medium">{user.name}</span>
                </button>
                
                <AnimatePresence>
                  {userMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute right-0 mt-2 w-48 bg-white rounded-2xl shadow-xl border border-stone-100 overflow-hidden"
                    >
                      <Link
                        to="/dashboard"
                        onClick={() => setUserMenuOpen(false)}
                        className="w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-stone-50 transition-colors"
                        data-testid="menu-dashboard"
                      >
                        <User className="w-4 h-4" />
                        <span className="text-sm">{t('nav.dashboard')}</span>
                      </Link>
                      {user.is_admin && (
                        <Link
                          to="/admin"
                          onClick={() => setUserMenuOpen(false)}
                          className="w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-stone-50 transition-colors"
                          data-testid="menu-admin"
                        >
                          <Settings className="w-4 h-4" />
                          <span className="text-sm">{t('nav.admin')}</span>
                        </Link>
                      )}
                      <button
                        onClick={() => {
                          handleLogout();
                          setUserMenuOpen(false);
                        }}
                        className="w-full px-4 py-3 text-left flex items-center gap-3 hover:bg-stone-50 transition-colors text-red-500"
                        data-testid="menu-logout"
                      >
                        <LogOut className="w-4 h-4" />
                        <span className="text-sm">{t('nav.logout')}</span>
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <Link
                to="/login"
                className="btn-primary text-sm px-4 sm:px-6 py-2 sm:py-2.5 whitespace-nowrap"
                data-testid="login-btn"
              >
                {t('nav.login')}
              </Link>
            )}

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-stone-100"
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-white border-t border-stone-100"
          >
            <div className="px-6 py-4 space-y-2">
              <Link
                to="/"
                onClick={() => { setActiveSection(null); setMobileMenuOpen(false); }}
                className={mobileNavClass('/')}
              >
                {t('nav.home')}
              </Link>
              <button
                onClick={() => {
                  setActiveSection('journeys');
                  setMobileMenuOpen(false);
                  if (window.location.pathname === '/') {
                    setTimeout(() => {
                      document.getElementById('journeys')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 350);
                  } else {
                    navigate('/');
                    setTimeout(() => {
                      document.getElementById('journeys')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 800);
                  }
                }}
                className={mobileNavClass('journeys')}
              >
                Explorar Viagens
              </button>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  if (window.location.pathname === '/') {
                    setTimeout(() => {
                      document.getElementById('main-journey')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 350);
                  } else {
                    navigate('/');
                    setTimeout(() => {
                      document.getElementById('main-journey')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 800);
                  }
                }}
                className="block py-3 text-[#FFBE98] font-bold w-full text-left"
              >
                Viagem Principal
              </button>
              <Link
                to="/plan-trip"
                onClick={() => setMobileMenuOpen(false)}
                className={mobileNavClass('/plan-trip')}
                data-testid="mobile-nav-plan-trip"
              >
                Planear Viagem
              </Link>
              {user && (
                <Link
                  to="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className={mobileNavClass('/dashboard')}
                >
                  {t('nav.dashboard')}
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};

export default Header;
