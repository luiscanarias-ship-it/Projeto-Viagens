import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CookiePolicy() {
  return (
    <div className="min-h-screen bg-[#FAFAF9] pt-24 pb-12 px-4" data-testid="cookie-policy-page">
      <div className="max-w-3xl mx-auto">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-[#FFBE98] font-medium text-sm mb-8 hover:text-[#E6A07C] transition-colors"
          data-testid="cookie-policy-back-link"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao inicio
        </Link>

        <h1 className="text-3xl font-bold text-[#2D2A26] mb-2">Politica de Cookies</h1>
        <p className="text-sm text-[#6B6661] mb-8">Ultima atualizacao: Fevereiro 2026</p>

        <div className="bg-white rounded-2xl p-8 shadow-sm space-y-8 text-[#6B6661] leading-relaxed">
          <p>
            A 4Luis utiliza cookies para melhorar a experiencia dos utilizadores e compreender a utilizacao da plataforma.
          </p>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">1. O que sao cookies</h2>
            <p>
              Cookies sao pequenos ficheiros armazenados no dispositivo do utilizador quando visita um website.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">2. Tipos de cookies utilizados</h2>
            <div className="space-y-4 mt-3">
              <div className="bg-stone-50 rounded-xl p-4">
                <h3 className="font-semibold text-[#2D2A26] mb-1">Cookies essenciais</h3>
                <p className="text-sm">Necessarios para o funcionamento da plataforma, como autenticacao e seguranca.</p>
              </div>
              <div className="bg-stone-50 rounded-xl p-4">
                <h3 className="font-semibold text-[#2D2A26] mb-1">Cookies analiticos</h3>
                <p className="text-sm">Utilizados para compreender como os utilizadores interagem com a plataforma e melhorar a experiencia.</p>
              </div>
              <div className="bg-stone-50 rounded-xl p-4">
                <h3 className="font-semibold text-[#2D2A26] mb-1">Cookies funcionais</h3>
                <p className="text-sm">Permitem memorizar preferencias como idioma ou configuracoes.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">3. Gestao de cookies</h2>
            <p>
              Os utilizadores podem aceitar ou configurar cookies atraves do banner apresentado na primeira visita.
            </p>
            <p className="mt-2">
              Tambem e possivel gerir cookies nas definicoes do navegador.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">4. Alteracoes</h2>
            <p>
              Esta politica pode ser atualizada periodicamente.
            </p>
          </section>

          <section className="pt-4 border-t border-stone-100">
            <p className="text-sm">
              Duvidas? Contacta-nos em{' '}
              <a
                href="mailto:mail@4luis.com"
                className="text-[#FFBE98] font-semibold hover:text-[#E6A07C] transition-colors"
                data-testid="cookie-policy-email"
              >
                mail@4luis.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
