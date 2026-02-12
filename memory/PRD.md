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

## User Personas
1. **Contribuidor**: Pessoa solidária que quer apoiar sonhos/viagens
2. **Administrador**: Gestor da plataforma (password: Admin1)
3. **Sponsor**: Utilizador que partilha links e ganha pontos

## O Que Foi Implementado

### 12 Fev 2026

#### Sistema de Sorteios Reintroduzido
- [x] Tab "Sorteios" no painel de admin
- [x] Lista viagens que atingiram 100% do objetivo de financiamento
- [x] Botão "Ver Participantes" mostra utilizadores com pontos
- [x] Botão "Realizar Sorteio" faz sorteio aleatório (ponderado por pontos)
- [x] Sorteio só pode ser feito uma vez por viagem
- [x] Vencedor é exibido após sorteio

#### Valor Objetivo Oculto nas Páginas Públicas
- [x] Homepage: cartões de viagem **NÃO** mostram barra de progresso nem valor objetivo
- [x] Página de detalhe: **NÃO** mostra barra de progresso
- [x] Página de detalhe: mostra citação emocional e data objetivo
- [x] Admin: **CONTINUA** a ver valores de financiamento (€X / €Y)

#### Nota "Maior Sonhador"
- [x] Sob o "Maior Sonhador" na homepage: "Um dos maiores sonhadores poderá ser convidado a viajar comigo"
- [x] Nota só aparece quando existe um "Maior Sonhador" (utilizador com mais pontos)

#### Correções Anteriores Validadas
- [x] "Planeia a tua viagem" na homepage tem campo de texto livre (não dropdown)
- [x] Dashboard do utilizador não mostra "números de registo" (apenas para admin)
- [x] Texto do link de sponsor refere "ganhar pontos para ser O Maior Sonhador"

### 11 Fev 2026

#### Refatoração "Bilhetes" para "Pontos"
- [x] Sistema de "bilhetes" convertido para "pontos"
- [x] "Maior Sonhador" baseado em total de pontos (não contribuições monetárias)
- [x] 1 ponto por cada 5€ contribuídos
- [x] Pontos a dobrar para pagamentos em crypto
- [x] Necessário 3+ referências para começar a ganhar pontos

#### Planeador de Viagem na Homepage
- [x] Campo de texto livre para destino
- [x] Recursos de viagem: Mapa (Bing), Hotéis, Voos, Recursos sociais
- [x] Links funcionais (substituídos Google Maps/Facebook/Instagram por alternativas)

#### Identidade Anónima Automática
- [x] Geração automática de alias poético (ex: "Buscador Sábio")
- [x] Geração automática de avatar via DiceBear API
- [x] Botão para regenerar identidade anónima

#### Upload de Avatar
- [x] Endpoint `/api/profile/avatar` (base64)
- [x] Validação de tamanho (máx 500KB)

### Funcionalidades Core
- [x] Homepage com hero emocional e lista de viagens
- [x] Seleção de idioma com tradução automática (PT, EN, ES, FR, DE, IT)
- [x] Modal de pagamento com múltiplos métodos
- [x] Sistema de autenticação duplo (JWT + Google)
- [x] Painel de administração completo (5 tabs)
- [x] Sistema de sponsor links
- [x] QR codes para pagamentos crypto
- [x] Design claro, sofisticado, emocional

## Backlog / Próximas Tarefas

### P1 (Importante)
- [ ] Email de confirmação automático após contribuição
- [ ] Email de confirmação automático após registo

### P2 (Nice to have)
- [ ] Testemunhos/mensagens de apoio em cada página de viagem
- [ ] Sistema de notificações dentro da aplicação
- [ ] Histórico de contribuições no dashboard

### Refatoração Técnica Recomendada
- [ ] Dividir `/app/backend/server.py` (2000+ linhas) em múltiplos routers
- [ ] Extrair componente reutilizável "Planeia a tua viagem"

## Credenciais
- **Admin Login**: admin@4luis.com / Admin1
- **Test User**: test@test.com / test
- **Crypto Address**: TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL (USDT TRC20)
- **MBWay**: +351968068535
- **PayPal**: paypal.me/LuisCanarias

## APIs Mockadas
- **GPT-5.2**: Tradução e planeamento de viagem (placeholder)
