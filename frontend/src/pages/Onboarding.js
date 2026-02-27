import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Heart, Users, Sparkles, Globe, ArrowRight, ArrowLeft,
  Gift, UserPlus, Award, Plane, ChevronRight, Check
} from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OnboardingStep = ({ children, isActive }) => (
  <AnimatePresence mode="wait">
    {isActive && (
      <motion.div
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -50 }}
        transition={{ duration: 0.4 }}
        className="w-full"
      >
        {children}
      </motion.div>
    )}
  </AnimatePresence>
);

const ProgressDots = ({ current, total }) => (
  <div className="flex gap-2 justify-center">
    {Array.from({ length: total }).map((_, i) => (
      <div
        key={i}
        className={`h-2 rounded-full transition-all duration-300 ${
          i === current 
            ? 'w-8 bg-[#FFBE98]' 
            : i < current 
              ? 'w-2 bg-[#FFBE98]/60' 
              : 'w-2 bg-stone-200'
        }`}
      />
    ))}
  </div>
);

const ActionCard = ({ icon: Icon, title, description, selected, onClick }) => (
  <button
    onClick={onClick}
    className={`p-6 rounded-2xl border-2 text-left transition-all duration-300 w-full ${
      selected 
        ? 'border-[#FFBE98] bg-[#FFBE98]/10 shadow-lg' 
        : 'border-stone-200 bg-white hover:border-[#FFBE98]/50 hover:shadow-md'
    }`}
  >
    <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
      selected ? 'bg-[#FFBE98]' : 'bg-[#E6F4F1]'
    }`}>
      <Icon className={`w-6 h-6 ${selected ? 'text-white' : 'text-[#2D2A26]'}`} />
    </div>
    <h3 className="font-bold text-[#2D2A26] mb-2">{title}</h3>
    <p className="text-sm text-[#6B6661]">{description}</p>
    {selected && (
      <div className="mt-4 flex items-center gap-2 text-[#FFBE98] text-sm font-medium">
        <Check className="w-4 h-4" /> Selecionado
      </div>
    )}
  </button>
);

const Onboarding = () => {
  const navigate = useNavigate();
  const { user, getAuthHeaders } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAction, setSelectedAction] = useState(null);
  const [completing, setCompleting] = useState(false);

  const totalSteps = 4;

  const completeOnboarding = async () => {
    setCompleting(true);
    try {
      await axios.post(`${API}/user/complete-onboarding`, {
        initial_action: selectedAction
      }, {
        headers: getAuthHeaders()
      });
    } catch (error) {
      console.error('Error completing onboarding:', error);
    }
    
    // Navigate based on selected action
    switch (selectedAction) {
      case 'support':
        navigate('/?action=contribute');
        break;
      case 'explore':
        navigate('/');
        break;
      case 'plan':
        navigate('/?section=plan-trip');
        break;
      default:
        navigate('/dashboard');
    }
  };

  const nextStep = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    } else if (selectedAction) {
      completeOnboarding();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FAFAF9] to-[#E6F4F1]/30 flex items-center justify-center p-6" data-testid="onboarding-page">
      <div className="max-w-2xl w-full">
        {/* Progress */}
        <div className="mb-8">
          <ProgressDots current={currentStep} total={totalSteps} />
        </div>

        {/* Steps Container */}
        <div className="bg-white rounded-3xl shadow-xl p-8 md:p-12 min-h-[500px] flex flex-col">
          
          {/* Step 1: Introdução ao CrowdDreaming */}
          <OnboardingStep isActive={currentStep === 0}>
            <div className="text-center flex-1 flex flex-col justify-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.2 }}
                className="w-24 h-24 bg-gradient-to-br from-[#FFBE98] to-[#E6A07C] rounded-full flex items-center justify-center mx-auto mb-8"
              >
                <Heart className="w-12 h-12 text-white" />
              </motion.div>
              
              <h1 className="text-3xl md:text-4xl font-bold text-[#2D2A26] mb-4">
                Bem-vindo ao <span className="text-[#FFBE98]">4Luis</span>
              </h1>
              
              <p className="text-lg text-[#6B6661] mb-6 max-w-md mx-auto">
                Isto não é apenas crowdfunding.
              </p>
              
              <p className="font-handwritten text-2xl text-[#FFBE98] mb-8">
                É CrowdDreaming.
              </p>
              
              <div className="bg-[#FAFAF9] rounded-2xl p-6 max-w-md mx-auto">
                <p className="text-[#6B6661]">
                  Uma comunidade onde cada contribuição não é apenas um donativo — 
                  é um <span className="font-semibold text-[#2D2A26]">gesto fraternal</span> que 
                  ajuda a tornar sonhos em realidade.
                </p>
              </div>
            </div>
          </OnboardingStep>

          {/* Step 2: Progressão (Contribuir → Convidar → Embaixador → Viagem) */}
          <OnboardingStep isActive={currentStep === 1}>
            <div className="flex-1">
              <h2 className="text-2xl md:text-3xl font-bold text-[#2D2A26] text-center mb-2">
                O Teu Caminho de Sonhador
              </h2>
              <p className="text-[#6B6661] text-center mb-8">
                Cresce connosco e desbloqueia novas possibilidades
              </p>
              
              <div className="space-y-4">
                {/* Step 1: Contribute */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="flex items-center gap-4 p-4 bg-[#FAFAF9] rounded-xl"
                >
                  <div className="w-12 h-12 bg-[#FFBE98] rounded-full flex items-center justify-center flex-shrink-0">
                    <Gift className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-[#2D2A26]">1. Contribui</h3>
                    <p className="text-sm text-[#6B6661]">Apoia uma viagem de sonho com qualquer valor</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-[#FFBE98]" />
                </motion.div>

                {/* Step 2: Invite */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  className="flex items-center gap-4 p-4 bg-[#FAFAF9] rounded-xl"
                >
                  <div className="w-12 h-12 bg-[#E6F4F1] rounded-full flex items-center justify-center flex-shrink-0">
                    <UserPlus className="w-6 h-6 text-[#2D2A26]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-[#2D2A26]">2. Convida</h3>
                    <p className="text-sm text-[#6B6661]">Partilha o teu link e traz novos sonhadores</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-[#6B6661]" />
                </motion.div>

                {/* Step 3: Ambassador */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className="flex items-center gap-4 p-4 bg-[#FAFAF9] rounded-xl"
                >
                  <div className="w-12 h-12 bg-[#E6F4F1] rounded-full flex items-center justify-center flex-shrink-0">
                    <Award className="w-6 h-6 text-[#2D2A26]" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-[#2D2A26]">3. Torna-te Embaixador</h3>
                    <p className="text-sm text-[#6B6661]">Contribui + 3 convites válidos = nível Embaixador</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-[#6B6661]" />
                </motion.div>

                {/* Step 4: Own Journey */}
                <motion.div 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 }}
                  className="flex items-center gap-4 p-4 bg-gradient-to-r from-[#FFBE98]/20 to-[#E6F4F1]/20 rounded-xl border border-[#FFBE98]/30"
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-[#FFBE98] to-[#E6A07C] rounded-full flex items-center justify-center flex-shrink-0">
                    <Plane className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-[#2D2A26]">4. Cria a Tua Viagem</h3>
                    <p className="text-sm text-[#6B6661]">Embaixadores podem criar e financiar a sua própria viagem de sonho</p>
                  </div>
                  <Sparkles className="w-5 h-5 text-[#FFBE98]" />
                </motion.div>
              </div>
            </div>
          </OnboardingStep>

          {/* Step 3: Impacto da Comunidade */}
          <OnboardingStep isActive={currentStep === 2}>
            <div className="text-center flex-1 flex flex-col justify-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", delay: 0.2 }}
                className="w-24 h-24 bg-[#E6F4F1] rounded-full flex items-center justify-center mx-auto mb-8"
              >
                <Users className="w-12 h-12 text-[#2D2A26]" />
              </motion.div>
              
              <h2 className="text-2xl md:text-3xl font-bold text-[#2D2A26] mb-4">
                Juntos Somos Mais Fortes
              </h2>
              
              <p className="text-lg text-[#6B6661] mb-8 max-w-md mx-auto">
                Cada sonhador que se junta à comunidade multiplica o impacto de todos.
              </p>
              
              <div className="grid grid-cols-3 gap-4 max-w-md mx-auto mb-8">
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="bg-[#FAFAF9] rounded-xl p-4"
                >
                  <p className="text-3xl font-bold text-[#FFBE98]">100%</p>
                  <p className="text-xs text-[#6B6661]">Vai para o sonhador</p>
                </motion.div>
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="bg-[#FAFAF9] rounded-xl p-4"
                >
                  <p className="text-3xl font-bold text-[#FFBE98]">0%</p>
                  <p className="text-xs text-[#6B6661]">Comissões</p>
                </motion.div>
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="bg-[#FAFAF9] rounded-xl p-4"
                >
                  <p className="text-3xl font-bold text-[#FFBE98]">∞</p>
                  <p className="text-xs text-[#6B6661]">Sonhos possíveis</p>
                </motion.div>
              </div>
              
              <div className="bg-gradient-to-r from-[#2D2A26] to-[#4A4640] rounded-2xl p-6 max-w-md mx-auto">
                <p className="text-white/90 italic">
                  "Quando apoias uma viagem, não estás apenas a dar dinheiro — 
                  estás a dar asas a um sonho."
                </p>
              </div>
            </div>
          </OnboardingStep>

          {/* Step 4: Escolha de Ação Inicial */}
          <OnboardingStep isActive={currentStep === 3}>
            <div className="flex-1">
              <div className="text-center mb-8">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", delay: 0.2 }}
                  className="w-16 h-16 bg-[#FFBE98] rounded-full flex items-center justify-center mx-auto mb-4"
                >
                  <Globe className="w-8 h-8 text-white" />
                </motion.div>
                
                <h2 className="text-2xl md:text-3xl font-bold text-[#2D2A26] mb-2">
                  Por Onde Queres Começar?
                </h2>
                <p className="text-[#6B6661]">
                  Escolhe a tua primeira ação como Sonhador
                </p>
              </div>
              
              <div className="space-y-4">
                <ActionCard
                  icon={Heart}
                  title="Apoiar a Viagem Principal"
                  description="Contribui para o sonho atual e faz parte da história"
                  selected={selectedAction === 'support'}
                  onClick={() => setSelectedAction('support')}
                />
                
                <ActionCard
                  icon={Users}
                  title="Explorar a Comunidade"
                  description="Descobre os sonhadores, embaixadores e viagens realizadas"
                  selected={selectedAction === 'explore'}
                  onClick={() => setSelectedAction('explore')}
                />
                
                <ActionCard
                  icon={Plane}
                  title="Planear uma Viagem"
                  description="Usa as nossas ferramentas para planear a viagem dos teus sonhos"
                  selected={selectedAction === 'plan'}
                  onClick={() => setSelectedAction('plan')}
                />
              </div>
            </div>
          </OnboardingStep>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-stone-100">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                currentStep === 0 
                  ? 'opacity-0 pointer-events-none' 
                  : 'text-[#6B6661] hover:text-[#2D2A26] hover:bg-stone-100'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
              Anterior
            </button>
            
            <button
              onClick={nextStep}
              disabled={currentStep === 3 && !selectedAction}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
                currentStep === 3 && !selectedAction
                  ? 'bg-stone-200 text-stone-400 cursor-not-allowed'
                  : 'bg-[#FFBE98] text-[#2D2A26] hover:bg-[#FFAB7D]'
              }`}
              data-testid="onboarding-next-btn"
            >
              {completing ? (
                <>
                  <div className="w-4 h-4 border-2 border-[#2D2A26] border-t-transparent rounded-full animate-spin" />
                  A entrar...
                </>
              ) : currentStep === 3 ? (
                <>
                  Começar a Sonhar
                  <Sparkles className="w-4 h-4" />
                </>
              ) : (
                <>
                  Continuar
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Skip option */}
        <div className="text-center mt-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-[#6B6661] hover:text-[#2D2A26] underline"
            data-testid="skip-onboarding-btn"
          >
            Saltar introdução
          </button>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
