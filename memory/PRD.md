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

### Autosave Automatico (2026-03-16)
- JourneyEditForm: autosave com debounce de 2s para localStorage
- Banner de recuperacao ao reabrir formulario com dados salvos (Manter/Descartar)
- Indicador visual "Autosaved" no header do formulario
- Create Journey Form: autosave identico com chave autosave_journey_create
- Indicador "Rascunho guardado" no formulario de criacao
- Limpeza automatica do autosave apos guardar ou cancelar
- Warning beforeunload quando ha alteracoes por guardar
- Dados expiram apos 24h

### Correcao FRONTEND_URL (2026-03-16)
- FRONTEND_URL no backend agora le de variavel de ambiente (nao hardcoded)
- Adicionado FRONTEND_URL ao backend/.env

### Preview de Emails antes de Enviar (2026-03-09)
- Todos os emails requerem confirmacao do admin antes de serem enviados
- Modal de preview mostra: HTML completo do email, assunto, numero de destinatarios
- Botoes "Cancelar" e "Confirmar e Enviar"
- 3 endpoints de preview: resumo semanal, novo sonho, sonho financiado
- Aplica-se a todos os emails: resumo semanal, anunciar novo sonho (com selector de viagem), sonho financiado

### Correcoes Admin e Navegacao (2026-03-09)
- Fix: Link "Viagens" no header agora faz scroll ate a seccao de viagens
- Fix: Login como admin redireciona para /admin automaticamente
- Novo: Botao "Suspender/Reativar" viagem (toggle visibilidade sem apagar)
- Novo: Botao estrela para definir viagem principal diretamente na lista
- Novo: "Anunciar Novo Sonho" com dropdown para selecionar qual viagem anunciar
- Storytelling editavel apos geracao IA (ja funcionava, confirmado)

### Formulario de Edicao de Viagens no Admin (2026-03-09)
- Novo componente JourneyEditForm.js com navegacao por 4 tabs (Basico/Conteudo/Storytelling/Configuracoes)
- Preview em tempo real da viagem (toggle sidebar)
- Indicador "Alteracoes por guardar" quando ha mudancas nao guardadas
- Validacao inline (nome obrigatorio, objetivo minimo 100EUR, URL valido)
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

### Banner de Cookies RGPD (2026-03-09)
- Banner amigavel aparece 15 segundos apos aceder ao site
- Imagem de bolacha a sonhar gerada por IA
- Botoes "Aceitar" e "Nao, obrigado"
- Preferencias guardadas em localStorage com validade de 6 meses

### Sistema de Emails (5 tipos - COMPLETO)
1. Mudanca de capitulo — Automatico nos marcos 25/50/75/100%
2. Resumo semanal — Botao no admin
3. Contribuicao via referral — Automatico
4. Sonho financiado — Botao no admin (>= 100%), marca viagem como financiada
5. Novo sonho — Botao no admin para anunciar nova viagem

### Homepage
- Hero CrowdDreaming, Storytelling Progressivo, Barra sticky
- MilestoneProgress, MilestoneCelebration
- Seccao "Sonhos em Materializacao" com 4 cartoes visuais

### Checkout Modal
- Badge "Mais popular" 20EUR, 3 passos, ecra de agradecimento

### Admin
- Gestao viagens/utilizadores/contribuicoes
- Botoes de email (Novo Sonho, Sonho Financiado, Resumo Semanal)
- Storytelling com 5 editores de capitulos

## Key Files
- frontend/src/components/JourneyEditForm.js (autosave integrado)
- frontend/src/components/EmailPreviewModal.js
- frontend/src/pages/Admin.js (autosave create form)
- frontend/src/pages/Home.js
- frontend/src/pages/JourneyDetail.js
- frontend/src/pages/Login.js
- frontend/src/contexts/AuthContext.js
- backend/server.py

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Refactoring: Dividir backend/server.py em modulos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
