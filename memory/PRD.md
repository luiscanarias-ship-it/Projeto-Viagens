# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise (Stripe desativado)
- **Email**: Resend
- **Auth**: JWT + Google OAuth
- **QR Codes**: qrcode (npm, toDataURL)
- **Crypto Prices**: CoinGecko API
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key (emergentintegrations)

## What's Been Implemented

### Checkout Modal 3 Passos
- Step 1: Selecao de valor (10/20/50/100/custom)
- Step 2: Metodo de pagamento (Crypto com badge TOP, MBWay, Revolut, Wise, PayPal)
- Step 3: Instrucoes com QR codes crypto (URI blockchain), deep links, referencia CN-XXXX

### Homepage (Atualizada 2026-03-06)
- "Como funciona o Crowddreaming" - 3 cards com icones
- Prova social "X sonhadores ja ajudaram esta plataforma"
- Imagem e badge "Viagem Principal" clicaveis -> detalhe da viagem
- Layout imersivo para viagem principal com imagem de fundo e overlay de texto
- Barra sticky de contribuicao que aparece no scroll (>600px) com detalhes da viagem e botao "Contribuir"
- Texto introdutorio na seccao "Planeia a tua viagem"
- Citacao inspiradora final com 4 linhas, incluindo "Juntos, transformamos sonhos em destinos."
- CheckoutModal renderizado corretamente na homepage
- "Planeia a tua viagem" com pesquisa de destino e links de recursos

### Pagina Detalhe Viagem
- Botao sticky "Apoiar esta viagem" fixo no topo ao fazer scroll

### Sistema Embaixador
- Dashboard: Progresso com referrals individuais (verde/cinza)
- Botao "Convidar mais amigos" copia link /invite/{alias}
- Pagina /invite/{alias} com imagem, mensagem convite, barra progresso, botao contribuir

### Admin
- Gestao viagens, utilizadores, contribuicoes
- Pesquisa por referencia de pagamento

### Onboarding de Convite
- Fluxo guiado apos registo via /invite/{alias}
- 6 seccoes: Boas-vindas, Viagem Principal, Progressao, Beneficios Embaixador, Progresso, Citacao inspiradora

### Sistema de Partilha Viral
- Componente ShareMenu reutilizavel com WhatsApp, Telegram, Email, Copiar link
- Dashboard: link de convite com botao "Partilhar convite"
- InvitePage e JourneyDetail com partilha integrada

### Sistema de Traducao
- Endpoint POST /api/translate usando GPT-5.2 via Emergent LLM Key
- 6 idiomas suportados: PT, EN, ES, FR, DE, IT
- Cache de traducoes no frontend
- Seletor de idioma persistente guardado na conta do utilizador

## Key Files
- `frontend/src/components/CheckoutModal.js` - Modal de checkout 3 passos
- `frontend/src/pages/JourneyDetail.js` - Pagina de viagem com sticky CTA
- `frontend/src/pages/Home.js` - Homepage com melhorias visuais
- `frontend/src/pages/Dashboard.js` - Dashboard com progresso Embaixador
- `frontend/src/pages/InvitePage.js` - Pagina de convite
- `frontend/src/pages/Admin.js` - Painel de administracao
- `frontend/src/contexts/LanguageContext.js` - Contexto de traducao com cache
- `frontend/src/components/ShareMenu.js` - Componente de partilha viral
- `backend/server.py` - API FastAPI principal

## Prioritized Backlog

### P1
- Verificar estabilidade do Painel de Administracao (smoke test)
- Melhorar formulario de edicao de viagens no Admin

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Ferramentas de planeamento (afiliados)
- Refactoring: Dividir CheckoutModal.js em sub-componentes
- Refactoring: Home.js a crescer em complexidade

## Credentials
- **Admin**: admin@4luis.com / Admin1
