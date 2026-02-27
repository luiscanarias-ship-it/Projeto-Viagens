# Relatório Técnico - 4Luis Platform
**Data:** 27 Fevereiro 2026

---

## 1️⃣ ESTRUTURA DE BASE DE DADOS

### Coleções MongoDB

| Coleção | Descrição |
|---------|-----------|
| `users` | Utilizadores da plataforma |
| `journeys` | Viagens (principal + embaixadores) |
| `contributions` | Contribuições/doações |
| `sponsor_links` | Links de convite/referral |
| `points` | Pontos ganhos por utilizadores |
| `user_sessions` | Sessões de autenticação |
| `email_queue` | Fila de emails enviados |
| `site_settings` | Configurações do site |
| `trip_gallery` | Galeria de fotos de viagens |

---

## 2️⃣ MODELO DE UTILIZADORES

### Campos Atuais da Collection `users`:

```javascript
{
  user_id: "user_xxxxx",           // ID único
  email: "email@example.com",      // Email (único)
  name: "Nome",                    // Nome
  surname: "Apelido",              // Apelido (opcional)
  password_hash: "hash...",        // Password encriptada (bcrypt)
  is_admin: false,                 // É administrador?
  avatar: "url",                   // Avatar personalizado
  picture: "url",                  // Foto do Google OAuth
  use_real_name: true,             // Mostrar nome real ou alias?
  anonymous_alias: "Sonhador X",   // Alias anónimo gerado
  anonymous_avatar: "url",         // Avatar anónimo
  
  // ✅ CAMPOS DE PROGRESSÃO (v2)
  sponsor_id: "user_yyyy",         // ✅ EXISTE - Quem convidou este user (imutável)
  level: "sonhador",               // ✅ EXISTE - sonhador | embaixador
  contributed_to_main_trip: false, // ✅ EXISTE - Contribuiu para viagem principal?
  valid_referrals_count: 0,        // ✅ EXISTE - Nº de referrals que contribuíram
  
  // Datas
  registered_at: "ISO date",
  embaixador_unlocked_at: null,    // Data em que se tornou embaixador
  created_at: "ISO date",
  
  // Subscrição (se aplicável)
  subscription_active: false,
  subscription_id: null,
  customer_id: null
}
```

### Sistema de Progressão:

| Estado | Descrição | Requisitos |
|--------|-----------|------------|
| **Visitante** | Não registado | - |
| **Sonhador** | Utilizador registado | Criar conta |
| **Embaixador** | Pode criar viagem própria | `contributed_to_main_trip = true` + `valid_referrals_count >= 3` |

### ✅ Progressão Automática:
**SIM** - Implementada no endpoint `confirm_contribution` (linha 2566-2695 server.py):
- Quando uma contribuição é confirmada, verifica se o user atingiu requisitos de Embaixador
- Atualiza automaticamente `level`, `valid_referrals_count`, `contributed_to_main_trip`
- Envia email de parabéns ao novo Embaixador

---

## 3️⃣ MODELO DE VIAGENS

### Campos Atuais da Collection `journeys`:

```javascript
{
  journey_id: "journey_xxxxx",
  name: "China",                    // Nome da viagem
  poetic_name: "Onde os Dragões...",// Nome poético
  description: "Descrição...",
  emotional_message: "Mensagem...",
  impact_description: "Impacto...",
  image_url: "https://...",
  goal_amount: 5000.0,              // Objetivo em EUR
  current_amount: 1250.0,           // Valor angariado
  currency: "EUR",
  target_date: "2026-06-01",        // Data objetivo (opcional)
  
  // ✅ FLAGS PRINCIPAIS
  is_active: true,                  // Viagem ativa?
  is_main_trip: true,               // ✅ EXISTE - É a viagem principal?
  is_ambassador_journey: false,     // É viagem de embaixador?
  
  // ✅ ESTADOS (lifecycle)
  status: "ativa",                  // ✅ EXISTE - Ver tabela abaixo
  
  // Localização
  region: "asia",                   // europa, asia, africa, americas, oceania
  country: "China",
  city: "Pequim",
  
  // Embaixador (se aplicável)
  ambassador_user_id: "user_xxx",
  ambassador_name: "Nome",
  application_message: "Porque quero...",
  
  // Datas de transição
  approved_at: null,
  funded_at: null,
  realized_at: null,
  closed_at: null,
  
  // História (após realização)
  story: "A minha experiência...",
  photos: ["url1", "url2"],
  
  // ✅ VISIBILIDADE
  is_featured: false,               // Em destaque?
  featured_at: null,
  featured_order: 0,
  visibility_score: 0.0,            // Score calculado
  visibility_boost: 0.0,            // Boost manual (-100 a +100)
  hide_from_listings: false,        // Ocultar das listagens?
  show_goal_amount: false,          // ✅ EXISTE - Mostrar objetivo € publicamente?
  
  // Admin
  owner_user_id: "user_admin",
  admin_notes: "Notas...",
  created_at: "ISO date",
  updated_at: "ISO date"
}
```

### ✅ Estados Existentes:

