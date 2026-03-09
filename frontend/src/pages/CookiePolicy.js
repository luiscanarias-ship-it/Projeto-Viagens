import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CookiePolicy() {
  return (
    <div className="min-h-screen bg-[#FAFAF9] py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <Link to="/" className="inline-flex items-center gap-2 text-[#FFBE98] font-medium text-sm mb-8 hover:text-[#E6A07C] transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Voltar ao inicio
        </Link>

        <h1 className="text-3xl font-bold text-[#2D2A26] mb-8">Politica de Cookies</h1>

        <div className="bg-white rounded-2xl p-8 shadow-sm space-y-6 text-[#6B6661] leading-relaxed">
          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">O que sao cookies?</h2>
            <p>
              Cookies sao pequenos ficheiros de texto que sao armazenados no teu dispositivo quando visitas um website. Sao amplamente utilizados para fazer os websites funcionarem de forma mais eficiente e para fornecer informacoes aos proprietarios do site.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">Como utilizamos cookies</h2>
            <p>A plataforma 4Luis utiliza cookies para:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Garantir o funcionamento correto do site</li>
              <li>Guardar as tuas preferencias (idioma, sessao)</li>
              <li>Analisar o trafego e uso do site para melhorar a experiencia</li>
              <li>Recordar o teu consentimento de cookies</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">Tipos de cookies que utilizamos</h2>

            <div className="space-y-4 mt-3">
              <div className="bg-stone-50 rounded-xl p-4">
                <h3 className="font-semibold text-[#2D2A26] mb-1">Cookies essenciais</h3>
                <p className="text-sm">Necessarios para o funcionamento basico do site. Incluem cookies de sessao e autenticacao. Nao podem ser desativados.</p>
              </div>

              <div className="bg-stone-50 rounded-xl p-4">
                <h3 className="font-semibold text-[#2D2A26] mb-1">Cookies analiticos</h3>
                <p className="text-sm">Ajudam-nos a entender como os visitantes interagem com o site, permitindo-nos melhorar a experiencia. Os dados sao anonimizados.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">Duracao do consentimento</h2>
            <p>
              O teu consentimento de cookies e valido por <strong className="text-[#2D2A26]">6 meses</strong>. Apos esse periodo, sera solicitada novamente a tua autorizacao.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">Como gerir cookies</h2>
            <p>
              Podes alterar a tua decisao a qualquer momento limpando os dados do browser ou atraves das definicoes do teu navegador. Para mais informacoes, consulta a documentacao do teu browser.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-bold text-[#2D2A26] mb-3">Contacto</h2>
            <p>
              Se tiveres duvidas sobre a nossa politica de cookies, contacta-nos em{' '}
              <a href="mailto:mail@4luis.com" className="text-[#FFBE98] font-semibold hover:text-[#E6A07C] transition-colors">
                mail@4luis.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
