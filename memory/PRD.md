# 4Luis - Plataforma de CrowdDreaming

## Original Problem Statement
Plataforma de angariação de fundos para viagens solidárias com sistema de níveis (Sonhador - Embaixador), múltiplos métodos de pagamento, e sistema de referrals.

## Architecture & Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI (Python 3.11)
- **Database**: MongoDB
- **Payments**: Crypto (BTC, ETH, USDT, USDC), MBWay, PayPal, Revolut, Wise (Stripe desativado)
- **Email**: Resend
- **Auth**: JWT + Google OAuth
- **QR Codes**: qrcode (npm, toDataURL)
- **Crypto Prices**: CoinGecko API

## What's Been Implemented

### Checkout Modal 3 Passos
- Step 1: Selecao de valor (10/20/50/100/custom)
- Step 2: Metodo de pagamento (Crypto com badge TOP, MBWay, Revolut, Wise, PayPal)
- Step 3: Instrucoes com QR codes crypto (URI blockchain), deep links, referencia CN-XXXX
- Crypto: QR com `protocol:address?amount=value`, botao "Abrir carteira", aviso de rede
- MBWay: Sem QR, botao "Abrir MBWay" (mbway://transfer) + "Copiar numero"
- Revolut: Botao "Abrir Revolut" (revolut.me/luism2npb)
- Wise: Botao "Abrir Wise" (wise.com/pay/me/luisc8030)
- PayPal: Botao "Abrir PayPal" (paypal.me/LuisCanarias/{amount})
- Navegacao entre passos (seta voltar)
- Mensagem "Depois de enviar o pagamento, volte aqui..."

### Homepage
- "Como funciona o Crowddreaming" - 3 cards com icones
- Prova social "X sonhadores ja ajudaram esta plataforma"
- Imagem e badge "Viagem Principal" clicaveis -> detalhe da viagem
- "Planeia a tua viagem" com cards de ferramentas futuras

### Pagina Detalhe Viagem
- Botao sticky "Apoiar esta viagem" fixo no topo ao fazer scroll

### Sistema Embaixador
- Dashboard: Progresso com referrals individuais (verde/cinza)
- Botao "Convidar mais amigos" copia link /invite/{alias}
- Pagina /invite/{alias} com imagem, mensagem convite, barra progresso, botao contribuir
- Promocao automatica: referrals >= 3 AND contributed = true

### Admin
- Gestao viagens, utilizadores, contribuicoes
- Pesquisa por referencia de pagamento

## Key Files
- `frontend/src/components/CheckoutModal.js` - Modal de checkout 3 passos
- `frontend/src/pages/JourneyDetail.js` - Pagina de viagem com sticky CTA
- `frontend/src/pages/Home.js` - Homepage com Como funciona + Prova social
- `frontend/src/pages/Dashboard.js` - Dashboard com progresso Embaixador
- `frontend/src/pages/InvitePage.js` - Pagina de convite
- `frontend/src/pages/Admin.js` - Painel de administracao
- `backend/server.py` - API FastAPI principal

## Prioritized Backlog

### P1
- Verificar estabilidade do Painel de Administracao
- Melhorar formulario de edicao de viagens no Admin

### P2
- Sistema de pontos
- Sorteio real
- Notificacoes in-app
- Ferramentas de planeamento (afiliados)

## Credentials
- **Admin**: admin@4luis.com / Admin1
