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

### P0 Mobile Optimization (2026-03-20)
- CSS touch targets: all buttons/links/inputs min-height 44px on touch devices
- Hero section: 60vh mobile / 65vh desktop, CTA visible without scrolling
- Search input + button: flex-col on mobile, flex-row on desktop
- Sticky bars: optimized padding/font for mobile (both Home and TravelPlanner)
- Input font-size 16px on mobile to prevent iOS zoom
- Contribute CTA: full-width on mobile, auto on desktop

### P1 Hero & Brand Clarity (2026-03-20)
- Opening question preserved: "E se os sonhos pudessem ser financiados por todos?"
- Hero subtitle: "Uma plataforma onde qualquer pessoa pode financiar viagens de sonho — e onde tu também podes financiar a tua."
- Trust signals: flex-col on mobile (stacked), flex-row on desktop (inline)
- Text hierarchy: sm/base on mobile, xl/2xl on desktop
- Curated dreams images: warm golden-hour style (Pexels/Unsplash)

### P2 SEO Preparation (2026-03-20)
- Backend: GET /api/plan/{slug} serves public travel plans by slug
- Backend: PATCH /api/plan/{slug}/visibility toggles public/private
- Backend: GET /api/sitemap.xml generates XML sitemap with static pages + journeys + public plans
- Backend: travel_plans now include slug and is_public fields (auto-generated on creation)
- Frontend: New /plano/:slug route renders PublicPlan page with SEO meta tags
- Frontend: Proper H1/H2 structure (single H1, section H2s)

### Affiliate Links Restructuring (2026-03-20)
- Backend: AFFILIATE_LINKS centralized config with placeholder base URLs (BOOKING_LINK_HERE, SKYSCANNER_LINK_HERE, GETYOURGUIDE_LINK_HERE, AIRALO_LINK_HERE, etc.)
- Frontend: buildDynamicLinks appends ?destination=X&checkin=Y&checkout=Z to any base URL
- Click tracking (POST /api/affiliate-click) remains fully functional
- Easy replacement: only change base URLs in AFFILIATE_LINKS config, no frontend changes needed
- affiliate_id field preserved for each platform

### Growth Loop e Monetizacao (2026-03-20)
- Notificacoes: sistema completo com create_notification(), GET /api/notifications, POST /api/notifications/mark-read
- Ambassador value section: grid 2x2 com 4 features premium
- InlineReferralCTA: CTA de referral contextual apos geracao do guia

### Sistema Ambassador (2026-03-20)
- Backend: recalculate_ambassador_status() dinamico, 3 endpoints (progress, generate-referral, features)
- Anti-abuse: prevencao self-referral, validacao de contribuicoes confirmadas > 0EUR
- Frontend: AmbassadorProgress, PremiumGate com blur + lock overlay
- AMBASSADOR_REQUIRED_REFERRALS = 3

### Copy de Alta Conversao dos CTAs (2026-03-20)
- getCTACopy: copy dinamico com emojis, urgencia e destino para 5 tipos de CTA x 5 tipos de viagem

### AI Travel Planner (2026-03-18)
- POST /api/ai/travel-plan (GPT-5.2, structured JSON)
- POST /api/ai/travel-plan/refine
- Cache em MongoDB, rate limit 5 req/hora/user

### Anteriores
- PayPal Live, RGPD, Viagem Principal, Bug fixes, Sistema suporte, Prova social

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /plano/:slug, /about, /dashboard, /admin, /login, /privacy, /terms

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Completar refatoracao do backend (APIRouters)
- Refatoracao do frontend (TravelPlanner.js -> subcomponentes)

### Backlog
- Geracao automatica de plano na viagem principal
- Sistema de gamificacao
- Smart Map e AI Assistant reais (Google Maps/Mapbox)
- Notificacoes push/email
- Open Graph images para planos publicos (/plano/:slug)

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend**: mail@4luis.com
- **PayPal**: Live (backend/.env)
