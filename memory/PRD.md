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

## O Que Foi Implementado

### Fase 1 - MVP (11 Fev 2026)
- API REST completa com FastAPI
- Autenticação JWT + Google OAuth
- CRUD de viagens (journeys)
- Sistema de contribuições e pagamentos
- Integração Stripe para cartões
- Sistema de sponsor links e referências
- Tradução automática via GPT-5.2
- Geração de bilhetes para sorteio

### Fase 2 - Novas Funcionalidades (11 Fev 2026)
- [x] **Contador de Sonhadores** na homepage
  - Total de sonhadores (contribuidores únicos)
  - "O Maior Sonhador" ao lado (apenas nome/alias, sem valores)
- [x] **Sistema de Privacidade do Utilizador**
  - Campo Alias para nome público alternativo
  - Toggle "Mostrar nome real publicamente"
  - Se desativado, mostra alias ou "Sonhador Anónimo"
- [x] **Secção "Entre em Contacto"** no final da homepage
  - Email configurável pelo admin
  - Mensagem personalizável
- [x] **Confirmação manual de pagamentos**
  - Tab "Contribuições" no admin
  - Confirmar/Rejeitar pagamentos pendentes
  - Atualização automática dos montantes
- [x] **Sistema de Sorteio**
  - Tab "Sorteio" no admin
  - Seleção de viagem
  - Regras claras do sorteio
  - Sorteio aleatório com resultado visual
- [x] **Progresso em percentagem**
  - Mostra apenas "XX% angariado"
  - Máximo de 100% mesmo que ultrapassado
- [x] **Configurações do site** (Admin)
  - Email de contacto editável
  - Mensagem de contacto editável
- [x] **Dashboard do Utilizador melhorado**
  - Tab "Meu Perfil" com configurações de privacidade
  - Editar nome, sobrenome, alias
  - Toggle para anonimato público

## Backlog / Próximas Tarefas

### P0 (Crítico)
- [ ] Email de confirmação de contribuição
- [ ] Notificações push

### P1 (Importante)
- [ ] Histórico de contribuições no dashboard utilizador
- [ ] Testemunhos/mensagens de apoio em cada viagem

### P2 (Nice to have)
- [ ] Avatar personalizado
- [ ] Integração Wise/Revolut/Monzo/Chase

## Credenciais
- **Admin Login**: admin@4luis.com / Admin1
- **Crypto Address**: TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL (USDT TRC20)
- **MBWay**: +351968068535
- **PayPal**: paypal.me/LuisCanarias

## Configurações Admin
Aceda a Admin → Configurações para definir:
- Email de contacto (mostrado na secção "Entre em Contacto")
- Mensagem de contacto personalizada
