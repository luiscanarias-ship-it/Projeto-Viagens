import React, { useState } from 'react';
import { Share2, Link2, Check } from 'lucide-react';

const ShareButton = ({ url, text, className = '' }) => {
  const [copied, setCopied] = useState(false);

  const shareData = {
    title: '4Luis - Sonha connosco',
    text: text || 'Ajuda este sonho a tornar-se realidade!',
    url: url || window.location.href
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        if (err.name !== 'AbortError') copyToClipboard();
      }
    } else {
      copyToClipboard();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(shareData.url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={handleShare}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
        copied
          ? 'bg-green-50 text-green-700 border border-green-200'
          : 'bg-stone-50 text-[#6B6661] hover:bg-[#FFBE98]/10 hover:text-[#2D2A26] border border-stone-200'
      } ${className}`}
      data-testid="share-button"
    >
      {copied ? (
        <>
          <Check className="w-4 h-4" />
          Link copiado!
        </>
      ) : (
        <>
          <Share2 className="w-4 h-4" />
          Partilhar este sonho
        </>
      )}
    </button>
  );
};

export default ShareButton;
