# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion + @paypal/react-paypal-js
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (collections: users, journeys, contributions, support_tickets, testimonials, drafts, offers, affiliate_clicks)
- **Payments**: PayPal Checkout (live), Crypto, MBWay, Revolut, Wise, Stripe
- **Email**: Resend (mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key
- **Object Storage**: Emergent Object Storage

## What's Been Implemented

### Pagina Planear Viagem + Afiliados (2026-03-18)
- Pagina /plan-trip com 7 seccoes (Voos, Alojamento, Atividades, Transporte, eSIM, Seguro, Mapa)
- Links afiliados configuraveis centralizados no backend (AFFILIATE_LINKS dict)
- Tracking de cliques: POST /api/affiliate-click + GET /api/admin/affiliate-stats
- Navegacao: link no header desktop e mobile

### Conformidade RGPD (2026-03-18)
- Checkbox obrigatorio no registo com link para politica
- Politica de Privacidade atualizada (PayPal, afiliados, cookies)
- Banner de cookies com mensagem completa

### Elementos de Confianca no Checkout (2026-03-18)
- Badge "Recomendado" + "Pagamento seguro" + "Nao partilhamos os teus dados bancarios"

### PayPal Live (2026-03-18)
- Credenciais live configuradas, ordens reais criadas com sucesso

### Sistema de Pagamentos (2026-03-18)
- PayPal Checkout SDK: create-order, capture-order, confirmacao automatica
- Metodos manuais mantidos: MBWay, Revolut, Wise, Crypto

### Consolidacao Logica de Negocio (2026-03-18)
- Campo total_contributed no User + Tabela Offers CRUD admin

### Sistema de Senha no Registo (2026-03-18)
- Confirmar senha, indicador forca, mostrar/ocultar

### Bug Fix: Scroll Ticket (2026-03-17)
- Corrigido scroll ao abrir ticket de suporte

### Anteriores
- Testemunhos, suporte V2, prova social, pagina sobre, refatoracao parcial, SEO, partilha, notificacoes, autosave

## Key API Endpoints

### Affiliates
- GET /api/affiliate-links (public, returns all links config)
- POST /api/affiliate-click {platform} (tracks click)
- GET /api/admin/affiliate-stats (admin analytics)

### PayPal
- GET /api/paypal/config
- POST /api/paypal/create-order
- POST /api/paypal/capture-order/{order_id}

### Offers (Admin)
- CRUD: GET/POST /api/admin/offers, PATCH/DELETE /api/admin/offers/:id

## Affiliate Links (Placeholder — to replace)
- skyscanner: https://www.skyscanner.pt
- booking: https://www.booking.com
- hotels: https://www.hotels.com
- getyourguide: https://www.getyourguide.com
- cars: https://www.discovercars.com
- airalo: https://www.airalo.com
- holafly: https://www.holafly.com
- insurance: https://www.iatiseguros.com
- googlemaps: https://maps.google.com

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
- **Resend sender**: mail@4luis.com
- **PayPal**: Live mode (credentials in backend/.env)
