import { useEffect } from 'react';

const SEO = ({ title, description, image, type }) => {
  const siteName = '4Luis';

  useEffect(() => {
    document.title = title ? title + ' | ' + siteName : siteName;
    
    const setMeta = (attr, name, content) => {
      if (!content) return;
      let el = document.querySelector(`meta[${attr}="${name}"]`);
      if (!el) {
        el = document.createElement('meta');
        el.setAttribute(attr, name);
        document.head.appendChild(el);
      }
      el.setAttribute('content', content);
    };

    const desc = description || 'A plataforma de CrowdDreaming para quem acredita que as viagens de sonho se podem concretizar.';
    setMeta('name', 'description', desc);
    setMeta('property', 'og:title', document.title);
    setMeta('property', 'og:description', desc);
    setMeta('property', 'og:site_name', siteName);
    setMeta('property', 'og:type', type || 'website');
    if (image) {
      setMeta('property', 'og:image', image);
      setMeta('property', 'og:image:width', '1200');
      setMeta('property', 'og:image:height', '630');
    }
    setMeta('property', 'og:url', window.location.href);
    setMeta('name', 'twitter:card', image ? 'summary_large_image' : 'summary');
    setMeta('name', 'twitter:title', document.title);
    setMeta('name', 'twitter:description', desc);
    if (image) {
      setMeta('name', 'twitter:image', image);
    }
  }, [title, description, image, type]);

  return null;
};

export default SEO;
