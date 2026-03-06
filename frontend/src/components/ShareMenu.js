import React, { useState, useRef, useEffect } from 'react';
import { Copy, Check, Share2, X } from 'lucide-react';

const SHARE_MESSAGE = (link) => `Acredito que os sonhos podem tornar-se realidade.\n\nEstou a ajudar a financiar uma viagem de sonho na 4Luis.\nSe quiseres participar também:\n\n${link}`;

const WhatsAppIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

const TelegramIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
  </svg>
);

const GmailIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
    <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z"/>
  </svg>
);

const ShareMenu = ({ inviteLink, buttonLabel = "Partilhar convite", buttonClassName }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setIsOpen(false);
    };
    if (isOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const message = SHARE_MESSAGE(inviteLink);
  const encodedMsg = encodeURIComponent(message);

  const shareWhatsApp = () => {
    window.open(`https://wa.me/?text=${encodedMsg}`, '_blank');
    setIsOpen(false);
  };

  const shareTelegram = () => {
    window.open(`https://t.me/share/url?url=${encodeURIComponent(inviteLink)}&text=${encodeURIComponent(message.replace(inviteLink, '').trim())}`, '_blank');
    setIsOpen(false);
  };

  const shareGmail = () => {
    const subject = encodeURIComponent('Junta-te a mim na 4Luis');
    const body = encodedMsg;
    window.open(`https://mail.google.com/mail/?view=cm&fs=1&su=${subject}&body=${body}`, '_blank');
    setIsOpen(false);
  };

  const copyLink = () => {
    navigator.clipboard.writeText(inviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const defaultBtnClass = "flex items-center justify-center gap-2 py-2.5 px-5 bg-[#FFBE98] text-[#2D2A26] rounded-xl text-sm font-semibold hover:bg-[#FFBE98]/80 transition-colors";

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={buttonClassName || defaultBtnClass}
        data-testid="share-menu-trigger"
      >
        <Share2 className="w-4 h-4" />
        {buttonLabel}
      </button>

      {isOpen && (
        <div className="absolute z-50 top-full mt-2 left-1/2 -translate-x-1/2 w-64 bg-white rounded-2xl shadow-2xl border border-stone-100 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
          data-testid="share-menu-dropdown"
        >
          <div className="flex items-center justify-between px-4 pt-3 pb-2">
            <p className="text-sm font-bold text-[#2D2A26]">Partilhar via</p>
            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-stone-100 rounded-full">
              <X className="w-3.5 h-3.5 text-[#6B6661]" />
            </button>
          </div>

          <div className="px-2 pb-2 space-y-0.5">
            <button onClick={shareWhatsApp} data-testid="share-whatsapp"
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-green-50 rounded-xl transition-colors group">
              <div className="w-9 h-9 bg-[#25D366] rounded-full flex items-center justify-center text-white flex-shrink-0">
                <WhatsAppIcon />
              </div>
              <span className="text-sm font-medium text-[#2D2A26] group-hover:text-[#25D366]">WhatsApp</span>
            </button>

            <button onClick={shareTelegram} data-testid="share-telegram"
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-blue-50 rounded-xl transition-colors group">
              <div className="w-9 h-9 bg-[#0088cc] rounded-full flex items-center justify-center text-white flex-shrink-0">
                <TelegramIcon />
              </div>
              <span className="text-sm font-medium text-[#2D2A26] group-hover:text-[#0088cc]">Telegram</span>
            </button>

            <button onClick={shareGmail} data-testid="share-gmail"
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-red-50 rounded-xl transition-colors group">
              <div className="w-9 h-9 bg-[#EA4335] rounded-full flex items-center justify-center text-white flex-shrink-0">
                <GmailIcon />
              </div>
              <span className="text-sm font-medium text-[#2D2A26] group-hover:text-[#EA4335]">Gmail</span>
            </button>

            <button onClick={copyLink} data-testid="share-copy-link"
              className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-stone-100 rounded-xl transition-colors group">
              <div className="w-9 h-9 bg-[#2D2A26] rounded-full flex items-center justify-center text-white flex-shrink-0">
                {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
              </div>
              <span className="text-sm font-medium text-[#2D2A26]">{copied ? 'Copiado!' : 'Copiar link'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShareMenu;
