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

### MB WAY Simplified Screen (2026-03-25)
- Removed multi-step instructions, large warning box, hidden phone toggle
- Phone number (+351 XXX XXX XXX) now immediately visible with "Copiar número" button
- Reference shown inline below phone as secondary element
- Single instruction line: "Abre a app MB WAY e envia o valor"
- Single primary CTA: "Já enviei o pagamento"
- Secondary "Abrir MB WAY" link (discrete)
- Trust message: "Confirmação em poucos minutos"
- No scroll required — all fits in viewport

### Email Notifications for Contributions (2026-03-25)
- **Pending email**: Enviado quando user confirma que fez o pagamento (endpoint confirm-details)
  - Subject: "Pagamento de {amount}€ em validação - 4Luis"
  - Content: detalhes do pagamento, método, referência, mensagem de reassurance
- **Confirmed email**: Enviado quando admin valida a contribuição (endpoint validate)
  - Subject: "Já fazes parte deste sonho"
  - Content: confirmação, valor, social proof (contributors_count), progress bar, CTA "Convidar amigos" com referral code e remaining_referrals
- Templates mobile-friendly com brand colors (soft peach #FFBE98)
- Integração via Resend (já configurado)

### Copy Optimization (2026-03-25)
- Informal tone ("tu") applied consistently across all contribution flow
- Step 1: "Quanto queres contribuir?" + "100% seguro · Sem registo obrigatório"
- Step 2: "Como preferes pagar" + PayPal "Pagamento rápido e seguro" + MBWay "Leva menos de 30 segundos"
- Step 3: "Segue estes 3 passos simples" + "Usa exatamente este valor para validação automática"
- CTA: "Ajuda a realizar este sonho" + "Já contribuí para este sonho"
- Post-payment: "Já fazes parte deste sonho" + "Queres partilhar com amigos?"
- Trust microcopy: "100% seguro · Sem registo obrigatório · Confirmação em poucos minutos"

### Step 3 Payment Confirmation Redesign (2026-03-25)
- New "Quase lá!" header with progress indicator
- Payment summary (destination, amount, method)
- Numbered instructions dynamic by method (MBWay, Crypto)
- Critical reference block with "Copiar" button and feedback
- Warning message for exact value validation
- Collapsed optional details (phone hidden by default)
- "Já fiz o pagamento" → confirmation form (name optional, email required)
- PUT /api/contributions/{id}/confirm-details endpoint
- Social proof (contributor count, progress %)
- Ambassador motivation hook
- Trust footer with manual validation message
- Mobile optimized (min-height 44px buttons, vertical layout)

### PostHog Analytics Removed (2026-03-24)
- Removed PostHog session recording: conflicted with PayPal cross-origin iframes
- Was causing "Uncaught runtime errors" overlay blocking payment methods
- PostHog can be re-added later with `recordCrossOriginIframes: false` and `disable_session_recording: true`

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

### Smart Map Premium Feature (2026-03-25)
- **Backend**: 3 new endpoints: POST /api/ai/geocode-plan (Photon/Nominatim with MongoDB cache), POST /api/ai/optimize-route (GPT-5.2 route optimization), POST /api/ai/improve-location (per-location AI suggestions)
- **Frontend**: SmartMap.js component with Leaflet map, CartoDB light tiles, custom peach SVG markers grouped by day, route polylines, sidebar with click-to-center, day filters (Todos/Dia 1/Dia 2), "Otimizar percurso" AI button, per-location "Melhorar este ponto" (Menos filas, Mais barato, Melhor horário), "Aplicar ao roteiro"
- **Geocoding**: Photon (Komoot) primary + Nominatim fallback, Portuguese verb stripping for better results, MongoDB cache for performance, retry logic for rate limits
- **PremiumGate**: Shows "Desbloqueia o mapa interativo" for non-ambassadors
- **Lazy loaded**: React.lazy + Suspense for performance
- **Mobile**: Full-screen map with bottom sheet for locations
- **Special Pins** (2026-03-25): Airport (blue) and Hotel (orange) SVG pins geocoded from flight_info/hotel_info. Sidebar "Referências" section. Dashed polyline airport→hotel. Airport popup shows transport info. Hotel popup shows name/address/area.

### Travel Context Feature (2026-03-25)
- **Backend**: AI prompt updated to generate flight_info (outbound/return with flight_number, airports, times), hotel_info (name, address, area, phone), airport_to_hotel (best_option, alternative, tip)
- **Backend**: Refine endpoint preserves flight_info, hotel_info, airport_to_hotel from previous plan (merge after AI response)
- **Backend**: Geocode endpoint returns special_pins with airport and hotel lat/lng
- **Frontend**: TravelContext.js component showing flight cards (outbound in blue, return in amber), hotel card, and airport-to-hotel transport with best option + alternative
- **Frontend**: Integrated in TravelPlanner.js between header and tab navigation

### AI Assistant Premium Feature (2026-03-25)
- **Backend**: New endpoint POST /api/ai/assistant with ambassador-level gating (401 for unauth, 403 for non-ambassador)
- **Frontend**: AIAssistant component embedded in TravelPlanner inside PremiumGate
- **Quick Actions**: 4 suggestion buttons (cheaper, unique experiences, day distribution, weather)
- **Responses**: Structured JSON with bullet-point suggestions, actionable items, "Aplicar ao roteiro" button
- **Integration**: Uses existing GPT-5.2 via emergentintegrations, connects to existing refine endpoint for applying suggestions
- **PremiumGate**: Shows "Desbloqueia o assistente completo" for non-ambassadors with blur overlay

### Referral/Ambassador System Optimization (2026-03-25)
- **PaymentSuccess redesign**: Added referral CTA with WhatsApp button, ambassador progress bar, unlock preview, and register CTA for non-logged users
- **Messaging consistency**: Replaced all generic "Partilhar"/"Copiar link" with action-oriented "Convidar amigos"/"Copiar convite" across Dashboard, ShareMenu, AmbassadorProgress, CheckoutModal
- **Dashboard labels**: "Referrals válidos" → "Amigos que contribuiram", dynamic slot numbering ("Convida o 1o amigo")
- **ShareMenu header**: "Partilhar via" → "Convidar via"
- **WhatsApp primary CTA**: Direct WhatsApp share button with pre-filled message including referral link in PaymentSuccess and AmbassadorProgress

### Active Navigation Highlight (2026-03-25)
- Desktop: active link gets text-[#FFBE98] + subtle 2px underline using `useLocation`
- Mobile: active link gets text-[#FFBE98] + left border accent
- Applies to: Home, Planear Viagem, Meu Painel, Administração
- "Viagem Principal" button keeps its own permanent peach style
- "Explorar Viagens" keeps neutral style (scroll-only, no distinct route)

### Shareable Public Plans (2026-03-25)
- **Backend**: GET /api/plan/{slug} returns full public plan data. GET /api/og-image/{slug} generates dynamic 1200x630 PNG using PIL (gradient peach→dark, destination, duration, summary, branding). POST /api/ai/travel-plan returns slug in response. PATCH /api/plan/{slug}/visibility for toggling.
- **Frontend**: PublicPlan.js — full overhaul with hero (destination, duration, summary), share bar (WhatsApp, Copy link, Web Share API), map preview teaser (gated for ambassadors), weather, packing, itinerary, checklist, local tips (limited to 3 + lock message). CTAs: "Criar o meu roteiro com IA" and "Contribuir para esta viagem" (conditional on journey_id). OG image URL set dynamically.
- **SEO**: Updated SEO.js to support og:image, og:type, twitter:card, twitter:image. All meta tags set dynamically per page.
- **Sitemap**: /api/sitemap.xml includes all public plan URLs.
- **Share flow**: TravelPlanner.js now shows public link after generation, handleShare uses slug URL instead of plain text.

### Contextual AI - Exploration Mode (2026-03-25)
- **Backend**: POST /api/ai/improve-location supports 6 interaction types: what_to_see, where_to_eat, how_to_next (exploration) + less_queues, cheaper, best_time (optimization)
- **Frontend**: SmartMap pin popup now shows 2 sections: "Explorar:" (O que ver aqui, Onde comer, Como chegar ao proximo) and "Otimizar:" (Menos filas, Mais barato, Melhor horario)
- **Integration**: Clicking any button triggers AI call, results displayed in overlay with "Aplicar ao roteiro" option
- **Citymapper-inspired**: "Como chegar ao proximo" provides simple transport comparison (time + mode)

## Prioritized Backlog
### P1
- Celebracao "Sonho 100% Financiado": UI especial/animacao quando viagem atinge 100%
### P2
- Ativar IfthenPay quando credenciais forem fornecidas
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
