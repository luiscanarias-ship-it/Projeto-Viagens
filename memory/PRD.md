# 4Luis - Plataforma de Angariação de Fundos

## Problema Original
Criar uma plataforma de angariação de fundos chamada "4Luis" (4Luis.com) com conceito de "crowddreaming" - não apenas crowdfunding, mas participação emocional em sonhos. Cada projeto é uma "viagem" com forte apelo emocional.

## Arquitetura
- **Frontend**: React 19 + TailwindCSS + Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Pagamentos**: Stripe Subscriptions + MBWay + PayPal + Crypto
- **Autenticação**: JWT + Google OAuth (Emergent Auth)

## Stripe Subscriptions (Implementado)

### Produto
- **Nome**: Sonhador
- **Preço**: €10/mês (recorrente)
- **price_id**: `price_1T1sngEBabTiQNkcaNBfBaHR`

### Endpoints
- `POST /api/subscription/create-checkout` - Cria sessão de checkout Stripe
- `POST /api/stripe/subscription-webhook` - Webhook handler
- `GET /api/subscription/status` - Estado da subscrição do utilizador

### Webhooks Configurados
1. `checkout.session.completed` → Ativa Sonhador
2. `invoice.paid` → Reforça estado ativo
3. `invoice.payment_failed` → Log de falha
4. `customer.subscription.deleted` → Desativa subscrição

### Fluxo
1. Utilizador clica CTA "Junta-te como Sonhador"
2. Redireciona para Stripe Checkout
3. Pagamento aprovado
4. Webhook recebido → `subscription_active = true`, `level = "sonhador"`
5. Se `valid_referrals_count >= 3` → `level = "premium"`

### Regras Premium
```
IF subscription_active = true
AND valid_referrals_count >= 3
THEN level = "premium"
```

### CTAs Implementados
- ✅ Dashboard (banner principal)
- ✅ Homepage (secção entre comunidade e viagens)

## Configuração Stripe (Necessário)

1. **STRIPE_API_KEY** no backend/.env (chave secreta)
2. **Webhook Endpoint** no Stripe Dashboard:
   - URL: `https://dream-trips-4.preview.emergentagent.com/api/stripe/subscription-webhook`
   - Eventos: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted`
3. **STRIPE_WEBHOOK_SECRET** no backend/.env (obtido após criar webhook)

## Schema da Base de Dados

### USERS (campos de subscrição)
```
subscription_active: boolean
level: "curioso" | "sonhador" | "premium"
stripe_customer_id: string
stripe_subscription_id: string
subscription_started_at: datetime
subscription_ended_at: datetime
last_payment_at: datetime
```

### SUBSCRIPTION_LOGS
```
log_id: string
user_id: string
event: string
session_id: string
created_at: datetime
```

## Admin Growth Dashboard

### 3 Perguntas Fundamentais
1. **A crescer?** - Novos users, sonhadores, premium (7 dias)
2. **Impacto real?** - Total €, contribuições, média, sponsor impact
3. **Quem puxa?** - Top sponsors, top contribuidores

### Métricas
- Platform Momentum Score
- total_users, active_users, premium_users
- total_contributions_value, average_contribution
- valid_referrals_total, journeys_funded

### Gráficos
- Evolução utilizadores
- Evolução financeira
- Evolução referrals
- Distribuição níveis

## Backlog

### P1 (Próximo)
- [ ] Testar fluxo completo de subscrição com Stripe real
- [ ] Configurar webhook no Stripe Dashboard

### P2
- [ ] UI de progressão para utilizadores
- [ ] Emails automáticos (ativação, cancelamento, Premium)
- [ ] Portal de gestão de subscrição (cancelar/alterar)

## Credenciais
- **Admin**: admin@4luis.com / Admin1
- **Test User**: test@test.com / test

## URLs
- **Webhook**: `/api/stripe/subscription-webhook`
- **Checkout**: `/api/subscription/create-checkout`
- **Status**: `/api/subscription/status`
