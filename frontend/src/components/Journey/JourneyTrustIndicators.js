import React from 'react';
import { ShieldCheck, Check, Clock } from 'lucide-react';

/**
 * JourneyTrustIndicators — displays certification badge and trust metrics.
 * Reusable across JourneyDetail and other pages.
 */
const JourneyTrustIndicators = ({ ambassadorInfo, trustIndicators }) => {
  if (!ambassadorInfo) return null;

  const certLevel = ambassadorInfo.certification_level;
  const certLabel = ambassadorInfo.certification_label;

  return (
    <div data-testid="journey-trust-block">
      {/* Certification Badge */}
      {certLabel && (
        <span
          className={`inline-flex items-center gap-1 mt-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
            certLevel === 'confiavel' ? 'bg-emerald-100 text-emerald-700'
            : certLevel === 'verificado' ? 'bg-blue-100 text-blue-700'
            : 'bg-[#FFBE98]/20 text-[#2D2A26]'
          }`}
          data-testid="certification-badge"
          title="Este embaixador foi validado pela 4Luis"
        >
          <ShieldCheck className="w-3 h-3" />
          {certLabel}
        </span>
      )}

      {/* Trust Indicators */}
      {trustIndicators && trustIndicators.confirmed_count > 0 && (
        <div className="flex items-center gap-3 mt-2 flex-wrap" data-testid="trust-indicators">
          <span className="text-[10px] text-[#6B6661] flex items-center gap-1">
            <Check className="w-3 h-3 text-emerald-500" />
            {trustIndicators.confirmed_count} pagamentos confirmados
          </span>
          {trustIndicators.confirmation_rate > 0 && (
            <span className="text-[10px] text-emerald-600 font-medium">
              {trustIndicators.confirmation_rate}% taxa de confirmação
            </span>
          )}
          {trustIndicators.avg_confirmation_label && (
            <span className="text-[10px] text-blue-600 font-medium flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Confirmação em {trustIndicators.avg_confirmation_label}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default JourneyTrustIndicators;
