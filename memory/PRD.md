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

### Checkout Modal
- Step 1: Selecao de valor (10-1000) com descricoes inspiradoras
- Badge "Mais popular" no valor de 20EUR - destaque visual com gradiente, texto branco, animacao pulse
- Botao de 20EUR com enfase visual (ring-2, shadow-sm)
- Step 2: Texto motivacional + metodo de pagamento
- Step 3: Instrucoes com QR codes crypto, deep links, referencia
- Ecra de agradecimento pos-contribuicao com ShareMenu
- Geracao automatica de descricoes por IA (GPT-5.2)

### MilestoneProgress (NOVO - 2026-03-09)
- Componente reutilizavel que mostra progresso para proximo marco
- Marcos: 25% (O Primeiro Passo), 50% (Meio Caminho), 75% (Quase La), 100% (Sonho Realizado)
- Mensagem urgente com icone Flame quando faltam < 5%
- Mensagem de conclusao com icone PartyPopper quando >= 100%
- Variantes dark e light para diferentes fundos
- Integrado em: Homepage hero, Homepage cards, JourneyDetail

### Storytelling Progressivo
- 5 capitulos (0-25%, 25-50%, 50-75%, 75-100%, 100%+)
- Variantes light (detalhe viagem) e dark (homepage)
- Capitulos personalizaveis por viagem no Admin
- Detecao automatica de mudanca de capitulo
- Protecao contra emails duplicados (chapters_emails_sent)
- Toggle de emails automaticos no Admin

### Emails Automaticos (ATIVO - 2026-03-09)
- Resend configurado com API key real
- Email automatico na mudanca de capitulo
- Template com storytelling (titulo, texto, botao contribuir)
- Protecao contra duplicados (flags por milestone: 25/50/75/100)
- Endpoint de teste: POST /api/admin/test-chapter-email/{journey_id}/{chapter_num}
- NOTA: Free tier - envia apenas para luis.canarias@gmail.com (verificar dominio para producao)

### Sistema Embaixador
- Dashboard: Progresso com referrals individuais
- Convite por link /invite/{alias}

### Admin
- Gestao viagens, utilizadores, contribuicoes
- Descricoes de contribuicao com geracao IA
- Storytelling Progressivo com 5 editores de capitulos
- Teste de email de capitulo

### Sistema de Partilha Viral
- ShareMenu com WhatsApp, Telegram, Email, Copiar

### Sistema de Traducao
- 6 idiomas com cache e persistencia

## Key Files
- `frontend/src/components/MilestoneProgress.js` - Progresso para proximo marco
- `frontend/src/components/StoryChapter.js` - Componente storytelling
- `frontend/src/components/CheckoutModal.js` - Modal checkout
- `frontend/src/components/ShareMenu.js` - Partilha viral
- `frontend/src/pages/Home.js` - Homepage
- `frontend/src/pages/JourneyDetail.js` - Detalhe viagem
- `frontend/src/pages/Admin.js` - Admin
- `backend/server.py` - API principal

## Prioritized Backlog

### P1
- Verificar dominio no Resend para enviar emails a todos os utilizadores
- Melhorar formulario de edicao de viagens no Admin
- Corrigir aviso HTML invalido no Admin (tr dentro de span)

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Refactoring: Dividir CheckoutModal.js
- Refactoring: Dividir backend/server.py (monolito ~4k linhas)

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend test recipient**: luis.canarias@gmail.com
