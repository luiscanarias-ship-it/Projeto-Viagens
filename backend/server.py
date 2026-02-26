from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx
import stripe
import resend

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

# Admin password
ADMIN_PASSWORD = "Admin1"
ADMIN_EMAIL = "admin@4luis.com"

app = FastAPI(title="4Luis API")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== ANONYMOUS IDENTITY GENERATOR ====================

# Poetic name combinations for anonymous users
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

# DiceBear avatar styles and colors for anonymous users
AVATAR_STYLES = ["adventurer", "avataaars", "big-smile", "bottts", "lorelei", "micah", "miniavs", "personas"]
AVATAR_BACKGROUNDS = ["b6e3f4", "c0aede", "d1d4f9", "ffd5dc", "ffdfbf", "e8f5e9", "fff3e0", "f3e5f5"]

def generate_anonymous_alias() -> str:
    """Generate a poetic anonymous alias"""
    prefix = random.choice(ALIAS_PREFIXES)
    suffix = random.choice(ALIAS_SUFFIXES)
    return f"{prefix} {suffix}"

def generate_anonymous_avatar(seed: str = None) -> str:
    """Generate an anonymous avatar URL using DiceBear API"""
    if not seed:
        seed = uuid.uuid4().hex[:8]
    style = random.choice(AVATAR_STYLES)
    bg_color = random.choice(AVATAR_BACKGROUNDS)
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}&backgroundColor={bg_color}"

# ==================== MODELS ====================

class UserBase(BaseModel):
    email: EmailStr
    name: str
    surname: Optional[str] = None
    avatar: Optional[str] = None
    use_real_name: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: Optional[str] = None
    sponsor_code: Optional[str] = None  # Link de sponsor usado no registo

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    user_id: str
    is_admin: bool = False
    created_at: datetime
    picture: Optional[str] = None

# Journey status lifecycle
JOURNEY_STATUSES = {
    "candidatura": {"name": "Candidatura", "description": "Aguarda aprovação do admin"},
    "aprovada": {"name": "Aprovada", "description": "Aprovada, aguarda ativação"},
    "ativa": {"name": "Ativa", "description": "Viagem ativa a receber contribuições"},
    "financiada": {"name": "Financiada", "description": "Objetivo de financiamento atingido"},
    "realizada": {"name": "Realizada", "description": "Viagem concluída"},
    "encerrada": {"name": "Encerrada", "description": "Viagem encerrada"}
}

class Journey(BaseModel):
    journey_id: str = Field(default_factory=lambda: f"journey_{uuid.uuid4().hex[:12]}")
    name: str
    poetic_name: str
    description: str
    emotional_message: str
    impact_description: str
    image_url: str
    goal_amount: float
    current_amount: float = 0.0
    currency: str = "EUR"
    target_date: Optional[str] = None
    is_active: bool = True
    is_main_trip: bool = False  # True for the main platform journey
    status: str = "ativa"  # candidatura | aprovada | ativa | financiada | realizada | encerrada
    # Location fields for organization
    region: Optional[str] = None  # Geographic region: europa, asia, africa, americas, oceania
    country: Optional[str] = None  # Country name
    city: Optional[str] = None  # City name
    # Ambassador journey fields
    is_ambassador_journey: bool = False
    ambassador_user_id: Optional[str] = None  # User ID of the ambassador who owns this journey
    ambassador_name: Optional[str] = None
    application_message: Optional[str] = None  # Message from ambassador when applying
    approved_at: Optional[str] = None
    funded_at: Optional[str] = None
    realized_at: Optional[str] = None
    closed_at: Optional[str] = None
    # Story & photos for realized journeys
    story: Optional[str] = None  # Story text after journey is realized
    photos: Optional[List[str]] = None  # List of photo URLs
    # Admin fields
    owner_user_id: Optional[str] = None  # Admin who created/approved the journey
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JourneyCreate(BaseModel):
    name: str
    poetic_name: str
    description: str
    emotional_message: str
    impact_description: str
    image_url: str
    goal_amount: float
    currency: str = "EUR"
    target_date: Optional[str] = None

class JourneyUpdate(BaseModel):
    name: Optional[str] = None
    poetic_name: Optional[str] = None
    description: Optional[str] = None
    emotional_message: Optional[str] = None
    impact_description: Optional[str] = None
    image_url: Optional[str] = None
    goal_amount: Optional[float] = None
    target_date: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    story: Optional[str] = None
    photos: Optional[List[str]] = None

# Ambassador journey application
class AmbassadorJourneyApplication(BaseModel):
    name: str
    poetic_name: str
    description: str
    emotional_message: str
    impact_description: str
    image_url: Optional[str] = None
    goal_amount: float
    currency: str = "EUR"
    target_date: Optional[str] = None
    application_message: str  # Why they want to create this journey

# ==================== CONTRIBUTION MODEL (v2) ====================

# Fixed contribution amounts (no custom values allowed)
FIXED_CONTRIBUTION_AMOUNTS = [10, 20, 50, 100, 200, 500, 1000]

# Crypto types supported
CRYPTO_TYPES = {
    "btc": {"name": "Bitcoin", "symbol": "BTC", "icon": "bitcoin", "color": "#F7931A"},
    "eth": {"name": "Ethereum", "symbol": "ETH", "icon": "ethereum", "color": "#627EEA"},
    "usdt": {"name": "Tether", "symbol": "USDT", "icon": "dollar", "color": "#26A17B"},
    "usdc": {"name": "USD Coin", "symbol": "USDC", "icon": "dollar", "color": "#2775CA"}
}

# Payment methods - crypto is FIRST (recommended)
PAYMENT_METHODS = {
    "crypto": {"name": "Criptomoedas", "type": "direct", "icon": "bitcoin", "recommended": True},
    "stripe": {"name": "Cartão (Stripe)", "type": "automatic", "icon": "credit-card", "recommended": False},
    "mbway": {"name": "MBWay", "type": "direct", "icon": "smartphone", "recommended": False},
    "paypal": {"name": "PayPal", "type": "direct", "icon": "paypal", "recommended": False},
    "revolut": {"name": "Revolut", "type": "direct", "icon": "wallet", "recommended": False},
    "wise": {"name": "Wise", "type": "direct", "icon": "globe", "recommended": False}
}

class Contribution(BaseModel):
    contribution_id: str = Field(default_factory=lambda: f"contrib_{uuid.uuid4().hex[:12]}")
    journey_id: str
    user_id: Optional[str] = None
    amount: int  # Fixed amounts only: 10, 20, 50, 100, 200, 500, 1000
    currency: str = "EUR"
    payment_method: str  # crypto, stripe, mbway, paypal, revolut, wise
    crypto_type: Optional[str] = None  # btc, eth, usdt, usdc (only for crypto payments)
    tx_hash: Optional[str] = None  # Transaction hash for crypto payments
    status: str = "pending"  # pending | confirmed | rejected
    is_main_trip: bool = True  # Always true for now (single main trip)
    validated_by: Optional[str] = None  # Admin user_id who validated
    validated_at: Optional[str] = None  # Datetime of validation
    sponsor_link_id: Optional[str] = None
    session_id: Optional[str] = None  # Stripe session if applicable
    contributor_name: Optional[str] = None  # For anonymous/unregistered
    contributor_email: Optional[str] = None
    public_message: Optional[str] = None  # Public message from supporter
    show_name: bool = True  # Whether to show real name or anonymous
    notes: Optional[str] = None  # Admin notes
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContributionCreate(BaseModel):
    journey_id: str
    amount: int  # Must be one of FIXED_CONTRIBUTION_AMOUNTS
    payment_method: str  # Must be one of PAYMENT_METHODS
    crypto_type: Optional[str] = None  # Required if payment_method is crypto
    tx_hash: Optional[str] = None  # Optional tx hash for verification
    sponsor_code: Optional[str] = None
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None
    public_message: Optional[str] = None  # Optional public message
    show_name: bool = True  # Show name publicly or anonymous

class SponsorLink(BaseModel):
    link_id: str = Field(default_factory=lambda: f"sponsor_{uuid.uuid4().hex[:8]}")
    user_id: str
    journey_id: str
    referral_count: int = 0
    successful_referrals: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Point(BaseModel):
    """Points earned by users - replaces the old Ticket system"""
    point_id: str  # Registration number
    user_id: str
    journey_id: str
    contribution_id: str
    points_value: int = 1  # How many points this entry represents
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TranslationRequest(BaseModel):
    texts: Dict[str, str]
    target_language: str

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, is_admin: bool = False) -> str:
    payload = {
        "user_id": user_id,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def get_current_user(request: Request) -> Optional[User]:
    # Check cookie first
    session_token = request.cookies.get("session_token")
    if session_token:
        session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
        if session:
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at > datetime.now(timezone.utc):
                user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
                if user:
                    return User(**user)
    
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = decode_jwt_token(token)
            user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0})
            if user:
                return User(**user)
        except HTTPException:
            pass
    return None

async def require_auth(request: Request) -> User:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    return user

async def require_admin(request: Request) -> User:
    user = await require_auth(request)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso de administrador necessário")
    return user

# ==================== EMAIL SYSTEM (RESEND) ====================

FRONTEND_URL = "https://journey-fund-3.preview.emergentagent.com"

def get_email_base_template(content: str, title: str = "4Luis") -> str:
    """Base HTML email template with 4Luis branding"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #FAFAF9;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #FAFAF9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="padding: 32px 40px 24px 40px; border-bottom: 1px solid #E6F4F1;">
                            <span style="font-size: 28px; font-weight: bold; color: #FFBE98;">4Luis</span>
                            <p style="margin: 8px 0 0 0; color: #6B6661; font-size: 14px;">Onde os sonhos ganham asas</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px 40px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #FAFAF9; border-radius: 0 0 16px 16px;">
                            <p style="margin: 0; color: #6B6661; font-size: 12px; text-align: center;">
                                Este é um email transacional automático da 4Luis.<br>
                                <a href="{FRONTEND_URL}" style="color: #FFBE98; text-decoration: none;">4Luis.com</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

def get_contribution_email_html(contributor_name: str, amount: float, journey_name: str, is_crypto: bool = False, crypto_type: str = None) -> str:
    """HTML template for contribution confirmation email"""
    crypto_badge = ""
    if is_crypto and crypto_type:
        crypto_badge = f"""
        <div style="margin: 24px 0; padding: 16px; background: linear-gradient(135deg, #F7931A20, #627EEA20); border-radius: 12px; text-align: center;">
            <span style="font-size: 24px;">🏆</span>
            <p style="margin: 8px 0 0 0; color: #2D2A26; font-weight: bold;">Contribuição em {crypto_type.upper()}</p>
            <p style="margin: 4px 0 0 0; color: #6B6661; font-size: 14px;">Badge especial de cripto-sonhador!</p>
        </div>
        """
    
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Obrigado, {contributor_name}! 💜</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        A tua contribuição foi confirmada com sucesso.
    </p>
    
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">Contribuíste</p>
        <p style="margin: 0; color: #2D2A26; font-size: 36px; font-weight: bold;">{amount}€</p>
        <p style="margin: 8px 0 0 0; color: #6B6661; font-size: 14px;">para "{journey_name}"</p>
    </div>
    
    {crypto_badge}
    
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        Graças a ti, este sonho está mais perto de se tornar realidade. 
        Cada contribuição é um gesto fraternal que faz a diferença.
    </p>
    
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold;">
            Ver o meu Dashboard
        </a>
    </div>
    """
    return get_email_base_template(content, "Contribuição Confirmada - 4Luis")

def get_referral_contribution_email_html(sponsor_name: str, invitee_name: str, amount: float, journey_name: str, 
                                         valid_referrals: int, contributed_to_main: bool) -> str:
    """HTML template for sponsor notification when their referral contributes"""
    progress_to_ambassador = ""
    
    # Calculate progress
    referrals_needed = max(0, 3 - valid_referrals)
    contribution_check = "✅" if contributed_to_main else "⬜"
    referrals_check = "✅" if valid_referrals >= 3 else "⬜"
    
    if contributed_to_main and valid_referrals >= 3:
        progress_to_ambassador = """
        <div style="margin: 24px 0; padding: 16px; background: linear-gradient(135deg, #FFBE9820, #E6F4F120); border-radius: 12px; text-align: center; border: 2px solid #FFBE98;">
            <span style="font-size: 32px;">🎉</span>
            <p style="margin: 8px 0 0 0; color: #2D2A26; font-weight: bold; font-size: 18px;">Parabéns! És agora Embaixador!</p>
            <p style="margin: 4px 0 0 0; color: #6B6661; font-size: 14px;">Podes criar a tua própria viagem de sonho.</p>
        </div>
        """
    else:
        progress_to_ambassador = f"""
        <div style="margin: 24px 0; padding: 16px; background-color: #FAFAF9; border-radius: 12px;">
            <p style="margin: 0 0 12px 0; color: #2D2A26; font-weight: bold;">Progresso para Embaixador:</p>
            <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">
                {contribution_check} Contribuir para a viagem principal
            </p>
            <p style="margin: 0; color: #6B6661; font-size: 14px;">
                {referrals_check} 3 convites válidos ({valid_referrals}/3)
            </p>
        </div>
        """
    
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Boa notícia, {sponsor_name}! 🌟</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        Alguém que convidaste acabou de contribuir para um sonho!
    </p>
    
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td style="padding-bottom: 12px;">
                    <p style="margin: 0; color: #6B6661; font-size: 14px;">Convidado</p>
                    <p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 18px; font-weight: bold;">{invitee_name}</p>
                </td>
            </tr>
            <tr>
                <td style="padding-bottom: 12px;">
                    <p style="margin: 0; color: #6B6661; font-size: 14px;">Contribuiu</p>
                    <p style="margin: 4px 0 0 0; color: #FFBE98; font-size: 24px; font-weight: bold;">{amount}€</p>
                </td>
            </tr>
            <tr>
                <td>
                    <p style="margin: 0; color: #6B6661; font-size: 14px;">Para a viagem</p>
                    <p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px;">{journey_name}</p>
                </td>
            </tr>
        </table>
    </div>
    
    {progress_to_ambassador}
    
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        O teu impacto na comunidade está a crescer. Continua a partilhar o teu link de convite!
    </p>
    
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold;">
            Ver o meu Dashboard
        </a>
    </div>
    """
    return get_email_base_template(content, "O teu convidado contribuiu! - 4Luis")

def get_admin_referral_notification_html(sponsor_name: str, sponsor_email: str, invitee_name: str, 
                                          invitee_email: str, amount: float, journey_name: str) -> str:
    """HTML template for admin notification when a referral contributes"""
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">📊 Nova Contribuição via Referral</h1>
    
    <div style="background-color: #FAFAF9; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr>
                <td colspan="2" style="padding-bottom: 16px; border-bottom: 1px solid #E6F4F1;">
                    <p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Contribuidor</p>
                    <p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px; font-weight: bold;">{invitee_name}</p>
                    <p style="margin: 2px 0 0 0; color: #6B6661; font-size: 14px;">{invitee_email}</p>
                </td>
            </tr>
            <tr>
                <td colspan="2" style="padding: 16px 0; border-bottom: 1px solid #E6F4F1;">
                    <p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Sponsor (quem convidou)</p>
                    <p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px; font-weight: bold;">{sponsor_name}</p>
                    <p style="margin: 2px 0 0 0; color: #6B6661; font-size: 14px;">{sponsor_email}</p>
                </td>
            </tr>
            <tr>
                <td style="padding-top: 16px; width: 50%;">
                    <p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Valor</p>
                    <p style="margin: 4px 0 0 0; color: #FFBE98; font-size: 24px; font-weight: bold;">{amount}€</p>
                </td>
                <td style="padding-top: 16px; width: 50%;">
                    <p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Viagem</p>
                    <p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px;">{journey_name}</p>
                </td>
            </tr>
        </table>
    </div>
    
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/admin" style="display: inline-block; padding: 14px 32px; background-color: #2D2A26; color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: bold;">
            Abrir Painel Admin
        </a>
    </div>
    """
    return get_email_base_template(content, "Notificação Admin - Contribuição Referral")

