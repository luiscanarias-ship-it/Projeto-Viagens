# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariacao de fundos para viagens solidarias com sistema de niveis (Sonhador - Embaixador), multiplos metodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise
- **Email**: Resend (PRODUCAO - mail@4luis.com)
- **Auth**: JWT + Google OAuth
- **Translation**: OpenAI GPT-5.2 via Emergent LLM Key

## What's Been Implemented

### Autosave com Sincronizacao no Servidor (2026-03-16)
- Dual-layer: localStorage (backup instantaneo) + servidor MongoDB (sync async)
- JourneyEditForm: autosave com debounce 2s local + 0.5s servidor
- Create Journey Form: mesmo mecanismo com chave journey_create/new
- Recuperacao de rascunhos do servidor (multi-dispositivo)
- Banner "Rascunho recuperado do servidor" com opcoes Manter/Descartar
- Indicador "Sincronizado" (verde) ou "Guardado localmente" (amber se server falhar)
- Limpeza automatica do draft apos guardar ou cancelar (local + servidor)
- Warning beforeunload quando ha alteracoes por guardar
- Dados expiram apos 24h (localStorage), servidor sem expiracao
- Backend endpoints: PUT/GET/DELETE /api/admin/drafts/{type}/{ref_id}, GET /api/admin/drafts

### Correcao FRONTEND_URL (2026-03-16)
- FRONTEND_URL no backend agora le de variavel de ambiente (nao hardcoded)
- Adicionado FRONTEND_URL ao backend/.env

### Preview de Emails antes de Enviar (2026-03-09)
- Todos os emails requerem confirmacao do admin antes de serem enviados
- Modal de preview mostra: HTML completo do email, assunto, numero de destinatarios
- Botoes "Cancelar" e "Confirmar e Enviar"
- 3 endpoints de preview: resumo semanal, novo sonho, sonho financiado

### Formulario de Edicao de Viagens no Admin (2026-03-09)
- JourneyEditForm.js com 4 tabs (Basico/Conteudo/Storytelling/Configuracoes)
- Preview em tempo real, validacao inline, geracao IA de storytelling

### Sistema de Confianca (2026-03-09)
- 3 niveis: Sonhador, Sonhador Verificado, Embaixador
- Badge visual na pagina da viagem

### Paginas Legais (2026-03-09)
- Privacidade, Termos, Cookies com design consistente

### Sistema de Emails (5 tipos - COMPLETO)
1. Mudanca de capitulo (automatico nos marcos 25/50/75/100%)
2. Resumo semanal (botao admin)
3. Contribuicao via referral (automatico)
4. Sonho financiado (botao admin >= 100%)
5. Novo sonho (botao admin com selector)

## Key Files
- frontend/src/components/JourneyEditForm.js (autosave dual-layer)
- frontend/src/components/EmailPreviewModal.js
- frontend/src/pages/Admin.js (autosave create form)
- frontend/src/pages/Home.js
- frontend/src/pages/JourneyDetail.js
- backend/server.py (drafts endpoints)

## Prioritized Backlog

### P1
- Celebracao especial quando viagem atinge 100%

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Refactoring: Dividir backend/server.py em modulos

## Credentials
- **Admin**: admin@4luis.com / Admin1
- **Resend sender**: mail@4luis.com
