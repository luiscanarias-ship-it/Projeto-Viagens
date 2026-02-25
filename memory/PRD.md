# 4Luis - Plataforma de Angariação de Fundos

## Problema Original
Criar uma plataforma de angariação de fundos chamada "4Luis" (4Luis.com) com conceito de "crowddreaming" - não apenas crowdfunding, mas participação emocional em sonhos. Cada projeto é uma "viagem" com forte apelo emocional.

## Arquitetura
- **Frontend**: React 19 + TailwindCSS + Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Pagamentos**: Stripe (automático) + MBWay/PayPal/Revolut/Wise/Crypto (diretos)
- **Autenticação**: JWT + Google OAuth (Emergent Auth)

---

## Modelo de Viagem Principal (v2 - ATUAL)

### Características
- **Viagem única** ativa até financiamento total
- **Valores fixos** de contribuição: €10, €20, €50, €100, €200, €500, €1000
- **Sem valor livre** - apenas montantes predefinidos
- **Zero comissões** - contribuições vão diretamente para o sonhador

### Métodos de Pagamento
| Método | Tipo | Descrição |
|--------|------|-----------|
| **Stripe** | Automático | Cartão (Visa, Mastercard) |
| **MBWay** | Direto | +351968068535 |
| **PayPal** | Direto | paypal.me/LuisCanarias |
| **Revolut** | Direto | @luis4dreams |
| **Wise** | Direto | luis@4luis.com |
| **Crypto** | Direto | USDT TRC20 |

### Modelo de Contribuição (v2)
```json
{
  "contribution_id": "string",
  "journey_id": "string",
  "user_id": "string | null",
  "amount": 10 | 20 | 50 | 100 | 200 | 500 | 1000,
  "payment_method": "stripe | mbway | paypal | revolut | wise | crypto",
  "status": "pending | confirmed | rejected",
  "is_main_trip": true,
  "validated_by": "admin_user_id | null",
  "validated_at": "datetime | null"
}
```

---

## Modelo de Utilizadores (v2)

### 3 Estados
| Estado | Descrição | Requisitos |
|--------|-----------|------------|
| **Visitante** | Não registado | Pode ver viagens |
| **Sonhador** | Utilizador registado | Pode contribuir, convidar |
| **Embaixador** | Sonhador ativo | Contribuiu + 3 referrals |

### Motor de Progressão
```
IF contributed_to_main_trip = true
AND valid_referrals_count >= 3
THEN level = "embaixador"
```

---

## Admin Reports (NOVO)

### Endpoints
- `GET /api/admin/contributions/reports` - Relatórios completos
- `GET /api/admin/contributions/pending` - Contribuições pendentes
- `PUT /api/admin/contributions/{id}/validate` - Validar contribuição

### Métricas Disponíveis
1. **Por Montante**: Contagem e total por valor (€10, €20, etc.)
2. **Por Método**: Contagem e total por método de pagamento
3. **Temporal**: Histórico diário (últimos 30 dias)
4. **Resumo**: Total confirmado, média, pendentes

---

## Endpoints Principais

### Contribuições (v2)
- `GET /api/contributions/config` - Configuração (valores fixos, métodos)
- `GET /api/contributions/payment-info` - Info de pagamentos diretos
- `POST /api/contributions/create` - Criar contribuição

### Admin
- `GET /api/admin/contributions/reports` - Relatórios
- `GET /api/admin/contributions/pending` - Pendentes
- `PUT /api/admin/contributions/{id}/validate` - Validar

---

## Backlog

### ✅ Concluído
- [x] Modelo de utilizadores v2 (visitante/sonhador/embaixador)
- [x] Dashboard do utilizador com progresso
- [x] Valores fixos de contribuição
- [x] 6 métodos de pagamento (Stripe, MBWay, PayPal, Revolut, Wise, Crypto)
- [x] Relatórios admin (por valor, método, temporal)
- [x] Validação de contribuições pelo admin

### P1 (Próximo)
- [ ] Emails automáticos:
  - Boas-vindas Sonhador
  - Contribuição registada
  - Contribuição confirmada
  - Embaixador desbloqueado

### P2 (Futuro)
- [ ] Formulário de candidatura Embaixador
- [ ] Notificações in-app
- [ ] Secção de testemunhos

---

## Credenciais de Teste

- **Admin**: `admin@4luis.com` / `Admin1`
- **Test User**: `test@test.com` / `test`

---

## Alterações Recentes

### 2026-02-25
- ✅ **Valores fixos**: €10, €20, €50, €100, €200, €500, €1000 (sem valor livre)
- ✅ **6 métodos de pagamento**: Stripe (auto) + MBWay, PayPal, Revolut, Wise, Crypto (diretos)
- ✅ **Modelo de contribuição v2**: Campos `validated_by`, `validated_at`, `is_main_trip`
- ✅ **Relatórios admin**: Por valor, por método, histórico temporal
- ✅ **UI atualizada**: Modal de pagamento com todos os métodos e instruções
- ✅ **Zero comissões**: Nota visível no fluxo de pagamento
