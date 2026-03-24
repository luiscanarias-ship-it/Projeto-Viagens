# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion + canvas-confetti + @paypal/react-paypal-js
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: PayPal Checkout (live), Stripe, Crypto, MBWay, Revolut, Wise
- **Auth**: JWT + Google OAuth
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key

## What's Been Implemented

### Differentiated Funding Celebration (2026-03-24)
- **Main journey (is_main_trip=true)**: When funding >= 100%, sets `funding_status = "pending_validation"`, notifies admin, keeps accepting contributions. Admin approves via `POST /api/admin/journey/{id}/approve-funding` → sets `funding_status = "completed"`, activates confetti celebration.
- **Ambassador journeys (is_ambassador_journey=true)**: Auto-completes to `funding_status = "completed"` with confetti, no manual validation needed.
- **CelebrationBanner component**: `variant="completed"` (confetti + trophy + gold banner) and `variant="pending_validation"` (amber banner "a aguardar confirmação").
- **FundedBadge / PendingBadge**: Inline badges for progress display.
- **Admin panel**: "Aguarda validação" badge + "Aprovar" button for pending journeys.
- **Progress API**: Returns `funding_status`, `is_main_trip`, `is_ambassador_journey`.
- **Home.js**: Differentiated text per status (completed/pending/active).

### Smart GYG Dynamic Link System (2026-03-21)
- buildGYGLink(destination, activityName?): ?q={query}&partner_id=WFPE9ME
- extractActivityName strips Portuguese stopwords
- GYG_CURATED_EXPERIENCES map (future-ready)
- GYG analytics script globally loaded

### P0 Mobile Optimization (2026-03-20)
- 44px touch targets, 60/65vh hero, responsive sticky bars, iOS zoom prevention

### P1 Hero & Brand (2026-03-20)
- CrowdDreaming copy, warm golden-hour curated images

### P2 SEO (2026-03-20)
- /api/plan/{slug}, /api/sitemap.xml, /plano/:slug with meta tags

### Affiliate Links (2026-03-20)
- Centralized AFFILIATE_LINKS, placeholders for non-GYG, click tracking active

### Growth Loop, Ambassador, CTA Copy, AI Travel Planner
- All previously implemented and functional

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /plano/:slug, /about, /dashboard, /admin

## Prioritized Backlog
### P2
- Refatoracao backend server.py → APIRouters modulares (6800+ lines)
- Refatoracao frontend TravelPlanner.js → subcomponentes (1100+ lines)
### Backlog
- Geracao automatica de plano na viagem principal
- Sistema de gamificacao
- Smart Map e AI Assistant reais
- Open Graph images para planos publicos
- Notificacoes push/email

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **GYG Partner ID**: WFPE9ME
