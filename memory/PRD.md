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

## Schema da Base de Dados

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
goal_amount: float // OCULTO nas páginas públicas
current_amount: float
status: "active" | "funded" | "closed"
owner_user_id: string (FK → users)
target_date: string
created_at: datetime
```

### CONTRIBUTIONS
```
contribution_id: string (PK)
journey_id: string (FK → journeys)
user_id: string (FK → users)
amount: float
status: "pending" | "completed" | "rejected"
confirmed: boolean
confirmed_at: datetime
sponsor_link_id: string (optional)
created_at: datetime
```

### SPONSOR_LINKS
```
link_id: string (PK) // sponsor_{uuid}
user_id: string (FK → users)
journey_id: string (FK → journeys)
referral_count: int
successful_referrals: int
created_at: datetime
```

## Motor Premium

**Regra:**
```
IF subscription_active = true
AND valid_referrals_count >= 3
THEN level = "premium"
```

**Fluxo de Sponsor:**
1. URL `4luis.com/?ref=sponsor_{uuid}` → sessionStorage
2. No registo, `sponsor_id` atribuído ao novo utilizador (IMUTÁVEL)
3. Contribuição confirmada → incrementa `valid_referrals_count` do sponsor
4. Verificação automática de condições Premium

## O Que Foi Implementado

### Admin Users Dashboard ✅ (17 Fev 2026)
- **Métricas principais**: Total users, Premium, Contribuições, Novos (7 dias)
- **Distribuição por Nível**: Gráfico visual Curioso/Sonhador/Premium
- **Top Sponsors**: Ranking por impacto (€ gerado pelos convidados)
- **Lista de Utilizadores**: Tabela com nome, nível, subscrição, referrals, contribuições, impacto
- **Ações por utilizador**:
  - Ativar/desativar subscrição
  - Alterar nível manualmente
  - Corrigir referrals válidos
  - Ver detalhes completos (quem convidou, quem convidou, impacto)

### Migração de Base de Dados ✅
- Novos campos em USERS: sponsor_id, level, subscription_active, valid_referrals_count
- Novos campos em JOURNEYS: status, owner_user_id
- Fluxo de registo com sponsor_code via URL
- Motor Premium automático

### Funcionalidades Core ✅
- Homepage com hero emocional e viagens
- Barra de progresso (sem valor objetivo público)
- Sistema de sorteios (quando 100% atingido)
- Nota "Maior Sonhador pode ser convidado a viajar"
- Upload de avatar e identidade anónima
- Planeador de viagem na homepage

## Backlog

### P1 (Próximo)
- [ ] **Stripe Subscriptions** - Ativar premium automaticamente via pagamento

### P2
- [ ] UI básica de progressão para utilizadores
- [ ] Emails automáticos (registo, contribuição)

### Congelado (v2)
- Sistema de Pontos (gamificação)
- Sorteios públicos

## Credenciais
- **Admin**: admin@4luis.com / Admin1
- **Test User**: test@test.com / test

## APIs Mockadas
- **GPT-5.2**: Tradução e planeamento de viagem (placeholder)
