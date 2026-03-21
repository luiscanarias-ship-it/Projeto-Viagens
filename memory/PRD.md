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

### Smart GYG Dynamic Link System (2026-03-21)
- buildGYGLink(destination, activityName?): generates ?q={query}&partner_id=WFPE9ME
- Destination-based fallback: ?q={destination}
- Activity-based: ?q={activity_name}+{destination} (e.g. ?q=teamlab%20tokyo)
- extractActivityName: strips Portuguese stopwords (visitar, ir a, conhecer, explorar, etc.)
- GYG_CURATED_EXPERIENCES: empty map, future-ready for exact URL mappings
- GYG analytics script loaded globally via index.html head (partner_id=WFPE9ME)
- Backend AFFILIATE_LINKS: GYG URL = https://www.getyourguide.com/s/ with affiliate_id=WFPE9ME
- All inline CTAs (InlineActivityCTA, TextWithCTA) generate activity-specific GYG links
- Click tracking remains fully functional

### P0 Mobile Optimization (2026-03-20)
- CSS touch targets: all buttons/links/inputs min-height 44px on touch devices
- Hero section: 60vh mobile / 65vh desktop, CTA visible without scrolling
- Search input + button: flex-col on mobile, flex-row on desktop
- Sticky bars: optimized padding/font for mobile (both Home and TravelPlanner)

### P1 Hero & Brand Clarity (2026-03-20)
- Opening question: "E se os sonhos pudessem ser financiados por todos?"
- Hero subtitle: "Uma plataforma onde qualquer pessoa pode financiar viagens de sonho — e onde tu também podes financiar a tua."
- Curated dreams images: warm golden-hour style (Pexels/Unsplash)

### P2 SEO Preparation (2026-03-20)
- GET /api/plan/{slug}, PATCH /api/plan/{slug}/visibility, GET /api/sitemap.xml
- Frontend: /plano/:slug with PublicPlan page + SEO meta tags
- Proper H1/H2 structure

### Affiliate Links Restructuring (2026-03-20)
- Centralized AFFILIATE_LINKS config with placeholder base URLs (except GYG which is now real)
- buildDynamicLinks appends ?destination=X&checkin=Y&checkout=Z to non-GYG links
- Click tracking active, affiliate_id preserved

### Growth Loop, Ambassador, CTA Copy, AI Travel Planner
- See previous PRD versions for full details

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /plano/:slug, /about, /dashboard, /admin

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
- Open Graph images para planos publicos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend**: mail@4luis.com
- **PayPal**: Live (backend/.env)
- **GYG Partner ID**: WFPE9ME
