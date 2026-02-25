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

## Estrutura da Homepage (v2 - ATUAL)

### 4 Secções Principais

1. **Viagem Principal** (hero section)
   - Experiência viva com imagem de fundo
   - Barra de progresso animada (%)
   - Feed das últimas contribuições
   - Botão "Contribuir para este Sonho"
   
2. **Planeia a Tua Viagem**
   - Ferramenta de pesquisa de destinos
   - Recursos: Mapas, Hotéis, Voos, Guias

3. **Sonhos em Fase de Materialização**
   - Viagens de embaixadores em angariação
   - Organizadas por região geográfica (Europa, Ásia, África, Américas, Oceânia)
   - Progress percentage em cada card

4. **Sonhos Realizados**
   - Viagens financiadas/concluídas
   - Organizadas por país
   - Fotos e histórias
   - Conteúdo curado enquanto não há casos reais

---

## Lifecycle de Viagens dos Embaixadores

### Estados
| Estado | Descrição | Ações |
|--------|-----------|-------|
| `candidatura` | Embaixador submeteu | Aguarda aprovação admin |
| `aprovada` | Admin aprovou | Pronta para ativação |
| `ativa` | A receber contribuições | Visível na homepage |
| `financiada` | Objetivo atingido (auto) | Move para "Sonhos Realizados" |
| `realizada` | Viagem concluída | Pode adicionar fotos/história |
| `encerrada` | Arquivada | Não visível |

### Transições Automáticas
- Quando `current_amount >= goal_amount` → Estado muda para `financiada`
- `is_active = False` → Remove da secção ativa
- Envia email ao embaixador
- Notifica administrador

---

## Sistema de Emails (MOCKADO)

### Templates Disponíveis
| Template | Evento | Destinatário |
|----------|--------|--------------|
| `journey_funded` | Viagem financiada | Embaixador |
| `admin_journey_funded` | Viagem financiada | Admin |
| `contribution_confirmed` | Contribuição validada | Contribuidor |
| `welcome` | Registo | Novo utilizador |
| `ambassador_unlocked` | Nível desbloqueado | Novo embaixador |

### Implementação
- Emails são guardados na collection `email_queue`
- Status: `queued` → `sent`
- **NOTA**: Sistema mockado - não envia emails reais

---

## Modelo de Utilizadores (v2)

| Estado | Descrição | Requisitos |
|--------|-----------|------------|
| **Visitante** | Não registado | Pode ver viagens |
| **Sonhador** | Utilizador registado | Pode contribuir, convidar |
| **Embaixador** | Sonhador ativo | Contribuiu + 3 referrals válidos |

### Motor de Progressão
```
IF contributed_to_main_trip = true
AND valid_referrals_count >= 3
THEN level = "embaixador"
```

---

## Métodos de Pagamento

| Método | Tipo | Info |
|--------|------|------|
| **Stripe** | Automático | Cartão (Visa, Mastercard) |
| **Crypto** | Direto | BTC, ETH, USDT (TRC20), USDC (XDC) |
| **MBWay** | Direto | +351968068535 |
| **PayPal** | Direto | paypal.me/LuisCanarias |
| **Revolut** | Direto | @luis4dreams |
| **Wise** | Direto | luis@4luis.com |

Valores fixos: €10, €20, €50, €100, €200, €500, €1000

---

## Endpoints Homepage

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/homepage/main-journey` | Viagem principal + progresso + contribuições |
| `GET /api/homepage/ambassador-journeys` | Viagens ativas por região |
| `GET /api/homepage/realized-journeys` | Viagens financiadas por país |
| `GET /api/homepage/curated-dreams` | Conteúdo inspiracional |

---

## Endpoints Admin

| Endpoint | Descrição |
|----------|-----------|
| `POST /api/admin/migrate-journey-status` | Migrar status 'active' → 'ativa' |
| `POST /api/admin/set-main-journey/{id}` | Definir viagem principal |
| `PUT /api/admin/ambassador-journeys/{id}/status` | Atualizar estado de viagem |
| `GET /api/admin/emails` | Ver fila de emails |

---

## Backlog

### ✅ Concluído (Sessão Atual)
- [x] Nova estrutura da homepage com 4 secções
- [x] Viagem Principal com experiência viva e barra de progresso
- [x] Planeia a tua viagem (ferramenta mantida)
- [x] Sonhos em Materialização (viagens embaixadores por região)
- [x] Sonhos Realizados (por país, fotos/histórias, conteúdo curado)
- [x] Lifecycle completo de viagens: candidatura → ativa → financiada → realizada
- [x] Transição automática para "financiada" quando objetivo atingido
- [x] Sistema de emails mockado para notificações
- [x] Endpoints admin para migração e gestão
- [x] **Onboarding guiado (4 ecrãs)**: Introdução, Progressão, Impacto, Escolha de ação

### ✅ Concluído (Sessões Anteriores)
- [x] Modelo de utilizadores v2 (visitante/sonhador/embaixador)
- [x] Dashboard do utilizador com progresso
- [x] Valores fixos de contribuição (6 montantes)
- [x] 6 métodos de pagamento incluindo crypto
- [x] Relatórios admin
- [x] Feed público de contribuições
- [x] Incentivo a pagamentos crypto (badges, destaque)

### P1 (Próximo)
- [ ] Integrar serviço de email real (Resend/SendGrid)
- [ ] Formulário UI para Embaixador criar viagem (endpoint existe)
- [ ] Página de Admin para gerir viagens de embaixadores

### P2 (Futuro)
- [ ] Notificações in-app
- [ ] Secção de testemunhos nas viagens
- [ ] Updates/blog em cada viagem
- [ ] Sistema de Pontos (congelado)

---

## Credenciais de Teste

- **Admin**: `admin@4luis.com` / `Admin1`
- **Test User**: `test@test.com` / `test`

---

## Alterações Recentes

### 2026-02-25 (Sessão 3 - Atual)
- ✅ Nova estrutura da homepage com 4 secções ordenadas
- ✅ Viagem Principal: experiência viva, barra de progresso, contribuições, CTA
- ✅ Sonhos em Materialização: viagens embaixadores organizadas por região
- ✅ Sonhos Realizados: organizados por país, fotos/histórias, conteúdo curado
- ✅ Lifecycle completo: candidatura → aprovada → ativa → financiada → realizada → encerrada
- ✅ Transição automática para "financiada" quando objetivo atingido
- ✅ Sistema de emails mockado com templates (contribution_confirmed, ambassador_unlocked, journey_funded)
- ✅ Migração de status 'active' → 'ativa' para consistência
- ✅ Endpoint para definir viagem principal
- ✅ **Onboarding guiado após registo (4 ecrãs)**:
  - Ecrã 1: Introdução ao crowddreaming
  - Ecrã 2: Progressão (contribuir → convidar → embaixador → viagem própria)
  - Ecrã 3: Impacto da comunidade (100%, 0% comissões, ∞ sonhos)
  - Ecrã 4: Escolha de ação inicial (apoiar viagem, explorar, planear)

### 2026-02-25 (Sessão 2)
- ✅ Feed de contribuições públicas com nome/alias, valor, mensagem
- ✅ Opção de contribuir anonimamente
- ✅ Valor total oculto ao público
- ✅ Barra pode exceder 100%

### 2026-02-25 (Sessão 1)
- ✅ Valores fixos: €10, €20, €50, €100, €200, €500, €1000
- ✅ 6 métodos de pagamento: Stripe, MBWay, PayPal, Revolut, Wise, Crypto
