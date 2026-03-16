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
- **Object Storage**: Emergent Object Storage (suporte a uploads de ficheiros)

## What's Been Implemented

### Sistema de Suporte Completo (2026-03-16)
**Area do Utilizador:**
- Seccao "Ajuda e Suporte" no dashboard com lista de pedidos e botao "Abrir novo pedido"
- Formulario de criacao: nome/email auto-preenchidos, tipo (8 opcoes), assunto, descricao, upload opcional
- Pagina de detalhe com visual de conversa (chat-like), campo de resposta, suporte a anexos
- IDs automaticos: SUP-2026-XXXXX

**Area do Admin:**
- Tab "Suporte" no painel admin com tabela completa (ID, utilizador, email, tipo, assunto, estado, prioridade, data)
- Filtros por estado, tipo, prioridade + pesquisa por ID/email/assunto
- Detalhe com conversa, resposta admin, alterar estado/prioridade, notas internas, download de anexos
- Botoes rapidos "Marcar como resolvido" e "Fechar pedido"

**Estados:** Aberto, Em analise, A aguardar resposta, Resolvido, Fechado
**Prioridades (admin only):** Baixa, Media, Alta, Urgente (auto-atribuidas por tipo)
**Emails automaticos:** Confirmacao, resposta admin, alteracao estado, resolvido, fechado, notificacao admin

**Uploads:** Object storage Emergent para screenshots/anexos (png, jpg, webp, pdf, max 5MB)

### Autosave com Sincronizacao no Servidor (2026-03-16)
- Dual-layer: localStorage + servidor MongoDB
- JourneyEditForm e Create Journey Form: autosave com debounce
- Recuperacao de rascunhos do servidor (multi-dispositivo)
- Indicador "Sincronizado" / "Guardado localmente"

### Correcao FRONTEND_URL (2026-03-16)
- FRONTEND_URL no backend agora le de variavel de ambiente

### Preview de Emails antes de Enviar (2026-03-09)
- Modal de preview com confirmacao antes de envio
- 3 endpoints de preview: resumo semanal, novo sonho, sonho financiado

### Formulario de Edicao de Viagens no Admin (2026-03-09)
- 4 tabs (Basico/Conteudo/Storytelling/Configuracoes), preview em tempo real

### Sistema de Confianca (2026-03-09)
- 3 niveis: Sonhador, Sonhador Verificado, Embaixador

### Paginas Legais (2026-03-09)
- Privacidade, Termos, Cookies

### Sistema de Emails (5 tipos + 6 suporte)
- Mudanca de capitulo, resumo semanal, contribuicao via referral, sonho financiado, novo sonho
- Suporte: confirmacao, resposta admin, alteracao estado, resolvido, fechado, notificacao admin

## Key Files
- frontend/src/components/SupportDashboard.js (seccao suporte no dashboard)
- frontend/src/pages/SupportNewTicket.js (formulario criacao)
- frontend/src/pages/SupportTicketDetail.js (detalhe com conversa)
- frontend/src/components/AdminSupportSection.js (gestao admin)
- frontend/src/components/JourneyEditForm.js (autosave)
- frontend/src/components/EmailPreviewModal.js
- frontend/src/pages/Admin.js
- frontend/src/pages/Dashboard.js
- backend/server.py

## Key API Endpoints (Support)
- POST /api/support/tickets — criar ticket
- GET /api/support/tickets — listar tickets do user
- GET /api/support/tickets/{id} — detalhe
- POST /api/support/tickets/{id}/reply — resposta do user
- POST /api/support/upload — upload ficheiro
- GET /api/admin/support/tickets — listar todos (com filtros)
- GET /api/admin/support/tickets/{id} — detalhe admin
- POST /api/admin/support/tickets/{id}/reply — resposta admin
- PUT /api/admin/support/tickets/{id}/status — alterar estado
- PUT /api/admin/support/tickets/{id}/priority — alterar prioridade
- POST /api/admin/support/tickets/{id}/note — nota interna

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
