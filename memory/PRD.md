# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto, MBWay, PayPal, Revolut, Wise
- **Email**: Resend (mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key
- **Object Storage**: Emergent Object Storage

## What's Been Implemented

### Melhorias Suporte V2 (2026-03-17)
1. CTA emocional nos emails de suporte (link para viagem principal ativa)
2. Stats dashboard no admin: 4 cards (Pedidos hoje, Em analise, A aguardar, Urgentes)
3. Templates de resposta rapida (4 templates predefinidos)
4. Estatisticas por tipo (ultimos 7 dias) com breakdown visual
5. Placeholder melhorado no formulario com orientacoes
6. Mensagem confirmacao mais humana apos envio

### Contador Tickets Abertos (2026-03-17)
- Badge na tab Suporte do admin + badge no dashboard do utilizador

### Sistema de Suporte Completo (2026-03-16)
- Area do utilizador: dashboard, criar pedido, detalhe com conversa
- Area do admin: lista com filtros, detalhe com acoes, notas internas
- 6 tipos de emails automaticos
- Upload de ficheiros via object storage
- IDs automaticos SUP-2026-XXXXX

### Autosave (2026-03-16)
- Dual-layer: localStorage + servidor MongoDB

### Funcionalidades Anteriores (2026-03-09)
- Preview de emails, formulario edicao viagens, sistema confianca, paginas legais

## Key Files
- frontend/src/components/AdminSupportSection.js
- frontend/src/components/SupportDashboard.js
- frontend/src/pages/SupportNewTicket.js
- frontend/src/pages/SupportTicketDetail.js
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