| Estado | Descrição | Transição |
|--------|-----------|-----------|
| `candidatura` | Aguarda aprovação admin | Embaixador submete |
| `ajustes_pedidos` | Admin pediu alterações | Admin solicita |
| `aprovada` | Aprovada, aguarda ativação | Admin aprova |
| `ativa` | A receber contribuições | Admin ativa |
| `financiada` | Objetivo atingido (AUTO) | `current_amount >= goal_amount` |
| `realizada` | Viagem concluída | Admin marca |
| `encerrada` | Arquivada | Admin encerra |

### ✅ Transição Automática para "financiada":
**SIM** - Implementada em `check_and_update_journey_funding_status()` (linha 3493-3555)
- Verifica `current_amount >= goal_amount`
- Muda status para "financiada"
- Define `is_active = False`
- Envia emails ao embaixador e admin

---

## 4️⃣ MODELO DE CONTRIBUIÇÕES

### Campos Atuais da Collection `contributions`:

```javascript
{
  contribution_id: "contrib_xxxxx",
  journey_id: "journey_xxxxx",
  user_id: "user_xxxxx",            // Opcional (pode ser anónimo)
  amount: 50,                       // ✅ Valores fixos: 10, 20, 50, 100, 200, 500, 1000
  currency: "EUR",
  
  // ✅ PAGAMENTO
  payment_method: "stripe",         // ✅ EXISTE - crypto, stripe, mbway, paypal, revolut, wise
  crypto_type: "btc",               // ✅ EXISTE - btc, eth, usdt, usdc (só para crypto)
  tx_hash: "0x...",                 // ✅ EXISTE - Hash da transação crypto
  
  // ✅ STATUS
  status: "pending",                // ✅ EXISTE - pending | confirmed | rejected
  is_main_trip: true,               // ✅ EXISTE - Contribuição para viagem principal?
  
  // Validação
  validated_by: "user_admin",       // Admin que validou
  validated_at: "ISO date",
  
  // Referral
  sponsor_link_id: "sponsor_xxx",   // Link de sponsor usado
  
  // Stripe
  session_id: "cs_xxx",             // Session ID do Stripe
  
  // Identificação
  contributor_name: "Nome",         // Nome do contribuidor
  contributor_email: "email@...",   // Email
  public_message: "Boa sorte!",     // Mensagem pública
  show_name: true,                  // Mostrar nome ou "Anónimo"?
  
  // Admin
  notes: "Notas admin...",
  created_at: "ISO date"
}
```

### Valores Fixos de Contribuição:
```
€10, €20, €50, €100, €200, €500, €1000
```

---

## 5️⃣ SISTEMA DE PAGAMENTOS

### ✅ Stripe:
| Item | Status |
|------|--------|
| Integração | ✅ ATIVO (emergentintegrations) |
| Checkout Session | ✅ Funcional |
| Webhook | ✅ ATIVO (`/api/webhook/stripe`) |
| Confirmação automática | ✅ Sim |

### ✅ Métodos Manuais Implementados:

| Método | Tipo | Info |
|--------|------|------|
| **Crypto** | Direto | BTC, ETH, USDT (TRC20), USDC (XDC) - QR codes e endereços |
| **MBWay** | Direto | +351968068535 |
| **PayPal** | Direto | paypal.me/LuisCanarias |
| **Revolut** | Direto | @luis4dreams |
| **Wise** | Direto | luis@4luis.com |

### ✅ Botões Ligados ao Backend:
**SIM** - Endpoint `/api/contributions/create` (linha 1122-1267):
- Valida montante (valores fixos)
- Valida método de pagamento
- Cria checkout Stripe se método = stripe
- Cria contribuição pendente se método direto
- Retorna info de pagamento

---

## 6️⃣ PAINEL ADMIN

### ✅ Tabs Existentes:

| Tab | Funcionalidade | Status |
|-----|----------------|--------|
| **Viagens** | CRUD de viagens, definir viagem principal | ✅ Funcional |
| **Contribuições** | Ver todas, confirmar/rejeitar pendentes | ✅ Funcional |
| **Utilizadores** | Ver users, alterar níveis, ver detalhes | ✅ Funcional |
| **Sponsors** | Relatório de referrals | ✅ Funcional |
| **Sorteios** | Ver participantes, realizar sorteio | ✅ Funcional |
| **Candidaturas** | Gerir candidaturas de embaixadores | ✅ Funcional |
| **Visibilidade** | Gerir destaque e ordenação de viagens | ✅ Funcional |
| **Emails** | Ver fila de emails enviados | ✅ Funcional |
| **Stats** | Estatísticas gerais | ✅ Funcional |
| **Settings** | Configurações do site | ✅ Funcional |

### ✅ Gestão de Candidaturas:
**FUNCIONAL** - Endpoints implementados:
- `GET /api/admin/ambassador-journeys` - Listar por estado
- `GET /api/admin/ambassador-journeys/{id}` - Detalhes completos
- `PUT /api/admin/ambassador-journeys/{id}/status` - Alterar estado

