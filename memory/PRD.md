# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB (collections: users, journeys, contributions, support_tickets, testimonials, drafts)
- **Payments**: Crypto, MBWay, PayPal, Revolut, Wise
- **Email**: Resend (mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key
- **Object Storage**: Emergent Object Storage

## What's Been Implemented

### Sistema de Testemunhos (2026-03-17)
- Admin marca tickets resolvidos como potenciais testemunhos
- Editor inline de texto curto no detalhe do ticket
- Email de autorizacao ao utilizador com botoes Autorizar/Nao autorizar
- Pagina de resultado da autorizacao (/testimonial/result)
- Fluxo completo: draft -> pending_auth -> authorized -> published
- Gestao na lista de suporte (Pedir autorizacao, Publicar, Apagar)
- Seccao "Sonhadores dizem" na homepage (cards com quote, nome, badge)
- Testemunhos compactos na sidebar da pagina da viagem
- Endpoint publico /api/testimonials/published (sem dados sensiveis)

### Melhorias Suporte V2 (2026-03-17)
- CTA emocional nos emails (link viagem principal)
- Stats dashboard admin (4 cards: hoje, em analise, aguardar, urgentes)
- Templates resposta rapida (4 predefinidos)
- Estatisticas por tipo (ultimos 7 dias)
- Placeholder melhorado no formulario
- Mensagem confirmacao mais humana

### Contador Tickets + Sistema Suporte Completo (2026-03-16/17)
- Suporte completo com area utilizador e admin
- 8 tipos de pedido, 5 estados, 4 prioridades
- 6 tipos de emails automaticos
- Upload ficheiros via object storage
- IDs automaticos SUP-2026-XXXXX

### Autosave (2026-03-16)
- Dual-layer: localStorage + servidor MongoDB

### Anteriores (2026-03-09)
- Preview emails, formulario edicao viagens, sistema confianca, paginas legais

## Key Files
- frontend/src/components/TestimonialsSection.js (publico)
- frontend/src/components/AdminSupportSection.js (admin + testemunhos)
- frontend/src/pages/TestimonialResult.js
- frontend/src/pages/SupportNewTicket.js
- frontend/src/pages/SupportTicketDetail.js
- frontend/src/pages/Home.js
- frontend/src/pages/JourneyDetail.js
- frontend/src/pages/Admin.js
- backend/server.py

## Key API Endpoints (Testimonials)
- POST /api/admin/support/tickets/{id}/testimonial — criar draft
- PUT /api/admin/testimonials/{id} — editar texto
- POST /api/admin/testimonials/{id}/request-auth — pedir autorizacao
- GET /api/testimonials/authorize/{token} — autorizar (publico)
- GET /api/testimonials/reject/{token} — rejeitar (publico)
- POST /api/admin/testimonials/{id}/publish — publicar
- GET /api/testimonials/published — listar publicados (publico)
- GET /api/admin/testimonials — listar todos (admin)
- DELETE /api/admin/testimonials/{id} — apagar

### Destaque Botao Viagem Principal (2026-03-17)
- Botao "Viagem Principal" na homepage redesenhado com maior destaque visual
- Tamanho aumentado, texto uppercase, borda dourada, glow exterior, hover com escala

### Momentos de Prova Social (2026-03-17)
- Homepage: Linha discreta "Mais de X sonhadores já contribuíram" abaixo do botão Contribuir (contador = contribuidores reais + 57)
- Página da viagem: Contexto social "Este sonho já está a ganhar forma" junto à barra de progresso com contador
- Checkout: Micro-testemunho "Contribuí em menos de 1 minuto — João" no passo de pagamento
- Pós-contribuição: Mensagem melhorada "Acabaste de ajudar este sonho a ganhar forma" + CTA partilha
- Emails: Bloco CTA emocional "Nunca deixes de sonhar, sonha connosco" + botão no footer de todos os emails
- Backend: Endpoints /homepage/main-journey e /journeys/{id}/progress incluem contributor_count e journey_contributor_count

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Sistema de pontos e sorteios
- Notificacoes in-app
- Refactoring: Dividir backend/server.py em modulos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
