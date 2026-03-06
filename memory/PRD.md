# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariação de fundos para viagens solidárias com sistema de níveis (Sonhador - Embaixador), múltiplos métodos de pagamento, e sistema de referrals.

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

### Homepage
- "Como funciona o Crowddreaming" - 3 cards com icones
- Prova social "X sonhadores ja ajudaram esta plataforma"
- Imagem e badge "Viagem Principal" clicaveis -> detalhe da viagem
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

### Traducao por IA (Implementado 2026-03-06)
- Endpoint POST /api/translate usando GPT-5.2 via Emergent LLM Key
- 6 idiomas suportados: PT, EN, ES, FR, DE, IT
- Cache de traducoes no frontend para evitar chamadas repetidas
- Toast notification com aviso "Traducao automatica por IA"
- Nota no footer quando idioma nao e portugues
- Seletor de idioma persistente: preferencia guardada na conta do utilizador
- PATCH /api/users/preferred-language para guardar preferencia
- Auto-sync no login: ao entrar, a plataforma muda para o idioma preferido
- Auto-traduz ao carregar pagina se idioma guardado nao e portugues
- Homepage totalmente traduzivel (50+ chaves de traducao)

## Key Files
- `frontend/src/components/CheckoutModal.js` - Modal de checkout 3 passos
- `frontend/src/pages/JourneyDetail.js` - Pagina de viagem com sticky CTA
- `frontend/src/pages/Home.js` - Homepage com Como funciona + Prova social
- `frontend/src/pages/Dashboard.js` - Dashboard com progresso Embaixador
- `frontend/src/pages/InvitePage.js` - Pagina de convite
- `frontend/src/pages/Admin.js` - Painel de administracao
- `frontend/src/contexts/LanguageContext.js` - Contexto de traducao com cache
- `backend/server.py` - API FastAPI principal

## Prioritized Backlog

### P1
- Verificar estabilidade do Painel de Administracao (smoke test passado)
- Melhorar formulario de edicao de viagens no Admin

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Ferramentas de planeamento (afiliados)
- Refactoring: Dividir CheckoutModal.js em sub-componentes

## Credentials
- **Admin**: admin@4luis.com / Admin1
