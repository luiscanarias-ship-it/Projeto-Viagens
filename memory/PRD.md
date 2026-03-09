# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise
- **Email**: Resend (configured but needs RESEND_API_KEY in .env)
- **Auth**: JWT + Google OAuth
- **QR Codes**: qrcode (npm, toDataURL)
- **Crypto Prices**: CoinGecko API
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key

## What's Been Implemented

### Homepage
- Hero com subtitulo CrowdDreaming em cor pessego
- Layout imersivo para viagem principal com imagem de fundo
- Storytelling Progressivo com capitulos baseados na percentagem
- Barra sticky de contribuicao no scroll
- "Como funciona o CrowdDreaming" com realce pessego
- Texto introdutorio na seccao "Planeia a tua viagem"
- Citacao inspiradora final com 3 linhas

### Checkout Modal
- Step 1: Selecao de valor (10-1000) com descricoes inspiradoras opcionais
- Badge "Mais popular" no valor de 20EUR
- Step 2: Texto motivacional + metodo de pagamento
- Step 3: Instrucoes com QR codes crypto, deep links, referencia
- Ecra de agradecimento pos-contribuicao com ShareMenu
- Descricoes de contribuicao configuraveis por viagem no Admin
- Geracao automatica de descricoes por IA (GPT-5.2)

### Storytelling Progressivo (Novo - 2026-03-09)
- Componente StoryChapter com 5 capitulos (0-25%, 25-50%, 50-75%, 75-100%, 100%+)
- Variantes light (detalhe viagem) e dark (homepage)
- Capitulos personalizaveis por viagem no Admin
- Detecao automatica de mudanca de capitulo na confirmacao de contribuicao
- Email automatico para todos os utilizadores na mudanca de fase
- Toggle de emails automaticos no Admin
- China populada com capitulos especificos

### Sistema Embaixador
- Dashboard: Progresso com referrals individuais
- Botao "Convidar mais amigos" copia link /invite/{alias}
- Pagina /invite/{alias} com convite e progresso

### Admin
- Gestao viagens, utilizadores, contribuicoes
- Descricoes de contribuicao com geracao IA
- Storytelling Progressivo com 5 editores de capitulos
- Pesquisa por referencia de pagamento
- Smoke test 100% estavel

### Sistema de Partilha Viral
- Componente ShareMenu com WhatsApp, Telegram, Email, Copiar
- Suporte para customMessage (usado no ecra de agradecimento)
- Integrado em Dashboard, InvitePage, JourneyDetail, CheckoutModal

### Sistema de Traducao
- 6 idiomas: PT, EN, ES, FR, DE, IT
- Cache de traducoes no frontend
- Seletor de idioma persistente

## Key Files
- `frontend/src/components/StoryChapter.js` - Componente de storytelling
- `frontend/src/components/CheckoutModal.js` - Modal de checkout
- `frontend/src/components/ShareMenu.js` - Componente de partilha
- `frontend/src/pages/JourneyDetail.js` - Pagina de viagem
- `frontend/src/pages/Home.js` - Homepage
- `frontend/src/pages/Admin.js` - Painel de administracao
- `frontend/src/contexts/LanguageContext.js` - Contexto de traducao
- `backend/server.py` - API FastAPI principal

## Prioritized Backlog

### P1
- Melhorar formulario de edicao de viagens no Admin
- Adicionar RESEND_API_KEY ao .env para emails funcionarem

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Ferramentas de planeamento (afiliados)
- Refactoring: Dividir CheckoutModal.js em sub-componentes

## Credentials
- **Admin**: admin@4luis.com / Admin1
