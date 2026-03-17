import { useEffect } from 'react';

const SEO = ({ title, description }) => {
  const siteName = '4Luis';

  useEffect(() => {
    document.title = title ? title + ' | ' + siteName : siteName;
    
    const setMeta = (name, content) => {
      if (!content) return;
      let el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute(name.startsWith('og:') || name.startsWith('twitter:') ? 'property' : 'name', name);
        document.head.appendChild(el);
      }
      el.setAttribute('content', content);
    };

    const desc = description || 'A plataforma de CrowdDreaming para quem acredita que as viagens de sonho se podem concretizar.';
    setMeta('description', desc);
    setMeta('og:title', document.title);
    setMeta('og:description', desc);
    setMeta('og:site_name', siteName);
    setMeta('twitter:card', 'summary_large_image');
    setMeta('twitter:title', document.title);
    setMeta('twitter:description', desc);
  }, [title, description]);

  return null;
};

export default SEO;
