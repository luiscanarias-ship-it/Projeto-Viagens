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

### Sistema de Senha no Registo (2026-03-18)
- Campos Senha + Confirmar senha com validacao em tempo real
- Indicador de forca (Fraca/Media/Forte) com barra visual
- Botao mostrar/ocultar senha
- Micro-copy informativo
- Icones apelativos em cada campo do formulario
- Botao bloqueado quando validacao falha

### Bug Fix: Scroll do Ticket de Suporte (2026-03-17)
- Corrigido scroll que levava ao final da conversa ao abrir ticket
- Scroll automatico para o fundo so ativa quando novas mensagens sao adicionadas

### Sistema de Testemunhos (2026-03-17)
- Fluxo completo: draft -> pending_auth -> authorized -> published
- Seccao "Sonhadores dizem" na homepage

### Melhorias Suporte V2 (2026-03-17)
- CTA emocional nos emails, stats dashboard admin, templates resposta rapida

### Momentos de Prova Social (2026-03-17)
- Homepage, pagina viagem, checkout, emails

### Pagina Sobre (2026-03-17)
- /about com estrutura narrativa

### Refatoracao Backend Parcial (2026-03-17)
- config.py, models.py, auth.py, email_service.py extraidos de server.py

### SEO e Meta Tags (2026-03-17)
- document.title dinamico + Open Graph

### Botao de Partilha + Notificacoes In-App (2026-03-17)
- Web Share API + fallback clipboard
- GET /api/notifications, bell no header, polling 30s

### Anteriores
- Autosave dual-layer, suporte completo, preview emails, sistema confianca, paginas legais

## Key Files
- frontend/src/pages/Login.js (sistema de senha melhorado)
- frontend/src/pages/SupportTicketDetail.js (scroll fix)
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
