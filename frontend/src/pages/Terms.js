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
        <p className="text-sm text-[#6B6661] mb-8">Última atualização: Fevereiro 2026</p>

        <div className="bg-white rounded-2xl p-8 shadow-sm space-y-8 text-[#6B6661] leading-relaxed">
          <p>
            Ao utilizar a plataforma 4Luis, o utilizador aceita os presentes termos.
          </p>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">1. Natureza da plataforma</h2>
            <p>
              A 4Luis é uma plataforma digital de CrowdDreaming, onde membros podem apoiar sonhos de viagem e acompanhar a evolução desses sonhos.
            </p>
            <p className="mt-2">
              A plataforma disponibiliza uma infraestrutura tecnológica que permite a realização de contribuições entre utilizadores e/ou para campanhas da própria plataforma.
            </p>
            <p className="mt-2">
              A 4Luis não garante a realização das viagens nem assume responsabilidade pela execução das mesmas.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">2. Contribuições</h2>
            <p>As contribuições feitas na plataforma são voluntárias.</p>
            <p className="mt-3">Estas contribuições podem destinar-se a:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Apoiar um Embaixador (sonhador responsável por uma viagem), sendo o valor atribuído ao respetivo Embaixador;</li>
              <li>Apoiar uma campanha promovida pela própria plataforma, sendo o valor atribuído à 4Luis.</li>
            </ul>
            <p className="mt-3">A 4Luis não cobra comissões sobre os valores de apoio destinados a campanhas de Embaixadores.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">3. Contribuição para a plataforma</h2>
            <p>
              Durante o processo de pagamento, o utilizador poderá, de forma opcional, adicionar uma contribuição adicional para a plataforma.
            </p>
            <p className="mt-3">Esta contribuição:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>É totalmente voluntária;</li>
              <li>Destina-se a suportar os custos de operação, desenvolvimento e manutenção da 4Luis;</li>
              <li>Não é transferida para o Embaixador nem afeta o valor do apoio à viagem.</li>
            </ul>
            <p className="mt-3">A não seleção desta contribuição não impede a realização do apoio.</p>
            <p className="mt-2">
              Para efeitos legais e fiscais, esta contribuição pode ser considerada como receita da plataforma pela prestação de serviços digitais.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">4. Processamento de pagamentos</h2>
            <p>
              Os pagamentos realizados na plataforma correspondem ao valor total apresentado no momento do checkout, podendo incluir:
            </p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>O valor de apoio à campanha;</li>
              <li>A contribuição opcional para a plataforma.</li>
            </ul>
            <p className="mt-3">A distribuição destes valores é efetuada internamente após confirmação do pagamento.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">5. Utilização da plataforma</h2>
            <p>Os utilizadores comprometem-se a:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Fornecer informações verdadeiras;</li>
              <li>Utilizar a plataforma de forma responsável;</li>
              <li>Não utilizar a plataforma para atividades ilegais ou fraudulentas.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">6. Sistema de convites</h2>
            <p>
              A plataforma permite que utilizadores convidem amigos para apoiar sonhos.
            </p>
            <p className="mt-2">
              O estatuto de Embaixador pode ser atribuído a utilizadores que cumpram os critérios definidos pela plataforma.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">7. Conteúdo</h2>
            <p>Os utilizadores são responsáveis pelos conteúdos que partilham.</p>
            <p className="mt-2">A 4Luis reserva-se o direito de remover conteúdos inadequados.</p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">8. Limitação de responsabilidade</h2>
            <p>A 4Luis não é responsável por:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Cancelamentos ou alterações de viagens;</li>
              <li>Incumprimento por parte de Embaixadores;</li>
              <li>Utilização indevida da plataforma por terceiros;</li>
              <li>Quaisquer perdas indiretas decorrentes da utilização da plataforma.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">9. Alterações</h2>
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
