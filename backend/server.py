from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import httpx

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

# Admin password
ADMIN_PASSWORD = "Admin1"

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
    target_date: Optional[str] = None  # Data objetivo para o financiamento (formato: YYYY-MM-DD)
    is_active: bool = True
    status: str = "active"  # active | funded | closed
    owner_user_id: Optional[str] = None  # Admin que criou a viagem
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

class Contribution(BaseModel):
    contribution_id: str = Field(default_factory=lambda: f"contrib_{uuid.uuid4().hex[:12]}")
    journey_id: str
    user_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    payment_method: str
    is_crypto: bool = False
    status: str = "pending"  # pending, completed, failed
    points_count: int = 0  # Changed from tickets_count to points_count
    sponsor_link_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContributionCreate(BaseModel):
    journey_id: str
    amount: float
    payment_method: str
    is_crypto: bool = False
    sponsor_code: Optional[str] = None

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
        # Novos campos ETAPA 1
        "sponsor_id": sponsor_id,  # IMUTÁVEL - quem convidou este utilizador
        "level": "curioso",  # curioso | sonhador | premium
        "subscription_active": False,
        "valid_referrals_count": 0,  # Referências que confirmaram contribuição
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "premium_unlocked_at": None,
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
    doc["status"] = "active"  # Default status
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

# Predefined contribution amounts
CONTRIBUTION_AMOUNTS = {
    "5": 5.0, "10": 10.0, "20": 20.0, "50": 50.0,
    "100": 100.0, "200": 200.0, "500": 500.0, "1000": 1000.0
}

