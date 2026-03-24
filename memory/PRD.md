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

### Geo-Prioritized Payment Methods (2026-03-24)
- Smart payment prioritization based on user location (ipapi.co)
- **Portugal (PT)**: MBWay primary ("Recomendado") → PayPal+Card secondary → Crypto → Multibanco ("Em breve")
- **International**: PayPal+Card primary ("Recomendado") → Crypto + MBWay secondary
- Apple Pay / Google Pay via PayPal Smart Buttons (enable-funding=card)
- IfthenPay config prepared with placeholders (enabled: false) for MBWay + Multibanco integration
- Removed Revolut and Wise from all flows
- Geolocation cached per session, 3s timeout fallback

### PayPal Smart Buttons (2026-03-24)
- Official SDK @paypal/react-paypal-js with vertical layout
- "Pay with PayPal" + "Debit or Credit Card" buttons
- createPayPalOrder/onPayPalApprove extracted as reusable handlers

### Differentiated Funding Celebration (2026-03-24)
- Main journey: pending_validation → admin approves → completed with confetti
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
- Activate IfthenPay when keys are available (MBWay + Multibanco automatic)
### P2
- Payout tracking system (coleção payouts, admin UI)
- Refatoracao backend server.py → APIRouters modulares
- Refatoracao frontend TravelPlanner.js → subcomponentes
### Backlog
- Geracao automatica de plano na viagem principal
- Sistema de gamificacao
- Smart Map e AI Assistant reais
- Open Graph images para planos publicos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **GYG Partner ID**: WFPE9ME