Ações disponíveis:
- ✅ Ver detalhes completos (dados viagem + embaixador + histórico)
- ✅ Aprovar e Ativar (muda para "ativa", publica)
- ✅ Pedir Ajustes (muda para "ajustes_pedidos", envia email)
- ✅ Rejeitar (encerra candidatura)

### ✅ Gestão de Visibilidade:
**FUNCIONAL** - Endpoints implementados:
- `GET /api/admin/journeys-with-visibility` - Viagens com score
- `PUT /api/admin/journeys/{id}/visibility` - Atualizar visibilidade
- `POST /api/admin/recalculate-visibility-scores` - Recalcular todos
- `PUT /api/admin/journeys/{id}/show-goal` - Toggle mostrar objetivo

Controlos:
- ✅ Destacar/Remover destaque
- ✅ Boost manual (-10, +10)
- ✅ Ocultar/Mostrar das listagens
- ✅ Toggle "Mostrar objetivo €"
- ✅ Recalcular scores

---

## 7️⃣ SISTEMA DE EMAILS

### Configuração:
```
Provider: Resend
API Key: RESEND_API_KEY (ambiente)
Sender: SENDER_EMAIL (ambiente)
```

### ✅ Emails Ativos:

| Email | Evento Trigger | Destinatário | Status |
|-------|----------------|--------------|--------|
| **Contribuição Confirmada** | Admin confirma contribuição | Contribuidor | ✅ ATIVO |
| **Referral Contribuiu (Sponsor)** | Convidado contribui | Quem convidou | ✅ ATIVO |
| **Referral Contribuiu (Admin)** | Convidado contribui | Admin | ✅ ATIVO |
| **Embaixador Desbloqueado** | User atinge requisitos | Novo embaixador | ✅ ATIVO |
| **Viagem Financiada (Embaixador)** | Objetivo atingido | Embaixador da viagem | ✅ ATIVO |
| **Viagem Financiada (Admin)** | Objetivo atingido | Admin | ✅ ATIVO |
| **Candidatura Aprovada** | Admin aprova candidatura | Embaixador | ✅ ATIVO |
| **Ajustes Pedidos** | Admin pede ajustes | Embaixador | ✅ ATIVO |

### Funções de Email (server.py):
- `send_email_resend()` - Função base (linha 596)
- `send_contribution_email()` - Email contribuição (linha 650)
- `send_referral_contribution_emails()` - Emails referral (linha 674)
- `send_ambassador_unlocked_email()` - Email embaixador (linha 724)
- `send_journey_funded_emails()` - Emails viagem financiada (linha 833)

---

## 8️⃣ RESUMO: O QUE ESTÁ FUNCIONAL

### ✅ 100% Funcional:
- Sistema de autenticação (JWT + Google OAuth)
- CRUD de viagens
- Sistema de contribuições com 6 métodos de pagamento
- Stripe checkout + webhook
- Sistema de níveis (Sonhador → Embaixador)
- Progressão automática de utilizadores
- Sistema de referrals/sponsors
- Candidaturas de embaixadores (submissão e gestão)
- Transição automática "financiada"
- Gestão de visibilidade
- Todos os emails comportamentais
- Painel Admin completo

### ⚠️ Funcional mas Dependente de Config:
- Emails: Requerem `RESEND_API_KEY` válido
- Stripe: Requer `STRIPE_API_KEY` válido

### 📝 Não Implementado / Futuro:
- Sistema de Pontos (estrutura existe, lógica parcial)
- Sorteio real (estrutura existe)
- Notificações in-app
- Blog/Updates por viagem

---

## 9️⃣ CREDENCIAIS DE TESTE

| Tipo | Email | Password |
|------|-------|----------|
| Admin | admin@4luis.com | Admin1 |
| User teste | (criar novo) | qualquer |

---

## 🔗 ENDPOINTS PRINCIPAIS

### Públicos:
- `GET /api/journeys` - Listar viagens ativas
- `GET /api/journeys/{id}` - Detalhe viagem
- `GET /api/journeys/{id}/progress` - Progresso (%)
- `GET /api/journeys/{id}/contributions` - Feed de contribuições
- `GET /api/contributions/config` - Config de contribuições
- `GET /api/contributions/payment-info` - Info de pagamento
- `POST /api/contributions/create` - Criar contribuição
- `GET /api/homepage/main-journey` - Viagem principal
- `GET /api/homepage/ambassador-journeys` - Viagens embaixadores
- `GET /api/homepage/realized-journeys` - Viagens realizadas

### Autenticados:
- `GET /api/auth/me` - User atual
- `GET /api/dashboard/stats` - Stats do user
- `POST /api/sponsor-links` - Criar link sponsor
- `POST /api/ambassador/apply` - Candidatura embaixador

### Admin:
- `GET /api/admin/journeys` - Todas as viagens
- `GET /api/admin/contributions` - Todas as contribuições
- `POST /api/admin/contributions/{id}/confirm` - Confirmar
- `GET /api/admin/users/dashboard` - Dashboard users
- `GET /api/admin/ambassador-journeys` - Candidaturas
- `PUT /api/admin/ambassador-journeys/{id}/status` - Alterar estado

---

**Relatório gerado automaticamente em 27/02/2026**
