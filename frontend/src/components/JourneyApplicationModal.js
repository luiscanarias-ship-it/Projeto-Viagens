import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, MapPin, Target, Calendar, Heart, CreditCard, Plane,
  Plus, Minus, ChevronRight, ChevronLeft, Check, AlertCircle,
  Smartphone, Bitcoin, ExternalLink, Globe, Clock, Sparkles
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PAYMENT_METHODS = [
  { id: 'stripe', name: 'Cartão (Stripe)', icon: CreditCard, description: 'Visa, Mastercard - automático' },
  { id: 'mbway', name: 'MBWay', icon: Smartphone, description: 'Pagamento móvel Portugal' },
  { id: 'paypal', name: 'PayPal', icon: ExternalLink, description: 'Transferência internacional' },
  { id: 'revolut', name: 'Revolut', icon: ExternalLink, description: 'Transferência rápida' },
  { id: 'wise', name: 'Wise', icon: ExternalLink, description: 'Baixas taxas internacionais' },
  { id: 'crypto', name: 'Criptomoedas', icon: Bitcoin, description: 'BTC, ETH, USDT, USDC' }
];

const FLEXIBILITY_OPTIONS = [
  { id: 'flexível', name: 'Flexível', description: 'Datas podem mudar conforme disponibilidade' },
  { id: 'semi-flexível', name: 'Semi-flexível', description: 'Pequenas alterações são possíveis' },
  { id: 'fixo', name: 'Datas fixas', description: 'Período específico, sem alterações' }
];

