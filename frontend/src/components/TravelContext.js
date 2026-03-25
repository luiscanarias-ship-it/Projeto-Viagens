import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plane, Building2, ArrowRight, Train, Car, Lightbulb, ChevronDown, ChevronUp, MapPin, Phone } from 'lucide-react';

const TravelContext = ({ plan }) => {
  const [expanded, setExpanded] = useState(true);
  const flight = plan?.flight_info;
  const hotel = plan?.hotel_info;
  const transport = plan?.airport_to_hotel;

  if (!flight && !hotel) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl border border-stone-200 overflow-hidden"
      data-testid="travel-context"
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gradient-to-r from-stone-50 to-white hover:from-stone-100 transition-colors"
        data-testid="travel-context-toggle"
      >
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-sky-100 rounded-lg flex items-center justify-center">
            <Plane className="w-3.5 h-3.5 text-sky-600" />
          </div>
          <p className="text-xs font-bold text-[#2D2A26]">Informacao de viagem</p>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-stone-400" /> : <ChevronDown className="w-4 h-4 text-stone-400" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Flights */}
          {flight && (
            <div className="space-y-2" data-testid="flight-info">
              {/* Outbound */}
              {flight.outbound && (
                <div className="flex items-center gap-3 bg-sky-50/50 rounded-lg p-2.5">
                  <Plane className="w-4 h-4 text-sky-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] font-bold text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded">{flight.outbound.flight_number}</span>
                      <span className="text-[10px] text-[#6B6661]">Ida</span>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="text-left">
                        <p className="text-[11px] font-semibold text-[#2D2A26]">{flight.outbound.departure_time}</p>
                        <p className="text-[9px] text-[#6B6661] truncate max-w-[120px]">{flight.outbound.departure_airport}</p>
                      </div>
                      <ArrowRight className="w-3 h-3 text-stone-300 shrink-0 mx-1" />
                      <div className="text-left">
                        <p className="text-[11px] font-semibold text-[#2D2A26]">{flight.outbound.arrival_time}</p>
                        <p className="text-[9px] text-[#6B6661] truncate max-w-[120px]">{flight.outbound.arrival_airport}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {/* Return */}
              {flight.return && (
                <div className="flex items-center gap-3 bg-amber-50/50 rounded-lg p-2.5">
                  <Plane className="w-4 h-4 text-amber-500 shrink-0 rotate-180" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] font-bold text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded">{flight.return.flight_number}</span>
                      <span className="text-[10px] text-[#6B6661]">Volta</span>
                    </div>
                    <div className="flex items-center gap-1.5 mt-1">
                      <div className="text-left">
                        <p className="text-[11px] font-semibold text-[#2D2A26]">{flight.return.departure_time}</p>
                        <p className="text-[9px] text-[#6B6661] truncate max-w-[120px]">{flight.return.departure_airport}</p>
                      </div>
                      <ArrowRight className="w-3 h-3 text-stone-300 shrink-0 mx-1" />
                      <div className="text-left">
                        <p className="text-[11px] font-semibold text-[#2D2A26]">{flight.return.arrival_time}</p>
                        <p className="text-[9px] text-[#6B6661] truncate max-w-[120px]">{flight.return.arrival_airport}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Hotel */}
          {hotel && hotel.name && (
            <div className="flex items-start gap-3 bg-amber-50/30 rounded-lg p-2.5" data-testid="hotel-info">
              <Building2 className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-semibold text-[#2D2A26]">{hotel.name}</p>
                {hotel.address && (
                  <p className="text-[9px] text-[#6B6661] flex items-center gap-1 mt-0.5">
                    <MapPin className="w-2.5 h-2.5 shrink-0" />{hotel.address}
                  </p>
                )}
                <div className="flex items-center gap-3 mt-0.5">
                  {hotel.area && <span className="text-[9px] text-amber-600 font-medium">{hotel.area}</span>}
                  {hotel.phone && (
                    <span className="text-[9px] text-[#6B6661] flex items-center gap-0.5">
                      <Phone className="w-2.5 h-2.5" />{hotel.phone}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Airport to Hotel transport */}
          {transport && (
            <div className="border border-stone-100 rounded-lg overflow-hidden" data-testid="transport-info">
              <div className="px-3 py-2 bg-stone-50">
                <p className="text-[10px] font-bold text-[#2D2A26]">Como ir do aeroporto para o hotel</p>
              </div>
              <div className="p-2.5 space-y-2">
                {/* Best option */}
                {transport.best_option && (
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 bg-emerald-50 rounded-lg flex items-center justify-center shrink-0">
                      <Train className="w-3.5 h-3.5 text-emerald-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-emerald-700">Melhor opcao</span>
                        <span className="text-[9px] text-[#6B6661]">{transport.best_option.mode}</span>
                      </div>
                      <p className="text-[10px] text-[#2D2A26] mt-0.5">{transport.best_option.details}</p>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-[9px] font-semibold text-[#6B6661]">{transport.best_option.duration}</span>
                        <span className="text-[9px] text-emerald-600 font-medium">{transport.best_option.cost}</span>
                      </div>
                    </div>
                  </div>
                )}
                {/* Alternative */}
                {transport.alternative && (
                  <div className="flex items-start gap-2.5">
                    <div className="w-7 h-7 bg-stone-100 rounded-lg flex items-center justify-center shrink-0">
                      <Car className="w-3.5 h-3.5 text-stone-500" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-stone-600">Alternativa</span>
                        <span className="text-[9px] text-[#6B6661]">{transport.alternative.mode}</span>
                      </div>
                      <p className="text-[10px] text-[#2D2A26] mt-0.5">{transport.alternative.details}</p>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-[9px] font-semibold text-[#6B6661]">{transport.alternative.duration}</span>
                        <span className="text-[9px] text-stone-500 font-medium">{transport.alternative.cost}</span>
                      </div>
                    </div>
                  </div>
                )}
                {/* Tip */}
                {transport.tip && (
                  <div className="flex items-start gap-1.5 bg-amber-50/50 rounded-md px-2.5 py-1.5 mt-1">
                    <Lightbulb className="w-3 h-3 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-[9px] text-amber-800">{transport.tip}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default TravelContext;
