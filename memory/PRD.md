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

### Critical Bug Fixes — Travel Plan Credibility (2026-03-26)
- **Bug 1 FIXED**: Template plans showed fake flight numbers (TAP TP448) and hotel names (Hotel Le Marais) as real bookings → Now shows **search suggestions** with affiliate links ("Comparar voos", "Ver hotéis no centro")
- **Bug 2 FIXED**: Map showed pins in Netherlands/Normandy instead of Paris → Geocoding threshold reduced from 5° (~500km) to 1° (~111km), food/restaurant activities filtered from geocoding
- **Bug 3**: LLM credit waste prevented — all 10 template destinations use 0 AI credits
- **TravelContext.js**: Rewritten to handle both suggestion mode (templates) and legacy AI format (backward compatible)

### Bug Fixes — Itinerário, Mapa e Popups (2026-03-26)
- **Bug 1 FIXED**: Dias com 0-1 atividades → Reescrito `build_template_itinerary` com distribuição 1-por-categoria, tracking de atividades usadas (set), e fallback para day_trips/stay_zones. Mínimo 3 atividades por dia, zero repetições
- **Bug 2 FIXED**: Mapa mostrava 0-2 marcadores → Geocoding agora extrai nomes dos parênteses (ex: "Sultan Ahmed" de "Mesquita Azul (Sultan Ahmed — gratis)") como nome primário de geocodificação, com fallback triplo. Istanbul passou de 0 para 14 marcadores
- **Bug 3 FIXED**: Popup mostrava "Dia 3 — Ponto 8" → Agora mostra nome do monumento em bold + tema do dia
- **day_trips** adicionados a todos os 19 destinos para viagens 6+ dias (3 excursões por cidade)

### Expansão do Motor de Templates — 9 Novos Destinos (2026-03-26)
- **9 destinos adicionados**: Berlim, Madrid, Praga, Viena, Budapeste, Istambul, Florença, Dubai, Bali (total: 19 cidades)
- **Stay Zones**: Cada cidade tem 3-4 zonas recomendadas para ficar, com transportes públicos que ligam ao aeroporto e descrição do vibe
- **Must See**: Lista prioritária de monumentos/sítios adaptada ao número de dias (regra: ~2 por dia, mínimo 3)
- **Template Types**: 3 tipos reutilizáveis (european_city_break, beach_destination, long_haul_trip) como Layer 4 fallback antes da AI
- **Novas zonas meteorológicas**: desert (Dubai) e tropical (Bali) com packing lists específicos
- **Arquitetura**: Dados separados em `destination_data.py` (manutenibilidade), funções em `destination_templates.py`
- **Frontend**: TravelContext.js renderiza stay_zones (numbered cards) e must_see (2-column grid) com iconografia
- **Testado**: 100% pass rate iteração 84 (19 destinos backend + frontend UI)

### Multiple Airports Per City (2026-03-26)
- **Bug FIXED**: Platform only suggested one airport per city (e.g., Paris showed only CDG), losing credibility
- **Fix**: `destination_templates.py` now stores `airports` as an array per destination with ALL commercial airports (code, name, distance, transport info)
- **Airports by city**: Paris (CDG, ORY, BVA), Roma (FCO, CIA), Barcelona (BCN, GRO), Londres (LHR, LGW, STN, LTN, SEN), Amesterdão (AMS, EIN), Tóquio (NRT, HND), Nova Iorque (JFK, EWR, LGA), Lisboa (LIS), Porto (OPO)
- **TravelContext.js**: Renders all airports in "Voos para {destination}" and "Como chegar ao centro da cidade" sections
- **Backend fix**: `build_template_itinerary` KeyError on `dest_data['hotel']['area']` → fixed to `dest_data.get('hotel_area', 'centro')`
- **Cache cleared**: Old cached plans without airports arrays removed from MongoDB
- **Tested**: 100% pass rate (iteration 83) — all airports render correctly in backend and frontend