def get_ambassador_unlocked_email_html(name: str) -> str:
    """HTML template for ambassador unlock notification"""
    content = f"""
    <div style="text-align: center; margin-bottom: 24px;">
        <span style="font-size: 64px;">🎖️</span>
    </div>
    
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 28px; text-align: center;">
        Parabéns, {name}!
    </h1>
    <p style="margin: 0 0 24px 0; color: #FFBE98; font-size: 20px; text-align: center; font-style: italic;">
        És agora Embaixador 4Luis
    </p>
    
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="margin: 0 0 16px 0; color: #2D2A26; font-weight: bold;">O que conquistaste:</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">✅ Contribuíste para a viagem principal</p>
        <p style="margin: 0; color: #6B6661; font-size: 14px;">✅ Convidaste 3+ pessoas que também contribuíram</p>
    </div>
    
    <div style="background: linear-gradient(135deg, #FFBE9820, #E6F4F120); border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="margin: 0 0 16px 0; color: #2D2A26; font-weight: bold;">Como Embaixador, agora podes:</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">🌟 Candidatar-te a criar a tua própria viagem de sonho</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">💜 Receber contribuições da comunidade</p>
        <p style="margin: 0; color: #6B6661; font-size: 14px;">✨ Inspirar outros a sonhar</p>
    </div>
    
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 16px 40px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 16px;">
            Começar a Criar o Meu Sonho
        </a>
    </div>
    """
    return get_email_base_template(content, "Parabéns Embaixador! - 4Luis")

async def send_email_resend(to_email: str, subject: str, html_content: str) -> dict:
    """Send email using Resend API (non-blocking)"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, email not sent")
        return {"status": "skipped", "reason": "API key not configured"}
    
    email_id = f"email_{uuid.uuid4().hex[:12]}"
    
    # Log email to database
    email_doc = {
        "email_id": email_id,
        "to_email": to_email,
        "subject": subject,
        "status": "sending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None,
        "error": None
    }
    await db.email_queue.insert_one(email_doc)
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        result = await asyncio.to_thread(resend.Emails.send, params)
        
        await db.email_queue.update_one(
            {"email_id": email_id},
            {"$set": {
                "status": "sent",
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "resend_id": result.get("id")
            }}
        )
        
        logger.info(f"Email sent successfully: {email_id} to {to_email}")
        return {"status": "sent", "email_id": email_id, "resend_id": result.get("id")}
        
    except Exception as e:
        error_msg = str(e)
        await db.email_queue.update_one(
            {"email_id": email_id},
            {"$set": {"status": "failed", "error": error_msg}}
        )
        logger.error(f"Failed to send email {email_id}: {error_msg}")
        return {"status": "failed", "email_id": email_id, "error": error_msg}

# ==================== BEHAVIORAL EMAIL FUNCTIONS ====================

async def send_contribution_email(contribution: dict, journey: dict):
    """
    EMAIL 1: Send email to contributor when contribution is confirmed
    """
    if not contribution.get("contributor_email"):
        return
    
    is_crypto = contribution.get("payment_method") == "crypto"
    crypto_type = contribution.get("crypto_type") if is_crypto else None
    
    html = get_contribution_email_html(
        contributor_name=contribution.get("contributor_name", "Sonhador"),
        amount=contribution.get("amount"),
        journey_name=journey.get("name", ""),
        is_crypto=is_crypto,
        crypto_type=crypto_type
    )
    
    await send_email_resend(
        to_email=contribution["contributor_email"],
        subject=f"Contribuição de {contribution.get('amount')}€ confirmada - 4Luis",
        html_content=html
    )

async def send_referral_contribution_emails(contribution: dict, journey: dict, contributor_user: dict, sponsor_user: dict):
    """
    EMAIL 2: When an invited user contributes, notify:
    - The sponsor (who invited them)
    - The admin (internal notification)
    """
    sponsor_email = sponsor_user.get("email")
    sponsor_name = sponsor_user.get("name", "Sonhador")
    invitee_name = contributor_user.get("name", contribution.get("contributor_name", "Sonhador"))
    invitee_email = contributor_user.get("email", contribution.get("contributor_email", ""))
    amount = contribution.get("amount")
    journey_name = journey.get("name", "")
    
    # Get sponsor's progress to ambassador
    valid_referrals = sponsor_user.get("valid_referrals_count", 0)
    contributed_to_main = sponsor_user.get("contributed_to_main_trip", False)
    
    # EMAIL 2a: Email to sponsor
    if sponsor_email:
        sponsor_html = get_referral_contribution_email_html(
            sponsor_name=sponsor_name,
            invitee_name=invitee_name,
            amount=amount,
            journey_name=journey_name,
            valid_referrals=valid_referrals,
            contributed_to_main=contributed_to_main
        )
        
        await send_email_resend(
            to_email=sponsor_email,
            subject=f"🌟 {invitee_name} contribuiu {amount}€ - O teu convite funcionou!",
            html_content=sponsor_html
        )
    
    # EMAIL 2b: Internal email to admin
    admin_html = get_admin_referral_notification_html(
        sponsor_name=sponsor_name,
        sponsor_email=sponsor_email or "N/A",
        invitee_name=invitee_name,
        invitee_email=invitee_email,
        amount=amount,
        journey_name=journey_name
    )
    
    await send_email_resend(
        to_email=ADMIN_EMAIL,
        subject=f"[Admin] Contribuição Referral: {invitee_name} → {amount}€",
        html_content=admin_html
    )

async def send_ambassador_unlocked_email(user_id: str):
    """
    EMAIL 3: Send email when a user unlocks Ambassador level
    """
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user or not user.get("email"):
        return
    
    html = get_ambassador_unlocked_email_html(
        name=user.get("name", "Embaixador")
    )
    
    await send_email_resend(
        to_email=user["email"],
        subject="🎖️ Parabéns! És agora Embaixador 4Luis!",
        html_content=html
    )
    
    logger.info(f"Ambassador unlocked email sent to user {user_id}")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email já registado")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    is_admin = user_data.password == ADMIN_PASSWORD
    
    # Resolve sponsor_id from sponsor_code (CRÍTICO - imutável após registo)
    sponsor_id = None
    if user_data.sponsor_code:
        sponsor_link = await db.sponsor_links.find_one(
            {"link_id": user_data.sponsor_code}, 
            {"_id": 0, "user_id": 1}
        )
        if sponsor_link:
            sponsor_id = sponsor_link["user_id"]
            # Incrementar referral_count do sponsor_link
            await db.sponsor_links.update_one(
                {"link_id": user_data.sponsor_code},
                {"$inc": {"referral_count": 1}}
            )
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "surname": user_data.surname,
        "password_hash": hash_password(user_data.password),
        "is_admin": is_admin,
        "avatar": None,
        "use_real_name": True,
        # Modelo v2: visitante (não registado) | sonhador (registado) | embaixador (contribuiu + 3 referrals)
        "sponsor_id": sponsor_id,  # IMUTÁVEL - quem convidou este utilizador
        "level": "sonhador",  # sonhador | embaixador (visitante = não registado)
        "contributed_to_main_trip": False,  # Tem contribuição confirmada na viagem principal
        "valid_referrals_count": 0,  # Referências que confirmaram contribuição
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "embaixador_unlocked_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_jwt_token(user_id, is_admin)
    return {
        "token": token,
        "user": {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "is_admin": is_admin
        }
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = create_jwt_token(user["user_id"], user.get("is_admin", False))
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user.get("is_admin", False)
        }
    }

@api_router.post("/auth/google/session")
async def process_google_session(request: Request, response: Response):
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id é obrigatório")
    
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Sessão Google inválida")
        google_data = resp.json()
    
    email = google_data.get("email")
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        is_admin = existing_user.get("is_admin", False)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": google_data.get("name"), "picture": google_data.get("picture")}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        is_admin = False
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": google_data.get("name"),
            "picture": google_data.get("picture"),
            "is_admin": is_admin,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    session_token = google_data.get("session_token")
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "user": {
            "user_id": user_id,
            "email": email,
            "name": google_data.get("name"),
            "picture": google_data.get("picture"),
            "is_admin": is_admin
        }
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logout realizado com sucesso"}

# ==================== JOURNEYS ROUTES ====================

@api_router.get("/journeys", response_model=List[dict])
async def get_journeys():
    journeys = await db.journeys.find({"is_active": True}, {"_id": 0}).to_list(100)
    return journeys

@api_router.get("/journeys/{journey_id}")
async def get_journey(journey_id: str):
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    return journey

@api_router.post("/admin/journeys")
async def create_journey(journey_data: JourneyCreate, request: Request):
    user = await require_admin(request)
    
    journey = Journey(**journey_data.model_dump())
    doc = journey.model_dump()
    doc["owner_user_id"] = user.user_id  # Admin que criou a viagem
    doc["status"] = "ativa"  # Default status - Portuguese
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.journeys.insert_one(doc)
    # Return without _id
    doc.pop("_id", None)
    return doc

@api_router.put("/admin/journeys/{journey_id}")
async def update_journey(journey_id: str, update_data: JourneyUpdate, request: Request):
    await require_admin(request)
    
    updates = {k: v for k, v in update_data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.journeys.update_one({"journey_id": journey_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    return await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})

@api_router.delete("/admin/journeys/{journey_id}")
async def delete_journey(journey_id: str, request: Request):
    await require_admin(request)
    result = await db.journeys.delete_one({"journey_id": journey_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    return {"message": "Viagem eliminada com sucesso"}

@api_router.get("/admin/journeys", response_model=List[dict])
async def get_all_journeys_admin(request: Request):
    await require_admin(request)
    journeys = await db.journeys.find({}, {"_id": 0}).to_list(100)
    return journeys

# ==================== CONTRIBUTIONS & PAYMENTS ====================

# ==================== CONTRIBUTIONS & PAYMENTS (v2) ====================

@api_router.get("/contributions/config")
async def get_contribution_config():
    """Get contribution configuration (fixed amounts and payment methods)"""
    return {
        "fixed_amounts": FIXED_CONTRIBUTION_AMOUNTS,
        "payment_methods": PAYMENT_METHODS,
        "crypto_types": CRYPTO_TYPES,
        "currency": "EUR",
        "note": "A plataforma não retém comissões. As contribuições vão diretamente para o sonhador."
    }

@api_router.post("/contributions/create")
async def create_contribution(request: Request):
    """Create a new contribution (for both Stripe and direct payments)"""
    data = await request.json()
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    journey_id = data.get("journey_id")
    sponsor_code = data.get("sponsor_code")
    contributor_name = data.get("contributor_name")
    contributor_email = data.get("contributor_email")
    
    # Validate amount
    if amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(
            status_code=400, 
            detail=f"Montante inválido. Valores permitidos: {FIXED_CONTRIBUTION_AMOUNTS}"
        )
    
    # Validate payment method
    if payment_method not in PAYMENT_METHODS:
        raise HTTPException(
            status_code=400, 
            detail=f"Método de pagamento inválido. Métodos permitidos: {list(PAYMENT_METHODS.keys())}"
        )
    
    # Check if journey exists and is the main trip
    journey = await db.journeys.find_one({"journey_id": journey_id, "is_active": True}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada ou inativa")
    
    # Validate crypto_type if payment_method is crypto
    crypto_type = data.get("crypto_type")
    tx_hash = data.get("tx_hash")
    
    if payment_method == "crypto":
        if not crypto_type or crypto_type not in CRYPTO_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de criptomoeda inválido. Tipos permitidos: {list(CRYPTO_TYPES.keys())}"
            )
    
    user = await get_current_user(request)
    user_id = user.user_id if user else None
    public_message = data.get("public_message")
    show_name = data.get("show_name", True)
    
    contribution_id = f"contrib_{uuid.uuid4().hex[:12]}"
    
    # For Stripe payments, create checkout session
    if payment_method == "stripe":
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
        )
        
        api_key = os.environ.get("STRIPE_API_KEY")
        if not api_key or api_key == 'sk_test_emergent':
            raise HTTPException(status_code=500, detail="Stripe não configurado")
        
        origin_url = data.get("origin_url", "https://journey-fund-3.preview.emergentagent.com")
        host_url = str(request.base_url).rstrip("/")
        webhook_url = f"{host_url}/api/webhook/stripe"
        
        stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
        
        success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/journey/{journey_id}"
        
        checkout_request = CheckoutSessionRequest(
            amount=float(amount),
            currency="eur",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "journey_id": journey_id,
                "user_id": user_id or "anonymous",
                "contribution_id": contribution_id,
                "sponsor_code": sponsor_code or "",
                "source": "4luis_platform"
            }
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        session_id = session.session_id
        
        # Create contribution record
        contribution_doc = {
            "contribution_id": contribution_id,
            "journey_id": journey_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "EUR",
            "payment_method": "stripe",
            "status": "pending",
            "is_main_trip": True,
            "sponsor_link_id": sponsor_code,
            "session_id": session_id,
            "contributor_name": contributor_name or (user.name if user else None),
            "contributor_email": contributor_email or (user.email if user else None),
            "public_message": public_message,
            "show_name": show_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.contributions.insert_one(contribution_doc)
        
        return {
            "contribution_id": contribution_id,
            "payment_method": "stripe",
            "checkout_url": session.url,
            "session_id": session_id
        }
    
    # For direct payments (MBWay, PayPal, Revolut, Wise, Crypto)
    else:
        contribution_doc = {
            "contribution_id": contribution_id,
            "journey_id": journey_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "EUR",
            "payment_method": payment_method,
            "crypto_type": crypto_type if payment_method == "crypto" else None,
            "tx_hash": tx_hash if payment_method == "crypto" else None,
            "status": "pending",  # Requires admin confirmation
            "is_main_trip": True,
            "sponsor_link_id": sponsor_code,
            "contributor_name": contributor_name or (user.name if user else None),
            "contributor_email": contributor_email or (user.email if user else None),
            "public_message": public_message,
            "show_name": show_name,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.contributions.insert_one(contribution_doc)
        
        # Update user's crypto badge if this is a crypto contribution
        if payment_method == "crypto" and user_id:
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"has_crypto_contribution": True}}
            )
        
        return {
            "contribution_id": contribution_id,
            "payment_method": payment_method,
            "crypto_type": crypto_type,
            "status": "pending",
            "message": "Contribuição registada. Aguarda confirmação após o pagamento ser recebido."
        }

@api_router.get("/contributions/payment-info")
async def get_payment_info():
    """Get direct payment information including all crypto addresses"""
    return {
        "mbway": {
            "phone": "+351968068535",
            "name": "Luis"
        },
        "paypal": {
            "link": "paypal.me/LuisCanarias"
        },
        "revolut": {
            "tag": "@luis4dreams",
            "note": "Usa o tag Revolut para enviar"
        },
        "wise": {
            "email": "luis@4luis.com"
        },
        "crypto": {
            "btc": {
                "name": "Bitcoin",
                "symbol": "BTC",
                "network": "Bitcoin Network",
                "address": "bc1qw34att4qwerdapfpzy3e98xz894uy7kz3sd7vm",
                "color": "#F7931A"
            },
            "eth": {
                "name": "Ethereum",
                "symbol": "ETH",
                "network": "Ethereum (ERC20)",
                "address": "0x48dF0E85dA06688445f3eEabaBE9DF57bA10A991",
                "color": "#627EEA"
            },
            "usdt": {
                "name": "Tether",
                "symbol": "USDT",
                "network": "Tron (TRC20)",
                "address": "TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL",
                "color": "#26A17B",
                "warning": "Use a mesma rede de depósito (TRC20) para que as criptomoedas não se percam."
            },
            "usdc": {
                "name": "USD Coin",
                "symbol": "USDC",
                "network": "XDC Network",
                "address": "xdc48dF0E85dA06688445f3eEabaBE9DF57bA10A991",
                "color": "#2775CA"
            }
        },
        "note": "A plataforma não retém comissões. O valor integral vai diretamente para o sonhador."
    }

@api_router.get("/journeys/{journey_id}/contributions")
async def get_journey_public_contributions(journey_id: str):
    """Get public feed of confirmed contributions for a journey"""
    # Get confirmed contributions only
    contributions = await db.contributions.find(
        {
            "journey_id": journey_id,
            "status": {"$in": ["confirmed", "completed"]}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    public_feed = []
    for c in contributions:
        # Determine display name
        if c.get("show_name", True):
            # Try to get user info if user_id exists
            if c.get("user_id"):
                user = await db.users.find_one({"user_id": c["user_id"]}, {"_id": 0, "name": 1, "anonymous_alias": 1, "use_real_name": 1})
                if user:
                    if user.get("use_real_name", True):
                        display_name = user.get("name", c.get("contributor_name", "Apoiante"))
                    else:
                        display_name = user.get("anonymous_alias", "Sonhador Anónimo")
                else:
                    display_name = c.get("contributor_name", "Apoiante")
            else:
                display_name = c.get("contributor_name", "Apoiante")
        else:
            display_name = "Sonhador Anónimo"
        
        # Check if crypto payment for badge
        is_crypto = c.get("payment_method") == "crypto"
        crypto_type = c.get("crypto_type") if is_crypto else None
        
        public_feed.append({
            "contribution_id": c["contribution_id"],
            "display_name": display_name,
            "amount": c["amount"],
            "message": c.get("public_message"),
            "is_crypto": is_crypto,
            "crypto_type": crypto_type,
            "created_at": c.get("created_at") or c.get("confirmed_at")
        })
    
    return {
        "count": len(public_feed),
        "contributions": public_feed
    }

@api_router.get("/journeys/{journey_id}/progress")
async def get_journey_progress(journey_id: str, request: Request):
    """Get journey progress - percentage is public, goal amount is admin-only"""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    
    # Calculate percentage (can exceed 100%)
    percentage = (current_amount / goal_amount) * 100 if goal_amount > 0 else 0
    is_funded = percentage >= 100
    
    # Check if user is admin to include goal_amount
    is_admin = False
    try:
        user = await get_current_user(request)
        if user:
            user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
            is_admin = user_data.get("is_admin", False) if user_data else False
    except:
        pass
    
    response = {
        "journey_id": journey_id,
        "current_amount": current_amount,
        "percentage": round(percentage, 1),
        "is_funded": is_funded,
        "status": journey.get("status", "active"),
        "target_date": journey.get("target_date"),
        "closing_message": "Financiamento total quase a fechar." if is_funded else None
    }
    
    # Only include goal_amount for admins
    if is_admin:
        response["goal_amount"] = goal_amount
    
    return response

@api_router.get("/contributions/checkout-status/{session_id}")
async def get_checkout_status(session_id: str, request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update payment transaction
    if status.payment_status == "paid":
        # Check if already processed
        existing = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if existing and existing.get("payment_status") != "completed":
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Update contribution
            contribution = await db.contributions.find_one({"session_id": session_id}, {"_id": 0})
            if contribution:
                # Calculate points (1 point per 5€)
                points_count = int(contribution["amount"] / 5)
                
                await db.contributions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "completed", "points_count": points_count}}
                )
                
                # Update journey amount
                await db.journeys.update_one(
                    {"journey_id": contribution["journey_id"]},
                    {"$inc": {"current_amount": contribution["amount"]}}
                )
                
                # Generate points if user has a sponsor link with 3+ referrals
                if contribution.get("user_id"):
                    await generate_points_for_user(contribution["user_id"], contribution["journey_id"], 
                                                   contribution["contribution_id"], points_count, contribution.get("is_crypto", False))
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        logger.info(f"Webhook received: {webhook_response.event_type}")
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

@api_router.post("/contributions/manual")
async def record_manual_contribution(request: Request):
    data = await request.json()
    journey_id = data.get("journey_id")
    amount = data.get("amount")  # Direct amount value
    payment_method = data.get("payment_method")
    is_crypto = data.get("is_crypto", False)
    sponsor_code = data.get("sponsor_code")
    name = data.get("name")
    surname = data.get("surname")
    email = data.get("email")
    
    # Validate amount against fixed amounts
    if amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(status_code=400, detail=f"Montante inválido. Valores permitidos: {FIXED_CONTRIBUTION_AMOUNTS}")
    
    user = await get_current_user(request)
    
    # If user provides data, create/update user
    user_id = None
    if email:
        existing = await db.users.find_one({"email": email}, {"_id": 0})
        if existing:
            user_id = existing["user_id"]
        else:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.insert_one({
                "user_id": user_id,
                "email": email,
                "name": name or "",
                "surname": surname or "",
                "is_admin": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    elif user:
        user_id = user.user_id
    
    # Calculate points (double for crypto)
    base_points = int(amount / 5)
    points_count = base_points * 2 if is_crypto else base_points
    
    contribution_id = f"contrib_{uuid.uuid4().hex[:12]}"
    contribution_doc = {
        "contribution_id": contribution_id,
        "journey_id": journey_id,
        "user_id": user_id,
        "amount": amount,
        "currency": "EUR" if not is_crypto else "USDT",
        "payment_method": payment_method,
        "is_crypto": is_crypto,
        "status": "pending_confirmation",
        "points_count": points_count,
        "sponsor_link_id": sponsor_code,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contributions.insert_one(contribution_doc)
    
    return {
        "contribution_id": contribution_id,
        "points_count": points_count,
        "message": "Contribuição registada. Aguarda confirmação do pagamento."
    }

# ==================== SPONSOR LINKS ====================

@api_router.post("/sponsor-links/create")
async def create_sponsor_link(request: Request):
    user = await require_auth(request)
    data = await request.json()
    journey_id = data.get("journey_id")
    
    # Check if link already exists
    existing = await db.sponsor_links.find_one(
        {"user_id": user.user_id, "journey_id": journey_id}, {"_id": 0}
    )
    if existing:
        return existing
    
    link = SponsorLink(user_id=user.user_id, journey_id=journey_id)
    doc = link.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.sponsor_links.insert_one(doc)
    # Return clean response without _id (MongoDB adds _id to doc after insert)
    return {
        "link_id": doc["link_id"],
        "user_id": doc["user_id"],
        "journey_id": doc["journey_id"],
        "referral_count": doc["referral_count"],
        "successful_referrals": doc["successful_referrals"],
        "created_at": doc["created_at"]
    }

@api_router.get("/sponsor-links/my-links")
async def get_my_sponsor_links(request: Request):
    user = await require_auth(request)
    links = await db.sponsor_links.find({"user_id": user.user_id}, {"_id": 0}).to_list(100)
    return links

@api_router.get("/sponsor-links/{link_id}")
async def get_sponsor_link(link_id: str):
    link = await db.sponsor_links.find_one({"link_id": link_id}, {"_id": 0})
    if not link:
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return link

@api_router.post("/sponsor-links/{link_id}/track")
async def track_sponsor_referral(link_id: str):
    result = await db.sponsor_links.update_one(
        {"link_id": link_id},
        {"$inc": {"referral_count": 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return {"message": "Referência registada"}

async def generate_points_for_user(user_id: str, journey_id: str, contribution_id: str, 
                                    points_count: int, is_crypto: bool):
    """Generate points for a user based on their contribution"""
    # Check if user has 3+ successful referrals (required to earn points)
    link = await db.sponsor_links.find_one(
        {"user_id": user_id, "journey_id": journey_id}, {"_id": 0}
    )
    
    if not link or link.get("successful_referrals", 0) < 3:
        return  # Not eligible for points yet
    
    # Get user initials for registration number
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    name_initial = (user.get("name", "X")[0]).upper() if user else "X"
    surname_initial = (user.get("surname", "X")[0]).upper() if user and user.get("surname") else "X"
    
    # Generate registration numbers (points)
    existing_count = await db.points.count_documents({"journey_id": journey_id})
    
    for i in range(points_count):
        registration_number = existing_count + i + 1
        point_id = f"{name_initial}{surname_initial}1{str(registration_number).zfill(7)}"
        
        await db.points.insert_one({
            "point_id": point_id,
            "user_id": user_id,
            "journey_id": journey_id,
            "contribution_id": contribution_id,
            "points_value": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

# ==================== USER POINTS ====================

@api_router.get("/points/my-points")
async def get_my_points(request: Request):
    """Get all points for the authenticated user"""
    user = await require_auth(request)
    points = await db.points.find({"user_id": user.user_id}, {"_id": 0}).to_list(1000)
    
    # Calculate total points
    total_points = sum(p.get("points_value", 1) for p in points)
    
    return {
        "points": points,
        "total_points": total_points,
        "registration_numbers": [p["point_id"] for p in points]
    }

@api_router.get("/points/journey/{journey_id}")
async def get_journey_points(journey_id: str, request: Request):
    """Get user's points for a specific journey"""
    user = await require_auth(request)
    points = await db.points.find(
        {"user_id": user.user_id, "journey_id": journey_id}, {"_id": 0}
    ).to_list(1000)
    return points

