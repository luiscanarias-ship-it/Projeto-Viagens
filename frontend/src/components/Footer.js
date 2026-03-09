import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Heart, Mail } from 'lucide-react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Footer = () => {
  const { t, language } = useLanguage();
  const [contactEmail, setContactEmail] = useState('contacto@4luis.com');

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

  return (
    <footer className="bg-white border-t border-stone-100 mt-auto" data-testid="footer">
      <div className="max-w-7xl mx-auto px-6 md:px-12 py-12 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <Link to="/" className="flex items-center gap-2 mb-2">
              <Heart className="w-6 h-6 text-[#FFBE98] fill-[#FFBE98]" />
              <span className="text-xl font-bold text-[#2D2A26]">4Luis</span>
            </Link>
            <p className="font-handwritten text-[#FFBE98] text-lg">Sonha connosco.</p>
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
            <Link to="/privacy" className="text-[#6B6661] hover:text-[#2D2A26] text-sm transition-colors" data-testid="footer-privacy-link">
              Privacy
            </Link>
            <Link to="/terms" className="text-[#6B6661] hover:text-[#2D2A26] text-sm transition-colors" data-testid="footer-terms-link">
              Terms
            </Link>
            <Link to="/cookies" className="text-[#6B6661] hover:text-[#2D2A26] text-sm transition-colors" data-testid="footer-cookies-link">
              Cookies
            </Link>
          </div>

          {/* Contact */}
          <div className="flex flex-col gap-2">
            <a 
              href={`mailto:${contactEmail}`}
              className="text-[#FFBE98] hover:text-[#FFAB7D] text-sm transition-colors flex items-center gap-2 font-medium"
              data-testid="footer-contact"
            >
              <Mail className="w-4 h-4" />
              Contacte-nos
            </a>
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
