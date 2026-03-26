import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Plane, Building2, ArrowRight, Train, Car, Lightbulb, ChevronDown, ChevronUp, MapPin, Phone, ExternalLink, Search, Star, Bed, Ticket } from 'lucide-react';

const GYG_PARTNER_ID = 'WFPE9ME';
const buildMustSeeGYGLink = (destination, sightName) => {
  const query = `${sightName} ${destination}`.toLowerCase().replace(/[^a-záàâãéèêíïóôõúüçñ\w\s]/gi, '').replace(/\s+/g, ' ').trim();
  return `https://www.getyourguide.com/s/?q=${encodeURIComponent(query)}&partner_id=${GYG_PARTNER_ID}`;
};

const TravelContext = ({ plan, affiliateLinks, onTrackAffiliate }) => {
  const [expanded, setExpanded] = useState(true);
  const flight = plan?.flight_info;
  const hotel = plan?.hotel_info;
  const transport = plan?.airport_to_hotel;
  const mustSee = plan?.must_see;
  const stayZones = hotel?.stay_zones;

  if (!flight && !hotel && !transport) return null;

  const isSuggestionFlight = flight?.suggestion === true;
  const isSuggestionHotel = hotel?.suggestion === true;
  const hasAirportList = transport?.airports && transport.airports.length > 0;
  const hasStayZones = stayZones && stayZones.length > 0;
  const hasMustSee = mustSee && mustSee.length > 0;

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
          <p className="text-xs font-bold text-[#2D2A26]">Informação de viagem</p>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 text-stone-400" /> : <ChevronDown className="w-4 h-4 text-stone-400" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Flights — suggestion with airports list */}
          {flight && isSuggestionFlight && (
            <div className="bg-sky-50/50 rounded-lg p-3" data-testid="flight-suggestion">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-sky-100 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                  <Search className="w-4 h-4 text-sky-600" />
                </div>
                <div className="flex-1">
                  <p className="text-[11px] font-semibold text-[#2D2A26]">Voos para {plan?.destination}</p>

                  {/* Airport list */}
                  {flight.airports && flight.airports.length > 0 && (
                    <div className="mt-2 space-y-1.5">
                      {flight.airports.map((ap, i) => (
                        <div key={ap.code} className="flex items-start gap-2 bg-white/70 rounded-md px-2.5 py-1.5 border border-sky-100/50">
                          <span className="text-[10px] font-bold text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded shrink-0 mt-0.5">{ap.code}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-[10px] font-medium text-[#2D2A26]">{ap.name}</p>
                            <p className="text-[9px] text-[#6B6661]">{ap.distance}</p>
                            <p className="text-[9px] text-sky-700">{ap.transport}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Legacy single airport */}
                  {!flight.airports && flight.destination_airport && (
                    <p className="text-[9px] text-[#6B6661] mt-0.5">Aeroporto: {flight.destination_airport}</p>
                  )}

                  {affiliateLinks?.skyscanner?.url && (
                    <a
                      href={affiliateLinks.skyscanner.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 mt-2 px-3 py-1.5 bg-sky-100 text-sky-700 rounded-lg text-[10px] font-semibold hover:bg-sky-200 transition-colors"
                      data-testid="flight-search-cta"
                    >
                      <Plane className="w-3 h-3" />Comparar voos <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Flights — legacy format (from AI plans) */}
          {flight && !isSuggestionFlight && flight.outbound && (
            <div className="space-y-2" data-testid="flight-info">
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

          {/* Hotel — legacy format (from AI plans) */}
          {hotel && !isSuggestionHotel && hotel.name && (
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

          {/* Airport to city transport — new format with all airports */}
          {transport && hasAirportList && (
            <div className="border border-stone-100 rounded-lg overflow-hidden" data-testid="transport-info">
              <div className="px-3 py-2 bg-stone-50">
                <p className="text-[10px] font-bold text-[#2D2A26]">Como chegar ao centro da cidade</p>
              </div>
              <div className="p-2.5 space-y-2">
                {transport.airports.map((ap) => (
                  <div key={ap.code} className="flex items-start gap-2.5">
                    <div className="w-7 h-7 bg-emerald-50 rounded-lg flex items-center justify-center shrink-0">
                      <Train className="w-3.5 h-3.5 text-emerald-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">{ap.code}</span>
                        <span className="text-[9px] text-[#2D2A26] font-medium">{ap.name}</span>
                      </div>
                      <p className="text-[10px] text-[#6B6661] mt-0.5">{ap.transport}</p>
                      <p className="text-[9px] text-stone-400">{ap.distance}</p>
                    </div>
                  </div>
                ))}
                {transport.tip && (
                  <div className="flex items-start gap-1.5 bg-amber-50/50 rounded-md px-2.5 py-1.5 mt-1">
                    <Lightbulb className="w-3 h-3 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-[9px] text-amber-800">{transport.tip}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Transport — legacy format (best + alternative) */}
          {transport && !hasAirportList && (transport.best_option || transport.alternative) && (
            <div className="border border-stone-100 rounded-lg overflow-hidden" data-testid="transport-info">
              <div className="px-3 py-2 bg-stone-50">
                <p className="text-[10px] font-bold text-[#2D2A26]">Como chegar ao centro da cidade</p>
              </div>
              <div className="p-2.5 space-y-2">
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
                {transport.tip && (
                  <div className="flex items-start gap-1.5 bg-amber-50/50 rounded-md px-2.5 py-1.5 mt-1">
                    <Lightbulb className="w-3 h-3 text-amber-500 shrink-0 mt-0.5" />
                    <p className="text-[9px] text-amber-800">{transport.tip}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Stay Zones — recommended areas to stay */}
          {hasStayZones && (
            <div className="border border-stone-100 rounded-lg overflow-hidden" data-testid="stay-zones">
              <div className="px-3 py-2 bg-[#FFBE98]/10">
                <p className="text-[10px] font-bold text-[#2D2A26] flex items-center gap-1.5">
                  <Bed className="w-3.5 h-3.5 text-[#FFBE98]" />Melhores zonas para ficar
                </p>
              </div>
              <div className="p-2.5 space-y-2">
                {stayZones.map((zone, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 p-2 rounded-lg bg-stone-50/50 hover:bg-stone-50 transition-colors">
                    <div className="w-5 h-5 bg-[#FFBE98]/20 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-[9px] font-bold text-[#FFBE98]">{idx + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-bold text-[#2D2A26]">{zone.name}</p>
                      <p className="text-[9px] text-[#6B6661] mt-0.5 leading-relaxed">{zone.description}</p>
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1">
                        <span className="text-[8px] text-emerald-600 font-semibold flex items-center gap-0.5">
                          <Train className="w-2.5 h-2.5" />{zone.transport_access}
                        </span>
                      </div>
                      <span className="inline-block text-[8px] text-stone-400 italic mt-0.5">{zone.vibe}</span>
                    </div>
                  </div>
                ))}
                {affiliateLinks?.booking?.url && (
                  <a
                    href={affiliateLinks.booking.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => onTrackAffiliate?.('booking')}
                    className="inline-flex items-center gap-1.5 mt-1 px-3 py-1.5 bg-[#FFBE98]/20 text-[#2D2A26] rounded-lg text-[10px] font-semibold hover:bg-[#FFBE98]/30 transition-colors"
                    data-testid="stay-zones-hotel-cta"
                  >
                    <Building2 className="w-3 h-3" />Comparar hotéis nestas zonas <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                  </a>
                )}
              </div>
            </div>
          )}

          {/* Must See — priority-ranked monuments with affiliate CTAs */}
          {hasMustSee && (
            <div className="border border-stone-100 rounded-lg overflow-hidden" data-testid="must-see">
              <div className="px-3 py-2 bg-amber-50/50">
                <p className="text-[10px] font-bold text-[#2D2A26] flex items-center gap-1.5">
                  <Star className="w-3.5 h-3.5 text-amber-500" />Imperdível — o que não podes perder
                </p>
              </div>
              <div className="p-2.5">
                <div className="space-y-1.5">
                  {mustSee.map((sight, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-stone-50/60 hover:bg-stone-50 transition-colors group">
                      <span className="w-5 h-5 bg-amber-100 rounded-full flex items-center justify-center shrink-0">
                        <span className="text-[8px] font-bold text-amber-600">{idx + 1}</span>
                      </span>
                      <span className="flex-1 text-[10px] text-[#2D2A26] font-medium leading-tight">{sight}</span>
                      <a
                        href={buildMustSeeGYGLink(plan?.destination, sight)}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => onTrackAffiliate?.('getyourguide')}
                        className="shrink-0 inline-flex items-center gap-1 text-[8px] font-bold text-[#FFBE98] bg-[#FFBE98]/8 hover:bg-[#FFBE98]/15 border border-[#FFBE98]/15 px-2 py-1 rounded-md transition-all opacity-70 group-hover:opacity-100"
                        data-testid={`must-see-cta-${idx}`}
                      >
                        <Ticket className="w-2.5 h-2.5" />Ver bilhetes
                        <ExternalLink className="w-2 h-2" />
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  );
};

export default TravelContext;
