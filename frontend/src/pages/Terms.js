import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Terms() {
  return (
    <div className="min-h-screen bg-[#FAFAF9] pt-24 pb-12 px-4" data-testid="terms-page">
      <div className="max-w-3xl mx-auto">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-[#FFBE98] font-medium text-sm mb-8 hover:text-[#E6A07C] transition-colors"
          data-testid="terms-back-link"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao inicio
        </Link>

        <h1 className="text-3xl font-bold text-[#2D2A26] mb-2">Termos e Condicoes</h1>
        <p className="text-sm text-[#6B6661] mb-8">Ultima atualizacao: Fevereiro 2026</p>

        <div className="bg-white rounded-2xl p-8 shadow-sm space-y-8 text-[#6B6661] leading-relaxed">
          <p>
            Ao utilizar a plataforma 4Luis, o utilizador aceita os presentes termos.
          </p>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">1. Natureza da plataforma</h2>
            <p>
              A 4Luis e uma plataforma de CrowdDreaming, onde membros podem apoiar sonhos de viagem e acompanhar a evolucao desses sonhos.
            </p>
            <p className="mt-2">
              A plataforma nao atua como intermediario financeiro nem garante a realizacao das viagens.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">2. Contribuicoes</h2>
            <p>As contribuicoes feitas na plataforma sao voluntarias.</p>
            <p className="mt-2">
              Dependendo do metodo de pagamento utilizado, os valores podem ser enviados diretamente ao sonhador responsavel pela viagem.
            </p>
            <p className="mt-2">A 4Luis nao cobra comissoes sobre contribuicoes.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">3. Utilizacao da plataforma</h2>
            <p>Os utilizadores comprometem-se a:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Fornecer informacoes verdadeiras</li>
              <li>Utilizar a plataforma de forma responsavel</li>
              <li>Nao utilizar a plataforma para atividades ilegais ou fraudulentas</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">4. Sistema de convites</h2>
            <p>
              A plataforma permite que utilizadores convidem amigos para apoiar sonhos.
            </p>
            <p className="mt-2">
              O estatuto de Embaixador pode ser atribuido a utilizadores que cumpram os criterios definidos pela plataforma.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">5. Conteudo</h2>
            <p>Os utilizadores sao responsaveis pelos conteudos que partilham.</p>
            <p className="mt-2">A 4Luis reserva-se o direito de remover conteudos inadequados.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">6. Limitacao de responsabilidade</h2>
            <p>A 4Luis nao e responsavel por:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Cancelamentos ou alteracoes de viagens</li>
              <li>Utilizacao indevida da plataforma por terceiros</li>
              <li>Perdas indiretas decorrentes da utilizacao da plataforma</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">7. Alteracoes</h2>
            <p>
              A 4Luis pode atualizar estes termos sempre que necessario.
            </p>
            <p className="mt-2">
              A continuacao da utilizacao da plataforma implica aceitacao das alteracoes.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
