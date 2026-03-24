# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion + canvas-confetti + @paypal/react-paypal-js
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: PayPal Smart Buttons (live, with card option), MBWay (manual), Crypto (manual)
- **Auth**: JWT + Google OAuth
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key

## What's Been Implemented

### PayPal Smart Buttons + Payment Cleanup (2026-03-24)
- Replaced custom PayPal UI with official PayPal Smart Buttons (SDK @paypal/react-paypal-js)
- Added "Debit or Credit Card" option via enable-funding=card
- Removed Revolut and Wise from frontend and backend
- Kept: PayPal (primary/recommended), MBWay (manual), Crypto (optional)
- Backend valid_methods: ["crypto", "mbway", "paypal"]

### Differentiated Funding Celebration (2026-03-24)
- Main journey: funding >= 100% → pending_validation → admin approves → completed with confetti
- Ambassador journeys: auto-completed with confetti (no manual validation)
- CelebrationBanner component (completed/pending_validation variants)
- Admin panel: approve funding button for pending journeys

### Smart GYG Dynamic Link System (2026-03-21)
- buildGYGLink with destination + activity-based search
- GYG analytics script globally loaded (partner_id=WFPE9ME)

### P0 Mobile / P1 Hero / P2 SEO (2026-03-20)
- 44px touch targets, 60/65vh hero, responsive sticky bars
- CrowdDreaming copy, warm golden-hour curated images
- /api/plan/{slug}, /api/sitemap.xml, /plano/:slug with meta tags

### Affiliate Links, Growth Loop, Ambassador, AI Travel Planner
- All previously implemented and functional

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /plano/:slug, /about, /dashboard, /admin

## Prioritized Backlog
### P2
- Refatoracao backend server.py → APIRouters modulares (6800+ lines)
- Refatoracao frontend TravelPlanner.js → subcomponentes (1100+ lines)
### Backlog
- Payout tracking system (coleção payouts, admin UI)
- Geracao automatica de plano na viagem principal
- Sistema de gamificacao
- Smart Map e AI Assistant reais
- Open Graph images para planos publicos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **GYG Partner ID**: WFPE9ME
