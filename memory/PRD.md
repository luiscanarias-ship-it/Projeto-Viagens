# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariação de fundos para viagens solidárias com sistema de níveis (Sonhador → Embaixador), múltiplos métodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise (Stripe desativado)
- **Email**: Resend
- **Auth**: JWT + Google OAuth
- **QR Codes**: qrcode.react
- **Crypto Prices**: CoinGecko API

## User Personas
1. **Visitante**: Não registado, pode ver viagens e contribuir
2. **Sonhador**: Utilizador registado, pode criar links de referral
3. **Embaixador**: Sonhador que contribuiu + tem 3 referrals válidos
4. **Admin**: Gestão completa da plataforma (admin@4luis.com / Admin1)

## Core Requirements (Static)
- Sistema de progressão: Visitante → Sonhador → Embaixador
- 5 métodos de pagamento ativos (Crypto destacado com badge "TOP")
- Sistema de referência de pagamento (CN-XXXX)
- Checkout modal de 3 passos (Valor → Pagamento → Instruções)
- QR codes para todos os métodos de pagamento
- Conversão automática EUR → Crypto via CoinGecko

## What's Been Implemented

### Session 27/02/2026
- Homepage com branding "4Luis" e "CrowdDreaming" em coral
- Stripe Payment Element (código existe, desativado na UI)
- Sistema de referência de pagamento (CN-XXXX)

### Session 05/03/2026
- Checkout modal de 3 passos completo com QR codes
- Layout compacto do Step 3 (QR + dados lado a lado, sem scroll)
- Conversão de preços cripto via CoinGecko
- Todos os métodos de pagamento: Crypto, MBWay, Revolut, Wise, PayPal

## Prioritized Backlog

### P1 (High Priority)
- Estabilidade do Painel de Administração (testes pendentes)
- Melhorar formulário de edição de viagens no Admin

### P2 (Medium Priority)
- Sistema de pontos
- Sorteio real
- Notificações in-app

## Key Files
- `frontend/src/components/CheckoutModal.js` - Modal de checkout 3 passos
- `frontend/src/pages/JourneyDetail.js` - Página de viagem
- `frontend/src/pages/Admin.js` - Painel de administração
- `backend/server.py` - API FastAPI principal

## Credentials
- **Admin**: admin@4luis.com / Admin1
