# 4Luis - Plataforma de Angariação de Fundos

## Problema Original
Criar uma plataforma de angariação de fundos chamada "4Luis" (4Luis.com) com conceito de "crowddreaming" - não apenas crowdfunding, mas participação emocional em sonhos. Cada projeto é uma "viagem" com forte apelo emocional.

## Arquitetura
- **Frontend**: React 19 + TailwindCSS + Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Pagamentos**: Stripe + MBWay + PayPal + Crypto (USDT TRC20)
- **Tradução**: GPT-5.2 via Emergent LLM Key
- **Autenticação**: JWT + Google OAuth (Emergent Auth)

## User Personas
1. **Contribuidor**: Pessoa solidária que quer apoiar sonhos/viagens
2. **Administrador**: Gestor da plataforma (password: Admin1)
3. **Sponsor**: Utilizador que partilha links e ganha bilhetes

## Requisitos Core (Implementados)
- [x] Homepage com hero emocional e lista de viagens
- [x] Seleção de idioma com tradução automática (PT, EN, ES, FR, DE, IT)
- [x] Página de detalhes de viagem com barra de progresso (% angariado)
- [x] Modal de pagamento com múltiplos métodos
- [x] Sistema de autenticação duplo (JWT + Google)
- [x] Painel de administração para CRUD de viagens
- [x] Sistema de sponsor links
- [x] QR codes para pagamentos crypto
- [x] Design claro, sofisticado, emocional (tons pêssego/coral)

## O Que Foi Implementado (11 Fev 2026)

### Backend
- API REST completa com FastAPI
- Autenticação JWT + Google OAuth
- CRUD de viagens (journeys)
- Sistema de contribuições e pagamentos
- Integração Stripe para cartões
- Sistema de sponsor links e referências
- Tradução automática via GPT-5.2
- Geração de bilhetes para sorteio

### Frontend
- Homepage com animações Framer Motion
- Cards de viagens com progresso visual
- Página de detalhes de viagem
- Modal de pagamento multi-método
- Login/Registo + Google Auth
- Dashboard do utilizador
- Painel de administração
- Seletor de idioma

## Backlog / Próximas Tarefas

### P0 (Crítico)
- [ ] Confirmação manual de pagamentos (MBWay, PayPal, Crypto)
- [ ] Sistema de sorteio de bilhetes

### P1 (Importante)
- [ ] Email de confirmação de contribuição
- [ ] Notificações push
- [ ] Histórico de contribuições no dashboard

### P2 (Nice to have)
- [ ] Testemunhos/mensagens de apoio em cada viagem
- [ ] Avatar personalizado
- [ ] Integração Wise/Revolut/Monzo/Chase

## Credenciais
- **Admin Login**: admin@4luis.com / Admin1
- **Crypto Address**: TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL (USDT TRC20)
- **MBWay**: +351968068535
- **PayPal**: paypal.me/LuisCanarias
