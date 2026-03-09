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

### Banner de Cookies RGPD (2026-03-09)
- Banner fixo no fundo na primeira visita com animacao slide-up
- Imagem de bolacha a sonhar gerada por IA
- Texto + botoes "Aceitar" e "Configurar"
- Painel de configuracao: Essenciais (sempre ativas), Analiticos, Marketing
- Preferencias guardadas em localStorage com validade de 6 meses
- z-index 9999 para aparecer acima de todos os elementos

### Sistema de Emails (5 tipos - COMPLETO)
1. Mudanca de capitulo — Automatico nos marcos 25/50/75/100%
2. Resumo semanal — Botao no admin
3. Contribuicao via referral — Automatico
4. Sonho financiado — Botao no admin (>= 100%), marca viagem como financiada
5. Novo sonho — Botao no admin para anunciar nova viagem
- Template padrao: titulo, narrativa, barra de progresso, botao CTA
- Remetente: mail@4luis.com

### Homepage
- Hero CrowdDreaming, Storytelling Progressivo, Barra sticky
- MilestoneProgress, MilestoneCelebration
- Seccao "Sonhos em Materializacao" com 4 cartoes visuais

### Viagens Embaixadores
- Japao (Manuel, 42%), Coreia do Sul (Sofia, 15%), Martinique (Ana, 60%), Maldivas (Pedro, 75%)

### Checkout Modal
- Badge "Mais popular" 20EUR, 3 passos, ecra de agradecimento

### Admin
- Gestao viagens/utilizadores/contribuicoes
- Botoes de email (Novo Sonho, Sonho Financiado, Resumo Semanal)
- Storytelling com 5 editores de capitulos

## Key Files
- frontend/src/components/CookieConsent.js
- frontend/src/components/MilestoneCelebration.js
- frontend/src/components/MilestoneProgress.js
- frontend/src/components/CheckoutModal.js
- frontend/src/pages/Home.js
- frontend/src/pages/JourneyDetail.js
- frontend/src/pages/Admin.js
- frontend/src/App.js
- backend/server.py

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%
- Melhorar formulario de edicao de viagens no Admin

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Refactoring: Dividir backend/server.py

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
