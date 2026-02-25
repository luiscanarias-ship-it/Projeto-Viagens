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

### Visibilidade de Dados
| Dado | Público | Admin |
|------|---------|-------|
| Barra de progresso | ✅ | ✅ |
| Percentagem angariada | ✅ | ✅ |
| Valor total (goal) | ❌ | ✅ |
| Data objetivo | ✅ | ✅ |
| Feed de contribuições | ✅ | ✅ |

### Após 100% do Financiamento
- A viagem **continua a aceitar contribuições**
- A barra pode **ultrapassar os 100%**
- Mostra banner: **"Financiamento total quase a fechar."**

---

## Métodos de Pagamento
| Método | Tipo | Descrição |
|--------|------|-----------|
| **Stripe** | Automático | Cartão (Visa, Mastercard) |
| **MBWay** | Direto | +351968068535 |
| **PayPal** | Direto | paypal.me/LuisCanarias |
| **Revolut** | Direto | @luis4dreams |
| **Wise** | Direto | luis@4luis.com |
| **Crypto** | Direto | USDT TRC20 |

---

## Modelo de Contribuição (v2)
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
  "validated_at": "datetime | null",
  "public_message": "string | null",
  "show_name": true | false,
  "contributor_name": "string | null"
}
```

---

## Feed de Contribuições Públicas
Cada contribuição mostra:
- **Nome ou alias** do apoiante (ou "Sonhador Anónimo")
- **Valor contribuído** (€)
- **Mensagem opcional** do apoiante
- **Data** da contribuição
- Formato: **Feed cronológico**

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

## Admin Reports

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

### Viagem
- `GET /api/journeys/{id}/progress` - Progresso (% público, goal_amount só admin)
- `GET /api/journeys/{id}/contributions` - Feed público de contribuições

### Contribuições
- `GET /api/contributions/config` - Configuração (valores fixos, métodos)
- `GET /api/contributions/payment-info` - Info de pagamentos diretos
- `POST /api/contributions/create` - Criar contribuição

---

## Backlog

### ✅ Concluído
- [x] Modelo de utilizadores v2 (visitante/sonhador/embaixador)
- [x] Dashboard do utilizador com progresso
- [x] Valores fixos de contribuição
- [x] 6 métodos de pagamento
- [x] Relatórios admin
- [x] Feed público de contribuições
- [x] Mensagem pública opcional
- [x] Opção de contribuir anonimamente
- [x] Barra de progresso pode ultrapassar 100%
- [x] Valor total oculto ao público

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

### 2026-02-25 (Sessão 2)
- ✅ **Feed de contribuições públicas**: Nome/alias, valor, mensagem, data
- ✅ **Mensagem pública opcional**: Campo no modal de pagamento
- ✅ **Toggle "Mostrar o meu nome"**: Opção de contribuir anonimamente
- ✅ **Valor total oculto**: Só admin vê o goal_amount
- ✅ **Barra pode exceder 100%**: Continua a aceitar contribuições após funding
- ✅ **Banner de encerramento**: "Financiamento total quase a fechar."

### 2026-02-25 (Sessão 1)
- ✅ Valores fixos: €10, €20, €50, €100, €200, €500, €1000
- ✅ 6 métodos de pagamento: Stripe, MBWay, PayPal, Revolut, Wise, Crypto
- ✅ Relatórios admin: Por valor, método, histórico temporal