### Hybrid Travel Plan Architecture (2026-03-26) — COST REDUCTION 70-90%
- **4-Layer System**: (1) Exact cache → (2) Fuzzy cache (same destination, different dates) → (3) Template engine → (4) Full AI (GPT-5.2)
- **Template Engine**: 10 destinations pré-configurados (Paris, Roma, Barcelona, Londres, Amesterdão, Tóquio, Nova Iorque, Lisboa, Porto) com hotéis reais, transportes, atrações, weather por mês, packing lists
- **Fuzzy Cache**: Adapta planos existentes a novas datas deterministicamente (0 custo AI)
- **Smart Aliases**: tokyo→toquio, london→londres, new york→nova iorque, amsterdam→amesterdão, rome→roma, etc.
- **Tiered Rate Limits**: Free=3/h, Registered=5/h, Ambassador/Admin=15/h
- **Optimized AI Prompt**: Prompt 50% menor para destinos desconhecidos, focado apenas no que a AI faz bem
- **Files**: `destination_templates.py` (template engine), `server.py` (hybrid endpoint)

### Product UX & Conversion Optimization (2026-03-26)
- **Visual Hierarchy**: btn-primary changed from peach to dark (#2D2A26) for stronger contrast. New btn-peach class for affiliate/monetization CTAs. btn-secondary uses peach outline
- **Home Hero**: CTA "Descobrir Viagens" now dark with Heart icon + shadow. Trust signals below
- **Home Contribute**: Main button, sticky bar, How it Works CTA all use dark bg with peach Heart icon
- **Home Plan Trip**: Search button darkened. Added benefit pills ("Roteiro com IA", "Mapa interativo", "Hotéis e voos")
- **Home Growth Loop**: Contextual invite prompt for logged-in users below contributions feed ("Conheces alguém que queira apoiar este sonho?" + "Convidar amigos" CTA)
- **Dashboard Emotional**: Sonhador card copy updated ("Estás a caminho de te tornares Embaixador"). Progress messages now mention ambassador benefits ("permite-te abrir a tua própria viagem"). Invite button darkened for contrast
- **Mobile**: All changes responsive-tested on 390px viewport

### Affiliate Links Fix (2026-03-25)
- **Bug**: 7 de 9 links de afiliados eram placeholders ("SKYSCANNER_LINK_HERE", etc.) que não funcionavam
- **Fix backend**: Substituídos todos os placeholders por URLs reais (skyscanner.pt, booking.com, hotels.com, discovercars.com, airalo.com, holafly.com/pt, iatiseguros.com)
- **Fix frontend**: `buildDynamicLinks` atualizado com construção de URLs específica por plataforma (Booking usa `?ss=`, Skyscanner usa `?query=`, Google Maps usa `/search/`)
- **PDF**: Links no guia offline agora também apontam para URLs reais
- **Nota**: Apenas GetYourGuide tem affiliate ID real (WFPE9ME). Os restantes usam URLs genéricas até o utilizador fornecer IDs de afiliado

### Analytics Dashboard (2026-03-25)
- **Endpoint**: GET /api/admin/analytics — aggregates funnel, affiliates, shares, referrals, top plans in one call
- **Funnel section**: Registos, Contribuições (completed + pending), Total Angariado, Embaixadores (com taxa conversão)
- **Affiliate Performance**: Bar chart by category (Hotéis, Experiências, Voos, eSIM, Transportes, Seguros) with total clicks
- **Share Metrics**: Bar chart by type (WhatsApp, Copy link, Partilha nativa, Link direto) with total
- **Referral System**: Referrals válidos, Referrers ativos, Média por referrer, Taxa embaixador
- **Top Plans**: Mais partilhados, Mais clicks afiliados, Mais conversões (journeys by amount)
- **UI**: First tab in Admin (default), clean cards with animated bars, peach brand accents

### Traffic Acquisition & Organic Growth (2026-03-25)
- **SEO**: index.html updated with lang="pt", proper meta description, OG defaults (og:title, og:description, og:type, og:site_name, twitter:card), theme-color "#FFBE98"
- **robots.txt**: Created with Disallow for /admin, /dashboard, /api/, /login, /auth/ and Sitemap reference
- **Sitemap**: Dynamic /api/sitemap.xml includes static pages + active journeys + public travel plans (auto-updates)
- **OG Images**: Dynamic 1200x630 PNG generation per plan via /api/og-image/{slug}
- **SSR**: Crawler proxy (setupProxy.js) redirects 15+ bot user agents to /api/ssr/plano/{slug} for pre-rendered HTML
- **Share Tracking**: New POST /api/track-share endpoint tracking whatsapp/copy/native/link events. Integrated in TravelPlanner.js and PublicPlan.js
- **Admin Analytics**: GET /api/admin/share-stats (share events by type), GET /api/admin/referral-stats (users, ambassadors, referral conversion rate), GET /api/admin/affiliate-stats (clicks by platform)
- **Performance**: SmartMap lazy loaded via React.lazy + Suspense
- **Sharing**: WhatsApp, native Web Share API, and copy-to-clipboard on PublicPlan and TravelPlanner
- Desktop: active link gets text-[#FFBE98] + subtle 2px underline using `useLocation`
- Mobile: active link gets text-[#FFBE98] + left border accent
- Applies to: Home, Planear Viagem (also covers /travel-planner), Meu Painel, Administração
- "Viagem Principal" button keeps its own permanent peach style
- "Explorar Viagens" keeps neutral style (scroll-only, no distinct route)

### Microcopy/Conversion Optimization (2026-03-25, verified 2026-03-25)
- Affiliate CTAs upgraded: "Evita filas — reservar entrada", "Muito procurado — garantir vaga", "Esgota rapido — garantir bilhete"
- Contextual getCTACopy function generates benefit-driven labels per destination type
- All affiliate logic (GetYourGuide, Skyscanner, insurance, eSIM) preserved intact

### Mobile-First Premium Layout Restructure (2026-03-25)
- **SmartMap**: Moved from actions footer to between TravelContext and tab navigation — "central element, high priority" as per spec.
- **AI Assistant**: Moved from actions footer to after itinerary tab content — "embedded" in the reading flow.
- **Premium Hint**: "Algumas funcionalidades sao exclusivas para Embaixadores" with Lock icon for non-ambassadors.
- **Conversion Block**: "Gostaste deste roteiro?" at bottom of card with dark gradient. Dual CTAs: "Criar o meu roteiro" (always) + "Tornar-me Embaixador" (non-ambassadors only).
- **Mobile Touch**: Copy/Share buttons min-h-[44px] for touch targets.
- **Layout Order**: Header → TopBookingBar → PremiumHint → TravelContext → SmartMap → Tabs → Content → AIAssistant → PlanningHub → ActionsFooter → ConversionBlock → Disclaimer.

### Public Plan Hero Redesign (2026-03-25)
- **Hero**: Full-viewport (100vh) with OG image as blurred background (blur 20px, brightness 0.3). Title: "{Destination} em {X} dias {flag}" with country flag emoji mapping (25+ countries). Subtitle emocional: "Roteiro inteligente para viver o melhor da cidade sem perder tempo nem cair em armadilhas". Badge "Gerado com IA". Two CTAs: "Explorar roteiro" (smooth scroll) + "Criar o meu" (glass button → /travel-planner). Animated scroll indicator.
- **Share Bar**: Sticky at top-20 (below fixed header) with backdrop blur. Shows destination + days + WhatsApp/Copy/Share buttons.
- **Content**: All existing sections preserved below hero (map teaser, weather, packing, itinerary, checklist, tips, CTAs).

### Server-Side SEO + PDF Cover (2026-03-25)
- **SSR Endpoint**: GET /api/ssr/plano/{slug} — Full HTML page with all OG meta tags (og:title, og:description, og:image, og:url, og:type), Twitter cards, schema.org TouristTrip structured data, canonical URL, and complete itinerary content visible without JavaScript. Crawlers (Facebook, WhatsApp, Twitter, Google, etc.) get pre-rendered HTML.
- **Crawler Proxy**: setupProxy.js detects 15+ crawler user agents and redirects /plano/{slug} to /api/ssr/plano/{slug} for SSR.
- **OG Image Upgrade**: Premium dark gradient design with 4Luis branding, destination, duration, dates, summary. 1200x630 PNG.
- **PDF Cover Page**: First page of offline PDF now includes the OG image (full-width), destination title, "Guia de viagem criado com IA" subtitle, dates, and 4Luis branding. Followed by PageBreak then existing content (unchanged).

### UX/Conversion Optimization (2026-03-25)
- **TopBookingBar**: Upgraded from compact chips to premium visual cards with icons, descriptions, and CTA buttons. Hotel card highlighted with peach gradient.
- **Planning Hub**: New "Planeamento da viagem" section after itinerary with 6 grouped links (voos, hoteis, seguro, eSIM, atividades, transportes) in 2-column grid.
- **SmartMap Affiliates**: Map pin popups now include "Evita filas — reservar experiencia aqui" GetYourGuide link.
- **AI Assistant Monetization**: After AI responses mentioning hotels/activities/tickets, contextual affiliate CTAs appear automatically.
- **PDF Affiliate Links**: "Links Uteis" section added to offline PDF with clickable affiliate URLs (booking, skyscanner, getyourguide, insurance, airalo).
- **Preserved**: All existing affiliate logic (ContextualCTA, InlineActivityCTA, TextWithCTA, EsimMicroCard, TipBookingLink, StickyBar) unchanged.

### Microcopy & Conversion Refinement (2026-03-25, verified 2026-03-25)
- **PlanTrip.js**: All 7 sections rewritten with benefit-driven titles ("Evita filas — reserva experiências", "Do aeroporto ao hotel sem stress", "Os imprevistos acontecem — protege-te") and CTAs ("Ver hotéis no centro", "Comparar voos (melhor preço)", "Reservar experiências (sem filas)")
- **TravelPlanner.js**: Formal "o seu/a sua" fully replaced with "o teu/a tua". "Planeie e reserve" → "Planeia e reserva". ACTIVITY_PATTERNS with "Evita filas", "Muito procurado", "Esgota rapido"
- **Emotional Layer**: "Este pode ser o início da tua próxima grande viagem" (PlanTrip + TravelPlanner premium hint). "Estás mais perto de te tornares Embaixador do que pensas" (conversion block)
- **Tone Consistency**: All user-facing text now uses informal "tu" form across PlanTrip, TravelPlanner, PublicPlan, SmartMap

### Offline Travel Guide PDF (2026-03-25)
- **Backend**: POST /api/ai/travel-plan/pdf — Ambassador-only. Generates clean PDF using ReportLab with 4Luis branding (peach header, Helvetica fonts). Includes: flight info (outbound/return tables), hotel details, airport-to-hotel transport, static map image (staticmap + CartoDB tiles), day-by-day itinerary (color-coded), weather/packing/checklist, local tips. Sections customizable via `sections` param.
- **Frontend**: OfflineGuideDownload.js component inside PremiumGate. Download button "Descarregar guia offline" + toggle to customize which sections to include (6 options). Downloads as blob and triggers browser download.
- **Map**: Static map generated server-side using `staticmap` library with CircleMarkers for locations, airport (blue), hotel (amber).

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

### Conversion & Monetization Optimization (2026-03-26)
- **Journey Progress Banner (Top)**: New `JourneyProgressBanner.js` component fetching `/api/homepage/main-journey`. Shows main journey name (China), progress bar (%), contributor count, pulsing "Contribuir" CTA linking to `/journey/{id}`. Displayed above the travel document card.
- **Journey Progress Banner (Mid)**: Dark gradient variant with emotional copy "Gostaste deste roteiro? Ajuda a tornar esta viagem real" + progress bar + "Contribuir" CTA. Placed between itinerary and AI assistant.
- **Must-See Affiliate CTAs**: Each must-see landmark now has a "Ver bilhetes" button linking to GYG search with destination+sight name (partner ID WFPE9ME). Changed from 2-column grid to full-width list layout for better CTA visibility.
- **Stay Zones Hotel CTA Fix**: Fixed broken `affiliateLinks?.hotel` reference to `affiliateLinks?.booking?.url` + added click tracking.
- **SmartMap Popup Enhancement**: Replaced single generic GYG link with two separate CTAs: "Evita filas — ver bilhetes" (sight-specific search) and "Reservar experiencia" (tour-specific search).
- **Final Conversion Block Update**: Primary CTA changed from "Criar o meu roteiro" to "Contribuir para o sonho" (pulsing heart). Secondary CTA "Criar o meu roteiro". Ambassador link moved below.
- **Ambassador Progression Visibility**: New dedicated block before Planning Hub showing compact progress bar + "Estas mais perto de te tornares Embaixador do que pensas" (visible only for logged-in non-ambassadors).
- **Files**: `JourneyProgressBanner.js` (new), `TravelPlanner.js` (modified), `TravelContext.js` (modified), `SmartMap.js` (modified)

### Conversion & Monetization Optimization Phase 2 (2026-03-26)
- **Social Proof Banner (NEW)**: `SocialProofBanner.js` — Mostra "59 pessoas já contribuíram" com lista dos últimos 3 contribuidores (nome, valor, timestamp relativo), barra de progresso, e CTA forte "Junta-te a eles" em dark bg
- **CTA Hierarchy Reforçada**: "Contribuir para o sonho" agora é o CTA dominante (full-width, texto maior, pulse suave). "Criar o meu roteiro" reduzido a link de texto
- **Ambassador Messaging como Oportunidade**: "Sabias que podes abrir a tua própria viagem de sonho?" + "O teu próximo passo: torna-te Embaixador" com benefícios claros
- **AI Assistant Monetização**: Keywords expandidos (hotel/alojamento/hostel/quarto/dormir + bilhete/experiência/atividade/fila/museu/tour/visita/excursão/ingresso/reservar), CTAs em dark bg com "Ver opções de alojamento" e "Ver opções"
- **Affiliate CTAs Otimizados**: Must-see items agora com botões dark bg "Evita filas" (mais visíveis), stay zones com tracking
- **Urgência**: Badge "Falta pouco!" quando progresso entre 10-100%
- **Ficheiros**: `SocialProofBanner.js` (novo), `TravelPlanner.js`, `AIAssistant.js`, `TravelContext.js` (modificados)

### Login UX + Password Recovery (2026-03-26)
- **Login Compacto**: Reescrita total do Login.js — spacing reduzido, nome/apelido lado-a-lado no registo, todo o conteúdo acima do fold
- **Helper Text**: "Entra para continuar a apoiar viagens e desbloquear a tua"
- **Forgot Password**: Link "Esqueceste-te da palavra-passe?" abre formulário integrado de recuperação
- **Password Reset (Backend)**: Endpoints POST `/api/auth/forgot-password` e `/api/auth/reset-password` com tokens single-use (UUID), expiração 30 min, bcrypt hash, sem revelação de existência de email
- **Reset Password Page**: Nova página `/reset-password` com validação de token e formulário de nova password
- **Email de Reset**: Template HTML via Resend com link direto para reset
- **Ficheiros**: `Login.js` (reescrito), `ResetPassword.js` (novo), `server.py` (endpoints), `App.js` (rota)

## Prioritized Backlog
### P1
- Celebracao "Sonho 100% Financiado": UI especial/animacao quando viagem atinge 100%
- Monetizacao do AI Assistant: sugestoes com CTAs de afiliados ("Ver opcoes")
### P2
- Ativar IfthenPay quando credenciais forem fornecidas
- Refatoracao backend server.py -> APIRouters modulares
- Refatoracao frontend TravelPlanner.js -> subcomponentes
### Backlog
- Geracao automatica de plano na viagem principal
- Sistema de gamificacao avancada
- Notificacoes push
- Consistencias de dados (viagens duplicadas, endpoint /api/health)

### Platform Tip System — Monetização Opcional (2026-04-11) — ⏸️ DESATIVADO (2026-04-15)
- **Status**: DESATIVADO por decisão estratégica — foco em crescimento da base de utilizadores e referrals
- **Reativar**: Alterar `TIP_SYSTEM_ENABLED = true` em CheckoutModal.js (linha ~27) e descomentar tab "revenue" em Admin.js
- **Conceito**: Sistema de contribuição opcional para manter a plataforma gratuita
- **Opções de Tip**: 2€ (default selecionado), 5€, 10€, "Não quero contribuir"
- **Regras de Distribuição**:
  - Campanha de Embaixador: 100% support_amount → embaixador, tip_amount → plataforma
  - Campanha da Plataforma: 100% support_amount → plataforma, tip_amount → plataforma
- **Checkout UI**: Secção com título "Ajuda-nos a manter esta plataforma gratuita para todos"
- **Backend**: Campos support_amount, tip_amount, ambassador_revenue, platform_revenue no modelo Contribution — PRESERVADOS
- **Admin Dashboard**: Tab "Receita" com métricas — CÓDIGO PRESERVADO, tab escondida
- **API Endpoints**: GET /api/contributions/config, GET /api/admin/platform-revenue — PRESERVADOS
- **Email**: send_tip_thank_you_email() em email_service.py — PRESERVADO
- **Ficheiros com código preservado**: CheckoutModal.js, server.py, config.py, Admin.js, models.py, email_service.py

### Tip System UX Improvements (2026-04-11) — ⏸️ DESATIVADO
- **Mensagem de Agradecimento**: "Sem pessoas como tu, esta plataforma não existia ❤️" — controlada por TIP_SYSTEM_ENABLED
- **Email de Agradecimento**: Enviado se tip > 0 — preservado em email_service.py
- **Microcopy**: "Contribuição opcional. Podes remover a qualquer momento." — preservado
- **Tracking**: average_tip, zero_tip_count, distribuição por valor — endpoint preservado

### Termos e Condições (2026-04-11)
- Footer atualizado: "Privacy" → "Privacidade", "Terms" → "Termos e Condições"
- Página /terms reescrita com 9 secções completas incluindo contribuição para plataforma e processamento de pagamentos
- Linha de aceitação de termos no checkout (Step 2): "Ao continuar, aceitas os Termos e Condições" com link

### Direct Payment Model + Ambassador Certification (2026-04-15)
- **Payment Modes**: `platform` (plataforma gere fundos) e `direct` (pagamento direto ao embaixador)
- **Journey Model**: Novos campos `payment_mode`, `ambassador_payment_methods`, `ambassador_payment_instructions`
- **Checkout**: Aviso "O pagamento é feito diretamente ao Embaixador. A 4Luis não gere os fundos." para mode direct
- **Certification Levels**: embaixador (auto) → verificado (admin) → confiável (histórico)
- **Badge na viagem**: Mostra nível de certificação do embaixador na página da viagem
- **Anti-fraude**: POST /api/ambassador/report para denunciar campanhas
- **API Endpoints**: 
  - GET /api/journey/{id}/payment-info
  - GET /api/ambassador/{id}/profile (certificação + stats)
  - PUT /api/admin/ambassador/{id}/certification
  - POST /api/ambassador/report
- **Ficheiros**: server.py, config.py, models.py, CheckoutModal.js, JourneyDetail.js, Home.js

### Growth Loop Optimizations (2026-04-15)
- Ecrã de sucesso: "Ajuda este sonho a ganhar forma" + motivação Embaixador
- Dashboard: "Estás a X passos" + "2/3 amigos já contribuíram"
- InvitePage: "Ao participar, também podes tornar-te Embaixador"
- Email de contribuição: CTA "Convidar amigos" + "O sonho continua a crescer"
- Benefícios simplificados: "Desbloqueia acesso especial + novas funcionalidades"

### Payment Validation + Trust System (2026-04-15)
- **Estados**: pending → awaiting_validation → confirmed / rejected (+ flagged após 7 dias)
- **Lembretes 24h + Timeout 7 dias**: Background task automática
- **Trust Indicators**: confirmed_count, confirmation_rate, total_raised
- **Badges**: Certificação + "X pagamentos confirmados, Y% taxa" na viagem + "Viagem aprovada pela 4Luis" no checkout

### Success Story System (2026-04-15)
- **Embaixador (financiada)**: "Este sonho foi financiado 🎉" + métricas + badge + partilha + CTAs
- **Main Trip (contínua)**: "O sonho já ganhou forma! Mas a viagem continua..." + prova social + CTA activo
- **Homepage (futuro)**: GET /api/success-stories pronto
- **Ficheiros**: SuccessStoryBanner.js, JourneyDetail.js, server.py

### Architecture Refactor (2026-04-16)
- **Backend Services Layer**: Criados 5 módulos independentes em /backend/services/
  - `payment_service.py` — revenue distribution, validação de montantes, cálculo de totais
  - `validation_service.py` — transições de estado, anti-fraude, flagging
  - `referral_service.py` — progressão ambassador, contagem de referrals
  - `ambassador_service.py` — certificação, trust indicators, tempo de confirmação
  - `journey_service.py` — progresso, status de funding
- **Backend Routes Structure**: Criada estrutura /backend/routes/ com __init__.py (shared deps)
- **Frontend Components**: Criados subcomponentes reutilizáveis
  - `Checkout/PaymentMethods.js` — métodos de pagamento geo-prioritized
  - `Journey/JourneyTrustIndicators.js` — badges e métricas de confiança
- **i18n**: Toast "Tradução automática por IA" já implementado no LanguageContext
- **Responsividade**: Mantida (mobile-first, CTAs acessíveis)
- **Nomenclatura**: User/Ambassador/Contributor/Sponsor definidos
- **server.py**: Mantido funcional (9026 linhas) — extracção progressiva via services

### Routes Extraction (2026-04-16)
- **auth_routes.py** ✅ EXTRAÍDO — register, login, forgot-password, reset-password, Google OAuth, /auth/me, logout
- **Padrão validado**: routes → services → models (sem dependências inversas)
- **Services importados**: notification_service.py para create_notification
- **server.py**: Reduzido ~250 linhas (de 9027 para ~8775)
- **Próximas extrações** (mesmo padrão): journey_routes.py, payment_routes.py, ambassador_routes.py
- **Testes**: Login, registo, forgot password — todos validados após extração

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **GYG Partner ID**: WFPE9ME
