import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

const JourneyCard = ({ journey, index }) => {
  const { t } = useLanguage();
  const progress = Math.min((journey.current_amount / journey.goal_amount) * 100, 100);

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

          {/* Progress */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-[#2D2A26] font-medium">
                €{journey.current_amount.toLocaleString()} {t('journeys.progress')}
              </span>
              <span className="text-[#6B6661]">
                €{journey.goal_amount.toLocaleString()} {t('journeys.goal')}
              </span>
            </div>
            <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                whileInView={{ width: `${progress}%` }}
                viewport={{ once: true }}
                transition={{ duration: 1, delay: 0.3 }}
                className="h-full progress-bar-warm rounded-full"
              />
            </div>
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
