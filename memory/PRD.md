# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (collections: users, journeys, contributions, support_tickets, testimonials, drafts)
- **Payments**: Crypto, MBWay, PayPal, Revolut, Wise
- **Email**: Resend (mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key
- **Object Storage**: Emergent Object Storage

## What's Been Implemented

### Bug Fix: Scroll do Ticket de Suporte (2026-03-17)
- Corrigido scroll que levava ao final da conversa ao abrir ticket
- Agora a pagina abre no topo, mostrando header e inicio da conversa
- Scroll automatico para o fundo so ativa quando novas mensagens sao adicionadas

### Sistema de Testemunhos (2026-03-17)
- Admin marca tickets resolvidos como potenciais testemunhos
- Editor inline de texto curto no detalhe do ticket
- Email de autorizacao ao utilizador com botoes Autorizar/Nao autorizar
- Pagina de resultado da autorizacao (/testimonial/result)
- Fluxo completo: draft -> pending_auth -> authorized -> published
- Gestao na lista de suporte (Pedir autorizacao, Publicar, Apagar)
- Seccao "Sonhadores dizem" na homepage (cards com quote, nome, badge)
- Testemunhos compactos na sidebar da pagina da viagem
- Endpoint publico /api/testimonials/published (sem dados sensiveis)

### Melhorias Suporte V2 (2026-03-17)
- CTA emocional nos emails (link viagem principal)
- Stats dashboard admin (4 cards: hoje, em analise, aguardar, urgentes)
- Templates resposta rapida (4 predefinidos)
- Estatisticas por tipo (ultimos 7 dias)
- Placeholder melhorado no formulario
- Mensagem confirmacao mais humana

### Contador Tickets + Sistema Suporte Completo (2026-03-16/17)
- Suporte completo com area utilizador e admin
- 8 tipos de pedido, 5 estados, 4 prioridades
- 6 tipos de emails automaticos
- Upload ficheiros via object storage
- IDs automaticos SUP-2026-XXXXX

### Autosave (2026-03-16)
- Dual-layer: localStorage + servidor MongoDB

### Anteriores (2026-03-09)
- Preview emails, formulario edicao viagens, sistema confianca, paginas legais

### Momentos de Prova Social (2026-03-17)
- Homepage, pagina viagem, checkout, emails

### Pagina Sobre (2026-03-17)
- /about com estrutura narrativa

### Refatoracao Backend Parcial (2026-03-17)
- config.py, models.py, auth.py, email_service.py extraidos de server.py

### SEO e Meta Tags (2026-03-17)
- document.title dinamico + Open Graph

### Botao de Partilha (2026-03-17)
- Web Share API + fallback clipboard

### Notificacoes In-App (2026-03-17)
- GET /api/notifications, bell no header, polling 30s

## Key Files
- frontend/src/pages/SupportTicketDetail.js (corrigido scroll)
- frontend/src/components/SupportDashboard.js
- frontend/src/pages/Dashboard.js
- frontend/src/pages/Home.js
- frontend/src/components/Header.js
- backend/server.py
- backend/config.py, models.py, auth.py, email_service.py

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Completar refatoracao do backend (mover endpoints para APIRouters em backend/routes/)
- Sistema de pontos e sorteios
- Notificacoes push/email (extensao das in-app)

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
