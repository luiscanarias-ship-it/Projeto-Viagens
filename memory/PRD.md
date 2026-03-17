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
- **Object Storage**: Emergent Object Storage (uploads de ficheiros)

## What's Been Implemented

### Contador de Tickets Abertos (2026-03-17)
- Admin: badge numerico na tab "Suporte" com total de tickets abertos
- Dashboard: badge "X abertos" ao lado do titulo "Ajuda e Suporte" com tickets do utilizador

### Sistema de Suporte Completo (2026-03-16)
**Area do Utilizador:**
- Seccao "Ajuda e Suporte" no dashboard com lista de pedidos e botao "Abrir novo pedido"
- Formulario de criacao: nome/email auto-preenchidos, tipo (8 opcoes), assunto, descricao, upload opcional
- Pagina de detalhe com visual de conversa (chat-like), campo de resposta, suporte a anexos
- IDs automaticos: SUP-2026-XXXXX

**Area do Admin:**
- Tab "Suporte" no painel admin com tabela completa
- Filtros por estado, tipo, prioridade + pesquisa por ID/email/assunto
- Detalhe com conversa, resposta admin, alterar estado/prioridade, notas internas
- Botoes rapidos "Marcar como resolvido" e "Fechar pedido"

**Estados:** Aberto, Em analise, A aguardar resposta, Resolvido, Fechado
**Prioridades:** Baixa, Media, Alta, Urgente (auto-atribuidas por tipo)
**Emails automaticos:** Confirmacao, resposta admin, alteracao estado, resolvido, fechado, notificacao admin
**Uploads:** Object storage Emergent (png, jpg, webp, pdf, max 5MB)

### Autosave com Sincronizacao no Servidor (2026-03-16)
- Dual-layer: localStorage + servidor MongoDB
- Recuperacao de rascunhos do servidor (multi-dispositivo)

### Preview de Emails antes de Enviar (2026-03-09)
- Modal de preview com confirmacao antes de envio

### Formulario de Edicao de Viagens no Admin (2026-03-09)
- 4 tabs, preview em tempo real, geracao IA de storytelling

### Sistema de Confianca (2026-03-09)
- 3 niveis: Sonhador, Sonhador Verificado, Embaixador

### Paginas Legais, Homepage, Checkout, Emails (anteriores)

## Key Files
- frontend/src/components/SupportDashboard.js
- frontend/src/pages/SupportNewTicket.js
- frontend/src/pages/SupportTicketDetail.js
- frontend/src/components/AdminSupportSection.js
- frontend/src/components/JourneyEditForm.js
- frontend/src/pages/Admin.js
- frontend/src/pages/Dashboard.js
- backend/server.py

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Sistema de pontos e sorteios
- Notificacoes in-app
- Refactoring: Dividir backend/server.py em modulos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
