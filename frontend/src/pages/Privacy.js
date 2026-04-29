import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Privacy() {
  return (
    <div className="min-h-screen bg-[#FAFAF9] pt-24 pb-12 px-4" data-testid="privacy-page">
      <div className="max-w-3xl mx-auto">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-[#FFBE98] font-medium text-sm mb-8 hover:text-[#E6A07C] transition-colors"
          data-testid="privacy-back-link"
        >
          <ArrowLeft className="w-4 h-4" />
          Voltar ao início
        </Link>

        <h1 className="text-3xl font-bold text-[#2D2A26] mb-2">Política de Privacidade</h1>
        <p className="text-sm text-[#6B6661] mb-8">Última atualização: Fevereiro 2026</p>

        <div className="bg-white rounded-2xl p-8 shadow-sm space-y-8 text-[#6B6661] leading-relaxed">
          <p>
            A 4Luis respeita a privacidade dos seus utilizadores e compromete-se a proteger os dados pessoais de acordo com o Regulamento Geral de Proteção de Dados (RGPD).
          </p>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">1. Quem somos</h2>
            <p>
              A 4Luis é uma plataforma digital de CrowdDreaming, onde utilizadores podem apoiar sonhos de viagem e acompanhar a evolução desses sonhos através de uma comunidade de sonhadores.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">2. Dados que recolhemos</h2>
            <p>Podemos recolher os seguintes dados:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Nome</li>
              <li>Endereço de email</li>
              <li>Dados de autenticação</li>
              <li>Informações relacionadas com contribuições</li>
              <li>Dados técnicos (IP, navegador, dispositivo)</li>
              <li>Dados de utilização da plataforma</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">3. Finalidade do tratamento</h2>
            <p>Os dados são utilizados para:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Criar e gerir contas de utilizador</li>
              <li>Processar contribuições</li>
              <li>Enviar comunicações relacionadas com sonhos e progresso das viagens</li>
              <li>Gerir convites e sistema de patrocinadores</li>
              <li>Melhorar o funcionamento da plataforma</li>
              <li>Garantir segurança e prevenção de fraude</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">4. Partilha de dados</h2>
            <p>A 4Luis não vende dados pessoais.</p>
            <p className="mt-2">
              Os dados podem ser partilhados apenas com prestadores de serviços necessários ao funcionamento da plataforma, como:
            </p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li><strong>PayPal</strong> — para processar pagamentos de contribuições. Os dados partilhados limitam-se ao necessário para completar a transação (nome, email, montante)</li>
              <li><strong>Serviços de envio de email</strong> — para comunicações transacionais e atualizações sobre viagens</li>
              <li><strong>Serviços de alojamento e infraestrutura</strong> — para manter a plataforma em funcionamento</li>
              <li><strong>Serviços de análise de utilização</strong> — para melhorar a experiência do utilizador</li>
            </ul>
            <p className="mt-3">
              A 4Luis não armazena nem tem acesso a dados bancários ou de cartão de crédito dos utilizadores. Todos os pagamentos são processados diretamente pelo PayPal em ambiente seguro.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">5. Afiliados e parcerias</h2>
            <p>
              A plataforma pode conter links para parceiros externos, nomeadamente plataformas de viagens e serviços relacionados. Estes links podem utilizar mecanismos de tracking para fins de parceria, permitindo identificar a origem da visita.
            </p>
            <p className="mt-2">
              A 4Luis utiliza também um sistema de patrocinadores que permite aos utilizadores convidar novos membros através de links personalizados. Estes links podem conter identificadores que associam novos registos ao patrocinador, possibilitando o acesso a ofertas ocasionais ou benefícios exclusivos.
            </p>
            <p className="mt-2">
              Os cookies de parceiros e de análise só são ativados após o consentimento explícito do utilizador através do banner de cookies apresentado na primeira visita ao site.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">6. Conservação de dados</h2>
            <p>
              Os dados são conservados apenas pelo período necessário ao funcionamento da plataforma e cumprimento de obrigações legais.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">7. Direitos dos utilizadores</h2>
            <p>Os utilizadores têm o direito de:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Aceder aos seus dados</li>
              <li>Corrigir dados incorretos</li>
              <li>Solicitar a eliminação dos dados</li>
              <li>Limitar ou opor-se ao tratamento</li>
            </ul>
            <p className="mt-3">
              Pedidos podem ser enviados para:{' '}
              <a
                href="mailto:suporte@4luis.com"
                className="text-[#FFBE98] font-semibold hover:text-[#E6A07C] transition-colors"
                data-testid="privacy-email"
              >
                luis@4luis.com
              </a>
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">8. Segurança</h2>
            <p>
              A 4Luis implementa medidas técnicas e organizativas adequadas para proteger os dados pessoais.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">9. Alterações</h2>
            <p>
              Esta política pode ser atualizada periodicamente. A versão mais recente estará sempre disponível nesta página.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
