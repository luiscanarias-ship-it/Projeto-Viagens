# 4Luis - Plataforma de Angariação de Fundos

## Problema Original
Criar uma plataforma de angariação de fundos chamada "4Luis" (4Luis.com) com conceito de "crowddreaming" - não apenas crowdfunding, mas participação emocional em sonhos. Cada projeto é uma "viagem" com forte apelo emocional.

## Arquitetura
- **Frontend**: React 19 + TailwindCSS + Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Pagamentos**: Stripe + MBWay + PayPal + Crypto (USDT TRC20)
- **Tradução**: GPT-5.2 via Emergent LLM Key (PLACEHOLDER)
- **Autenticação**: JWT + Google OAuth (Emergent Auth)

## Schema da Base de Dados (Atualizado 12 Fev 2026)

### USERS
```
user_id: string (PK)
email: string
name: string
surname: string (optional)
password_hash: string
avatar: string (base64, optional)
use_real_name: boolean
sponsor_id: string (FK → users) // IMUTÁVEL - quem convidou
level: "curioso" | "sonhador" | "premium"
subscription_active: boolean
valid_referrals_count: int
registered_at: datetime
premium_unlocked_at: datetime (optional)
created_at: datetime
```

### JOURNEYS (aka TRIPS)
```
journey_id: string (PK)
name: string
poetic_name: string
description: string
emotional_message: string
impact_description: string
image_url: string
goal_amount: float
current_amount: float
currency: string
target_date: string (optional)
is_active: boolean
status: "active" | "funded" | "closed"
owner_user_id: string (FK → users)
created_at: datetime
updated_at: datetime
```

### CONTRIBUTIONS
```
contribution_id: string (PK)
journey_id: string (FK → journeys)
user_id: string (FK → users)
amount: float
currency: string
payment_method: string
is_crypto: boolean
status: "pending" | "completed" | "rejected"
confirmed: boolean
confirmed_at: datetime (optional)
sponsor_link_id: string (optional)
created_at: datetime
```

### SPONSOR_LINKS
```
link_id: string (PK) // sponsor_{uuid}
user_id: string (FK → users)
journey_id: string (FK → journeys)
referral_count: int // pessoas que clicaram/registaram
successful_referrals: int // pessoas que contribuíram
created_at: datetime
```

### POINTS (congelado para v2)
### RAFFLE_RESULTS (congelado para v2)

## Motor Premium (Implementado - sem UI ainda)

**Regra:**
```
IF subscription_active = true
AND valid_referrals_count >= 3
THEN level = "premium"
```

**Fluxo de Sponsor:**
1. Utilizador entra via `4luis.com/?ref=sponsor_{uuid}`
2. `sponsor_code` guardado em sessionStorage
3. No registo, `sponsor_id` é atribuído ao novo utilizador (IMUTÁVEL)
4. Quando contribuição é confirmada:
   - Se user tem `sponsor_id` → incrementa `valid_referrals_count` do sponsor
   - Verifica condições Premium automaticamente

## O Que Foi Implementado

### 12 Fev 2026 (Sessão Atual)

#### ETAPA 1 - Expansão USERS ✅
- `sponsor_id` (relation → users, imutável)
- `level` ("curioso" | "sonhador" | "premium")
- `subscription_active` (boolean)
- `valid_referrals_count` (int)
- `registered_at`, `premium_unlocked_at`

#### ETAPA 2 - Fluxo de Registo com Sponsor ✅
- URL `?ref=sponsor_{uuid}` capturada no frontend
- `sponsor_code` guardado em sessionStorage
- Registo passa `sponsor_code` ao backend
- Backend resolve `sponsor_code → sponsor_user_id`
- `sponsor_id` guardado no novo utilizador (imutável)
- `referral_count` incrementado no sponsor_link

#### ETAPA 3 - Expansão JOURNEYS ✅
- `owner_user_id` (admin que criou)
- `status` ("active" | "funded" | "closed")
- Status atualiza automaticamente para "funded" quando objetivo atingido

#### ETAPA 4 - Motor de Contribuições ✅
- Quando contribuição confirmada:
  - `confirmed = true`, `confirmed_at` guardado
  - Se user tem sponsor → `valid_referrals_count++` no sponsor
  - Verifica condições Premium automaticamente
  - Atualiza `successful_referrals` no sponsor_link

#### Endpoints Admin Novos ✅
- `PUT /api/admin/users/{user_id}/subscription` - Ativar/desativar subscrição
- `GET /api/admin/users` - Listar todos utilizadores com info de sponsor
- `POST /api/admin/migrate-users` - Migrar utilizadores existentes

### Funcionalidades Anteriores
- [x] Barra de progresso visível (sem valor objetivo)
- [x] Sistema de sorteios (quando 100% atingido)
- [x] Nota sob Maior Sonhador
- [x] Upload de avatar
- [x] Identidade anónima automática
- [x] Planeador de viagem na homepage

## Backlog / Próximas Tarefas

### P1 (Importante)
- [ ] Email de confirmação automático após contribuição
- [ ] Email de confirmação automático após registo
- [ ] UI para admin gerir subscrições (ativar Premium manualmente)

### P2 (Nice to have)
- [ ] Dashboard Premium para utilizadores
- [ ] Stripe Subscriptions para activação automática
- [ ] Testemunhos/mensagens nas viagens
- [ ] Sistema de notificações in-app

### Congelado (v2)
- Sistema de Pontos (gamificação)
- Sorteios públicos

## Credenciais
- **Admin Login**: admin@4luis.com / Admin1
- **Test User**: test@test.com / test

## APIs Mockadas
- **GPT-5.2**: Tradução e planeamento de viagem (placeholder)
