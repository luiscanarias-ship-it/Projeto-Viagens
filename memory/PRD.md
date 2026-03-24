# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion + canvas-confetti + @paypal/react-paypal-js
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: PayPal Smart Buttons (live, with card/Apple Pay/Google Pay), MBWay (manual), Crypto (manual)
- **Auth**: JWT + Google OAuth
- **AI**: OpenAI GPT-5.2 via Emergent LLM Key
- **Geolocation**: ipapi.co (free, 30k req/month)

## What's Been Implemented

### MB WAY Manual UX Improvement (2026-03-24)
- Phone number hidden by default behind "Mostrar detalhes de envio" toggle
- Copy reference button with "Copiar"/"Copiado!" feedback
- Clear 3-step instructions (numbered)
- "Abrir MBWay" deep link for mobile
- Bug fixed: backend was rejecting mbway as payment method (added to valid_methods)

### Payouts System for Ambassadors (2026-03-24)
- New `payouts` collection in MongoDB
- Auto-creation of payout record when ambassador journey reaches 100% funding
- Admin endpoints: GET /api/admin/payouts, PUT /api/admin/payouts/{payout_id}/status
- Admin UI: new "Payouts" tab with summary cards, status filters, edit/process actions
- Ambassador notification when payout is marked as completed

### Geo-Prioritized Payment Methods (2026-03-24)
- Smart payment prioritization based on user location (ipapi.co)
- **Portugal (PT)**: MBWay primary -> PayPal+Card secondary -> Crypto -> Multibanco ("Em breve")
- **International**: PayPal+Card primary -> Crypto + MBWay secondary
- IfthenPay config prepared with placeholders (enabled: false)
- Removed Revolut and Wise from all flows

### PayPal Smart Buttons (2026-03-24)
- Official SDK @paypal/react-paypal-js with vertical layout
- "Pay with PayPal" + "Debit or Credit Card" buttons

### Differentiated Funding Celebration (2026-03-24)
- Main journey: pending_validation -> admin approves -> completed with confetti
- Ambassador journeys: auto-completed with confetti

### Smart GYG Links, Mobile, Hero, SEO, Affiliate Links, Ambassador System
- All previously implemented and functional

## Active Payment Methods
| Method | Type | Status |
|---|---|---|
| PayPal (+ Card, Apple Pay, Google Pay) | Automatic | ACTIVE (live) |
| MBWay | Manual (admin confirms) | ACTIVE |
| Crypto (BTC, ETH, USDT, USDC) | Manual (admin confirms) | ACTIVE |
| Multibanco (IfthenPay) | Automatic | PREPARED (not yet active) |
| MBWay (IfthenPay) | Automatic | PREPARED (not yet active) |

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /plano/:slug, /about, /dashboard, /admin

## Prioritized Backlog
### P1
- Celebracao "Sonho 100% Financiado": UI especial/animacao quando viagem atinge 100%
### P2
- Ativar IfthenPay quando credenciais forem fornecidas
- Smart Map e AI Assistant reais (substituir placeholders)
- Refatoracao backend server.py -> APIRouters modulares
- Refatoracao frontend TravelPlanner.js -> subcomponentes
### Backlog
- Geracao automatica de plano na viagem principal
- Sistema de gamificacao
- Notificacoes push/email automaticas
- Open Graph images para planos publicos
- SEO: meta description, favicon, og:image
- Consistencias de dados (viagens duplicadas, endpoint /api/health)

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **GYG Partner ID**: WFPE9ME
