import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Quote } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BADGE_STYLES = {
  'Sonhador': 'bg-[#FFF0E6] text-[#B87333]',
  'Sonhador Verificado': 'bg-green-50 text-green-700',
  'Embaixador': 'bg-amber-50 text-amber-700',
};

const TestimonialsSection = ({ variant = 'default' }) => {
  const [testimonials, setTestimonials] = useState([]);

  useEffect(() => {
    axios.get(`${API}/testimonials/published`).then(res => {
      setTestimonials(res.data.testimonials || []);
    }).catch(() => {});
  }, []);

  if (testimonials.length === 0) return null;

  if (variant === 'compact') {
    return (
      <div className="space-y-3" data-testid="testimonials-compact">
        {testimonials.slice(0, 2).map((t, i) => (
          <motion.div key={t.testimonial_id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-stone-100">
            <p className="text-sm text-[#2D2A26] italic leading-relaxed">&ldquo;{t.text}&rdquo;</p>
            <p className="text-xs text-[#6B6661] mt-2 flex items-center gap-2">
              <span>— {t.user_name}</span>
              <span className={`px-1.5 py-0.5 rounded text-xs font-semibold ${BADGE_STYLES[t.badge] || BADGE_STYLES['Sonhador']}`}>
                {t.badge}
              </span>
            </p>
          </motion.div>
        ))}
      </div>
    );
  }

  return (
    <section className="py-16 px-4" data-testid="testimonials-section">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-[#2D2A26]">Sonhadores dizem</h2>
          <p className="text-[#6B6661] text-sm mt-2">Experiencias reais de quem confia na 4Luis</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {testimonials.slice(0, 6).map((t, i) => (
            <motion.div key={t.testimonial_id}
              initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: i * 0.08 }}
              className="bg-white rounded-2xl border border-stone-100 p-6 shadow-sm hover:shadow-md transition-shadow"
              data-testid={`testimonial-card-${i}`}>
              <Quote className="w-5 h-5 text-[#FFBE98] mb-3" />
              <p className="text-[#2D2A26] text-sm leading-relaxed italic">&ldquo;{t.text}&rdquo;</p>
              <div className="mt-4 pt-3 border-t border-stone-100 flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-[#FFBE98]/20 flex items-center justify-center text-xs font-bold text-[#FFBE98]">
                  {t.user_name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#2D2A26]">{t.user_name}</p>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${BADGE_STYLES[t.badge] || BADGE_STYLES['Sonhador']}`}>
                    {t.badge}
                  </span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default TestimonialsSection;
