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

## O Que Foi Implementado (11 Fev 2026)

### Funcionalidades Core
- [x] Homepage com hero emocional e lista de viagens
- [x] Seleção de idioma com tradução automática (PT, EN, ES, FR, DE, IT)
- [x] Página de detalhes de viagem com barra de progresso (% angariado)
- [x] Modal de pagamento com múltiplos métodos (Stripe, MBWay, PayPal, Crypto)
- [x] Sistema de autenticação duplo (JWT + Google)
- [x] Painel de administração completo
- [x] Sistema de sponsor links (corrigido bug de serialização - 11 Fev)
- [x] QR codes para pagamentos crypto
- [x] Design claro, sofisticado, emocional

### Dashboard do Utilizador (Atualizado 11 Fev)
- [x] Secção "Meu Perfil" sem campo sobrenome (apenas Nome)
- [x] Secção "Links de Sponsor" com nota detalhada sobre regras do voucher (5.000€ ou 5% até 2.500€)
- [x] Secção "Meus Bilhetes" com texto incentivando 3 amigos para ganhar bilhetes

### Testes Completos (11 Fev)
- [x] Mobile responsiveness testado em 3 viewports (mobile, tablet, desktop)
- [x] Todos os meios de pagamento testados (Stripe, MBWay, PayPal, Crypto)
- [x] Backend: 25/25 testes passaram (100%)
- [x] Frontend: todas funcionalidades operacionais

### Data Objetivo (11 Fev)
- [x] Campo `target_date` adicionado ao modelo Journey no backend
- [x] JourneyCard mostra "Data objetivo: DD/MM/YYYY" junto à percentagem
- [x] Admin pode definir/editar data objetivo para cada viagem
- [x] Funciona em desktop e mobile

### Upload de Avatar (11 Fev)
- [x] Endpoint `/api/profile/avatar` para upload de imagem (base64)
- [x] Botão de câmara no perfil do utilizador para alterar foto
- [x] Validação de tamanho (máx 500KB) e tipo de ficheiro
- [x] Funciona em desktop e mobile

### Identidade Anónima Automática (11 Fev)
- [x] Geração automática de nome fictício (ex: "Buscador Sábio", "Nómada Curioso")
- [x] Geração automática de avatar usando DiceBear API
- [x] Quando utilizador desativa "Mostrar nome real", sistema gera identidade
- [x] Botão "Gerar nova identidade anónima" para regenerar
- [x] Identidade anónima usada em rankings e lista de vencedores

### Secção Comunidade (Homepage)
- [x] **"Cada contributo é um passo de luz"** - frase de destaque
- [x] **Contador de Sonhadores** - número de contribuidores únicos
- [x] **O Maior Sonhador** - destaque sem mostrar valores (respeita privacidade)
- [x] **Viagens Sorteadas** - contador com valor total em prémios
- [x] **Felizes Contemplados** - lista de vencedores (nome/alias/anónimo)

### Sistema de Privacidade
- [x] Campo **Alias** no perfil (nome público alternativo)
- [x] Toggle **"Mostrar nome real publicamente"**
- [x] Se desativado → mostra alias ou "Sonhador Anónimo"

### Painel Admin (4 tabs)
- [x] **Viagens**: CRUD completo
- [x] **Contribuições**: Confirmar/Rejeitar pagamentos manuais
- [x] **Sorteio**: Sistema completo com regras e sorteio aleatório
- [x] **Configurações**: Email de contacto editável

### Outros
- [x] Link "Contacte-nos" no footer (mailto configurável)
- [x] Progresso em percentagem apenas (máx 100%)

## Backlog / Próximas Tarefas

### P1 (Importante)
- [ ] Email de confirmação de contribuição
- [ ] Histórico de contribuições no dashboard

### P2 (Nice to have)
- [ ] Notificações push
- [ ] Testemunhos/mensagens de apoio em cada viagem
- [ ] Integração Wise/Revolut/Monzo/Chase

## Credenciais
- **Admin Login**: admin@4luis.com / Admin1
- **Crypto Address**: TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL (USDT TRC20)
- **MBWay**: +351968068535
- **PayPal**: paypal.me/LuisCanarias

## URLs
- **Frontend**: https://dream-trips-4.preview.emergentagent.com
- **API**: https://dream-trips-4.preview.emergentagent.com/api
