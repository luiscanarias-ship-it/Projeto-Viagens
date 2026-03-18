# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (collections: users, journeys, contributions, support_tickets, testimonials, drafts, offers)
- **Payments**: Crypto, MBWay, PayPal, Revolut, Wise, Stripe
- **Email**: Resend (mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key
- **Object Storage**: Emergent Object Storage

## DB Schema

### Users
- user_id (PK), email (unique), password_hash, is_admin (role), name, surname
- total_contributed (default 0, updated on contribution confirm)
- level (sonhador/embaixador), sponsor_id, valid_referrals_count
- contributed_to_main_trip, created_at, registered_at

### Journeys
- journey_id (PK), name, description, goal_amount, current_amount (default 0)
- status (ativa/completed), target_date, is_active, is_main_trip, created_at

### Contributions
- contribution_id (PK), user_id (FK), journey_id (FK), amount
- payment_method, status (pending/confirmed/completed/rejected), created_at

### Offers (admin only)
- offer_id (PK), user_id (FK), type (voucher/parceiro)
- description, status (pending/sent), created_at

## What's Been Implemented

### Consolidacao Logica de Negocio (2026-03-18)
- Campo total_contributed no User (modelo, registo, 3 pontos de confirmacao)
- Migracao de 12 users existentes
- Tabela Offers com CRUD admin (GET, POST, PATCH, DELETE)
- Logica automatica: contribuicao confirmada -> atualiza journey + user atomicamente

### Sistema de Senha no Registo (2026-03-18)
- Campos Senha + Confirmar senha com validacao em tempo real
- Indicador de forca, botao mostrar/ocultar, micro-copy

### Bug Fix: Scroll do Ticket de Suporte (2026-03-17)
- Corrigido scroll que levava ao final da conversa ao abrir ticket

### Anteriores (2026-03-17 e antes)
- Sistema de testemunhos, melhorias suporte V2, momentos de prova social
- Pagina sobre, refatoracao backend parcial, SEO e meta tags
- Botao de partilha, notificacoes in-app, autosave dual-layer
- Suporte completo, preview emails, sistema confianca, paginas legais

## Key API Endpoints

### Offers (Admin)
- GET /api/admin/offers?status=&user_id=
- POST /api/admin/offers {user_id, type, description}
- PATCH /api/admin/offers/:id {status}
- DELETE /api/admin/offers/:id

### Core (existentes)
- GET /api/journeys, GET /api/journeys/:id
- POST /api/contributions, GET /api/my-contributions
- POST /api/admin/contributions/:id/confirm
- POST /api/admin/contributions/:id/validate

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Completar refatoracao do backend (mover endpoints para APIRouters em backend/routes/)

### Backlog
- Sistema de gamificacao (pontos e sorteios)
- Integracao PayPal
- Sistema de ofertas automatico
- Notificacoes push/email

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