const StepIndicator = ({ currentStep, totalSteps }) => (
  <div className="flex items-center justify-center gap-2 mb-8">
    {Array.from({ length: totalSteps }).map((_, i) => (
      <div key={i} className="flex items-center">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
          i < currentStep 
            ? 'bg-green-500 text-white' 
            : i === currentStep 
              ? 'bg-[#FFBE98] text-[#2D2A26]' 
              : 'bg-stone-200 text-[#6B6661]'
        }`}>
          {i < currentStep ? <Check className="w-4 h-4" /> : i + 1}
        </div>
        {i < totalSteps - 1 && (
          <div className={`w-8 h-0.5 mx-1 ${i < currentStep ? 'bg-green-500' : 'bg-stone-200'}`} />
        )}
      </div>
    ))}
  </div>
);

const JourneyApplicationModal = ({ isOpen, onClose, onSuccess, authHeaders }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  // Form state
  const [formData, setFormData] = useState({
    // Step 1: Basic Info
    name: '',
    destination_country: '',
    destination_city: '',
    description: '',
    
    // Step 2: Travel Plan
    cities_to_visit: [''],
    duration_days: 7,
    main_activities: [''],
    
    // Step 3: Calendar
    start_date_approximate: '',
    end_date_approximate: '',
    flexibility: 'flexível',
    
    // Step 4: Motivation & Financial
    goal_amount: 1000,
    personal_motivation: '',
    why_this_destination: '',
    
    // Step 5: Payment Methods
    payment_methods: ['stripe'],
    
    // Optional
    poetic_name: '',
    image_url: ''
  });

  const totalSteps = 5;

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const addArrayItem = (field) => {
    setFormData(prev => ({
      ...prev,
      [field]: [...prev[field], '']
    }));
  };

  const removeArrayItem = (field, index) => {
    if (formData[field].length > 1) {
      setFormData(prev => ({
        ...prev,
        [field]: prev[field].filter((_, i) => i !== index)
      }));
    }
  };

  const updateArrayItem = (field, index, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].map((item, i) => i === index ? value : item)
    }));
  };

  const togglePaymentMethod = (methodId) => {
    setFormData(prev => {
      const methods = prev.payment_methods.includes(methodId)
        ? prev.payment_methods.filter(m => m !== methodId)
        : [...prev.payment_methods, methodId];
      return { ...prev, payment_methods: methods };
    });
  };

  const validateStep = () => {
    switch (currentStep) {
      case 0:
        if (!formData.name.trim()) return 'O nome da viagem é obrigatório';
        if (!formData.destination_country.trim()) return 'O país de destino é obrigatório';
        if (!formData.description.trim() || formData.description.length < 50) 
          return 'A descrição deve ter pelo menos 50 caracteres';
        break;
      case 1:
        if (formData.cities_to_visit.filter(c => c.trim()).length === 0) 
          return 'Adiciona pelo menos uma cidade';
        if (formData.duration_days < 1 || formData.duration_days > 365) 
          return 'A duração deve ser entre 1 e 365 dias';
        if (formData.main_activities.filter(a => a.trim()).length === 0) 
          return 'Adiciona pelo menos uma atividade';
        break;
      case 2:
        if (!formData.start_date_approximate.trim()) 
          return 'A data aproximada de início é obrigatória';
        break;
      case 3:
        if (formData.goal_amount < 100) return 'O objetivo mínimo é 100€';
        if (formData.goal_amount > 50000) return 'O objetivo máximo é 50.000€';
        if (!formData.personal_motivation.trim() || formData.personal_motivation.length < 100) 
          return 'A motivação pessoal deve ter pelo menos 100 caracteres';
        if (!formData.why_this_destination.trim() || formData.why_this_destination.length < 50) 
          return 'Explica porquê este destino (mínimo 50 caracteres)';
        break;
      case 4:
        if (formData.payment_methods.length === 0) 
          return 'Seleciona pelo menos um método de pagamento';
        break;
      default:
        break;
    }
    return null;
  };

  const nextStep = () => {
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError('');
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    setError('');
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    const validationError = validateStep();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      // Clean up arrays
      const cleanedData = {
        ...formData,
        cities_to_visit: formData.cities_to_visit.filter(c => c.trim()),
        main_activities: formData.main_activities.filter(a => a.trim())
      };

      const response = await axios.post(
        `${API}/ambassador/apply-journey`,
        cleanedData,
        { headers: authHeaders }
      );

      onSuccess(response.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao submeter candidatura');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
          data-testid="journey-application-modal"
        >
          {/* Header */}
          <div className="p-6 border-b border-stone-100 flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-[#2D2A26]">Candidatura de Viagem</h2>
              <p className="text-sm text-[#6B6661]">Partilha o teu sonho com a comunidade</p>
            </div>
            <button 
              onClick={onClose} 
              className="p-2 hover:bg-stone-100 rounded-full transition-colors"
              data-testid="close-modal-btn"
            >
              <X className="w-5 h-5 text-[#6B6661]" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            <StepIndicator currentStep={currentStep} totalSteps={totalSteps} />

            {/* Step 1: Basic Info */}
            {currentStep === 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <MapPin className="w-12 h-12 text-[#FFBE98] mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-[#2D2A26]">Destino da Viagem</h3>
                  <p className="text-sm text-[#6B6661]">Para onde queres ir?</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Nome da Viagem *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => updateField('name', e.target.value)}
                    placeholder="Ex: Aventura no Japão, Caminho de Santiago..."
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                    data-testid="journey-name-input"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                      País de Destino *
                    </label>
                    <input
                      type="text"
                      value={formData.destination_country}
                      onChange={(e) => updateField('destination_country', e.target.value)}
                      placeholder="Ex: Japão"
                      className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                      Cidade Principal
                    </label>
                    <input
                      type="text"
                      value={formData.destination_city}
                      onChange={(e) => updateField('destination_city', e.target.value)}
                      placeholder="Ex: Tóquio"
                      className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Descrição da Viagem * <span className="text-[#6B6661] font-normal">(mín. 50 caracteres)</span>
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => updateField('description', e.target.value)}
                    placeholder="Descreve a tua viagem de sonho... O que vais fazer? O que esperas descobrir?"
                    rows={4}
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98] resize-none"
                    data-testid="journey-description-input"
                  />
                  <p className="text-xs text-[#6B6661] mt-1">{formData.description.length}/50 caracteres mínimos</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Nome Poético <span className="text-[#6B6661] font-normal">(opcional)</span>
                  </label>
                  <input
                    type="text"
                    value={formData.poetic_name}
                    onChange={(e) => updateField('poetic_name', e.target.value)}
                    placeholder="Ex: Onde o Sol Nasce Primeiro"
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                  />
                </div>
              </motion.div>
            )}

            {/* Step 2: Travel Plan */}
            {currentStep === 1 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <Plane className="w-12 h-12 text-[#FFBE98] mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-[#2D2A26]">Plano de Viagem</h3>
                  <p className="text-sm text-[#6B6661]">Como vais organizar a tua aventura?</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Cidades a Visitar *
                  </label>
                  {formData.cities_to_visit.map((city, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={city}
                        onChange={(e) => updateArrayItem('cities_to_visit', index, e.target.value)}
                        placeholder={`Cidade ${index + 1}`}
                        className="flex-1 px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                      />
                      {formData.cities_to_visit.length > 1 && (
                        <button
                          onClick={() => removeArrayItem('cities_to_visit', index)}
                          className="p-3 text-red-500 hover:bg-red-50 rounded-xl"
                        >
                          <Minus className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('cities_to_visit')}
                    className="flex items-center gap-2 text-[#FFBE98] hover:text-[#E6A07C] text-sm font-medium"
                  >
                    <Plus className="w-4 h-4" /> Adicionar cidade
                  </button>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Duração (dias) *
                  </label>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() => updateField('duration_days', Math.max(1, formData.duration_days - 1))}
                      className="p-3 bg-stone-100 hover:bg-stone-200 rounded-xl"
                    >
                      <Minus className="w-5 h-5" />
                    </button>
                    <span className="text-2xl font-bold text-[#2D2A26] w-16 text-center">
                      {formData.duration_days}
                    </span>
                    <button
                      onClick={() => updateField('duration_days', Math.min(365, formData.duration_days + 1))}
                      className="p-3 bg-stone-100 hover:bg-stone-200 rounded-xl"
                    >
                      <Plus className="w-5 h-5" />
                    </button>
                    <span className="text-[#6B6661]">dias</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Principais Atividades *
                  </label>
                  {formData.main_activities.map((activity, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={activity}
                        onChange={(e) => updateArrayItem('main_activities', index, e.target.value)}
                        placeholder={`Atividade ${index + 1} (ex: visitar templos, fazer hiking...)`}
                        className="flex-1 px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                      />
                      {formData.main_activities.length > 1 && (
                        <button
                          onClick={() => removeArrayItem('main_activities', index)}
                          className="p-3 text-red-500 hover:bg-red-50 rounded-xl"
                        >
                          <Minus className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayItem('main_activities')}
                    className="flex items-center gap-2 text-[#FFBE98] hover:text-[#E6A07C] text-sm font-medium"
                  >
                    <Plus className="w-4 h-4" /> Adicionar atividade
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 3: Calendar */}
            {currentStep === 2 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <Calendar className="w-12 h-12 text-[#FFBE98] mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-[#2D2A26]">Calendário Previsto</h3>
                  <p className="text-sm text-[#6B6661]">Quando planeias fazer esta viagem?</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                      Data de Início Aproximada *
                    </label>
                    <input
                      type="text"
                      value={formData.start_date_approximate}
                      onChange={(e) => updateField('start_date_approximate', e.target.value)}
                      placeholder="Ex: Março 2026"
                      className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                      Data de Fim Aproximada
                    </label>
                    <input
                      type="text"
                      value={formData.end_date_approximate}
                      onChange={(e) => updateField('end_date_approximate', e.target.value)}
                      placeholder="Ex: Abril 2026"
                      className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-3">
                    Flexibilidade das Datas
                  </label>
                  <div className="space-y-3">
                    {FLEXIBILITY_OPTIONS.map((option) => (
                      <button
                        key={option.id}
                        onClick={() => updateField('flexibility', option.id)}
                        className={`w-full p-4 rounded-xl border-2 text-left transition-all ${
                          formData.flexibility === option.id
                            ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                            : 'border-stone-200 hover:border-[#FFBE98]/50'
                        }`}
                      >
                        <p className="font-medium text-[#2D2A26]">{option.name}</p>
                        <p className="text-sm text-[#6B6661]">{option.description}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 4: Motivation & Financial */}
            {currentStep === 3 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <Heart className="w-12 h-12 text-[#FFBE98] mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-[#2D2A26]">Motivação & Objetivo</h3>
                  <p className="text-sm text-[#6B6661]">Conta-nos porque este sonho é importante</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Objetivo Financeiro *
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="number"
                      value={formData.goal_amount}
                      onChange={(e) => updateField('goal_amount', parseInt(e.target.value) || 0)}
                      min={100}
                      max={50000}
                      className="flex-1 px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98] text-2xl font-bold text-center"
                    />
                    <span className="text-2xl font-bold text-[#6B6661]">€</span>
                  </div>
                  <p className="text-xs text-[#6B6661] mt-2">Mínimo: 100€ | Máximo: 50.000€</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Motivação Pessoal * <span className="text-[#6B6661] font-normal">(mín. 100 caracteres)</span>
                  </label>
                  <textarea
                    value={formData.personal_motivation}
                    onChange={(e) => updateField('personal_motivation', e.target.value)}
                    placeholder="Porque é que esta viagem é importante para ti? O que te motiva a realizá-la?"
                    rows={4}
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98] resize-none"
                  />
                  <p className="text-xs text-[#6B6661] mt-1">{formData.personal_motivation.length}/100 caracteres mínimos</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[#2D2A26] mb-2">
                    Porquê Este Destino? * <span className="text-[#6B6661] font-normal">(mín. 50 caracteres)</span>
                  </label>
                  <textarea
                    value={formData.why_this_destination}
                    onChange={(e) => updateField('why_this_destination', e.target.value)}
                    placeholder="O que te atrai neste destino específico? O que esperas descobrir ou aprender?"
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-[#FFBE98] resize-none"
                  />
                  <p className="text-xs text-[#6B6661] mt-1">{formData.why_this_destination.length}/50 caracteres mínimos</p>
                </div>
              </motion.div>
            )}

            {/* Step 5: Payment Methods */}
            {currentStep === 4 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-6"
              >
                <div className="text-center mb-6">
                  <CreditCard className="w-12 h-12 text-[#FFBE98] mx-auto mb-2" />
                  <h3 className="text-lg font-bold text-[#2D2A26]">Métodos de Pagamento</h3>
                  <p className="text-sm text-[#6B6661]">Quais métodos aceitas para receber contribuições?</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {PAYMENT_METHODS.map((method) => {
                    const Icon = method.icon;
                    const isSelected = formData.payment_methods.includes(method.id);
                    return (
                      <button
                        key={method.id}
                        onClick={() => togglePaymentMethod(method.id)}
                        className={`p-4 rounded-xl border-2 text-left transition-all ${
                          isSelected
                            ? 'border-[#FFBE98] bg-[#FFBE98]/10'
                            : 'border-stone-200 hover:border-[#FFBE98]/50'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${isSelected ? 'bg-[#FFBE98]' : 'bg-stone-100'}`}>
                            <Icon className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-[#6B6661]'}`} />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-[#2D2A26] text-sm">{method.name}</p>
                            <p className="text-xs text-[#6B6661]">{method.description}</p>
                          </div>
                          {isSelected && <Check className="w-5 h-5 text-[#FFBE98]" />}
                        </div>
                      </button>
                    );
                  })}
                </div>

                <div className="bg-[#E6F4F1]/50 rounded-xl p-4 mt-6">
                  <p className="text-sm text-[#6B6661]">
                    <strong>Nota:</strong> Os métodos selecionados serão disponibilizados aos contribuidores. 
                    Certifica-te de que tens conta ativa nos métodos escolhidos.
                  </p>
                </div>

                {/* Summary */}
                <div className="bg-stone-50 rounded-xl p-6 mt-6">
                  <h4 className="font-bold text-[#2D2A26] mb-4 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-[#FFBE98]" />
                    Resumo da Candidatura
                  </h4>
                  <div className="space-y-2 text-sm">
                    <p><strong>Viagem:</strong> {formData.name || '—'}</p>
                    <p><strong>Destino:</strong> {formData.destination_city ? `${formData.destination_city}, ` : ''}{formData.destination_country || '—'}</p>
                    <p><strong>Duração:</strong> {formData.duration_days} dias</p>
                    <p><strong>Objetivo:</strong> {formData.goal_amount}€</p>
                    <p><strong>Início previsto:</strong> {formData.start_date_approximate || '—'}</p>
                    <p><strong>Pagamentos:</strong> {formData.payment_methods.length} método(s)</p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Error Message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3"
              >
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <p className="text-red-700 text-sm">{error}</p>
              </motion.div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-stone-100 flex items-center justify-between">
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                currentStep === 0
                  ? 'opacity-0 pointer-events-none'
                  : 'text-[#6B6661] hover:text-[#2D2A26] hover:bg-stone-100'
              }`}
            >
              <ChevronLeft className="w-4 h-4" />
              Anterior
            </button>

            {currentStep < totalSteps - 1 ? (
              <button
                onClick={nextStep}
                className="flex items-center gap-2 px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium hover:bg-[#FFAB7D] transition-colors"
                data-testid="next-step-btn"
              >
                Continuar
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex items-center gap-2 px-6 py-3 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-medium hover:bg-[#FFAB7D] transition-colors disabled:opacity-50"
                data-testid="submit-application-btn"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-[#2D2A26] border-t-transparent rounded-full animate-spin" />
                    A submeter...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Submeter Candidatura
                  </>
                )}
              </button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default JourneyApplicationModal;
