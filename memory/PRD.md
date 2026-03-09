# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise
- **Email**: Resend (ATIVO - re_KsK6NdBc_*)
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
- Mensagem de progresso para proximo marco (MilestoneProgress) no hero e cards
- Banner de celebracao de marcos (MilestoneCelebration)
- Seccao "Sonhos em Fase de Materializacao" redesenhada com cartoes visuais (max 4)

### Seccao Sonhos em Materializacao (2026-03-09)
- Grid de 4 cartoes visuais com imagem, titulo, nome do sonhador, barra de progresso, percentagem
- Layout responsivo: 4 colunas desktop, 2 tablet, 1 mobile
- Cada cartao liga a pagina de detalhe da viagem
- Botao "Explorar mais sonhos" quando existem mais de 4 viagens
- 4 viagens artificiais criadas: Costa Amalfitana (Manuel, 42%), Bali (Sofia, 15%), Pamukkale (Ana, 60%), Ha Long Bay (Pedro, 75%)

### Checkout Modal
- Step 1: Selecao de valor (10-1000) com descricoes inspiradoras
- Badge "Mais popular" no valor de 20EUR - destaque visual com gradiente, texto branco, animacao pulse
- Botao de 20EUR com enfase visual (ring-2, shadow-sm)
- Step 2: Texto motivacional + metodo de pagamento
- Step 3: Instrucoes com QR codes crypto, deep links, referencia
- Ecra de agradecimento pos-contribuicao com ShareMenu
- Geracao automatica de descricoes por IA (GPT-5.2)

### MilestoneProgress (2026-03-09)
- Componente reutilizavel que mostra progresso para proximo marco
- Marcos: 25% (O Primeiro Passo), 50% (Meio Caminho), 75% (Quase La), 100% (Sonho Realizado)
- Mensagem urgente com icone Flame quando faltam < 5%
- Variantes dark e light para diferentes fundos
- Integrado em: Homepage hero, JourneyDetail

### MilestoneCelebration (2026-03-09)
- Banner animado com confetti quando um marco e atingido (25%, 50%, 75%, 100%)
- Mensagem: "O sonho entrou numa nova fase" com titulo do capitulo
- Auto-dismiss apos 8 segundos, botao de fechar (X)
- SessionStorage previne repeticao na mesma sessao
- Backend rastreia last_milestone_reached e last_milestone_at
- Integrado em: JourneyDetail e Homepage

### Storytelling Progressivo
- 5 capitulos (0-25%, 25-50%, 50-75%, 75-100%, 100%+)
- Variantes light (detalhe viagem) e dark (homepage)
- Capitulos personalizaveis por viagem no Admin
- Detecao automatica de mudanca de capitulo
- Protecao contra emails duplicados (chapters_emails_sent)
- Toggle de emails automaticos no Admin

### Emails Automaticos (ATIVO)
- Resend configurado com API key real
- Email automatico na mudanca de capitulo
- NOTA: Free tier - envia apenas para luis.canarias@gmail.com

### Sistema Embaixador
- Dashboard: Progresso com referrals individuais
- Convite por link /invite/{alias}

### Admin
- Gestao viagens, utilizadores, contribuicoes
- Descricoes de contribuicao com geracao IA
- Storytelling Progressivo com 5 editores de capitulos

### Sistema de Partilha Viral
- ShareMenu com WhatsApp, Telegram, Email, Copiar

### Sistema de Traducao
- 6 idiomas com cache e persistencia

## Key Files
- `frontend/src/components/MilestoneCelebration.js` - Celebracao de marcos
- `frontend/src/components/MilestoneProgress.js` - Progresso para proximo marco
- `frontend/src/components/StoryChapter.js` - Componente storytelling
- `frontend/src/components/CheckoutModal.js` - Modal checkout
- `frontend/src/components/ShareMenu.js` - Partilha viral
- `frontend/src/pages/Home.js` - Homepage
- `frontend/src/pages/JourneyDetail.js` - Detalhe viagem
- `frontend/src/pages/Admin.js` - Admin
- `backend/server.py` - API principal

## Prioritized Backlog

### P0
- Celebracao especial quando viagem atinge 100% (pagina dedicada com contribuidores, partilha, confetti)

### P1
- Verificar dominio no Resend para enviar emails a todos os utilizadores
- Melhorar formulario de edicao de viagens no Admin

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Refactoring: Dividir CheckoutModal.js
- Refactoring: Dividir backend/server.py (monolito ~5k linhas)

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend test recipient**: luis.canarias@gmail.com