# ==================== USER CONTRIBUTIONS ====================

@api_router.get("/contributions/my-contributions")
async def get_my_contributions(request: Request):
    """Get all contributions for the authenticated user"""
    user = await require_auth(request)
    contributions = await db.contributions.find(
        {"user_id": user.user_id, "status": "completed"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Calculate totals
    total_amount = sum(c.get("amount", 0) for c in contributions)
    total_count = len(contributions)
    last_contribution = contributions[0] if contributions else None
    
    return {
        "contributions": contributions,
        "total_amount": total_amount,
        "total_count": total_count,
        "last_contribution": last_contribution
    }

@api_router.get("/dashboard/user-stats")
async def get_user_dashboard_stats(request: Request):
    """Get comprehensive stats for user dashboard - Modelo v2: sonhador → embaixador"""
    user = await require_auth(request)
    user_id = user.user_id
    
    # Get full user data
    user_data = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    
    # Get main journey (first active one)
    main_journey = await db.journeys.find_one(
        {"is_active": True, "status": "active"},
        {"_id": 0}
    )
    
    # Get user's contributions
    contributions = await db.contributions.find(
        {"user_id": user_id, "status": "completed"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    total_contributed = sum(c.get("amount", 0) for c in contributions)
    
    # Check if user has contributed to main trip
    contributed_to_main = False
    if main_journey:
        main_trip_contribution = await db.contributions.find_one({
            "user_id": user_id,
            "journey_id": main_journey["journey_id"],
            "status": "completed"
        })
        contributed_to_main = main_trip_contribution is not None
    
    # Get sponsor links and calculate impact
    sponsor_links = await db.sponsor_links.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    # Calculate impact: sum of contributions from users who registered via this user's link
    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1}
    ).to_list(1000)
    invited_user_ids = [u["user_id"] for u in invited_users]
    
    # Total contributed by invited users (these are the "valid referrals")
    invited_contributions = await db.contributions.find(
        {"user_id": {"$in": invited_user_ids}, "status": "completed"},
        {"_id": 0}
    ).to_list(10000)
    impact_amount = sum(c.get("amount", 0) for c in invited_contributions)
    
    # Count unique users who contributed (valid referrals)
    valid_referrals_from_db = user_data.get("valid_referrals_count", 0)
    
    # Get main sponsor link for this journey
    main_sponsor_link = None
    if main_journey:
        main_sponsor_link = await db.sponsor_links.find_one(
            {"user_id": user_id, "journey_id": main_journey["journey_id"]},
            {"_id": 0}
        )
    
    # Calculate progression status
    level = user_data.get("level", "sonhador")
    can_become_embaixador = contributed_to_main and valid_referrals_from_db >= 3 and level != "embaixador"
    
    return {
        "user": {
            "user_id": user_id,
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "level": level,  # sonhador | embaixador
            "contributed_to_main_trip": contributed_to_main or user_data.get("contributed_to_main_trip", False),
            "valid_referrals_count": valid_referrals_from_db,
            "embaixador_unlocked_at": user_data.get("embaixador_unlocked_at"),
            "can_become_embaixador": can_become_embaixador
        },
        "contributions": {
            "total_amount": total_contributed,
            "total_count": len(contributions),
            "last_contribution": contributions[0] if contributions else None
        },
        "invites": {
            "total_invited": len(invited_users),
            "total_contributed_by_invites": len(invited_contributions),
            "impact_amount": impact_amount,
            "sponsor_links": sponsor_links
        },
        "main_journey": main_journey,
        "main_sponsor_link": main_sponsor_link
    }

# ==================== USER PROFILE ====================

@api_router.post("/user/complete-onboarding")
async def complete_onboarding(request: Request):
    """Mark user onboarding as complete"""
    user = await require_auth(request)
    data = await request.json()
    
    initial_action = data.get("initial_action")  # support, explore, plan
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "onboarding_completed": True,
            "onboarding_completed_at": datetime.now(timezone.utc).isoformat(),
            "onboarding_initial_action": initial_action
        }}
    )
    
    return {
        "message": "Onboarding completo",
        "initial_action": initial_action
    }

@api_router.get("/user/onboarding-status")
async def get_onboarding_status(request: Request):
    """Check if user has completed onboarding"""
    user = await require_auth(request)
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    
    return {
        "onboarding_completed": user_data.get("onboarding_completed", False),
        "onboarding_completed_at": user_data.get("onboarding_completed_at"),
        "initial_action": user_data.get("onboarding_initial_action")
    }

@api_router.get("/profile")
async def get_user_profile(request: Request):
    """Get current user profile with privacy settings"""
    user = await require_auth(request)
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return user_data

@api_router.put("/profile")
async def update_user_profile(request: Request):
    """Update user profile including privacy settings"""
    user = await require_auth(request)
    data = await request.json()
    
    allowed_fields = ["name", "surname", "alias", "use_real_name", "avatar"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # If user is going anonymous and doesn't have an anonymous identity yet, generate one
    if "use_real_name" in updates and updates["use_real_name"] == False:
        current_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
        
        # Generate alias if not already set
        if not current_user.get("anonymous_alias"):
            updates["anonymous_alias"] = generate_anonymous_alias()
        
        # Generate anonymous avatar if not already set
        if not current_user.get("anonymous_avatar"):
            updates["anonymous_avatar"] = generate_anonymous_avatar(user.user_id)
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": updates}
    )
    
    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0})
    return updated_user

@api_router.post("/profile/generate-anonymous")
async def generate_anonymous_identity(request: Request):
    """Generate a new anonymous identity (alias and avatar) for the user"""
    user = await require_auth(request)
    
    new_alias = generate_anonymous_alias()
    new_avatar = generate_anonymous_avatar(uuid.uuid4().hex[:8])
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {
            "anonymous_alias": new_alias,
            "anonymous_avatar": new_avatar,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "anonymous_alias": new_alias,
        "anonymous_avatar": new_avatar
    }

