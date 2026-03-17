import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle } from 'lucide-react';

const TestimonialResult = () => {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const action = params.get('action');
  const authorized = action === 'authorized';

  return (
    <div className="min-h-screen bg-[#FAFAF9] flex items-center justify-center px-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="max-w-md text-center" data-testid="testimonial-result">
        <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 ${authorized ? 'bg-green-100' : 'bg-stone-100'}`}>
          {authorized
            ? <CheckCircle className="w-8 h-8 text-green-600" />
            : <XCircle className="w-8 h-8 text-stone-500" />}
        </div>
        <h1 className="text-2xl font-bold text-[#2D2A26] mb-3">
          {authorized ? 'Obrigado pela tua autorizacao!' : 'Tudo bem, respeitamos a tua decisao.'}
        </h1>
        <p className="text-[#6B6661] text-sm leading-relaxed mb-8">
          {authorized
            ? 'O teu testemunho sera publicado na plataforma 4Luis para ajudar outros utilizadores a confiar no projeto. Obrigado por fazeres parte do sonho!'
            : 'O teu testemunho nao sera publicado. Agradecemos o teu tempo e a tua honestidade.'}
        </p>
        <button onClick={() => navigate('/')}
          className="px-6 py-2.5 bg-[#FFBE98] text-[#2D2A26] rounded-xl font-semibold text-sm hover:bg-[#f0a878] transition-colors"
          data-testid="back-home-btn">
          Voltar ao inicio
        </button>
      </motion.div>
    </div>
  );
};

export default TestimonialResult;
