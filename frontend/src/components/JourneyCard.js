import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Calendar } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const JourneyCard = ({ journey, index }) => {
  const { t } = useLanguage();
  // Only show progress if goal_amount exists and is greater than 0 (for internal calculation only)
  const hasProgress = journey.goal_amount && journey.goal_amount > 0;
  const progress = hasProgress ? Math.min((journey.current_amount / journey.goal_amount) * 100, 100) : 0;

  // Format target date for display
  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-PT', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="card-journey group"
      data-testid={`journey-card-${journey.journey_id}`}
    >
      <Link to={`/journey/${journey.journey_id}`}>
        {/* Image */}
        <div className="relative h-64 overflow-hidden">
          <img
            src={journey.image_url}
            alt={journey.name}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
          <div className="absolute bottom-4 left-4 right-4">
            <span className="text-white/80 text-sm font-handwritten text-lg">
              {journey.poetic_name}
            </span>
            <h3 className="text-white text-2xl font-bold mt-1">{journey.name}</h3>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-[#6B6661] text-sm mb-4 line-clamp-2">
            {journey.emotional_message}
          </p>

          {/* Progress - Hidden progress bar, only show date */}
          <div className="mb-4">
            {journey.target_date && (
              <p className="text-xs text-[#6B6661] flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Data objetivo: {formatDate(journey.target_date)}
              </p>
            )}
          </div>

          {/* CTA */}
          <div className="flex items-center justify-between">
            <span className="text-[#FFBE98] font-semibold group-hover:text-[#FFAB7D] transition-colors">
              {t('journeys.support')}
            </span>
            <ArrowRight className="w-5 h-5 text-[#FFBE98] transition-transform group-hover:translate-x-2" />
          </div>
        </div>
      </Link>
    </motion.div>
  );
};

export default JourneyCard;