@api_router.post("/profile/avatar")
async def upload_avatar(request: Request):
    """Upload user avatar image (accepts base64 encoded image)"""
    user = await require_auth(request)
    data = await request.json()
    
    image_data = data.get("image")
    if not image_data:
        raise HTTPException(status_code=400, detail="Imagem não fornecida")
    
    # Validate that it's a valid base64 image data URL
    if not image_data.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Formato de imagem inválido")
    
    # Check image size (max 500KB for base64)
    if len(image_data) > 700000:  # ~500KB in base64
        raise HTTPException(status_code=400, detail="Imagem muito grande. Máximo 500KB.")
    
    # Update user avatar
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"avatar": image_data, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Avatar atualizado com sucesso", "avatar": image_data}

# ==================== TRANSLATION ====================

@api_router.post("/translate")
async def translate_texts(translation_req: TranslationRequest):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de tradução não configurada")
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"translate_{uuid.uuid4().hex[:8]}",
        system_message=f"""You are a professional translator. Translate the provided texts to {translation_req.target_language}. 
        Keep the emotional, warm, and poetic tone. Return ONLY a JSON object with the same keys but translated values.
        Do not add any explanation, just the JSON."""
    ).with_model("openai", "gpt-5.2")
    
    texts_json = str(translation_req.texts)
    user_message = UserMessage(text=f"Translate this JSON to {translation_req.target_language}: {texts_json}")
    
    try:
        response = await chat.send_message(user_message)
        # Parse response as JSON
        import json
        # Clean response
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        translated = json.loads(clean_response)
        return {"translations": translated, "note": "Tradução automática por IA. Podem existir pequenas imprecisões."}
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return {"translations": translation_req.texts, "error": "Erro na tradução"}

# ==================== STRIPE SUBSCRIPTIONS ====================

