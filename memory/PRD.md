# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariação de fundos para viagens solidárias com sistema de níveis (Sonhador → Embaixador), múltiplos métodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Stripe Payment Element (inline), Crypto, MBWay, PayPal, Revolut, Wise
- **Email**: Resend
- **Auth**: JWT + Google OAuth

## User Personas
1. **Visitante**: Não registado, pode ver viagens e contribuir
2. **Sonhador**: Utilizador registado, pode criar links de referral
3. **Embaixador**: Sonhador que contribuiu + tem 3 referrals válidos, pode criar viagens próprias
4. **Admin**: Gestão completa da plataforma

## Core Requirements (Static)
- Sistema de progressão: Visitante → Sonhador → Embaixador
- 6 métodos de pagamento (Crypto destacado, Stripe automático)
- Sistema de candidaturas de embaixadores
- Gestão de visibilidade de viagens
- Emails comportamentais

## What's Been Implemented

### Session 27/02/2026
- ✅ Restauração do projeto do GitHub
- ✅ Homepage: Frase "Aqui, cada gesto ilumina um caminho" - mesma cor/fonte do "4Luis", bold
- ✅ Homepage: Texto alterado para "A plataforma de CrowdDreaming..."
- ✅ "CrowdDreaming" destacado em coral em toda a plataforma
- ✅ Botão "Apoiar esta viagem" abre diretamente modal de pagamento
- ✅ **Stripe Payment Element integrado (inline, sem redirect)**
  - Backend: PaymentIntent via `/api/contributions/create`
  - Frontend: `StripePaymentForm.js` com Payment Element
  - Webhook atualizado para `payment_intent.succeeded`
  - Suporta Card, Bancontact, Amazon Pay, EPS

## Prioritized Backlog

### P0 (Critical)
- Nenhum item pendente

### P1 (High Priority)
- Testar fluxo completo de pagamento com cartão de teste
- Adicionar tratamento de erro 3D Secure

### P2 (Medium Priority)
- Sistema de pontos (estrutura existe)
- Sorteio real
- Notificações in-app

## Next Tasks
1. Testar pagamento end-to-end com cartão teste Stripe
2. Configurar webhook em produção
3. Adicionar mais métodos de pagamento locais (se necessário)

## API Keys Required
- STRIPE_API_KEY (Secret Key)
- STRIPE_PUBLISHABLE_KEY 
- RESEND_API_KEY (para emails)