@api_router.post("/contributions/create-checkout")
async def create_stripe_checkout(request: Request):
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
    )
    
    data = await request.json()
    amount_key = str(data.get("amount_key"))
    journey_id = data.get("journey_id")
    origin_url = data.get("origin_url")
    sponsor_code = data.get("sponsor_code")
    
    if amount_key not in CONTRIBUTION_AMOUNTS:
        raise HTTPException(status_code=400, detail="Montante inválido")
    
    amount = CONTRIBUTION_AMOUNTS[amount_key]
    user = await get_current_user(request)
    user_id = user.user_id if user else None
    
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/journey/{journey_id}"
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "journey_id": journey_id,
            "user_id": user_id or "anonymous",
            "sponsor_code": sponsor_code or "",
            "source": "4luis_platform"
        }
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create pending contribution record
    contribution_id = f"contrib_{uuid.uuid4().hex[:12]}"
    contribution_doc = {
        "contribution_id": contribution_id,
        "journey_id": journey_id,
        "user_id": user_id,
        "amount": amount,
        "currency": "EUR",
        "payment_method": "stripe",
        "is_crypto": False,
        "status": "pending",
        "tickets_count": 0,
        "sponsor_link_id": sponsor_code,
        "session_id": session.session_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contributions.insert_one(contribution_doc)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "contribution_id": contribution_id,
        "amount": amount,
        "currency": "EUR",
        "user_id": user_id,
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

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
    amount_key = str(data.get("amount_key"))
    payment_method = data.get("payment_method")
    is_crypto = data.get("is_crypto", False)
    sponsor_code = data.get("sponsor_code")
    name = data.get("name")
    surname = data.get("surname")
    email = data.get("email")
    
    if amount_key not in CONTRIBUTION_AMOUNTS:
        raise HTTPException(status_code=400, detail="Montante inválido")
    
    amount = CONTRIBUTION_AMOUNTS[amount_key]
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

# ==================== USER PROFILE ====================

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

# ==================== PAYMENT INFO ====================

@api_router.get("/payment-info")
async def get_payment_info():
    return {
        "mbway": {
            "phone": "+351968068535",
            "name": "Luis"
        },
        "paypal": {
            "link": "paypal.me/LuisCanarias"
        },
        "crypto": {
            "currency": "USDT",
            "network": "Tron (TRC20)",
            "address": "TGcWs89gTkkxARVT8UJsCFUMc9sQkvUmtL",
            "warning": "Use a mesma rede de depósito (TRC20) para que as criptomoedas não se percam."
        },
        "wise": {
            "email": "luis@4luis.com"
        }
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
    
    # Check if journey reached goal - update status to "funded"
    journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
    if journey and journey.get("current_amount", 0) >= journey.get("goal_amount", float('inf')):
        await db.journeys.update_one(
            {"journey_id": contribution["journey_id"]},
            {"$set": {"status": "funded"}}
        )
    
    # Update sponsor link if applicable
    if contribution.get("sponsor_link_id"):
        await db.sponsor_links.update_one(
            {"link_id": contribution["sponsor_link_id"]},
            {"$inc": {"successful_referrals": 1}}
        )
    
    # MOTOR PREMIUM: Se o utilizador que contribuiu tem sponsor_id, incrementar valid_referrals_count do sponsor
    if contribution.get("user_id"):
        contributing_user = await db.users.find_one({"user_id": contribution["user_id"]}, {"_id": 0})
        if contributing_user and contributing_user.get("sponsor_id"):
            sponsor_user_id = contributing_user["sponsor_id"]
            
            # Incrementar valid_referrals_count do sponsor
            await db.users.update_one(
                {"user_id": sponsor_user_id},
                {"$inc": {"valid_referrals_count": 1}}
            )
            
            # Verificar se sponsor atinge condições Premium
            sponsor = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0})
            if sponsor:
                valid_refs = sponsor.get("valid_referrals_count", 0)
                subscription = sponsor.get("subscription_active", False)
                current_level = sponsor.get("level", "curioso")
                
                # MOTOR PREMIUM: subscription_active + valid_referrals >= 3 = premium
                if subscription and valid_refs >= 3 and current_level != "premium":
                    await db.users.update_one(
                        {"user_id": sponsor_user_id},
                        {"$set": {
                            "level": "premium",
                            "premium_unlocked_at": datetime.now(timezone.utc).isoformat()
                        }}
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
    
    return {"message": "Contribuição confirmada com sucesso"}

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
    await require_admin(request)
    
    result = await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {"status": "rejected", "rejected_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")
    
    return {"message": "Contribuição rejeitada"}

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
    week_ago_iso = week_ago.isoformat()
    
    total_users = len(users)
    active_subscriptions = sum(1 for u in users if u.get("subscription_active"))
    premium_users = sum(1 for u in users if u.get("level") == "premium")
    sonhador_users = sum(1 for u in users if u.get("level") == "sonhador")
    curioso_users = sum(1 for u in users if u.get("level") == "curioso")
    
    # Weekly signups
    weekly_signups = sum(1 for u in users if (u.get("registered_at") or u.get("created_at", "")) >= week_ago_iso)
    
    # Total contributions value
    total_contributions_value = sum(c.get("amount", 0) for c in all_contributions)
    
    # Total valid referrals
    valid_referrals_total = sum(u.get("valid_referrals_count", 0) for u in users)
    
    # Top sponsors (by impact value)
    top_sponsors = sorted(
        [{"user_id": uid, "name": next((u["name"] for u in users if u["user_id"] == uid), "?"), "impact_value": data["value"], "referrals_count": len(data["referrals"])} 
         for uid, data in sponsor_impact.items() if data["value"] > 0],
        key=lambda x: x["impact_value"],
        reverse=True
    )[:5]
    
    return {
        "metrics": {
            "total_users": total_users,
            "active_subscriptions": active_subscriptions,
            "premium_users": premium_users,
            "sonhador_users": sonhador_users,
            "curioso_users": curioso_users,
            "weekly_signups": weekly_signups,
            "total_contributions_value": total_contributions_value,
            "valid_referrals_total": valid_referrals_total,
            "total_contributions_count": len(all_contributions),
            "total_sponsor_impact": sum(s["value"] for s in sponsor_impact.values())
        },
        "level_distribution": {
            "curioso": curioso_users,
            "sonhador": sonhador_users,
            "premium": premium_users
        },
        "charts": {
            "signups_by_month": get_monthly_counts([u.get("registered_at") or u.get("created_at") for u in users]),
            "contributions_by_month": get_monthly_contributions(all_contributions)
        },
        "top_sponsors": top_sponsors,
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

# ==================== ROOT ====================

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
