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
          Voltar ao início
        </Link>

        <h1 className="text-3xl font-bold text-[#2D2A26] mb-2">Termos e Condições</h1>
        <p className="text-sm text-[#6B6661] mb-8">Última atualização: Abril 2026</p>

        <div className="bg-white rounded-2xl p-8 shadow-sm space-y-8 text-[#6B6661] leading-relaxed">
          <p>
            Ao utilizar a plataforma 4Luis, o utilizador aceita os presentes termos.
          </p>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">1. Natureza da plataforma</h2>
            <p>
              A 4Luis é uma plataforma digital de CrowdDreaming que permite aos utilizadores apoiar sonhos de viagem e acompanhar a sua evolução.
            </p>
            <p className="mt-2">
              A plataforma disponibiliza uma infraestrutura tecnológica que facilita a ligação entre pessoas que desejam apoiar e pessoas que desejam realizar os seus sonhos.
            </p>
            <p className="mt-2">
              A 4Luis não organiza viagens, não atua como agência de viagens e não garante a realização das mesmas.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">2. Contribuições</h2>
            <p>As contribuições realizadas na plataforma são voluntárias.</p>
            <p className="mt-2">
              Estas contribuições destinam-se a apoiar um sonho de viagem apresentado na plataforma, podendo ser promovido por um utilizador (Embaixador) ou pela própria 4Luis.
            </p>
            <p className="mt-2">A 4Luis não cobra comissões sobre os valores destinados aos sonhos.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">3. Destino dos fundos</h2>
            <p>
              Os valores contribuídos destinam-se exclusivamente ao apoio do sonho de viagem selecionado.
            </p>
            <p className="mt-2">
              A forma de gestão e utilização dos fundos é da responsabilidade do respetivo Embaixador ou da 4Luis, no caso de campanhas próprias.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">4. Processamento de pagamentos</h2>
            <p>
              Os pagamentos correspondem ao valor apresentado no momento do checkout.
            </p>
            <p className="mt-2">
              A 4Luis disponibiliza diferentes métodos de pagamento, podendo alguns implicar procedimentos específicos por parte do utilizador.
            </p>
            <p className="mt-2">
              A confirmação da contribuição depende da validação do pagamento.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">5. Utilização da plataforma</h2>
            <p>Os utilizadores comprometem-se a:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Fornecer informações verdadeiras;</li>
              <li>Utilizar a plataforma de forma responsável;</li>
              <li>Não utilizar a plataforma para atividades ilegais, abusivas ou fraudulentas.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">6. Sistema de convites e estatutos</h2>
            <p>
              A plataforma permite que os utilizadores convidem outras pessoas a participar.
            </p>
            <p className="mt-2">
              A atribuição de estatutos, como o de Embaixador, depende de critérios definidos pela plataforma e pode ser alterada ou revista a qualquer momento.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">7. Conteúdo</h2>
            <p>Os utilizadores são responsáveis pelos conteúdos que partilham na plataforma.</p>
            <p className="mt-2">A 4Luis reserva-se o direito de remover conteúdos que considere inadequados, ilegais ou contrários aos valores da plataforma.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">8. Limitação de responsabilidade</h2>
            <p>A 4Luis não é responsável por:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Cancelamentos, alterações ou não realização de viagens;</li>
              <li>Incumprimento por parte de Embaixadores;</li>
              <li>Utilização indevida da plataforma por terceiros;</li>
              <li>Quaisquer danos indiretos resultantes da utilização da plataforma.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">9. Alterações aos termos</h2>
            <p>
              A 4Luis pode atualizar estes termos sempre que necessário.
            </p>
            <p className="mt-2">
              A continuação da utilização da plataforma após alterações implica a aceitação dos novos termos.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
