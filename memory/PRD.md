# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise
- **Email**: Resend (PRODUCAO - mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key

## What's Been Implemented

### Sistema de Emails (5 tipos - COMPLETO 2026-03-09)
1. **Mudanca de capitulo** — Automatico quando viagem atinge 25/50/75/100%
2. **Resumo semanal** — Botao no admin, envia progresso de todas as viagens ativas
3. **Contribuicao via referral** — Automatico quando convidado contribui
4. **Sonho financiado** — Botao no admin (so aparece quando >= 100%), marca viagem como financiada
5. **Novo sonho** — Botao no admin para anunciar nova viagem a todos os utilizadores
- Template padrao: titulo, texto narrativo, barra de progresso, botao CTA
- Remetente: mail@4luis.com (dominio verificado na Resend)
- Helpers reutilizaveis: _build_standard_email, _build_email_progress_bar, _build_email_cta_button

### Endpoints de Email Admin
- POST /api/admin/emails/weekly-summary
- POST /api/admin/emails/dream-funded/{journey_id}
- POST /api/admin/emails/new-journey/{journey_id}

### Homepage
- Hero com subtitulo CrowdDreaming
- Storytelling Progressivo com capitulos
- Barra sticky de contribuicao
- MilestoneProgress no hero e cards
- MilestoneCelebration banner
- Seccao "Sonhos em Fase de Materializacao" com 4 cartoes visuais

### Viagens Artificiais (Embaixadores)
- Japao (Manuel, 42%), Coreia do Sul (Sofia, 15%), Martinique (Ana, 60%), Maldivas (Pedro, 75%)

### Checkout Modal
- Badge "Mais popular" 20EUR com gradiente e animacao pulse
- 3 passos com descricoes inspiradoras
- Ecra de agradecimento com partilha

### MilestoneProgress
- Marcos: 25%, 50%, 75%, 100% com mensagens dinamicas
- Mensagem urgente quando faltam < 5%

### MilestoneCelebration
- Banner animado com confetti nos marcos
- Auto-dismiss 8s, sessionStorage previne repeticao

### Admin
- Gestao viagens, utilizadores, contribuicoes
- Botoes de email por viagem (Novo Sonho, Sonho Financiado)
- Botao Resumo Semanal no header
- Storytelling Progressivo com 5 editores de capitulos

## Key Files
- frontend/src/components/MilestoneCelebration.js
- frontend/src/components/MilestoneProgress.js
- frontend/src/components/CheckoutModal.js
- frontend/src/pages/Home.js
- frontend/src/pages/JourneyDetail.js
- frontend/src/pages/Admin.js
- backend/server.py

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100% (pagina com contribuidores, partilha, confetti)
- Melhorar formulario de edicao de viagens no Admin

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Refactoring: Dividir backend/server.py (monolito ~5k linhas)

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
