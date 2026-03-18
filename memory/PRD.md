# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion + @paypal/react-paypal-js
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (collections: users, journeys, contributions, support_tickets, testimonials, drafts, offers, affiliate_clicks, travel_plans)
- **Payments**: PayPal Checkout (live), Crypto, MBWay, Revolut, Wise, Stripe
- **Email**: Resend (mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Object Storage**: Emergent Object Storage

## What's Been Implemented

### AI Travel Planner (2026-03-18)
- POST /api/ai/travel-plan (GPT-5.2, structured JSON response)
- Formulario: destino, datas, tipo viagem
- Resultados: roteiro dia-a-dia, clima, packing, checklist, dicas locais
- Cache em MongoDB (travel_plans), rate limit 5 req/hora/user
- Barra de afiliados nos resultados (Booking, Skyscanner, GetYourGuide, Airalo)

### Pagina Planear Viagem + Afiliados (2026-03-18)
- /plan-trip com 7 seccoes, links configuraveis centralizados, tracking cliques

### PayPal Live + Sistema Pagamentos (2026-03-18)
- PayPal Checkout SDK live, metodos manuais mantidos

### Conformidade RGPD (2026-03-18)
- Checkbox registo, politica privacidade, banner cookies

### Anteriores
- Consolidacao logica negocio, sistema senha, scroll fix, testemunhos, suporte, prova social, SEO, notificacoes, autosave

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /about, /dashboard, /admin, /login, /privacy, /terms

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%
- Substituir links placeholder por links de afiliado reais

### P2
- Completar refatoracao do backend (APIRouters)

### Backlog
- Sistema de gamificacao
- Notificacoes push/email

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend**: mail@4luis.com
- **PayPal**: Live (backend/.env)
