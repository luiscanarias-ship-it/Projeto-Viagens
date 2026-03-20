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

### AI Travel Planner (2026-03-18, melhorado 2026-03-19)
- POST /api/ai/travel-plan (GPT-5.2, structured JSON response, aceita trip_type string ou array)
- POST /api/ai/travel-plan/refine (ajustar plano com feedback do utilizador)
- Multi-select tipo de viagem (Cultural, Aventura, Passeio, Gastronomica, Romantica, Familia)
- Documento unificado com tabs: Guia (clima+packing+booking), Roteiro, Checklist, Dicas
- Seccoes ocultaveis com persistencia em localStorage
- Funcionalidade "Ajustar plano": input inline para refinamento iterativo
- Botoes: Copiar para clipboard, Partilhar (Web Share API)
- CTAs contextuais entre seccoes (Booking, Skyscanner, Airalo, GetYourGuide)
- Seccao de Booking melhorada com 4 items, tags e descricoes
- Barra sticky no fundo (Hoteis, Voos, Atividades) visivel ao scrollar
- Cache em MongoDB (travel_plans), rate limit 5 req/hora/user
- Responsivo em mobile (375px+)
- Monetizacao contextual: TopBookingBar no header, InlineActivityCTA no itinerario (detecao keywords), ContextualCTA entre seccoes, eSIM CTA no checklist tech, booking hints nas dicas, tracking de cliques via POST /api/affiliate-click (2026-03-19)

### Pagina Planear Viagem + Afiliados (2026-03-18, melhorado 2026-03-18)
- /plan-trip com 7 seccoes reordenadas (Hotels>Flights>Activities>Cars>eSIM>Insurance>Map)
- Integracao AI Planner no topo com CTA destacado
- Links configuraveis centralizados, tracking cliques
- Textos corrigidos para portugues europeu com acentos

### PayPal Live + Sistema Pagamentos (2026-03-18)
- PayPal Checkout SDK live, metodos manuais mantidos

### Conformidade RGPD (2026-03-18)
- Checkbox registo, politica privacidade, banner cookies

### Pagina Viagem Principal (2026-03-19)
- Removidas seccoes legacy: Bing Maps, Onde Ficar, Voos e Transportes, O Que Dizem nas Redes
- Adicionado CTA "Planeie esta viagem com IA" que liga ao AI Travel Planner com destino pre-preenchido
- Mantidas seccoes de contribuicao intactas (apoiantes, testemunhos, checkout modal, sticky bar)
- Limpeza de imports e estado nao utilizado

### Melhorias Tecnicas de Estabilidade (2026-03-19)
- Models: Adicionado updated_at a User e Contribution, criado modelo TravelPlan
- AI: Logging de requests, timeout 45s com asyncio.wait_for, mensagens amigaveis, race condition corrigida
- Seguranca: Validacao de inputs (destino max 200 chars, formato de data, limites de trip_type)
- Consistencia frontend: botoes unificados com btn-primary

### Bug Fix: Scroll SupportTicketDetail (2026-03-19)
- Corrigido bug recorrente de scroll na pagina de detalhes do ticket de suporte
- Implementado useLayoutEffect para scroll sincrono antes do paint

### Restauração da Identidade Visual (2026-03-20)
- Revertido #E67E22 (laranja agressivo) para #FFBE98 (soft peach) em TravelPlanner.js, Header.js e index.css
- Background restaurado para #FAFAF9, borders para stone-100/stone-200
- Sticky bar: 3 botões iguais (bg-[#2D2A26]), sem pulse/ênfase
- Melhorias estruturais mantidas: hover lift (-translate-y-0.5) + shadow em CTAs
- CTAs primários usam bg-[#2D2A26] (escuro, não peach) para melhor contraste
- Zero referências #E67E22, #FFF6ED ou #F5E6DA restantes

### Melhoria Visual dos CTAs de Afiliados (2026-03-20)
- Cor de marca reforçada: #E67E22 (hover #D35400) substituiu #FFBE98 pálido nos CTAs
- CTAs inline convertidos em soft-buttons com fundo beige (#FFF6ED), padding, border-radius
- Hover effects: translateY(-2px), shadow intensificado, cor mais forte
- Ícones aumentados 10-15%, cor de marca #E67E22
- Enfase seletivo: CTAs primários (trust=true) com estilo forte + label "Recomendado pela 4Luis", secundários discretos
- StickyBar: botão booking com pulse animation, outros botões secondary style
- Design system peach completo: bg #FFF6ED, borders #F5E6DA, primary #E67E22
- Consistência total: Header.js, index.css e TravelPlanner.js unificados no mesmo design system
- Zero referências #FFBE98 restantes

### Anteriores
- Consolidacao logica negocio, sistema senha, scroll fix, testemunhos, suporte, prova social, SEO, notificacoes, autosave

## Key Pages
- / (Home), /journey/:id, /plan-trip, /travel-planner, /about, /dashboard, /admin, /login, /privacy, /terms

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
- **Resend**: mail@4luis.com
- **PayPal**: Live (backend/.env)
