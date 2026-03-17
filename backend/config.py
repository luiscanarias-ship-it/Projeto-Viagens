import os
import logging
import stripe
import resend
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'luis4dreams_secret_key_2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Stripe Config
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY', '')
STRIPE_SONHADOR_PRICE_ID = "price_1T1sngEBabTiQNkcaNBfBaHR"
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
stripe.api_key = STRIPE_API_KEY

# Resend Email Config
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
resend.api_key = RESEND_API_KEY

# Admin credentials
ADMIN_PASSWORD = "Admin1"
ADMIN_EMAIL = "admin@4luis.com"

# Frontend URL
FRONTEND_URL = os.environ.get('FRONTEND_URL')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Contribution constants
FIXED_CONTRIBUTION_AMOUNTS = [10, 20, 50, 100, 200, 500, 1000]

CRYPTO_TYPES = {
    "btc": {"name": "Bitcoin", "symbol": "BTC", "icon": "bitcoin", "color": "#F7931A"},
    "eth": {"name": "Ethereum", "symbol": "ETH", "icon": "ethereum", "color": "#627EEA"},
    "usdt": {"name": "Tether", "symbol": "USDT", "icon": "dollar", "color": "#26A17B"},
    "usdc": {"name": "USD Coin", "symbol": "USDC", "icon": "dollar", "color": "#2775CA"}
}

PAYMENT_METHODS = {
    "crypto": {"name": "Criptomoedas", "type": "direct", "icon": "bitcoin", "recommended": True},
    "stripe": {"name": "Cartão (Stripe)", "type": "automatic", "icon": "credit-card", "recommended": False},
    "mbway": {"name": "MBWay", "type": "direct", "icon": "smartphone", "recommended": False},
    "paypal": {"name": "PayPal", "type": "direct", "icon": "paypal", "recommended": False},
    "revolut": {"name": "Revolut", "type": "direct", "icon": "wallet", "recommended": False},
    "wise": {"name": "Wise", "type": "direct", "icon": "globe", "recommended": False}
}

# Journey status lifecycle
JOURNEY_STATUSES = {
    "candidatura": {"name": "Candidatura", "description": "Aguarda aprovação do admin"},
    "ajustes_pedidos": {"name": "Ajustes Pedidos", "description": "Admin pediu ajustes ao embaixador"},
    "aprovada": {"name": "Aprovada", "description": "Aprovada, aguarda ativação"},
    "ativa": {"name": "Ativa", "description": "Viagem ativa a receber contribuições"},
    "financiada": {"name": "Financiada", "description": "Objetivo de financiamento atingido"},
    "realizada": {"name": "Realizada", "description": "Viagem concluída"},
    "encerrada": {"name": "Encerrada", "description": "Viagem encerrada"}
}

# Anonymous identity
ALIAS_PREFIXES = [
    "Sonhador", "Viajante", "Explorador", "Aventureiro", "Navegador",
    "Peregrino", "Descobridor", "Caminhante", "Nómada", "Errante",
    "Buscador", "Observador", "Contemplador", "Andarilho", "Vagabundo"
]

ALIAS_SUFFIXES = [
    "Misterioso", "Sereno", "Curioso", "Audaz", "Sábio",
    "Tranquilo", "Intrépido", "Silencioso", "Luminoso", "Etéreo",
    "Radiante", "Encantado", "Celestial", "Infinito", "Dourado",
    "Prateado", "Estrelado", "Solar", "Lunar", "Cósmico"
]

AVATAR_STYLES = ["adventurer", "avataaars", "big-smile", "bottts", "lorelei", "micah", "miniavs", "personas"]
AVATAR_BACKGROUNDS = ["b6e3f4", "c0aede", "d1d4f9", "ffd5dc", "ffdfbf", "e8f5e9", "fff3e0", "f3e5f5"]

# Support ticket constants
TICKET_TYPES = [
    "Problema tecnico", "Pagamento", "Conta e acesso",
    "Convites e referrals", "Viagens e sonhos",
    "Reclamacao", "Sugestao", "Outro"
]
TICKET_STATUSES = ["Aberto", "Em analise", "A aguardar resposta", "Resolvido", "Fechado"]
TICKET_PRIORITIES = ["Baixa", "Media", "Alta", "Urgente"]