@api_router.post("/subscription/create-checkout")
async def create_subscription_checkout(request: Request):
    """Create Stripe Checkout Session for Sonhador subscription (€10/month)"""
    user = await require_auth(request)
    
    if not STRIPE_API_KEY or STRIPE_API_KEY == 'sk_test_emergent':
        raise HTTPException(status_code=500, detail="Stripe não configurado")
    
    # Get full user data from DB
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    
    # Check if user already has active subscription
    if user_data and user_data.get("subscription_active"):
        raise HTTPException(status_code=400, detail="Já tens uma subscrição ativa")
    
    # Get frontend URL for redirects
    frontend_url = os.environ.get('FRONTEND_URL', 'https://journey-fund-3.preview.emergentagent.com')
    
    try:
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price": STRIPE_SONHADOR_PRICE_ID,
                "quantity": 1
            }],
            client_reference_id=user.user_id,
            customer_email=user.email,
            success_url=f"{frontend_url}/dashboard?sub=success",
            cancel_url=f"{frontend_url}/dashboard?sub=cancel",
            metadata={
                "user_id": user.user_id,
                "product": "sonhador"
            }
        )
        
        # Log the checkout creation
        await db.subscription_logs.insert_one({
            "log_id": f"log_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "event": "checkout_created",
            "session_id": checkout_session.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error creating checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar sessão de pagamento: {str(e)}")

@api_router.post("/stripe/subscription-webhook")
async def stripe_subscription_webhook(request: Request):
    """Handle Stripe subscription webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # Log raw webhook
    await db.subscription_logs.insert_one({
        "log_id": f"log_{uuid.uuid4().hex[:12]}",
        "event": "webhook_received",
        "payload_size": len(payload),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    event_id = None
    try:
        # Verify webhook signature if secret is configured
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            event_type = event.type
            event_id = event.id
            event_data = event.data.object
        else:
            # For testing without webhook secret - parse JSON directly
            import json
            payload_json = json.loads(payload)
            event_type = payload_json.get("type")
            event_id = payload_json.get("id", f"test_{uuid.uuid4().hex[:8]}")
            event_data = payload_json.get("data", {}).get("object", {})
    except ValueError as e:
        logging.error(f"Invalid webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Invalid webhook signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    logging.info(f"Processing Stripe webhook: {event_type}")
    
    # Handle checkout.session.completed - Subscription started
    if event_type == "checkout.session.completed":
        user_id = event_data.get("client_reference_id") or event_data.get("metadata", {}).get("user_id")
        
        if user_id and event_data.get("mode") == "subscription":
            await activate_subscription(user_id, event_data.get("subscription"), event_data.get("customer"))
            
    # Handle invoice.paid - Payment successful
    elif event_type == "invoice.paid":
        customer_id = event_data.get("customer")
        subscription_id = event_data.get("subscription")
        
        if subscription_id:
            # Find user by stripe_customer_id or subscription_id
            user = await db.users.find_one({
                "$or": [
                    {"stripe_customer_id": customer_id},
                    {"stripe_subscription_id": subscription_id}
                ]
            }, {"_id": 0})
            
            if user:
                await db.users.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "subscription_active": True,
                        "last_payment_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
    
    # Handle invoice.payment_failed - Payment failed
    elif event_type == "invoice.payment_failed":
        customer_id = event_data.get("customer")
        
        user = await db.users.find_one({"stripe_customer_id": customer_id}, {"_id": 0})
        if user:
            await db.subscription_logs.insert_one({
                "log_id": f"log_{uuid.uuid4().hex[:12]}",
                "user_id": user["user_id"],
                "event": "payment_failed",
                "invoice_id": event_data.get("id"),
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            # Could notify user here (P2)
    
    # Handle customer.subscription.deleted - Subscription cancelled
    elif event_type == "customer.subscription.deleted":
        customer_id = event_data.get("customer")
        customer_email = event_data.get("customer_email")
        
        # Try to find user by customer_id first, then by email
        user = await db.users.find_one({"stripe_customer_id": customer_id}, {"_id": 0})
        if not user and customer_email:
            user = await db.users.find_one({"email": customer_email}, {"_id": 0})
        
        if user:
            await deactivate_subscription(user["user_id"])
    
    # Log the processed event
    await db.subscription_logs.insert_one({
        "log_id": f"log_{uuid.uuid4().hex[:12]}",
        "event": f"webhook_processed_{event_type}",
        "event_id": event_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "success"}

async def activate_subscription(user_id: str, subscription_id: str = None, customer_id: str = None):
    """Activate subscription and check Premium eligibility"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        logging.error(f"User not found for subscription activation: {user_id}")
        return
    
    # Update user with subscription data
    update_data = {
        "subscription_active": True,
        "level": "sonhador",
        "subscription_started_at": datetime.now(timezone.utc).isoformat()
    }
    
    if subscription_id:
        update_data["stripe_subscription_id"] = subscription_id
    if customer_id:
        update_data["stripe_customer_id"] = customer_id
    
    # Check Premium eligibility: subscription + 3 valid referrals
    valid_referrals = user.get("valid_referrals_count", 0)
    if valid_referrals >= 3:
        update_data["level"] = "premium"
        update_data["premium_unlocked_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    # Log activation
    await db.subscription_logs.insert_one({
        "log_id": f"log_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "event": "subscription_activated",
        "level": update_data["level"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logging.info(f"Subscription activated for user {user_id}, level: {update_data['level']}")

async def deactivate_subscription(user_id: str):
    """Deactivate subscription - user loses Premium if had it"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return
    
    # Keep valid_referrals_count, just change level
    new_level = "sonhador" if user.get("valid_referrals_count", 0) >= 1 else "curioso"
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "subscription_active": False,
            "level": new_level,
            "subscription_ended_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log deactivation
    await db.subscription_logs.insert_one({
        "log_id": f"log_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "event": "subscription_deactivated",
        "previous_level": user.get("level"),
        "new_level": new_level,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logging.info(f"Subscription deactivated for user {user_id}, level changed to: {new_level}")

@api_router.get("/subscription/status")
async def get_subscription_status(request: Request):
    """Get current user's subscription status"""
    user = await require_auth(request)
    
    # Get full user data from DB
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_data:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    return {
        "subscription_active": user_data.get("subscription_active", False),
        "level": user_data.get("level", "curioso"),
        "valid_referrals_count": user_data.get("valid_referrals_count", 0),
        "subscription_started_at": user_data.get("subscription_started_at"),
        "premium_unlocked_at": user_data.get("premium_unlocked_at"),
        "can_upgrade_to_premium": user_data.get("subscription_active", False) and user_data.get("valid_referrals_count", 0) >= 3 and user_data.get("level") != "premium"
    }

# ==================== ADMIN STATS ====================

@api_router.get("/admin/stats")
async def get_admin_stats(request: Request):
    await require_admin(request)
    
    total_contributions = await db.contributions.count_documents({"status": "completed"})
    total_amount = 0
    contributions = await db.contributions.find({"status": "completed"}, {"_id": 0}).to_list(10000)
    for c in contributions:
        total_amount += c.get("amount", 0)
    
    total_users = await db.users.count_documents({})
    total_journeys = await db.journeys.count_documents({})
    
    return {
        "total_contributions": total_contributions,
        "total_amount_raised": total_amount,
        "total_users": total_users,
        "total_journeys": total_journeys
    }

# ==================== RAFFLE STATS (PUBLIC) ====================

@api_router.get("/raffle-stats")
async def get_public_raffle_stats():
    """Get public statistics about completed raffles"""
    # Get all raffle results
    raffles = await db.raffle_results.find({}, {"_id": 0}).sort("drawn_at", -1).to_list(100)
    
    total_raffles = len(raffles)
    total_prize_amount = sum(r.get("prize_amount", 0) for r in raffles)
    
    # Get winners with privacy respect
    winners = []
    for raffle in raffles:
        winner_user_id = raffle.get("winner_user_id")
        if winner_user_id:
            user = await db.users.find_one({"user_id": winner_user_id}, {"_id": 0})
            if user:
                # Check privacy settings
                use_real_name = user.get("use_real_name", True)
                if use_real_name and user.get("name"):
                    display_name = user.get("name", "").split()[0]  # First name only
                    display_avatar = user.get("avatar") or user.get("picture")
                else:
                    # Use anonymous identity
                    display_name = user.get("anonymous_alias") or user.get("alias") or "Sonhador Anónimo"
                    display_avatar = user.get("anonymous_avatar") or user.get("avatar") or user.get("picture")
                
                # Get journey name
                journey = await db.journeys.find_one({"journey_id": raffle.get("journey_id")}, {"_id": 0, "name": 1})
                
                winners.append({
                    "name": display_name,
                    "avatar_url": display_avatar,
                    "journey_name": journey.get("name") if journey else "",
                    "prize_amount": raffle.get("prize_amount", 0),
                    "drawn_at": raffle.get("drawn_at")
                })
    
    return {
        "total_raffles": total_raffles,
        "total_prize_amount": total_prize_amount,
        "winners": winners
    }

# ==================== SITE SETTINGS ====================

@api_router.get("/settings")
async def get_site_settings():
    """Get public site settings"""
    settings = await db.site_settings.find_one({"setting_id": "main"}, {"_id": 0})
    if not settings:
        # Default settings
        return {
            "contact_email": "contacto@4luis.com",
            "contact_message": "Tem alguma questão? Entre em contacto connosco."
        }
    return {
        "contact_email": settings.get("contact_email", "contacto@4luis.com"),
        "contact_message": settings.get("contact_message", "Tem alguma questão? Entre em contacto connosco.")
    }

@api_router.put("/admin/settings")
async def update_site_settings(request: Request):
    """Update site settings (admin only)"""
    await require_admin(request)
    data = await request.json()
    
    await db.site_settings.update_one(
        {"setting_id": "main"},
        {"$set": {
            "setting_id": "main",
            "contact_email": data.get("contact_email"),
            "contact_message": data.get("contact_message"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"message": "Configurações atualizadas com sucesso"}

@api_router.get("/admin/settings")
async def get_admin_settings(request: Request):
    """Get all site settings (admin only)"""
    await require_admin(request)
    settings = await db.site_settings.find_one({"setting_id": "main"}, {"_id": 0})
    if not settings:
        return {
            "contact_email": "contacto@4luis.com",
            "contact_message": "Tem alguma questão? Entre em contacto connosco."
        }
    return settings

# ==================== DREAMERS STATS ====================

@api_router.get("/dreamers-stats")
async def get_dreamers_stats():
    """Get public statistics about dreamers (contributors) - top dreamer based on POINTS"""
    # Count unique dreamers (users who contributed)
    pipeline = [
        {"$match": {"status": {"$in": ["completed", "pending_confirmation"]}}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "total"}
    ]
    result = await db.contributions.aggregate(pipeline).to_list(1)
    total_dreamers = result[0]["total"] if result else 0
    
    # Get top dreamer by POINTS (not monetary contribution)
    top_pipeline = [
        {"$group": {
            "_id": "$user_id",
            "total_points": {"$sum": "$points_value"}
        }},
        {"$sort": {"total_points": -1}},
        {"$limit": 1}
    ]
    top_result = await db.points.aggregate(top_pipeline).to_list(1)
    
    top_dreamer = None
    top_journey_name = None
    
    if top_result:
        top_user_id = top_result[0]["_id"]
        total_points = top_result[0]["total_points"]
        
        user = await db.users.find_one({"user_id": top_user_id}, {"_id": 0})
        if user:
            # Get the journey this user supported most
            journey_pipeline = [
                {"$match": {"user_id": top_user_id}},
                {"$group": {"_id": "$journey_id", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 1}
            ]
            journey_result = await db.points.aggregate(journey_pipeline).to_list(1)
            
            if journey_result:
                journey = await db.journeys.find_one({"journey_id": journey_result[0]["_id"]}, {"_id": 0, "name": 1})
                if journey:
                    top_journey_name = journey.get("name")
            
            # Check if user wants to show real name or stay anonymous
            use_real_name = user.get("use_real_name", True)
            if use_real_name and user.get("name"):
                display_name = user.get("name", "Anónimo").split()[0]
                display_avatar = user.get("avatar") or user.get("picture")
            else:
                display_name = user.get("anonymous_alias") or user.get("alias") or "Sonhador Anónimo"
                display_avatar = user.get("anonymous_avatar") or user.get("avatar") or user.get("picture")
            
            top_dreamer = {
                "name": display_name,
                "has_avatar": bool(display_avatar),
                "avatar_url": display_avatar,
                "total_points": total_points,
                "journey_name": top_journey_name,
                "tagline": f"Sonhou mais alto com {top_journey_name}" if top_journey_name else None
            }
    
    return {
        "total_dreamers": total_dreamers,
        "top_dreamer": top_dreamer
    }

# ==================== ADMIN CONTRIBUTIONS MANAGEMENT ====================

@api_router.get("/admin/contributions")
async def get_all_contributions(request: Request):
    """Get all contributions for admin management"""
    await require_admin(request)
    contributions = await db.contributions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Enrich with user and journey info
    for contrib in contributions:
        if contrib.get("user_id"):
            user = await db.users.find_one({"user_id": contrib["user_id"]}, {"_id": 0, "name": 1, "email": 1})
            contrib["user_name"] = user.get("name") if user else "Desconhecido"
            contrib["user_email"] = user.get("email") if user else ""
        else:
            contrib["user_name"] = "Anónimo"
            contrib["user_email"] = ""
        
        journey = await db.journeys.find_one({"journey_id": contrib["journey_id"]}, {"_id": 0, "name": 1})
        contrib["journey_name"] = journey.get("name") if journey else "Desconhecida"
    
    return contributions

@api_router.put("/admin/contributions/{contribution_id}/confirm")
async def confirm_contribution(contribution_id: str, request: Request):
    """Confirm a manual payment contribution"""
    await require_admin(request)
    
    contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")
    
    if contribution["status"] == "completed":
        return {"message": "Contribuição já confirmada"}
    
    # Update contribution status
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "status": "completed", 
            "confirmed": True,  # Campo explícito de confirmação
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update journey amount
    await db.journeys.update_one(
        {"journey_id": contribution["journey_id"]},
        {"$inc": {"current_amount": contribution["amount"]}}
    )
    
    # Check if journey reached goal - update status automatically
    await check_and_update_journey_funding_status(contribution["journey_id"])
    
    # Update sponsor link if applicable
    if contribution.get("sponsor_link_id"):
        await db.sponsor_links.update_one(
            {"link_id": contribution["sponsor_link_id"]},
            {"$inc": {"successful_referrals": 1}}
        )
    
    # MOTOR EMBAIXADOR v2: Verificar progressão do utilizador que contribuiu E do sponsor
    if contribution.get("user_id"):
        contributing_user = await db.users.find_one({"user_id": contribution["user_id"]}, {"_id": 0})
        
        # Marcar que o utilizador contribuiu para a viagem principal
        # (consideramos a primeira viagem ativa como "principal" ou is_main_trip=True)
        main_journey = await db.journeys.find_one(
            {"$or": [{"is_main_trip": True}, {"is_active": True, "status": "ativa"}]}, 
            {"_id": 0}
        )
        is_main_trip = main_journey and contribution["journey_id"] == main_journey.get("journey_id")
        
        if is_main_trip and contributing_user:
            # Atualizar contributed_to_main_trip
            await db.users.update_one(
                {"user_id": contribution["user_id"]},
                {"$set": {"contributed_to_main_trip": True}}
            )
            
            # Verificar se este utilizador agora qualifica para Embaixador
            valid_refs = contributing_user.get("valid_referrals_count", 0)
            current_level = contributing_user.get("level", "sonhador")
            
            if valid_refs >= 3 and current_level != "embaixador":
                await db.users.update_one(
                    {"user_id": contribution["user_id"]},
                    {"$set": {
                        "level": "embaixador",
                        "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                # Send email notification
                await send_ambassador_unlocked_email(contribution["user_id"])
        
        # Se o utilizador que contribuiu tem sponsor, incrementar valid_referrals_count do sponsor
        if contributing_user and contributing_user.get("sponsor_id"):
            sponsor_user_id = contributing_user["sponsor_id"]
            
            # Incrementar valid_referrals_count do sponsor
            await db.users.update_one(
                {"user_id": sponsor_user_id},
                {"$inc": {"valid_referrals_count": 1}}
            )
            
            # Verificar se sponsor atinge condições Embaixador
            sponsor = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0})
            if sponsor:
                valid_refs = sponsor.get("valid_referrals_count", 0)
                contributed = sponsor.get("contributed_to_main_trip", False)
                current_level = sponsor.get("level", "sonhador")
                
                # MOTOR EMBAIXADOR: contributed_to_main_trip + valid_referrals >= 3 = embaixador
                was_already_ambassador = current_level == "embaixador"
                if contributed and valid_refs >= 3 and not was_already_ambassador:
                    await db.users.update_one(
                        {"user_id": sponsor_user_id},
                        {"$set": {
                            "level": "embaixador",
                            "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    # EMAIL 3: Send ambassador unlock email to sponsor
                    await send_ambassador_unlocked_email(sponsor_user_id)
                
                # EMAIL 2: Send referral contribution emails (to sponsor + admin)
                journey_for_email = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
                if journey_for_email:
                    # Refresh sponsor data to get updated valid_referrals_count
                    sponsor_updated = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0})
                    await send_referral_contribution_emails(
                        contribution=contribution,
                        journey=journey_for_email,
                        contributor_user=contributing_user,
                        sponsor_user=sponsor_updated
                    )
    
    # Generate points if user has 3+ referrals
    if contribution.get("user_id"):
        await generate_points_for_user(
            contribution["user_id"], 
            contribution["journey_id"],
            contribution_id,
            contribution.get("points_count", 0),
            contribution.get("is_crypto", False)
        )
    
    # EMAIL 1: Send confirmation email to contributor
    journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
    if journey:
        await send_contribution_email(contribution, journey)
    
    return {"message": "Contribuição confirmada com sucesso"}

@api_router.get("/admin/emails")
async def get_email_queue(request: Request, status: Optional[str] = None, limit: int = 50):
    """Get email queue - Admin only"""
    await require_admin(request)
    
    query = {}
    if status:
        query["status"] = status
    
    emails = await db.email_queue.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Stats
    total = await db.email_queue.count_documents({})
    sent = await db.email_queue.count_documents({"status": "sent"})
    queued = await db.email_queue.count_documents({"status": "queued"})
    failed = await db.email_queue.count_documents({"status": "failed"})
    
    return {
        "emails": emails,
        "stats": {
            "total": total,
            "sent": sent,
            "queued": queued,
            "failed": failed
        }
    }

@api_router.get("/admin/sponsors-report")
async def get_sponsors_report(request: Request):
    """Get report of sponsors who have 3+ successful referrals - Admin only"""
    await require_admin(request)
    
    # Find all sponsor links with 3+ successful referrals
    sponsors = await db.sponsor_links.find(
        {"successful_referrals": {"$gte": 3}},
        {"_id": 0}
    ).to_list(1000)
    
    report = []
    for sponsor in sponsors:
        user = await db.users.find_one({"user_id": sponsor["user_id"]}, {"_id": 0, "name": 1, "email": 1, "alias": 1})
        journey = await db.journeys.find_one({"journey_id": sponsor["journey_id"]}, {"_id": 0, "name": 1})
        
        # Get user's total points
        points = await db.points.find({"user_id": sponsor["user_id"]}, {"_id": 0}).to_list(1000)
        total_points = sum(p.get("points_value", 1) for p in points)
        registration_numbers = [p["point_id"] for p in points]
        
        report.append({
            "user_id": sponsor["user_id"],
            "user_name": user.get("name") if user else "Desconhecido",
            "user_email": user.get("email") if user else "",
            "alias": user.get("alias") if user else None,
            "journey_name": journey.get("name") if journey else "Desconhecida",
            "successful_referrals": sponsor["successful_referrals"],
            "total_referrals": sponsor["referral_count"],
            "total_points": total_points,
            "registration_numbers": registration_numbers,
            "created_at": sponsor.get("created_at")
        })
    
    # Sort by total points descending
    report.sort(key=lambda x: x["total_points"], reverse=True)
    
    return {
        "total_qualified_sponsors": len(report),
        "sponsors": report
    }

@api_router.put("/admin/contributions/{contribution_id}/reject")
async def reject_contribution(contribution_id: str, request: Request):
    """Reject a contribution"""
    admin = await require_admin(request)
    
    result = await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "status": "rejected", 
            "validated_by": admin.user_id,
            "validated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")
    
    return {"message": "Contribuição rejeitada"}

# ==================== ADMIN CONTRIBUTION REPORTS ====================

@api_router.get("/admin/contributions/reports")
async def get_contribution_reports(request: Request):
    """Get comprehensive contribution reports for admin"""
    await require_admin(request)
    
    # Get all completed contributions
    all_contributions = await db.contributions.find(
        {"status": "confirmed"},
        {"_id": 0}
    ).to_list(10000)
    
    # Also include "completed" status for backwards compatibility
    completed_contributions = await db.contributions.find(
        {"status": "completed"},
        {"_id": 0}
    ).to_list(10000)
    
    contributions = all_contributions + completed_contributions
    
    # 1. Group by amount
    by_amount = {}
    for c in contributions:
        amount = c.get("amount", 0)
        if amount not in by_amount:
            by_amount[amount] = {"count": 0, "total": 0}
        by_amount[amount]["count"] += 1
        by_amount[amount]["total"] += amount
    
    # Sort by amount
    amount_report = [
        {"amount": amt, "count": data["count"], "total": data["total"]}
        for amt, data in sorted(by_amount.items())
    ]
    
    # 2. Group by payment method
    by_method = {}
    for c in contributions:
        method = c.get("payment_method", "unknown")
        if method not in by_method:
            by_method[method] = {"count": 0, "total": 0, "method_info": PAYMENT_METHODS.get(method, {})}
        by_method[method]["count"] += 1
        by_method[method]["total"] += c.get("amount", 0)
    
    method_report = [
        {"method": method, "name": data["method_info"].get("name", method), "count": data["count"], "total": data["total"]}
        for method, data in by_method.items()
    ]
    
    # 3. Temporal history (last 30 days, grouped by day)
    from collections import defaultdict
    temporal = defaultdict(lambda: {"count": 0, "total": 0})
    
    for c in contributions:
        created_at = c.get("created_at", "")
        if isinstance(created_at, str):
            day = created_at[:10]  # YYYY-MM-DD
        else:
            day = created_at.strftime("%Y-%m-%d")
        temporal[day]["count"] += 1
        temporal[day]["total"] += c.get("amount", 0)
    
    # Sort by date and get last 30 days
    temporal_report = [
        {"date": day, "count": data["count"], "total": data["total"]}
        for day, data in sorted(temporal.items(), reverse=True)[:30]
    ]
    
    # 4. Summary totals
    total_amount = sum(c.get("amount", 0) for c in contributions)
    total_count = len(contributions)
    avg_contribution = total_amount / total_count if total_count > 0 else 0
    
    # 5. Pending contributions
    pending = await db.contributions.find(
        {"status": "pending"},
        {"_id": 0}
    ).to_list(1000)
    pending_count = len(pending)
    pending_amount = sum(c.get("amount", 0) for c in pending)
    
    return {
        "summary": {
            "total_confirmed": total_count,
            "total_amount": total_amount,
            "average_contribution": round(avg_contribution, 2),
            "pending_count": pending_count,
            "pending_amount": pending_amount
        },
        "by_amount": amount_report,
        "by_payment_method": method_report,
        "temporal_history": temporal_report
    }

@api_router.get("/admin/contributions/pending")
async def get_pending_contributions(request: Request):
    """Get all pending contributions that need admin validation"""
    await require_admin(request)
    
    pending = await db.contributions.find(
        {"status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    # Enrich with user info
    for contrib in pending:
        if contrib.get("user_id"):
            user = await db.users.find_one(
                {"user_id": contrib["user_id"]}, 
                {"_id": 0, "name": 1, "email": 1}
            )
            contrib["user_name"] = user.get("name") if user else contrib.get("contributor_name", "Desconhecido")
            contrib["user_email"] = user.get("email") if user else contrib.get("contributor_email", "")
        else:
            contrib["user_name"] = contrib.get("contributor_name", "Anónimo")
            contrib["user_email"] = contrib.get("contributor_email", "")
        
        journey = await db.journeys.find_one(
            {"journey_id": contrib["journey_id"]}, 
            {"_id": 0, "name": 1}
        )
        contrib["journey_name"] = journey.get("name") if journey else "Desconhecida"
    
    return {
        "count": len(pending),
        "contributions": pending
    }

@api_router.put("/admin/contributions/{contribution_id}/validate")
async def validate_contribution(contribution_id: str, request: Request):
    """Validate (confirm or reject) a contribution with notes"""
    admin = await require_admin(request)
    data = await request.json()
    
    action = data.get("action")  # "confirm" or "reject"
    notes = data.get("notes", "")
    
    if action not in ["confirm", "reject"]:
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'confirm' ou 'reject'")
    
    contribution = await db.contributions.find_one(
        {"contribution_id": contribution_id}, 
        {"_id": 0}
    )
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")
    
    if contribution["status"] != "pending":
        raise HTTPException(status_code=400, detail="Esta contribuição já foi processada")
    
    new_status = "confirmed" if action == "confirm" else "rejected"
    
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "status": new_status,
            "validated_by": admin.user_id,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes
        }}
    )
    
    # If confirmed, update journey amount and check progression
    if action == "confirm":
        # Update journey amount
        await db.journeys.update_one(
            {"journey_id": contribution["journey_id"]},
            {"$inc": {"current_amount": contribution["amount"]}}
        )
        
        # Check if journey reached goal - use helper function
        await check_and_update_journey_funding_status(contribution["journey_id"])
        
        # MOTOR EMBAIXADOR: Update user progression
        if contribution.get("user_id"):
            user = await db.users.find_one(
                {"user_id": contribution["user_id"]}, 
                {"_id": 0}
            )
            
            if user:
                # Mark contributed to main trip
                main_journey = await db.journeys.find_one(
                    {"$or": [{"is_main_trip": True}, {"is_active": True, "status": "ativa"}]}, 
                    {"_id": 0}
                )
                is_main = main_journey and contribution["journey_id"] == main_journey.get("journey_id")
                
                if is_main:
                    await db.users.update_one(
                        {"user_id": contribution["user_id"]},
                        {"$set": {"contributed_to_main_trip": True}}
                    )
                    
                    # Check embaixador eligibility
                    valid_refs = user.get("valid_referrals_count", 0)
                    if valid_refs >= 3 and user.get("level") != "embaixador":
                        await db.users.update_one(
                            {"user_id": contribution["user_id"]},
                            {"$set": {
                                "level": "embaixador",
                                "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                
                # Update sponsor's referral count
                if user.get("sponsor_id"):
                    sponsor_id = user["sponsor_id"]
                    await db.users.update_one(
                        {"user_id": sponsor_id},
                        {"$inc": {"valid_referrals_count": 1}}
                    )
                    
                    # Check sponsor's embaixador eligibility
                    sponsor = await db.users.find_one(
                        {"user_id": sponsor_id}, 
                        {"_id": 0}
                    )
                    if sponsor:
                        if (sponsor.get("contributed_to_main_trip") and 
                            sponsor.get("valid_referrals_count", 0) >= 3 and 
                            sponsor.get("level") != "embaixador"):
                            await db.users.update_one(
                                {"user_id": sponsor_id},
                                {"$set": {
                                    "level": "embaixador",
                                    "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                                }}
                            )
    
    return {
        "message": f"Contribuição {new_status}",
        "contribution_id": contribution_id,
        "status": new_status
    }

# ==================== ADMIN USER MANAGEMENT ====================

@api_router.put("/admin/users/{user_id}/subscription")
async def toggle_user_subscription(user_id: str, request: Request):
    """Toggle subscription_active for a user (v1 - manual activation)"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    new_status = not user.get("subscription_active", False)
    update_data = {"subscription_active": new_status}
    
    # Check if user now qualifies for premium
    if new_status and user.get("valid_referrals_count", 0) >= 3:
        update_data["level"] = "premium"
        update_data["premium_unlocked_at"] = datetime.now(timezone.utc).isoformat()
    elif not new_status and user.get("level") == "premium":
        # Downgrade from premium if subscription deactivated
        update_data["level"] = "sonhador" if user.get("valid_referrals_count", 0) >= 1 else "curioso"
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    return {
        "message": f"Subscrição {'ativada' if new_status else 'desativada'}",
        "subscription_active": new_status,
        "level": update_data.get("level", user.get("level", "curioso"))
    }

@api_router.get("/admin/users/dashboard")
async def get_users_dashboard(request: Request):
    """Get comprehensive users dashboard with metrics and insights - Admin only"""
    await require_admin(request)
    
    # Get all users
    users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    # Get all contributions for calculations
    all_contributions = await db.contributions.find(
        {"status": "completed"},
        {"_id": 0}
    ).to_list(10000)
    
    # Calculate contribution totals per user
    user_contributions = {}
    for contrib in all_contributions:
        uid = contrib.get("user_id")
        if uid:
            if uid not in user_contributions:
                user_contributions[uid] = {"total": 0, "count": 0}
            user_contributions[uid]["total"] += contrib.get("amount", 0)
            user_contributions[uid]["count"] += 1
    
    # Calculate sponsor impact (€ generated by referrals)
    sponsor_impact = {}
    for user in users:
        if user.get("sponsor_id"):
            sponsor_id = user["sponsor_id"]
            if sponsor_id not in sponsor_impact:
                sponsor_impact[sponsor_id] = {"value": 0, "referrals": []}
            # Add this user's contributions to sponsor's impact
            user_contribs = user_contributions.get(user["user_id"], {"total": 0})
            sponsor_impact[sponsor_id]["value"] += user_contribs["total"]
            sponsor_impact[sponsor_id]["referrals"].append({
                "user_id": user["user_id"],
                "name": user.get("name"),
                "contributed": user_contribs["total"]
            })
    
    # Enrich users with all metrics
    enriched_users = []
    for user in users:
        user_id = user["user_id"]
        
        # Sponsor info
        sponsor_name = None
        if user.get("sponsor_id"):
            sponsor = await db.users.find_one(
                {"user_id": user["sponsor_id"]}, 
                {"_id": 0, "name": 1, "email": 1}
            )
            sponsor_name = sponsor.get("name") if sponsor else "Desconhecido"
        
        # Referrals made by this user
        referrals_made = await db.users.count_documents({"sponsor_id": user_id})
        
        # User's contributions
        contribs = user_contributions.get(user_id, {"total": 0, "count": 0})
        
        # Impact value (€ generated by people this user invited)
        impact = sponsor_impact.get(user_id, {"value": 0, "referrals": []})
        
        enriched_users.append({
            "user_id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "alias": user.get("alias"),
            "avatar": user.get("avatar"),
            "level": user.get("level", "curioso"),
            "subscription_active": user.get("subscription_active", False),
            "valid_referrals_count": user.get("valid_referrals_count", 0),
            "referrals_made": referrals_made,
            "contributions_total": contribs["total"],
            "contributions_count": contribs["count"],
            "sponsor_id": user.get("sponsor_id"),
            "sponsor_name": sponsor_name,
            "sponsor_impact_value": impact["value"],
            "invited_users": impact["referrals"],
            "registered_at": user.get("registered_at") or user.get("created_at"),
            "premium_unlocked_at": user.get("premium_unlocked_at"),
            "is_admin": user.get("is_admin", False)
        })
    
    # Sort by valid_referrals_count desc (identifies community builders)
    enriched_users.sort(key=lambda x: (x["valid_referrals_count"], x["sponsor_impact_value"]), reverse=True)
    
    # Calculate dashboard metrics
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    week_ago_iso = week_ago.isoformat()
    month_ago_iso = month_ago.isoformat()
    
    total_users = len(users)
    active_subscriptions = sum(1 for u in users if u.get("subscription_active"))
    premium_users = sum(1 for u in users if u.get("level") == "premium")
    sonhador_users = sum(1 for u in users if u.get("level") == "sonhador")
    curioso_users = sum(1 for u in users if u.get("level") == "curioso")
    
    # Active users (contributed in last 30 days)
    active_user_ids = set(c.get("user_id") for c in all_contributions if c.get("created_at", "") >= month_ago_iso)
    active_users = len(active_user_ids)
    sonhadores_ativos = sum(1 for u in users if u.get("level") == "sonhador" and u.get("user_id") in active_user_ids)
    premium_ativos = sum(1 for u in users if u.get("level") == "premium" and u.get("user_id") in active_user_ids)
    
    # Weekly signups
    weekly_signups = sum(1 for u in users if (u.get("registered_at") or u.get("created_at", "")) >= week_ago_iso)
    weekly_sonhadores = sum(1 for u in users if u.get("level") == "sonhador" and (u.get("registered_at") or u.get("created_at", "")) >= week_ago_iso)
    weekly_premium = sum(1 for u in users if u.get("level") == "premium" and (u.get("registered_at") or u.get("created_at", "")) >= week_ago_iso)
    
    # Total contributions
    total_contributions_value = sum(c.get("amount", 0) for c in all_contributions)
    total_contributions_count = len(all_contributions)
    average_contribution_value = total_contributions_value / total_contributions_count if total_contributions_count > 0 else 0
    
    # Referrals
    referrals_total = sum(u.get("referrals_made", 0) for u in enriched_users)
    valid_referrals_total = sum(u.get("valid_referrals_count", 0) for u in users)
    weekly_referrals = 0  # Would need timestamp tracking on referrals
    
    # Journeys funded
    all_journeys = await db.journeys.find({}, {"_id": 0}).to_list(100)
    journeys_funded = sum(1 for j in all_journeys if j.get("status") == "funded")
    journeys_active = sum(1 for j in all_journeys if j.get("status") == "active")
    
    # Top sponsors (by impact value)
    top_sponsors = sorted(
        [{"user_id": uid, "name": next((u["name"] for u in users if u["user_id"] == uid), "?"), "impact_value": data["value"], "referrals_count": len(data["referrals"])} 
         for uid, data in sponsor_impact.items() if data["value"] > 0],
        key=lambda x: x["impact_value"],
        reverse=True
    )[:5]
    
    # Top contributors (by total contributed)
    top_contributors = sorted(
        [{"user_id": u["user_id"], "name": u["name"], "total_contributed": u["contributions_total"], "contributions_count": u["contributions_count"]}
         for u in enriched_users if u["contributions_total"] > 0],
        key=lambda x: x["total_contributed"],
        reverse=True
    )[:5]
    
    # Platform Momentum Score (novos_registos + novos_sonhadores + contribuições_semana + referrals_válidos_semana)
    weekly_contributions = sum(1 for c in all_contributions if c.get("created_at", "") >= week_ago_iso)
    momentum_score = weekly_signups + weekly_sonhadores + weekly_contributions + valid_referrals_total
    
    # Referrals evolution by month
    referrals_by_month = []
    for u in users:
        reg_date = u.get("registered_at") or u.get("created_at", "")
        if reg_date and u.get("sponsor_id"):
            month_key = reg_date[:7]
            existing = next((r for r in referrals_by_month if r["month"] == month_key), None)
            if existing:
                existing["count"] += 1
            else:
                referrals_by_month.append({"month": month_key, "count": 1})
    referrals_by_month.sort(key=lambda x: x["month"])
    
    return {
        "metrics": {
            # Utilizadores
            "total_users": total_users,
            "active_users": active_users,
            "sonhadores_ativos": sonhadores_ativos,
            "premium_ativos": premium_ativos,
            "active_subscriptions": active_subscriptions,
            "premium_users": premium_users,
            "sonhador_users": sonhador_users,
            "curioso_users": curioso_users,
            # Financeiro
            "total_contributions_value": total_contributions_value,
            "total_contributions_count": total_contributions_count,
            "average_contribution_value": round(average_contribution_value, 2),
            "total_sponsor_impact": sum(s["value"] for s in sponsor_impact.values()),
            # Growth
            "weekly_signups": weekly_signups,
            "weekly_sonhadores": weekly_sonhadores,
            "weekly_premium": weekly_premium,
            "weekly_contributions": weekly_contributions,
            "referrals_total": referrals_total,
            "valid_referrals_total": valid_referrals_total,
            # Impacto social
            "journeys_funded": journeys_funded,
            "journeys_active": journeys_active,
            # Momentum
            "momentum_score": momentum_score
        },
        "level_distribution": {
            "curioso": curioso_users,
            "sonhador": sonhador_users,
            "premium": premium_users
        },
        "charts": {
            "signups_by_month": get_monthly_counts([u.get("registered_at") or u.get("created_at") for u in users]),
            "contributions_by_month": get_monthly_contributions(all_contributions),
            "referrals_by_month": referrals_by_month[-12:]
        },
        "top_sponsors": top_sponsors,
        "top_contributors": top_contributors,
        "users": enriched_users
    }

def get_monthly_counts(dates):
    """Group dates by month and count"""
    from collections import defaultdict
    counts = defaultdict(int)
    for date_str in dates:
        if date_str:
            try:
                # Handle ISO format
                month_key = date_str[:7]  # YYYY-MM
                counts[month_key] += 1
            except:
                pass
    # Return sorted by month
    return [{"month": k, "count": v} for k, v in sorted(counts.items())[-12:]]

def get_monthly_contributions(contributions):
    """Group contributions by month with totals"""
    from collections import defaultdict
    monthly = defaultdict(lambda: {"count": 0, "amount": 0})
    for contrib in contributions:
        date_str = contrib.get("created_at", "")
        if date_str:
            try:
                month_key = date_str[:7]  # YYYY-MM
                monthly[month_key]["count"] += 1
                monthly[month_key]["amount"] += contrib.get("amount", 0)
            except:
                pass
    return [{"month": k, "count": v["count"], "amount": v["amount"]} for k, v in sorted(monthly.items())[-12:]]

@api_router.get("/admin/users/{user_id}/detail")
async def get_user_detail(user_id: str, request: Request):
    """Get detailed user profile with full history - Admin only"""
    await require_admin(request)
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    # Get user's contributions
    contributions = await db.contributions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Get user's sponsor links
    sponsor_links = await db.sponsor_links.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get who this user invited
    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1, "created_at": 1, "level": 1}
    ).to_list(1000)
    
    # Get sponsor info
    sponsor_info = None
    if user.get("sponsor_id"):
        sponsor = await db.users.find_one(
            {"user_id": user["sponsor_id"]},
            {"_id": 0, "user_id": 1, "name": 1, "email": 1}
        )
        sponsor_info = sponsor
    
    # Calculate impact value
    impact_value = 0
    for invited in invited_users:
        invited_contribs = await db.contributions.find(
            {"user_id": invited["user_id"], "status": "completed"},
            {"_id": 0, "amount": 1}
        ).to_list(1000)
        invited["contributions_total"] = sum(c.get("amount", 0) for c in invited_contribs)
        impact_value += invited["contributions_total"]
    
    return {
        "user": user,
        "contributions": contributions,
        "contributions_total": sum(c.get("amount", 0) for c in contributions if c.get("status") == "completed"),
        "sponsor_links": sponsor_links,
        "sponsor_info": sponsor_info,
        "invited_users": invited_users,
        "sponsor_impact_value": impact_value
    }

@api_router.put("/admin/users/{user_id}/level")
async def update_user_level(user_id: str, request: Request):
    """Manually update user level - Admin only"""
    await require_admin(request)
    
    data = await request.json()
    new_level = data.get("level")
    
    if new_level not in ["curioso", "sonhador", "premium"]:
        raise HTTPException(status_code=400, detail="Nível inválido. Use: curioso, sonhador, premium")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    update_data = {"level": new_level}
    if new_level == "premium" and not user.get("premium_unlocked_at"):
        update_data["premium_unlocked_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    return {"message": f"Nível atualizado para {new_level}", "level": new_level}

@api_router.put("/admin/users/{user_id}/referrals")
async def update_user_referrals(user_id: str, request: Request):
    """Manually correct user's valid_referrals_count - Admin only"""
    await require_admin(request)
    
    data = await request.json()
    new_count = data.get("valid_referrals_count")
    
    if not isinstance(new_count, int) or new_count < 0:
        raise HTTPException(status_code=400, detail="Contagem inválida")
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"valid_referrals_count": new_count}}
    )
    
    # Check if premium conditions are now met
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if user and user.get("subscription_active") and new_count >= 3 and user.get("level") != "premium":
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"level": "premium", "premium_unlocked_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": f"Referrals atualizados para {new_count}", "valid_referrals_count": new_count}

@api_router.get("/admin/users")
async def get_all_users(request: Request):
    """Get all users with their sponsor/premium status - Admin only (simplified)"""
    await require_admin(request)
    
    users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0}
    ).to_list(1000)
    
    # Enrich with sponsor info
    for user in users:
        if user.get("sponsor_id"):
            sponsor = await db.users.find_one(
                {"user_id": user["sponsor_id"]}, 
                {"_id": 0, "name": 1, "email": 1}
            )
            user["sponsor_name"] = sponsor.get("name") if sponsor else "Desconhecido"
        
        # Count referrals made by this user
        referrals = await db.users.count_documents({"sponsor_id": user["user_id"]})
        user["referrals_made"] = referrals
    
    return {
        "total_users": len(users),
        "users": users
    }

@api_router.post("/admin/migrate-users")
async def migrate_existing_users(request: Request):
    """Add new fields to existing users (one-time migration)"""
    await require_admin(request)
    
    # Update all users that don't have the new fields
    result = await db.users.update_many(
        {"level": {"$exists": False}},
        {"$set": {
            "sponsor_id": None,
            "level": "curioso",
            "subscription_active": False,
            "valid_referrals_count": 0,
            "registered_at": None,
            "premium_unlocked_at": None
        }}
    )
    
    # Also update journeys that don't have new fields
    journey_result = await db.journeys.update_many(
        {"status": {"$exists": False}},
        {"$set": {
            "status": "active",
            "owner_user_id": None
        }}
    )
    
    return {
        "users_migrated": result.modified_count,
        "journeys_migrated": journey_result.modified_count,
        "message": "Migração concluída"
    }

# ==================== AMBASSADOR JOURNEYS ====================

async def check_and_update_journey_funding_status(journey_id: str):
    """Check if journey reached funding goal and update status automatically"""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return None
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    current_status = journey.get("status", "ativa")
    
    # Check if funded (100%+)
    if current_amount >= goal_amount and current_status == "ativa":
        # Update status to "financiada"
        await db.journeys.update_one(
            {"journey_id": journey_id},
            {"$set": {
                "status": "financiada",
                "funded_at": datetime.now(timezone.utc).isoformat(),
                "is_active": False,  # Remove from active journeys
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Create notification for admin
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "type": "journey_funded",
            "title": "Viagem Financiada!",
            "message": f"A viagem '{journey.get('name')}' atingiu o objetivo de financiamento.",
            "journey_id": journey_id,
            "for_admin": True,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # If ambassador journey, notify ambassador and send email
        if journey.get("is_ambassador_journey") and journey.get("ambassador_user_id"):
            ambassador_user_id = journey["ambassador_user_id"]
            
            # Create in-app notification
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "your_journey_funded",
                "title": "A tua viagem foi financiada!",
                "message": f"Parabéns! A tua viagem '{journey.get('name')}' atingiu o objetivo de financiamento.",
                "journey_id": journey_id,
                "user_id": ambassador_user_id,
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Send email to ambassador
            ambassador = await db.users.find_one({"user_id": ambassador_user_id}, {"_id": 0})
            if ambassador and ambassador.get("email"):
                await queue_email(
                    to_email=ambassador["email"],
                    to_name=ambassador.get("name", "Embaixador"),
                    subject="Parabéns! A tua viagem foi financiada! - 4Luis",
                    template="journey_funded",
                    data={
                        "ambassador_name": ambassador.get("name"),
                        "journey_name": journey.get("name"),
                        "journey_id": journey_id,
                        "amount_raised": current_amount
                    }
                )
        
        # Also send email to admin
        await queue_email(
            to_email="admin@4luis.com",
            to_name="Admin 4Luis",
            subject=f"Viagem Financiada: {journey.get('name')}",
            template="admin_journey_funded",
            data={
                "journey_name": journey.get("name"),
                "journey_id": journey_id,
                "amount_raised": current_amount,
                "ambassador_name": journey.get("ambassador_name", "N/A")
            }
        )
        
        logger.info(f"Journey {journey_id} automatically moved to 'financiada' status")
        return "financiada"
    
    return current_status

@api_router.post("/ambassador/journey/apply")
async def apply_for_ambassador_journey(request: Request):
    """Submit an application for an ambassador journey"""
    user = await require_auth(request)
    
    # Check if user is an ambassador
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_data or user_data.get("level") != "embaixador":
        raise HTTPException(status_code=403, detail="Apenas embaixadores podem candidatar-se a criar viagens")
    
    data = await request.json()
    
    # Validate required fields
    required = ["name", "poetic_name", "description", "emotional_message", "impact_description", "goal_amount", "application_message"]
    for field in required:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"Campo obrigatório em falta: {field}")
    
    journey_id = f"journey_{uuid.uuid4().hex[:12]}"
    
    journey_doc = {
        "journey_id": journey_id,
        "name": data["name"],
        "poetic_name": data["poetic_name"],
        "description": data["description"],
        "emotional_message": data["emotional_message"],
        "impact_description": data["impact_description"],
        "image_url": data.get("image_url", "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=800"),
        "goal_amount": float(data["goal_amount"]),
        "current_amount": 0.0,
        "currency": data.get("currency", "EUR"),
        "target_date": data.get("target_date"),
        "is_active": False,  # Not active until approved
        "is_main_trip": False,
        "status": "candidatura",  # Application status
        "is_ambassador_journey": True,
        "ambassador_user_id": user.user_id,
        "ambassador_name": user_data.get("name"),
        "application_message": data["application_message"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journeys.insert_one(journey_doc)
    
    # Notify admin
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "type": "ambassador_journey_application",
        "title": "Nova Candidatura de Viagem",
        "message": f"{user_data.get('name')} submeteu uma candidatura para a viagem '{data['name']}'.",
        "journey_id": journey_id,
        "user_id": user.user_id,
        "for_admin": True,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": "Candidatura submetida com sucesso",
        "journey_id": journey_id,
        "status": "candidatura"
    }

@api_router.get("/ambassador/my-journeys")
async def get_my_ambassador_journeys(request: Request):
    """Get all journeys created by the current ambassador"""
    user = await require_auth(request)
    
    journeys = await db.journeys.find(
        {"ambassador_user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "count": len(journeys),
        "journeys": journeys
    }

@api_router.get("/admin/ambassador-journeys")
async def get_ambassador_journeys(request: Request, status: Optional[str] = None):
    """Get all ambassador journeys - Admin only"""
    await require_admin(request)
    
    query = {"is_ambassador_journey": True}
    if status:
        query["status"] = status
    
    journeys = await db.journeys.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Group by status
    by_status = {}
    for s in JOURNEY_STATUSES:
        by_status[s] = [j for j in journeys if j.get("status") == s]
    
    return {
        "total": len(journeys),
        "by_status": by_status,
        "journeys": journeys
    }

@api_router.put("/admin/ambassador-journeys/{journey_id}/status")
async def update_ambassador_journey_status(journey_id: str, request: Request):
    """Update ambassador journey status - Admin only"""
    admin = await require_admin(request)
    data = await request.json()
    
    new_status = data.get("status")
    admin_notes = data.get("admin_notes")
    
    if new_status not in JOURNEY_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Estados permitidos: {list(JOURNEY_STATUSES.keys())}")
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Set timestamps based on status
    if new_status == "aprovada":
        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
        update_data["owner_user_id"] = admin.user_id
    elif new_status == "ativa":
        update_data["is_active"] = True
    elif new_status == "financiada":
        update_data["funded_at"] = datetime.now(timezone.utc).isoformat()
        update_data["is_active"] = False
    elif new_status == "realizada":
        update_data["realized_at"] = datetime.now(timezone.utc).isoformat()
        update_data["is_active"] = False
    elif new_status == "encerrada":
        update_data["closed_at"] = datetime.now(timezone.utc).isoformat()
        update_data["is_active"] = False
    
    if admin_notes:
        update_data["admin_notes"] = admin_notes
    
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": update_data}
    )
    
    # Notify ambassador
    if journey.get("ambassador_user_id"):
        status_messages = {
            "aprovada": "A tua candidatura de viagem foi aprovada!",
            "ativa": "A tua viagem está agora ativa e a receber contribuições!",
            "financiada": "Parabéns! A tua viagem foi totalmente financiada!",
            "realizada": "A tua viagem foi marcada como realizada!",
            "encerrada": "A tua viagem foi encerrada."
        }
        
        if new_status in status_messages:
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": f"journey_status_{new_status}",
                "title": f"Viagem: {JOURNEY_STATUSES[new_status]['name']}",
                "message": status_messages[new_status],
                "journey_id": journey_id,
                "user_id": journey["ambassador_user_id"],
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    return {
        "message": f"Estado atualizado para '{JOURNEY_STATUSES[new_status]['name']}'",
        "journey_id": journey_id,
        "new_status": new_status
    }

@api_router.get("/journeys/realized")
async def get_realized_journeys():
    """Get all realized/funded journeys (Sonhos Realizados section)"""
    journeys = await db.journeys.find(
        {"status": {"$in": ["financiada", "realizada"]}},
        {"_id": 0, "goal_amount": 0}  # Hide goal_amount from public
    ).sort("funded_at", -1).to_list(100)
    
    return {
        "count": len(journeys),
        "journeys": journeys
    }

@api_router.get("/journeys/active")
async def get_active_journeys():
    """Get all active journeys accepting contributions"""
    journeys = await db.journeys.find(
        {"status": "ativa", "is_active": True},
        {"_id": 0, "goal_amount": 0}  # Hide goal_amount from public
    ).sort("created_at", -1).to_list(100)
    
    # Add progress percentage
    for j in journeys:
        # Calculate progress without revealing goal
        j["is_funded"] = False
    
    return {
        "count": len(journeys),
        "journeys": journeys
    }

# ==================== RAFFLE SYSTEM ====================

@api_router.get("/admin/journeys-ready-for-raffle")
async def get_journeys_ready_for_raffle(request: Request):
    """Get all journeys that have reached their funding goal and are ready for raffle"""
    await require_admin(request)
    
    # Find journeys where current_amount >= goal_amount
    journeys = await db.journeys.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    ready_journeys = []
    for journey in journeys:
        if journey.get("current_amount", 0) >= journey.get("goal_amount", float('inf')):
            # Check if raffle already done for this journey
            existing_raffle = await db.raffle_results.find_one(
                {"journey_id": journey["journey_id"]},
                {"_id": 0}
            )
            
            # Count participants (users with points for this journey)
            participants_pipeline = [
                {"$match": {"journey_id": journey["journey_id"]}},
                {"$group": {"_id": "$user_id"}},
                {"$count": "total"}
            ]
            participants_result = await db.points.aggregate(participants_pipeline).to_list(1)
            participant_count = participants_result[0]["total"] if participants_result else 0
            
            ready_journeys.append({
                "journey_id": journey["journey_id"],
                "name": journey["name"],
                "goal_amount": journey["goal_amount"],
                "current_amount": journey["current_amount"],
                "participant_count": participant_count,
                "raffle_done": existing_raffle is not None,
                "raffle_result": existing_raffle
            })
    
    return {
        "ready_journeys": ready_journeys,
        "total_ready": len(ready_journeys)
    }

@api_router.get("/admin/raffle/{journey_id}")
async def get_raffle_participants(journey_id: str, request: Request):
    """Get all participants (users with points) for a journey raffle"""
    await require_admin(request)
    
    # Get all points for this journey
    points = await db.points.find({"journey_id": journey_id}, {"_id": 0}).to_list(10000)
    
    # Group by user and count their points
    user_points = {}
    for point in points:
        user_id = point["user_id"]
        if user_id not in user_points:
            user_points[user_id] = {"total_points": 0, "entries": []}
        user_points[user_id]["total_points"] += point.get("points_value", 1)
        user_points[user_id]["entries"].append(point["point_id"])
    
    # Enrich with user info
    participants = []
    for user_id, data in user_points.items():
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "name": 1, "email": 1})
        participants.append({
            "user_id": user_id,
            "user_name": user.get("name") if user else "Desconhecido",
            "user_email": user.get("email") if user else "",
            "total_points": data["total_points"],
            "entries": data["entries"]
        })
    
    # Sort by total points descending
    participants.sort(key=lambda x: x["total_points"], reverse=True)
    
    # Check if raffle already done
    existing_raffle = await db.raffle_results.find_one({"journey_id": journey_id}, {"_id": 0})
    
    return {
        "journey_id": journey_id,
        "total_participants": len(participants),
        "total_points": sum(p["total_points"] for p in participants),
        "participants": participants,
        "raffle_done": existing_raffle is not None,
        "raffle_result": existing_raffle
    }

@api_router.post("/admin/raffle/{journey_id}/draw")
async def draw_raffle_winner(journey_id: str, request: Request):
    """Draw a random winner from participants (weighted by points)"""
    import random
    
    await require_admin(request)
    
    # Check if raffle already done
    existing_raffle = await db.raffle_results.find_one({"journey_id": journey_id}, {"_id": 0})
    if existing_raffle:
        raise HTTPException(status_code=400, detail="Sorteio já foi realizado para esta viagem")
    
    # Get all points for this journey
    points = await db.points.find({"journey_id": journey_id}, {"_id": 0}).to_list(10000)
    
    if not points:
        raise HTTPException(status_code=400, detail="Não há participantes para este sorteio")
    
    # Random selection (each point is an entry)
    winning_point = random.choice(points)
    
    # Get winner info
    user = await db.users.find_one({"user_id": winning_point["user_id"]}, {"_id": 0})
    
    # Get journey info
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    
    # Save raffle result
    raffle_result = {
        "raffle_id": f"raffle_{uuid.uuid4().hex[:12]}",
        "journey_id": journey_id,
        "winning_point_id": winning_point["point_id"],
        "winner_user_id": winning_point["user_id"],
        "winner_name": user.get("name") if user else "Desconhecido",
        "winner_email": user.get("email") if user else "",
        "drawn_at": datetime.now(timezone.utc).isoformat()
    }
    await db.raffle_results.insert_one(raffle_result)
    
    return {
        "winner": {
            "point_id": winning_point["point_id"],
            "name": user.get("name") if user else "Desconhecido",
            "email": user.get("email") if user else ""
        },
        "total_entries": len(points),
        "journey_name": journey.get("name") if journey else ""
    }

# ==================== TRIP GALLERY ====================

@api_router.get("/gallery")
async def get_trip_gallery():
    """Get photos from completed trips by raffle winners"""
    photos = await db.trip_photos.find({"is_approved": True}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return photos

@api_router.post("/gallery/upload")
async def upload_trip_photo(request: Request):
    """Upload a trip photo (authenticated users who won a raffle)"""
    user = await require_auth(request)
    data = await request.json()
    
    # Check if user won a raffle
    raffle = await db.raffle_results.find_one({"winner_user_id": user.user_id}, {"_id": 0})
    if not raffle:
        raise HTTPException(status_code=403, detail="Apenas vencedores de sorteios podem adicionar fotos")
    
    photo_doc = {
        "photo_id": f"photo_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "journey_id": data.get("journey_id"),
        "image_url": data.get("image_url"),
        "caption": data.get("caption", ""),
        "location": data.get("location", ""),
        "is_approved": True,  # Auto-approve for now
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.trip_photos.insert_one(photo_doc)
    
    return {"message": "Foto adicionada com sucesso", "photo_id": photo_doc["photo_id"]}

@api_router.get("/admin/gallery")
async def get_all_gallery_photos(request: Request):
    """Get all gallery photos for admin"""
    await require_admin(request)
    photos = await db.trip_photos.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return photos

@api_router.put("/admin/gallery/{photo_id}/approve")
async def approve_gallery_photo(photo_id: str, request: Request):
    """Approve a gallery photo"""
    await require_admin(request)
    await db.trip_photos.update_one({"photo_id": photo_id}, {"$set": {"is_approved": True}})
    return {"message": "Foto aprovada"}

@api_router.delete("/admin/gallery/{photo_id}")
async def delete_gallery_photo(photo_id: str, request: Request):
    """Delete a gallery photo"""
    await require_admin(request)
    await db.trip_photos.delete_one({"photo_id": photo_id})
    return {"message": "Foto eliminada"}

# ==================== AI TRIP PLANNER ====================

@api_router.post("/journey/{journey_id}/ai-planner")
async def ai_trip_planner(journey_id: str, request: Request):
    """AI-powered trip planning assistant"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    data = await request.json()
    user_question = data.get("question", "")
    
    # Get journey info
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Serviço de IA não configurado")
    
    destination = journey.get("name", "")
    
    system_message = f"""Você é um assistente especializado em planeamento de viagens para {destination}. 
    Ajude o utilizador a planear a sua viagem de sonho com:
    - Roteiros detalhados (3, 5 ou 7 dias)
    - Melhores locais a visitar e atrações imperdíveis
    - Recomendações de hotéis e alojamentos para diferentes orçamentos
    - Restaurantes e gastronomia local
    - Dicas de transporte (como se deslocar, passes, apps úteis)
    - Melhor época para visitar
    - Dicas culturais e de etiqueta
    - Estimativas de custos
    - Segurança e precauções
    
    REGRAS DE FORMATAÇÃO IMPORTANTES:
    - Use texto limpo e bem estruturado
    - Use parágrafos separados para cada tópico
    - Use listas com hífens (-) para enumerar itens
    - NÃO use caracteres especiais como *, #, ** no início das frases
    - NÃO use markdown ou formatação especial
    - Seja claro, organizado e fácil de ler
    - Responda sempre em português de Portugal."""
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"planner_{journey_id}_{uuid.uuid4().hex[:8]}",
        system_message=system_message
    ).with_model("openai", "gpt-5.2")
    
    try:
        user_message = UserMessage(text=user_question or f"Ajuda-me a planear uma viagem para {destination}. O que me recomendas?")
        response = await chat.send_message(user_message)
        
        # Clean up the response - remove markdown formatting characters
        clean_response = response
        if isinstance(clean_response, str):
            # Remove markdown bold/italic markers
            clean_response = clean_response.replace("**", "").replace("__", "")
            clean_response = clean_response.replace("*", "").replace("_", "")
            # Remove markdown headers
            import re
            clean_response = re.sub(r'^#{1,6}\s*', '', clean_response, flags=re.MULTILINE)
            # Clean up excessive whitespace
            clean_response = re.sub(r'\n{3,}', '\n\n', clean_response)
        
        return {"response": clean_response, "destination": destination}
    except Exception as e:
        logger.error(f"AI Planner error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar pedido de IA")

@api_router.get("/travel-resources/{destination}")
async def get_custom_travel_resources(destination: str):
    """Get curated travel resources for any custom destination"""
    from urllib.parse import unquote
    
    destination = unquote(destination)
    destination_encoded = destination.replace(" ", "%20")
    destination_plus = destination.replace(" ", "+")
    destination_slug = destination.lower().replace(" ", "-")
    
    resources = {
        "destination": destination,
        "map": {
            "title": "Bing Maps",
            "description": f"Explore {destination} no mapa",
            "url": f"https://www.bing.com/maps?q={destination_plus}",
        },
        "hotels": [
            {"name": "Trivago", "url": f"https://www.trivago.pt/?search={destination_plus}"},
            {"name": "TripAdvisor", "url": f"https://www.tripadvisor.pt/Search?q={destination_plus}"},
            {"name": "Kayak", "url": f"https://www.kayak.pt/hotels/{destination_slug}"},
            {"name": "Airbnb", "url": f"https://www.airbnb.pt/s/{destination_encoded}/homes"},
            {"name": "ALL Accor", "url": "https://all.accor.com/pt-pt/world/index.shtml"}
        ],
        "flights": [
            {"name": "TAP", "url": "https://www.flytap.com/pt-pt"},
            {"name": "Ryanair", "url": "https://www.ryanair.com/pt/pt"},
            {"name": "EasyJet", "url": "https://www.easyjet.com/pt"},
            {"name": "Momondo", "url": f"https://www.momondo.pt/flight-search/{destination_slug}"}
        ],
        "social": [
            {"name": "GetYourGuide", "url": f"https://www.getyourguide.pt/s/?q={destination_plus}", "description": "Tours e atividades"},
            {"name": "Pinterest", "url": f"https://www.pinterest.pt/search/pins/?q={destination_plus}%20travel", "description": "Inspiração visual"},
            {"name": "WikiVoyage", "url": f"https://pt.wikivoyage.org/wiki/{destination_encoded}", "description": "Guia colaborativo"},
            {"name": "Reddit", "url": f"https://www.reddit.com/search/?q={destination_plus}%20travel", "description": "Experiências reais"}
        ]
    }
    
    return resources

@api_router.get("/journey/{journey_id}/travel-resources")
async def get_travel_resources(journey_id: str):
    """Get curated travel resources for a destination"""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    destination = journey.get("name", "")
    destination_encoded = destination.replace(" ", "%20")
    destination_plus = destination.replace(" ", "+")
    destination_slug = destination.lower().replace(" ", "-")
    
    # Build resource links for the destination
    resources = {
        "destination": destination,
        "map": {
            "title": "Bing Maps",
            "description": f"Explore {destination} no mapa",
            "url": f"https://www.bing.com/maps?q={destination_plus}",
            "icon": "map"
        },
        "hotels": [
            {
                "name": "Trivago",
                "url": f"https://www.trivago.pt/?search={destination_plus}",
                "icon": "trivago"
            },
            {
                "name": "TripAdvisor",
                "url": f"https://www.tripadvisor.pt/Search?q={destination_plus}",
                "icon": "tripadvisor"
            },
            {
                "name": "Kayak",
                "url": f"https://www.kayak.pt/hotels/{destination_slug}",
                "icon": "kayak"
            },
            {
                "name": "Airbnb",
                "url": f"https://www.airbnb.pt/s/{destination_encoded}/homes",
                "icon": "airbnb"
            },
            {
                "name": "ALL Accor",
                "url": "https://all.accor.com/pt-pt/world/index.shtml",
                "icon": "accor"
            }
        ],
        "flights": [
            {
                "name": "TAP",
                "url": "https://www.flytap.com/pt-pt",
                "icon": "tap"
            },
            {
                "name": "Ryanair",
                "url": "https://www.ryanair.com/pt/pt",
                "icon": "ryanair"
            },
            {
                "name": "EasyJet",
                "url": "https://www.easyjet.com/pt",
                "icon": "easyjet"
            },
            {
                "name": "Momondo",
                "url": f"https://www.momondo.pt/flight-search/{destination_slug}",
                "icon": "momondo"
            }
        ],
        "social": [
            {
                "name": "GetYourGuide",
                "url": f"https://www.getyourguide.pt/s/?q={destination_plus}",
                "icon": "getyourguide",
                "description": "Tours e atividades guiadas"
            },
            {
                "name": "Pinterest",
                "url": f"https://www.pinterest.pt/search/pins/?q={destination_plus}%20travel",
                "icon": "pinterest",
                "description": "Inspiração visual de viagem"
            },
            {
                "name": "WikiVoyage",
                "url": f"https://pt.wikivoyage.org/wiki/{destination_encoded}",
                "icon": "wikivoyage",
                "description": "Guia de viagem colaborativo"
            },
            {
                "name": "Reddit",
                "url": f"https://www.reddit.com/search/?q={destination_plus}%20travel",
                "icon": "reddit",
                "description": "Discussões e experiências reais"
            }
        ],
        "blogs": [
            {
                "name": "Alma de Viajante",
                "url": f"https://www.almadeviajante.com/?s={destination_encoded}",
                "icon": "blog",
                "description": "Blog português de viagens"
            },
            {
                "name": "Viaje Comigo",
                "url": f"https://www.viajecomigo.com/?s={destination_encoded}",
                "icon": "blog",
                "description": "Dicas e roteiros"
            },
            {
                "name": "Lonely Planet",
                "url": f"https://www.lonelyplanet.com/search?q={destination_encoded}",
                "icon": "lonelyplanet",
                "description": "Guias de viagem mundiais"
            }
        ]
    }
    
    return resources

# ==================== SEED DATA ====================

@api_router.post("/seed-journeys")
async def seed_journeys():
    # Check if already seeded
    count = await db.journeys.count_documents({})
    if count > 0:
        return {"message": "Dados já existem"}
    
    journeys = [
        {
            "journey_id": "journey_china001",
            "name": "China",
            "poetic_name": "Onde os Dragões Dançam",
            "description": "Uma viagem pela milenar cultura chinesa",
            "emotional_message": "Cada passo na Grande Muralha é um passo na história da humanidade",
            "impact_description": "Ajude o Luis a descobrir os segredos do Império do Meio",
            "image_url": "https://images.unsplash.com/photo-1758637689971-fe6124e7cabd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2ODl8MHwxfHNlYXJjaHwxfHxkcmVhbXklMjBjaGluYSUyMGxhbmRzY2FwZXxlbnwwfHx8fDE3NzA4MTc0NzZ8MA&ixlib=rb-4.1.0&q=85",
            "goal_amount": 5000.0,
            "current_amount": 1250.0,
            "currency": "EUR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "journey_id": "journey_japan001",
            "name": "Japão",
            "poetic_name": "Onde as Cerejeiras Sussurram",
            "description": "Uma viagem pela terra do sol nascente",
            "emotional_message": "Entre templos ancestrais e néon futurista, encontra-se a alma japonesa",
            "impact_description": "Participe nesta viagem de descoberta e harmonia",
            "image_url": "https://images.unsplash.com/photo-1752997670940-7be547066b85?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzh8MHwxfHNlYXJjaHwxfHxqYXBhbiUyMGNoZXJyeSUyMGJsb3Nzb20lMjBzdHJlZXR8ZW58MHx8fHwxNzcwODE3NDgzfDA&ixlib=rb-4.1.0&q=85",
            "goal_amount": 6000.0,
            "current_amount": 2400.0,
            "currency": "EUR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "journey_id": "journey_vietnam001",
            "name": "Vietname",
            "poetic_name": "Onde o Rio Abraça a Terra",
            "description": "Uma viagem pelos campos de arroz e baías mágicas",
            "emotional_message": "Na Baía de Ha Long, cada rocha conta uma história de milhões de anos",
            "impact_description": "Ajude a realizar este sonho de cores e sabores",
            "image_url": "https://images.unsplash.com/photo-1560113781-cb0bddd6772b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODF8MHwxfHNlYXJjaHwxfHx2aWV0bmFtJTIwaGElMjBsb25nJTIwYmF5JTIwc3Vuc2V0fGVufDB8fHx8MTc3MDgxNzQ4N3ww&ixlib=rb-4.1.0&q=85",
            "goal_amount": 4000.0,
            "current_amount": 800.0,
            "currency": "EUR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "journey_id": "journey_paris001",
            "name": "Paris",
            "poetic_name": "Onde o Amor Ilumina",
            "description": "Uma viagem pela cidade luz",
            "emotional_message": "Cada rua de Paris é um poema escrito em pedra e luz",
            "impact_description": "Participe nesta aventura romântica e cultural",
            "image_url": "https://images.unsplash.com/photo-1646352690381-92a7537f3385?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwzfHxwYXJpcyUyMHN0cmVldCUyMG1vcm5pbmclMjBsaWdodHxlbnwwfHx8fDE3NzA4MTc0OTJ8MA&ixlib=rb-4.1.0&q=85",
            "goal_amount": 3000.0,
            "current_amount": 1500.0,
            "currency": "EUR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "journey_id": "journey_london001",
            "name": "Londres",
            "poetic_name": "Onde a História Respira",
            "description": "Uma viagem pela capital britânica",
            "emotional_message": "Entre tradição e modernidade, Londres conta histórias de séculos",
            "impact_description": "Ajude a concretizar este sonho de descoberta",
            "image_url": "https://images.unsplash.com/photo-1543829285-3606cff6d1e5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwxfHxsb25kb24lMjBhcmNoaXRlY3R1cmUlMjB3YXJtJTIwbGlnaHR8ZW58MHx8fHwxNzcwODE3NDk3fDA&ixlib=rb-4.1.0&q=85",
            "goal_amount": 3500.0,
            "current_amount": 700.0,
            "currency": "EUR",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.journeys.insert_many(journeys)
    return {"message": "Dados de viagens criados com sucesso", "count": len(journeys)}

# ==================== HOMEPAGE ENDPOINTS ====================

@api_router.get("/homepage/main-journey")
async def get_main_journey_details():
    """Get the main journey with full details for homepage"""
    # Find the main journey (is_main_trip=True or first active one)
    journey = await db.journeys.find_one(
        {"$or": [{"is_main_trip": True}, {"is_active": True, "status": "ativa"}]},
        {"_id": 0, "goal_amount": 0, "admin_notes": 0}  # Hide sensitive fields
    )
    
    if not journey:
        return {"journey": None, "progress": None, "contributions": [], "updates": []}
    
    journey_id = journey["journey_id"]
    
    # Get progress (without goal amount)
    current_amount = journey.get("current_amount", 0)
    # We need to get goal_amount privately for percentage calculation
    full_journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    goal_amount = full_journey.get("goal_amount", 1) if full_journey else 1
    percentage = min((current_amount / goal_amount) * 100, 100) if goal_amount > 0 else 0
    
    progress = {
        "current_amount": current_amount,
        "percentage": round(percentage, 1),
        "is_funded": percentage >= 100
    }
    
    # Get recent contributions for the feed
    contributions = await db.contributions.find(
        {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Format contributions for public display
    public_contributions = []
    for c in contributions:
        if c.get("show_name", True) and c.get("contributor_name"):
            display_name = c.get("contributor_name")
        else:
            display_name = "Sonhador Anónimo"
        
        public_contributions.append({
            "display_name": display_name,
            "amount": c.get("amount"),
            "message": c.get("public_message"),
            "is_crypto": c.get("payment_method") == "crypto",
            "crypto_type": c.get("crypto_type") if c.get("payment_method") == "crypto" else None,
            "created_at": c.get("created_at")
        })
    
    # Get journey updates (future feature - for now return empty)
    updates = []
    
    return {
        "journey": journey,
        "progress": progress,
        "contributions": public_contributions,
        "updates": updates
    }

@api_router.get("/homepage/ambassador-journeys")
async def get_active_ambassador_journeys():
    """Get active ambassador journeys organized by region for 'Sonhos em Materialização' section"""
    journeys = await db.journeys.find(
        {
            "is_ambassador_journey": True,
            "status": "ativa",
            "is_active": True
        },
        {"_id": 0, "goal_amount": 0, "admin_notes": 0, "application_message": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Organize by region
    regions = {
        "europa": {"name": "Europa", "journeys": []},
        "asia": {"name": "Ásia", "journeys": []},
        "africa": {"name": "África", "journeys": []},
        "americas": {"name": "Américas", "journeys": []},
        "oceania": {"name": "Oceânia", "journeys": []},
        "outro": {"name": "Outros", "journeys": []}
    }
    
    for j in journeys:
        region = j.get("region", "outro") or "outro"
        region = region.lower()
        if region not in regions:
            region = "outro"
        
        # Calculate progress percentage
        full_journey = await db.journeys.find_one({"journey_id": j["journey_id"]}, {"_id": 0, "goal_amount": 1, "current_amount": 1})
        if full_journey:
            goal = full_journey.get("goal_amount", 1)
            current = full_journey.get("current_amount", 0)
            j["progress_percentage"] = round((current / goal) * 100, 1) if goal > 0 else 0
        else:
            j["progress_percentage"] = 0
        
        regions[region]["journeys"].append(j)
    
    # Filter out empty regions
    result = {k: v for k, v in regions.items() if v["journeys"]}
    
    return {
        "total_count": len(journeys),
        "regions": result
    }

@api_router.get("/homepage/realized-journeys")
async def get_realized_journeys_for_homepage():
    """Get realized journeys organized by country for 'Sonhos Realizados' section"""
    journeys = await db.journeys.find(
        {"status": {"$in": ["financiada", "realizada"]}},
        {"_id": 0, "goal_amount": 0, "admin_notes": 0, "application_message": 0}
    ).sort("funded_at", -1).to_list(100)
    
    # Organize by country
    countries = {}
    
    for j in journeys:
        country = j.get("country") or j.get("name", "Destino").split(",")[-1].strip() or "Desconhecido"
        
        if country not in countries:
            countries[country] = {
                "name": country,
                "region": j.get("region"),
                "journeys": []
            }
        
        countries[country]["journeys"].append(j)
    
    # Sort countries alphabetically
    sorted_countries = dict(sorted(countries.items()))
    
    return {
        "total_count": len(journeys),
        "countries": sorted_countries
    }

# Curated content for "Sonhos Realizados" when there are no real cases yet
@api_router.get("/homepage/curated-dreams")
async def get_curated_dreams():
    """Get curated content for Sonhos Realizados section when no real cases exist"""
    # Check if there are real realized journeys
    real_count = await db.journeys.count_documents({"status": {"$in": ["financiada", "realizada"]}})
    
    if real_count > 0:
        return {"use_curated": False, "curated_dreams": []}
    
    # Return curated inspirational content
    curated_dreams = [
        {
            "id": "curated_1",
            "name": "Caminho de Santiago",
            "country": "Espanha",
            "region": "europa",
            "image_url": "https://images.unsplash.com/photo-1543785734-4b6e564642f8?w=800",
            "story": "Uma peregrinação de autodescoberta pelos caminhos ancestrais da Península Ibérica.",
            "is_curated": True
        },
        {
            "id": "curated_2",
            "name": "Montanhas do Nepal",
            "country": "Nepal",
            "region": "asia",
            "image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800",
            "story": "Onde o céu encontra a terra, uma jornada de elevação espiritual nos Himalaias.",
            "is_curated": True
        },
        {
            "id": "curated_3",
            "name": "Costa Amalfitana",
            "country": "Itália",
            "region": "europa",
            "image_url": "https://images.unsplash.com/photo-1534113414509-0eec2bfb493f?w=800",
            "story": "Cores vibrantes e paisagens deslumbrantes no coração do Mediterrâneo.",
            "is_curated": True
        },
        {
            "id": "curated_4",
            "name": "Deserto do Sahara",
            "country": "Marrocos",
            "region": "africa",
            "image_url": "https://images.unsplash.com/photo-1489493887464-892be6d1daae?w=800",
            "story": "Noites estreladas e dunas infinitas, uma experiência de silêncio profundo.",
            "is_curated": True
        }
    ]
    
    return {
        "use_curated": True,
        "curated_dreams": curated_dreams,
        "message": "Estes são sonhos inspiracionais. Sê o primeiro a realizar o teu!"
    }

# ==================== ROOT ====================

@api_router.post("/admin/migrate-journey-status")
async def migrate_journey_status(request: Request):
    """One-time migration: Update all journeys with status='active' to status='ativa'"""
    await require_admin(request)
    
    result = await db.journeys.update_many(
        {"status": "active"},
        {"$set": {"status": "ativa"}}
    )
    
    return {
        "message": f"Migrated {result.modified_count} journeys from 'active' to 'ativa'",
        "modified_count": result.modified_count
    }

@api_router.post("/admin/set-main-journey/{journey_id}")
async def set_main_journey(journey_id: str, request: Request):
    """Set a journey as the main platform journey"""
    await require_admin(request)
    
    # First, unset any existing main journey
    await db.journeys.update_many(
        {"is_main_trip": True},
        {"$set": {"is_main_trip": False}}
    )
    
    # Set the new main journey
    result = await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {"is_main_trip": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    return {"message": f"Journey {journey_id} set as main trip"}

@api_router.get("/")
async def root():
    return {"message": "4Luis API - Onde os sonhos ganham asas"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
