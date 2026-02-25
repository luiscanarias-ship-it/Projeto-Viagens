# 4Luis - Plataforma de Angariação de Fundos

## Problema Original
Criar uma plataforma de angariação de fundos chamada "4Luis" (4Luis.com) com conceito de "crowddreaming" - não apenas crowdfunding, mas participação emocional em sonhos. Cada projeto é uma "viagem" com forte apelo emocional.

## Arquitetura
- **Frontend**: React 19 + TailwindCSS + Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Pagamentos**: Stripe (apenas para contribuições)
- **Autenticação**: JWT + Google OAuth (Emergent Auth)

---

## Modelo de Utilizadores v2 (ATUAL)

### 3 Estados de Utilizador

| Estado | Descrição | Requisitos |
|--------|-----------|------------|
| **Visitante** | Não registado | Pode ver viagens |
| **Sonhador** | Utilizador registado | Pode contribuir, gerar links, convidar |
| **Embaixador** | Sonhador ativo | Contribuiu + 3 referrals válidos |

### Motor de Progressão para Embaixador
```
IF contributed_to_main_trip = true
AND valid_referrals_count >= 3
THEN level = "embaixador"
```

### Benefícios por Nível
- **Sonhador**: Acesso completo à plataforma, pode convidar amigos
- **Embaixador**: Pode candidatar-se a abrir viagem própria

### Campos do Utilizador (Schema)
```json
{
  "user_id": "string",
  "email": "string",
  "name": "string",
  "level": "sonhador | embaixador",
  "contributed_to_main_trip": "boolean",
  "valid_referrals_count": "number",
  "sponsor_id": "string (imutável)",
  "embaixador_unlocked_at": "datetime | null"
}
```

---

## User Dashboard v1 (Implementado)

### 5 Blocos do Dashboard

1. **Estado Atual** - Badge com nível (Sonhador/Embaixador)
2. **Progresso para Embaixador** - Checklist visual:
   - [ ] Contribuir para viagem principal
   - [ ] 3 referrals válidos (barra de progresso)
3. **Convites** - Link de sponsor, copiar, partilhar, estatísticas
4. **Contribuições Pessoais** - Total €, nº contribuições, última
5. **Viagem Principal** - Progresso, valor, botão "Apoiar"

### Adaptação por Nível
- **Sonhador**: Mostra checklist de progresso
- **Embaixador**: Mostra "Desbloqueado!" + CTA candidatura

---

## Stripe (Contribuições)

### Uso Atual
- Stripe é usado **apenas para pagamentos de contribuições**
- Removida a subscrição mensal como requisito de progressão

### Endpoints de Contribuição
- `POST /api/contributions/create-checkout` - Checkout Stripe
- `GET /api/contributions/checkout-status/{session_id}` - Status
- `POST /api/webhook/stripe` - Webhook de pagamentos

---

## Endpoints Principais

### Dashboard
- `GET /api/dashboard/user-stats` - Stats completos do user

### Contribuições
- `POST /api/contributions/create-checkout` - Iniciar pagamento
- `GET /api/contributions/my-contributions` - Histórico

### Admin
- `GET /api/admin/contributions` - Todas contribuições
- `PUT /api/admin/contributions/{id}/confirm` - Confirmar manual
- `GET /api/admin/users/dashboard` - Growth dashboard

---

## Backlog

### P1 (Próximo)
- [ ] Emails automáticos:
  - Boas-vindas ao Sonhador
  - Convite aceite
  - Contribuição de convidado
  - Embaixador desbloqueado

### P2 (Futuro)
- [ ] Secção de testemunhos nas páginas de viagem
- [ ] Sistema de notificações in-app
- [ ] Formulário de candidatura Embaixador

### P3 (Backlog)
- [ ] Reintroduzir sistema de "Pontos"
- [ ] Gamificação avançada

---

## Credenciais de Teste

- **Admin**: `admin@4luis.com` / `Admin1`
- **Test User**: `test@test.com` / `test`

---

## Alterações Recentes

### 2026-02-17
- ✅ Implementado User Dashboard v1 com 5 blocos
- ✅ Testados webhooks Stripe Subscriptions
- ✅ Motor Premium validado (subscription + 3 referrals)

### 2026-02-25
- ✅ **Atualização Modelo v2**: Removida subscrição como requisito
- ✅ Novos estados: Visitante → Sonhador → Embaixador
- ✅ Novo motor: contributed_to_main_trip + 3 referrals = embaixador
- ✅ Dashboard atualizado com checklist de progresso
- ✅ Migração de utilizadores existentes
