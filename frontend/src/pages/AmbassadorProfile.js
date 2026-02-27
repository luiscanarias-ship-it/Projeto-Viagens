import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  MapPin, Heart, Users, Award, Calendar, Globe, 
  ChevronRight, Sparkles, Camera, Quote, Bitcoin,
  ArrowLeft, Share2, ExternalLink
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const StatCard = ({ icon: Icon, value, label, highlight = false }) => (
  <div className={`p-4 rounded-xl text-center ${highlight ? 'bg-gradient-to-br from-[#FFBE98]/20 to-[#E6F4F1]/20 border border-[#FFBE98]/30' : 'bg-[#FAFAF9]'}`}>
    <Icon className={`w-6 h-6 mx-auto mb-2 ${highlight ? 'text-[#FFBE98]' : 'text-[#6B6661]'}`} />
    <p className={`text-2xl font-bold ${highlight ? 'text-[#FFBE98]' : 'text-[#2D2A26]'}`}>{value}</p>
    <p className="text-sm text-[#6B6661]">{label}</p>
  </div>
);

const AmbassadorProfile = () => {
  const { userId } = useParams();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await axios.get(`${API}/ambassador/${userId}/public-profile`);
        setProfile(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Erro ao carregar perfil');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [userId]);

  const shareProfile = () => {
    const url = window.location.href;
    if (navigator.share) {
      navigator.share({
        title: `Perfil de ${profile?.identity?.display_name} - 4Luis`,
        url: url
      });
    } else {
      navigator.clipboard.writeText(url);
      alert('Link copiado!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAF9]">
        <div className="w-12 h-12 border-4 border-[#FFBE98] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAFAF9] px-6">
        <div className="text-center">
          <p className="text-[#6B6661] mb-4">{error}</p>
          <Link to="/" className="text-[#FFBE98] hover:underline">Voltar à página inicial</Link>
        </div>
      </div>
    );
  }

  const { identity, current_journey, contributions, social_impact, realized_journeys, testimonials } = profile;

  return (
    <div className="min-h-screen bg-[#FAFAF9]" data-testid="ambassador-profile-page">
      {/* Header */}
      <div className="bg-white border-b border-stone-100">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-[#6B6661] hover:text-[#2D2A26]">
            <ArrowLeft className="w-5 h-5" />
            <span>Voltar</span>
          </Link>
          <button onClick={shareProfile} className="flex items-center gap-2 text-[#6B6661] hover:text-[#2D2A26]">
            <Share2 className="w-5 h-5" />
            <span className="hidden sm:inline">Partilhar</span>
          </button>
        </div>
      </div>

      {/* Profile Header */}
      <section className="bg-white pb-8">
        <div className="max-w-4xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center gap-6 pt-8">
            {/* Avatar */}
            <motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="relative"
            >
              <img 
                src={identity.avatar} 
                alt={identity.display_name}
                className="w-32 h-32 rounded-full object-cover border-4 border-white shadow-lg"
              />
              {identity.is_ambassador && (
                <div className="absolute -bottom-2 -right-2 w-10 h-10 bg-gradient-to-br from-[#FFBE98] to-[#E6A07C] rounded-full flex items-center justify-center shadow-lg">
                  <Award className="w-5 h-5 text-white" />
                </div>
              )}
            </motion.div>

            {/* Info */}
            <div className="text-center md:text-left flex-1">
              <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                <h1 className="text-2xl md:text-3xl font-bold text-[#2D2A26]">
                  {identity.display_name}
                </h1>
                {identity.is_ambassador && (
                  <span className="px-3 py-1 bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] text-white text-sm font-medium rounded-full">
                    Embaixador
                  </span>
                )}
              </div>
              
              {identity.country && (
                <p className="text-[#6B6661] flex items-center justify-center md:justify-start gap-1 mb-2">
                  <MapPin className="w-4 h-4" /> {identity.country}
                </p>
              )}
              
              {identity.bio && (
                <p className="text-[#6B6661] max-w-md">{identity.bio}</p>
              )}
              
              <p className="text-sm text-[#6B6661] mt-2 flex items-center justify-center md:justify-start gap-1">
                <Calendar className="w-4 h-4" />
                Membro desde {new Date(identity.member_since).toLocaleDateString('pt-PT', { month: 'long', year: 'numeric' })}
              </p>
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Current Journey */}
        {current_journey && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl overflow-hidden shadow-sm"
            data-testid="current-journey-section"
          >
            <div className="p-6 border-b border-stone-100">
              <h2 className="text-xl font-bold text-[#2D2A26] flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-[#FFBE98]" />
                Viagem Atual
              </h2>
            </div>
            
            <div className="md:flex">
              <div className="md:w-1/3">
                <img 
                  src={current_journey.image_url} 
                  alt={current_journey.name}
                  className="w-full h-48 md:h-full object-cover"
                />
              </div>
              <div className="p-6 md:w-2/3">
                <h3 className="text-xl font-bold text-[#2D2A26] mb-1">{current_journey.name}</h3>
                {current_journey.poetic_name && (
                  <p className="font-handwritten text-[#FFBE98] mb-3">{current_journey.poetic_name}</p>
                )}
                
                {(current_journey.country || current_journey.city) && (
                  <p className="text-[#6B6661] text-sm flex items-center gap-1 mb-3">
                    <Globe className="w-4 h-4" />
                    {current_journey.city && `${current_journey.city}, `}{current_journey.country}
                  </p>
                )}
                
                <p className="text-[#6B6661] mb-4 line-clamp-3">{current_journey.description}</p>
                
                {/* Progress */}
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-[#6B6661]">Progresso</span>
                    <span className="font-bold text-[#2D2A26]">{current_journey.progress_percentage}%</span>
                  </div>
                  <div className="h-3 bg-stone-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(current_journey.progress_percentage, 100)}%` }}
                    />
                  </div>
                </div>
                
                <Link 
                  to={`/journey/${current_journey.journey_id}`}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold hover:bg-[#FFAB7D] transition-colors"
                  data-testid="support-journey-btn"
                >
                  <Heart className="w-5 h-5" /> Apoiar esta Viagem
                </Link>
              </div>
            </div>
          </motion.section>
        )}

        {/* Stats Grid */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-xl font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-[#FFBE98]" />
            Impacto na Comunidade
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard 
              icon={Heart} 
              value={`${contributions.total_amount}€`} 
              label="Total Contribuído"
              highlight={contributions.total_amount > 0}
            />
            <StatCard 
              icon={Users} 
              value={social_impact.people_invited} 
              label="Pessoas Convidadas"
            />
            <StatCard 
              icon={Sparkles} 
              value={social_impact.contributions_generated} 
              label="Contribuições Geradas"
            />
            <StatCard 
              icon={Globe} 
              value={`${social_impact.amount_generated}€`} 
              label="Impacto Total"
              highlight={social_impact.amount_generated > 0}
            />
          </div>
        </motion.section>

        {/* Contribution Badges */}
        <motion.section 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl p-6 shadow-sm"
          data-testid="contributions-section"
        >
          <h2 className="text-xl font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
            <Heart className="w-5 h-5 text-[#FFBE98]" />
            Contribuições
          </h2>
          
          <div className="flex flex-wrap gap-3">
            {contributions.contributed_to_main_journey && (
              <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#FFBE98]/20 to-[#E6F4F1]/20 rounded-full border border-[#FFBE98]/30">
                <Heart className="w-4 h-4 text-[#FFBE98]" />
                <span className="text-sm font-medium text-[#2D2A26]">Apoiou a Viagem Principal</span>
              </div>
            )}
            
            {contributions.has_crypto_contributions && (
              <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#F7931A]/10 to-[#627EEA]/10 rounded-full border border-[#F7931A]/30">
                <Bitcoin className="w-4 h-4 text-[#F7931A]" />
                <span className="text-sm font-medium text-[#2D2A26]">Cripto-Sonhador</span>
              </div>
            )}
            
            {contributions.total_count > 0 && (
              <div className="flex items-center gap-2 px-4 py-2 bg-[#E6F4F1] rounded-full">
                <span className="text-sm font-medium text-[#2D2A26]">{contributions.total_count} contribuições</span>
              </div>
            )}
            
            {identity.is_ambassador && (
              <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#FFBE98] to-[#E6A07C] rounded-full">
                <Award className="w-4 h-4 text-white" />
                <span className="text-sm font-medium text-white">Embaixador 4Luis</span>
              </div>
            )}
          </div>
          
          {contributions.total_count === 0 && (
            <p className="text-[#6B6661] text-center py-4">Ainda não há contribuições registadas.</p>
          )}
        </motion.section>

        {/* Realized Journeys */}
        {realized_journeys && realized_journeys.length > 0 && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            data-testid="realized-journeys-section"
          >
            <h2 className="text-xl font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
              <Camera className="w-5 h-5 text-[#FFBE98]" />
              Viagens Realizadas
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {realized_journeys.map((journey) => (
                <div key={journey.journey_id} className="bg-white rounded-2xl overflow-hidden shadow-sm">
                  <div className="relative h-40">
                    <img 
                      src={journey.image_url} 
                      alt={journey.name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                    <div className="absolute bottom-4 left-4 right-4">
                      <h3 className="text-white font-bold">{journey.name}</h3>
                      {journey.country && (
                        <p className="text-white/80 text-sm flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {journey.country}
                        </p>
                      )}
                    </div>
                    <span className="absolute top-4 right-4 px-2 py-1 bg-green-500 text-white text-xs rounded-full">
                      ✓ Realizada
                    </span>
                  </div>
                  
                  {journey.story && (
                    <div className="p-4">
                      <p className="text-[#6B6661] text-sm italic line-clamp-3">"{journey.story}"</p>
                    </div>
                  )}
                  
                  {journey.photos && journey.photos.length > 0 && (
                    <div className="px-4 pb-4 flex gap-2">
                      {journey.photos.slice(0, 4).map((photo, idx) => (
                        <img 
                          key={idx} 
                          src={photo} 
                          alt="" 
                          className="w-12 h-12 rounded-lg object-cover"
                        />
                      ))}
                      {journey.photos.length > 4 && (
                        <div className="w-12 h-12 rounded-lg bg-stone-100 flex items-center justify-center text-sm text-[#6B6661]">
                          +{journey.photos.length - 4}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Testimonials (Placeholder) */}
        {testimonials && testimonials.length > 0 && (
          <motion.section 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <h2 className="text-xl font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
              <Quote className="w-5 h-5 text-[#FFBE98]" />
              Testemunhos
            </h2>
            
            <div className="space-y-4">
              {testimonials.map((testimonial, idx) => (
                <div key={idx} className="bg-white rounded-2xl p-6 shadow-sm">
                  <p className="text-[#6B6661] italic mb-4">"{testimonial.text}"</p>
                  <p className="text-sm font-medium text-[#2D2A26]">— {testimonial.author}</p>
                </div>
              ))}
            </div>
          </motion.section>
        )}

        {/* Empty State for Non-Ambassadors */}
        {!identity.is_ambassador && contributions.total_count === 0 && social_impact.people_invited === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-stone-200 mx-auto mb-4" />
            <p className="text-[#6B6661]">Este utilizador ainda está a começar a sua jornada na 4Luis.</p>
          </div>
        )}
      </div>

      {/* CTA Footer */}
      {current_journey && (
        <section className="bg-gradient-to-r from-[#2D2A26] to-[#4A4640] py-8">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <p className="text-white/80 mb-4">Queres ajudar {identity.display_name} a realizar este sonho?</p>
            <Link 
              to={`/journey/${current_journey.journey_id}`}
              className="inline-flex items-center gap-2 px-8 py-4 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-bold hover:bg-[#FFAB7D] transition-colors"
            >
              <Heart className="w-5 h-5" /> Contribuir Agora
            </Link>
          </div>
        </section>
      )}
    </div>
  );
};

export default AmbassadorProfile;
