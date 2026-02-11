import React from 'react';
import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const Footer = () => {
  const { t, language } = useLanguage();

  return (
    <footer className="bg-white border-t border-stone-100 mt-auto" data-testid="footer">
      <div className="max-w-7xl mx-auto px-6 md:px-12 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <Link to="/" className="flex items-center gap-2 mb-4">
              <Heart className="w-6 h-6 text-[#FFBE98] fill-[#FFBE98]" />
              <span className="text-xl font-bold text-[#2D2A26]">4Luis</span>
            </Link>
            <p className="text-[#6B6661] text-sm font-handwritten text-xl">
              {t('footer.tagline')}
            </p>
          </div>

          {/* Links */}
          <div className="flex flex-col gap-2">
            <Link to="/" className="text-[#6B6661] hover:text-[#2D2A26] text-sm transition-colors">
              {t('nav.home')}
            </Link>
            <Link to="/#journeys" className="text-[#6B6661] hover:text-[#2D2A26] text-sm transition-colors">
              {t('nav.journeys')}
            </Link>
            <Link to="/login" className="text-[#6B6661] hover:text-[#2D2A26] text-sm transition-colors">
              {t('nav.login')}
            </Link>
          </div>

          {/* Legal */}
          <div className="flex flex-col gap-2">
            <span className="text-[#6B6661] text-sm">{t('footer.privacy')}</span>
            <span className="text-[#6B6661] text-sm">{t('footer.terms')}</span>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-stone-100">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-[#6B6661]">
              © {new Date().getFullYear()} 4Luis. Todos os direitos reservados.
            </p>
            {language !== 'pt' && (
              <p className="text-xs text-[#6B6661] italic">
                {t('footer.translation_note')}
              </p>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
