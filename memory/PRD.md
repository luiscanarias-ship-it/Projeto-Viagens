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

### Formulario de Edicao de Viagens no Admin (2026-03-09)
- Novo componente JourneyEditForm.js com navegacao por 4 tabs (Basico/Conteudo/Storytelling/Configuracoes)
- Preview em tempo real da viagem (toggle sidebar)
- Indicador "Alteracoes por guardar" quando ha mudancas nao guardadas
- Validacao inline (nome obrigatorio, objetivo minimo 100€, URL valido)
- Geracao de storytelling com IA (5 capitulos) via novo endpoint /api/admin/generate-story-chapters
- Geracao de descricoes de contribuicao com IA (ja existia, agora integrada no novo form)
- Animacoes suaves na transicao entre tabs

### Sistema de Confianca (2026-03-09)
- 3 niveis de confianca: Sonhador, Sonhador Verificado, Embaixador
- Badge visual na pagina da viagem (peach/verde/dourado) com icones criativos
- "Membro da 4Luis desde dd/mm/aaaa" junto ao nome do sonhador
- Admin pode alterar nivel via painel de utilizadores
- Botao discreto "Reportar problema" (mailto:mail@4luis.com) no final da pagina da viagem

### Disclaimer de Contribuicoes (2026-03-09)
- Disclaimer subtil na pagina da viagem (sidebar, abaixo do botao "Apoiar esta Viagem")
- Disclaimer subtil no checkout modal (step 1, abaixo do botao "Continuar")
- Texto sobre natureza voluntaria das contribuicoes e limitacao de responsabilidade

### Paginas Legais (2026-03-09)
- Pagina de Privacidade (/privacy) com 8 seccoes e email luis@4luis.com
- Pagina de Termos e Condicoes (/terms) com 7 seccoes
- Pagina de Politica de Cookies (/cookies e /politica-cookies) com 4 seccoes e 3 tipos de cookies
- Links no footer: Privacy, Terms, Cookies
- Todas as paginas com design consistente e link "Voltar ao inicio"

### Banner de Cookies RGPD (2026-03-09, refinado 2026-03-09)
- Banner amigavel aparece 15 segundos apos aceder ao site
- Imagem de bolacha a sonhar gerada por IA
- Texto pessoal: "Ola... Nos somos as cookies!" + "Autorizas-nos?"
- Botoes "Aceitar" e "Nao, obrigado"
- Link "aqui" para pagina /politica-cookies
- Preferencias guardadas em localStorage com validade de 6 meses
- z-index 9999, posicao bottom-right
- Pagina de Politica de Cookies (/politica-cookies) com 4 seccoes e 3 tipos de cookies

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
