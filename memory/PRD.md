# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion + @paypal/react-paypal-js
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (collections: users, journeys, contributions, support_tickets, testimonials, drafts, offers)
- **Payments**: PayPal Checkout (sandbox), Crypto, MBWay, Revolut, Wise, Stripe
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
- payment_method (paypal/mbway/revolut/wise/crypto)
- status (pending/confirmed/completed/failed/rejected)
- paypal_order_id (for PayPal), payment_reference (for manual), created_at

### Offers (admin only)
- offer_id (PK), user_id (FK), type (voucher/parceiro)
- description, status (pending/sent), created_at

## What's Been Implemented

### Sistema de Pagamentos Completo (2026-03-18)
- PayPal Checkout SDK: create-order, capture-order, confirmacao automatica
- Frontend: botao PayPal SDK no step 2, metodos manuais separados
- Backend: GET /api/paypal/config, POST /api/paypal/create-order, POST /api/paypal/capture-order/{id}
- Idempotencia no capture (evita duplicacao)
- Atualizacao automatica: contribution confirmed, journey.current_amount, user.total_contributed
- Progressao embaixador funciona com PayPal
- Notificacao + email enviados apos pagamento

### Consolidacao Logica de Negocio (2026-03-18)
- Campo total_contributed no User (modelo, registo, 3 pontos de confirmacao + PayPal)
- Migracao de 12 users existentes
- Tabela Offers com CRUD admin (GET, POST, PATCH, DELETE)

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

### PayPal
- GET /api/paypal/config (client_id + mode)
- POST /api/paypal/create-order {amount, journey_id}
- POST /api/paypal/capture-order/{order_id}

### Manual Contributions
- POST /api/contributions/create {amount, payment_method, journey_id}
- GET /api/contributions/payment-info

### Offers (Admin)
- GET /api/admin/offers
- POST /api/admin/offers
- PATCH /api/admin/offers/:id
- DELETE /api/admin/offers/:id

### Core
- GET /api/journeys, GET /api/journeys/:id
- GET /api/my-contributions
- POST /api/admin/contributions/:id/confirm
- POST /api/admin/contributions/:id/validate

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Completar refatoracao do backend (mover endpoints para APIRouters em backend/routes/)

### Backlog
- Sistema de gamificacao (pontos e sorteios)
- Mudar PayPal de sandbox para producao
- Notificacoes push/email

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
- **PayPal**: Sandbox mode (credentials in backend/.env)
