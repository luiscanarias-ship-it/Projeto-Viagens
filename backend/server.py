from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware
import os
import random
import asyncio
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import re
import stripe

# Import shared modules
from config import (
    db, client, logger, JWT_SECRET, JWT_ALGORITHM, ADMIN_PASSWORD, ADMIN_EMAIL,
    STRIPE_API_KEY, STRIPE_SONHADOR_PRICE_ID, STRIPE_WEBHOOK_SECRET, FRONTEND_URL,
    FIXED_CONTRIBUTION_AMOUNTS, PAYMENT_METHODS, CRYPTO_TYPES, JOURNEY_STATUSES,
    TICKET_TYPES, TICKET_STATUSES, TICKET_PRIORITIES,
    PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_API_URL, PAYPAL_MODE,
    TIP_OPTIONS, DEFAULT_TIP_AMOUNT,
    CERTIFICATION_LEVELS, TRUSTED_AMBASSADOR_MIN_SUPPORTERS, TRUSTED_AMBASSADOR_MIN_RAISED
)
from models import (
    UserBase, UserCreate, UserLogin, User, Journey, JourneyCreate, JourneyUpdate,
    AmbassadorJourneyApplication, Contribution, ContributionCreate, SponsorLink,
    Point, TranslationRequest, Offer, OfferCreate,
    generate_anonymous_alias, generate_anonymous_avatar,
    generate_payment_reference
)
from auth import (
    hash_password, verify_password, create_jwt_token, decode_jwt_token,
    get_current_user, require_auth, require_admin
)
from email_service import (
    get_email_base_template, send_email_resend,
    get_contribution_email_html, get_referral_contribution_email_html,
    get_admin_referral_notification_html, get_ambassador_unlocked_email_html,
    get_journey_funded_email_html, get_admin_journey_funded_html,
    send_contribution_email, send_referral_contribution_emails,
    send_ambassador_unlocked_email, send_journey_funded_emails,
    send_weekly_summary_emails, send_dream_funded_announcement,
    send_new_journey_email,
    send_contribution_confirmed_email, send_contribution_pending_email,
    _build_email_progress_bar, _build_email_cta_button, _build_standard_email,
    send_tip_thank_you_email
)

app = FastAPI(title="4Luis API")
api_router = APIRouter(prefix="/api")

# ==================== REVENUE DISTRIBUTION ====================

async def calculate_revenue_distribution(contribution: dict) -> dict:
    """
    Calculate revenue distribution for a contribution.
    
    Rules:
    - Ambassador campaign: 100% support_amount → ambassador, tip_amount → platform
    - Platform campaign: 100% support_amount → platform, tip_amount → platform
    
    Returns dict with ambassador_revenue and platform_revenue
    """
    support_amount = contribution.get("support_amount") or contribution.get("amount", 0)
    tip_amount = contribution.get("tip_amount", 0)
    is_ambassador_journey = contribution.get("is_ambassador_journey", False)
    ambassador_user_id = contribution.get("ambassador_user_id")
    
    if is_ambassador_journey and ambassador_user_id:
        # Ambassador campaign: support goes to ambassador, tip goes to platform
        return {
            "ambassador_revenue": support_amount,
            "platform_revenue": tip_amount,
            "ambassador_user_id": ambassador_user_id
        }
    else:
        # Platform campaign: everything goes to platform
        return {
            "ambassador_revenue": 0,
            "platform_revenue": support_amount + tip_amount,
            "ambassador_user_id": None
        }


async def apply_revenue_distribution(contribution_id: str):
    """
    Apply revenue distribution after payment is confirmed.
    Updates the contribution with ambassador_revenue and platform_revenue.
    """
    contribution = await db.contributions.find_one(
        {"contribution_id": contribution_id},
        {"_id": 0}
    )
    if not contribution:
        return
    
    distribution = await calculate_revenue_distribution(contribution)
    
    # Update contribution with distribution
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "ambassador_revenue": distribution["ambassador_revenue"],
            "platform_revenue": distribution["platform_revenue"]
        }}
    )
    
    # If ambassador journey, update ambassador's total earnings
    if distribution["ambassador_user_id"] and distribution["ambassador_revenue"] > 0:
        await db.users.update_one(
            {"user_id": distribution["ambassador_user_id"]},
            {"$inc": {"ambassador_earnings": distribution["ambassador_revenue"]}}
        )
    
    logger.info(f"Revenue distribution applied for {contribution_id}: ambassador={distribution['ambassador_revenue']}€, platform={distribution['platform_revenue']}€")
    
    return distribution

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
            sponsor_user_id = sponsor_link["user_id"]
            # Anti-abuse: prevent self-referral (check if sponsor email matches new user email)
            sponsor_user = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0, "email": 1})
            if sponsor_user and sponsor_user.get("email") != user_data.email:
                sponsor_id = sponsor_user_id
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
        "total_contributed": 0,  # Soma de todas as contribuições confirmadas
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "embaixador_unlocked_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Notify sponsor that a friend registered
    if sponsor_id:
        asyncio.create_task(create_notification(
            sponsor_id, "referral_registered",
            f"O teu amigo {user_data.name} acabou de se registar! Falta contribuir para a Viagem Principal.",
            {"referred_name": user_data.name, "referred_user_id": user_id}
        ))
    
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

# ==================== PASSWORD RESET ====================

@api_router.post("/auth/forgot-password")
async def forgot_password(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    # Always return success to not reveal if email exists
    if not email:
        return {"message": "Se este email existir, vais receber instruções."}
    
    user = await db.users.find_one({"email": email}, {"_id": 0, "user_id": 1, "name": 1})
    if user:
        token = str(uuid.uuid4())
        await db.password_resets.delete_many({"user_id": user["user_id"]})
        await db.password_resets.insert_one({
            "token": token,
            "user_id": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
            "used": False
        })
        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        name = user.get("name", "Sonhador")
        html_content = get_email_base_template(f"""
            <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px 0;">Recuperar palavra-passe</h2>
            <p style="color: #6B6661; font-size: 14px; line-height: 1.6;">
                Olá {name},<br><br>
                Recebemos um pedido para repor a tua palavra-passe. Clica no botão abaixo para criar uma nova.
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <a href="{reset_link}" style="display: inline-block; background-color: #FFBE98; color: #2D2A26; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 14px;">
                    Repor palavra-passe
                </a>
            </div>
            <p style="color: #9B9590; font-size: 12px; line-height: 1.5;">
                Este link expira em 30 minutos.<br>
                Se não fizeste este pedido, ignora este email.
            </p>
        """, "Recuperar palavra-passe — 4Luis")
        try:
            await send_email_resend(email, "Recuperar palavra-passe — 4Luis", html_content)
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
    
    return {"message": "Se este email existir, vais receber instruções."}

@api_router.post("/auth/reset-password")
async def reset_password(request: Request):
    data = await request.json()
    token = data.get("token", "")
    new_password = data.get("password", "")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token e nova palavra-passe são obrigatórios.")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="A palavra-passe deve ter pelo menos 8 caracteres.")
    
    reset_doc = await db.password_resets.find_one({"token": token, "used": False}, {"_id": 0})
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Link inválido ou já utilizado.")
    
    expires_at = datetime.fromisoformat(reset_doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="O link expirou. Solicita uma nova recuperação.")
    
    await db.users.update_one(
        {"user_id": reset_doc["user_id"]},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    await db.password_resets.update_one({"token": token}, {"$set": {"used": True}})
    
    return {"message": "Palavra-passe atualizada com sucesso."}


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
            "avatar": None,
            "use_real_name": True,
            "anonymous_alias": generate_anonymous_alias(),
            "sponsor_id": None,
            "level": "sonhador",
            "contributed_to_main_trip": False,
            "valid_referrals_count": 0,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "embaixador_unlocked_at": None,
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
    
    # Also generate JWT token for Authorization header fallback
    jwt_token = create_jwt_token(user_id, is_admin)
    
    return {
        "token": jwt_token,
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
    
    # If this is an ambassador journey, include ambassador info
    if journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "password_hash": 0, "email": 0}
        )
        if ambassador:
            # Determine display name based on privacy settings
            use_real_name = ambassador.get("use_real_name", True)
            if use_real_name:
                display_name = ambassador.get("name", "Embaixador")
                display_avatar = ambassador.get("avatar") or f"https://api.dicebear.com/7.x/initials/svg?seed={ambassador.get('name', 'E')}"
            else:
                display_name = ambassador.get("anonymous_alias") or "Sonhador"
                display_avatar = ambassador.get("anonymous_avatar") or f"https://api.dicebear.com/7.x/shapes/svg?seed={journey['ambassador_user_id']}"
            
            journey["ambassador_info"] = {
                "user_id": journey["ambassador_user_id"],
                "display_name": display_name,
                "avatar": display_avatar,
                "country": ambassador.get("country"),
                "level": ambassador.get("level", "sonhador"),
                "certification_level": ambassador.get("certification_level", "embaixador"),
                "certification_label": CERTIFICATION_LEVELS.get(ambassador.get("certification_level", "embaixador"), {}).get("label", "Embaixador 4Luis"),
                "member_since": ambassador.get("registered_at") or ambassador.get("created_at")
            }
        elif journey.get("ambassador_name"):
            # Fallback for sample/seeded journeys where user doesn't exist in DB
            name = journey["ambassador_name"]
            journey["ambassador_info"] = {
                "user_id": journey["ambassador_user_id"],
                "display_name": name,
                "avatar": f"https://api.dicebear.com/7.x/initials/svg?seed={name}",
                "country": None,
                "level": "sonhador",
                "member_since": journey.get("created_at")
            }
    
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
    
    updates = {}
    for k, v in update_data.model_dump().items():
        if v is not None:
            updates[k] = v
        elif isinstance(v, bool):
            updates[k] = v
    # Explicitly handle boolean fields that can be False
    raw = update_data.model_dump()
    for bool_field in ['is_active', 'is_main_trip', 'show_goal_amount', 'story_emails_enabled']:
        if bool_field in raw and raw[bool_field] is not None:
            updates[bool_field] = raw[bool_field]
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
    
    # Enrich with ambassador names
    for j in journeys:
        if j.get("is_ambassador_journey") and j.get("ambassador_user_id"):
            amb = await db.users.find_one({"user_id": j["ambassador_user_id"]}, {"_id": 0, "name": 1})
            j["ambassador_name"] = amb.get("name", "Embaixador") if amb else "Embaixador"
    
    return journeys

# ==================== CONTRIBUTIONS & PAYMENTS ====================

# ==================== CONTRIBUTIONS & PAYMENTS (v2) ====================

@api_router.get("/contributions/config")
async def get_contribution_config():
    """Get contribution configuration (fixed amounts, payment methods, and tip options)"""
    return {
        "fixed_amounts": FIXED_CONTRIBUTION_AMOUNTS,
        "payment_methods": PAYMENT_METHODS,
        "crypto_types": CRYPTO_TYPES,
        "tip_options": TIP_OPTIONS,
        "default_tip": DEFAULT_TIP_AMOUNT,
        "currency": "EUR",
        "note": "100% do teu apoio vai para o sonhador. A contribuição para a plataforma é totalmente opcional."
    }

@api_router.post("/contributions/create")
async def create_contribution(request: Request):
    """Create a new contribution with payment reference for external payments"""
    data = await request.json()
    support_amount = data.get("support_amount")  # Amount for journey/ambassador
    tip_amount = data.get("tip_amount", 0)  # Optional platform tip
    amount = data.get("amount")  # Total (for backward compatibility)
    payment_method = data.get("payment_method")
    journey_id = data.get("journey_id")
    sponsor_code = data.get("sponsor_code")
    contributor_name = data.get("contributor_name")
    contributor_email = data.get("contributor_email")
    
    # Handle backward compatibility: if support_amount not provided, use amount
    if support_amount is None:
        support_amount = amount
        tip_amount = 0
    
    # Calculate total payment amount
    total_amount = support_amount + tip_amount
    
    # Validate support_amount
    if support_amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(
            status_code=400, 
            detail=f"Montante inválido. Valores permitidos: {FIXED_CONTRIBUTION_AMOUNTS}"
        )
    
    # Validate tip_amount (must be 0 or one of the tip options)
    valid_tip_values = [opt["value"] for opt in TIP_OPTIONS]
    if tip_amount not in valid_tip_values:
        raise HTTPException(
            status_code=400, 
            detail=f"Valor de contribuição para a plataforma inválido. Valores permitidos: {valid_tip_values}"
        )
    
    # Validate payment method (Stripe temporarily disabled)
    valid_methods = ["crypto", "paypal", "mbway"]
    if payment_method not in valid_methods:
        raise HTTPException(
            status_code=400, 
            detail=f"Método de pagamento inválido. Métodos permitidos: {valid_methods}"
        )
    
    # Check if journey exists and is active
    journey = await db.journeys.find_one({"journey_id": journey_id, "is_active": True}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada ou inativa")
    
    # Validate crypto_type if payment_method is crypto
    crypto_type = data.get("crypto_type")
    
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
    
    # Generate unique payment reference
    payment_reference = generate_payment_reference()
    # Ensure uniqueness
    while await db.contributions.find_one({"payment_reference": payment_reference}):
        payment_reference = generate_payment_reference()
    
    # Create contribution with payment reference
    contribution_doc = {
        "contribution_id": contribution_id,
        "journey_id": journey_id,
        "user_id": user_id,
        "amount": total_amount,  # Total payment amount
        "support_amount": support_amount,  # Amount for journey/ambassador
        "tip_amount": tip_amount,  # Optional platform tip
        "currency": "EUR",
        "payment_method": payment_method,
        "crypto_type": crypto_type if payment_method == "crypto" else None,
        "payment_reference": payment_reference,
        "status": "pending",  # Requires admin confirmation
        "is_main_trip": journey.get("is_main_trip", False),
        "is_ambassador_journey": journey.get("is_ambassador_journey", False),
        "ambassador_user_id": journey.get("ambassador_user_id"),
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
        "payment_reference": payment_reference,
        "payment_method": payment_method,
        "crypto_type": crypto_type,
        "support_amount": support_amount,
        "tip_amount": tip_amount,
        "amount": total_amount,
        "status": "pending",
        "message": f"Contribuição registada. Use o código {payment_reference} na descrição do pagamento."
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

@api_router.get("/stripe/config")
async def get_stripe_config():
    """Get Stripe publishable key for frontend"""
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    return {"publishable_key": publishable_key}

# ==================== PAYPAL CHECKOUT ====================

async def get_paypal_access_token():
    """Get PayPal OAuth2 access token"""
    import base64
    auth_str = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.post(
            f"{PAYPAL_API_URL}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_str}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data="grant_type=client_credentials"
        )
        if resp.status_code != 200:
            logger.error(f"PayPal auth failed: {resp.text}")
            raise HTTPException(status_code=500, detail="Erro ao autenticar com PayPal")
        return resp.json()["access_token"]

@api_router.get("/paypal/config")
async def get_paypal_config():
    """Get PayPal client ID for frontend SDK"""
    return {"client_id": PAYPAL_CLIENT_ID, "mode": PAYPAL_MODE}

@api_router.post("/paypal/create-order")
async def paypal_create_order(request: Request):
    """Create a PayPal order for a contribution with optional platform tip"""
    data = await request.json()
    support_amount = data.get("support_amount")  # Amount for journey/ambassador
    tip_amount = data.get("tip_amount", 0)  # Optional platform tip
    amount = data.get("amount")  # Total (for backward compatibility)
    journey_id = data.get("journey_id")
    
    # Handle backward compatibility
    if support_amount is None:
        support_amount = amount
        tip_amount = 0
    
    # Calculate total payment
    total_amount = support_amount + tip_amount
    
    if support_amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(status_code=400, detail=f"Montante invalido: {FIXED_CONTRIBUTION_AMOUNTS}")
    
    # Validate tip amount
    valid_tip_values = [opt["value"] for opt in TIP_OPTIONS]
    if tip_amount not in valid_tip_values:
        raise HTTPException(status_code=400, detail=f"Valor de contribuição para a plataforma inválido")
    
    journey = await db.journeys.find_one({"journey_id": journey_id, "is_active": True}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem nao encontrada ou inativa")
    
    user = await get_current_user(request)
    user_id = user.user_id if user else None
    contributor_name = data.get("contributor_name") or (user.name if user else None)
    contributor_email = data.get("contributor_email") or (user.email if user else None)
    sponsor_code = data.get("sponsor_code")
    
    # Create contribution as pending
    contribution_id = f"contrib_{uuid.uuid4().hex[:12]}"
    payment_reference = generate_payment_reference()
    while await db.contributions.find_one({"payment_reference": payment_reference}):
        payment_reference = generate_payment_reference()
    
    # Get PayPal access token and create order
    access_token = await get_paypal_access_token()
    
    # PayPal order uses total amount (support + tip)
    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": contribution_id,
            "description": f"Contribuicao 4Luis - {journey.get('name', 'Viagem')}",
            "amount": {
                "currency_code": "EUR",
                "value": f"{total_amount:.2f}"
            }
        }]
    }
    
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.post(
            f"{PAYPAL_API_URL}/v2/checkout/orders",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=order_payload
        )
        if resp.status_code not in (200, 201):
            logger.error(f"PayPal create order failed: {resp.text}")
            raise HTTPException(status_code=500, detail="Erro ao criar ordem PayPal")
        
        paypal_order = resp.json()
    
    # Save contribution with PayPal order ID
    contribution_doc = {
        "contribution_id": contribution_id,
        "journey_id": journey_id,
        "user_id": user_id,
        "amount": total_amount,  # Total payment amount
        "support_amount": support_amount,  # Amount for journey/ambassador
        "tip_amount": tip_amount,  # Platform tip
        "currency": "EUR",
        "payment_method": "paypal",
        "payment_reference": payment_reference,
        "paypal_order_id": paypal_order["id"],
        "status": "pending",
        "is_main_trip": journey.get("is_main_trip", False),
        "is_ambassador_journey": journey.get("is_ambassador_journey", False),
        "ambassador_user_id": journey.get("ambassador_user_id"),
        "sponsor_link_id": sponsor_code,
        "contributor_name": contributor_name,
        "contributor_email": contributor_email,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.contributions.insert_one(contribution_doc)
    
    return {
        "paypal_order_id": paypal_order["id"],
        "contribution_id": contribution_id,
        "support_amount": support_amount,
        "tip_amount": tip_amount,
        "total_amount": total_amount,
        "status": "CREATED"
    }

@api_router.post("/paypal/capture-order/{order_id}")
async def paypal_capture_order(order_id: str, request: Request):
    """Capture a PayPal order after user approval — marks contribution as completed"""
    # Find the contribution by paypal_order_id
    contribution = await db.contributions.find_one(
        {"paypal_order_id": order_id},
        {"_id": 0}
    )
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuicao nao encontrada")
    
    # Idempotency: if already completed, return success
    if contribution["status"] in ("completed", "confirmed"):
        return {
            "status": "ALREADY_CAPTURED",
            "contribution_id": contribution["contribution_id"],
            "message": "Pagamento ja confirmado"
        }
    
    # Capture the PayPal order
    access_token = await get_paypal_access_token()
    
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.post(
            f"{PAYPAL_API_URL}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        if resp.status_code not in (200, 201):
            logger.error(f"PayPal capture failed: {resp.text}")
            # Mark as failed
            await db.contributions.update_one(
                {"paypal_order_id": order_id},
                {"$set": {"status": "failed"}}
            )
            raise HTTPException(status_code=500, detail="Erro ao capturar pagamento PayPal")
        
        capture_data = resp.json()
    
    if capture_data.get("status") != "COMPLETED":
        await db.contributions.update_one(
            {"paypal_order_id": order_id},
            {"$set": {"status": "failed", "paypal_response": capture_data.get("status")}}
        )
        raise HTTPException(status_code=400, detail=f"PayPal status: {capture_data.get('status')}")
    
    contribution_id = contribution["contribution_id"]
    journey_id = contribution["journey_id"]
    amount = contribution["amount"]
    support_amount = contribution.get("support_amount") or amount
    user_id = contribution.get("user_id")
    
    # Update contribution to completed
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "status": "confirmed",
            "confirmed": True,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
            "validated_by": "paypal_capture",
            "paypal_capture_id": capture_data.get("id")
        }}
    )
    
    # Apply revenue distribution (ambassador vs platform)
    distribution = await apply_revenue_distribution(contribution_id)
    
    # Update journey current_amount with support_amount only (not tip)
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$inc": {"current_amount": support_amount}}
    )
    
    # Update user total_contributed
    if user_id:
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"total_contributed": amount}}
        )
    
    # Check if journey reached goal
    await check_and_update_journey_funding_status(journey_id)
    await check_and_update_story_chapter(journey_id)
    
    # Process ambassador progression using robust recalculation
    if user_id:
        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        if user_doc:
            main_journey = await db.journeys.find_one(
                {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]},
                {"_id": 0}
            )
            is_main = main_journey and journey_id == main_journey.get("journey_id")
            if is_main:
                await db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"contributed_to_main_trip": True}}
                )
                # Recalculate for the contributor
                await recalculate_ambassador_status(user_id)
            
            # Recalculate sponsor's ambassador status
            if user_doc.get("sponsor_id"):
                await recalculate_ambassador_status(user_doc["sponsor_id"])
        
        # Send notification
        journey_name = (await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0, "name": 1})) or {}
        await create_notification(
            user_id,
            "contribution",
            f"A tua contribuicao de {amount}EUR para {journey_name.get('name', 'esta viagem')} foi confirmada automaticamente.",
            {"journey_id": journey_id, "amount": amount}
        )
    
    # Send confirmation email
    journey_doc = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    updated_contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if journey_doc and updated_contribution:
        asyncio.create_task(send_contribution_email(updated_contribution, journey_doc))
        # Send tip thank you email if tip was given
        if updated_contribution.get("tip_amount", 0) > 0:
            asyncio.create_task(send_tip_thank_you_email(updated_contribution))
    
    return {
        "status": "COMPLETED",
        "contribution_id": contribution_id,
        "amount": amount,
        "support_amount": support_amount,
        "tip_amount": contribution.get("tip_amount", 0),
        "message": "Pagamento confirmado com sucesso"
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

@api_router.put("/contributions/{contribution_id}/confirm-details")
async def confirm_contribution_details(contribution_id: str, request: Request):
    """User confirms they made the payment and optionally provides name/email"""
    body = await request.json()
    contributor_name = body.get("contributor_name")
    contributor_email = body.get("contributor_email")
    proof_image_url = body.get("proof_image_url")  # Optional screenshot proof

    if not contributor_email:
        raise HTTPException(status_code=400, detail="Email é obrigatório")

    contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")

    journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
    is_direct = journey and journey.get("payment_mode") == "direct"
    
    # For direct payment: set awaiting_validation (ambassador must confirm)
    # For platform payment: keep as pending (admin confirms)
    new_status = "awaiting_validation" if is_direct else "pending"

    update_fields = {
        "status": new_status,
        "contributor_email": contributor_email,
        "user_confirmed_payment": True,
        "confirmed_by_user_at": datetime.now(timezone.utc).isoformat()
    }
    if contributor_name:
        update_fields["contributor_name"] = contributor_name
    if proof_image_url:
        update_fields["proof_image_url"] = proof_image_url

    # Anti-fraud: limit pending contributions per email (max 3 pending)
    pending_count = await db.contributions.count_documents({
        "contributor_email": contributor_email,
        "status": {"$in": ["pending", "awaiting_validation"]},
        "contribution_id": {"$ne": contribution_id}
    })
    if pending_count >= 3:
        raise HTTPException(
            status_code=429,
            detail="Tens demasiadas contribuições pendentes. Aguarda a validação antes de enviar mais."
        )

    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": update_fields}
    )

    # Send pending confirmation email to contributor
    updated_contribution = {**contribution, **update_fields}
    if journey:
        try:
            await send_contribution_pending_email(updated_contribution, journey)
        except Exception as e:
            logger.error(f"Failed to send pending email: {e}")

    # Notify ambassador for direct payments
    if is_direct and journey.get("ambassador_user_id"):
        amb_id = journey["ambassador_user_id"]
        amount = contribution.get("support_amount") or contribution.get("amount", 0)
        asyncio.create_task(create_notification(
            amb_id, "payment_awaiting_validation",
            f"Nova contribuição de {amount}€ para '{journey.get('name', '')}' aguarda a tua confirmação.",
            {"contribution_id": contribution_id, "journey_id": journey["journey_id"], "amount": amount}
        ))

    return {
        "status": new_status,
        "message": "Obrigado! A tua contribuição será validada em breve."
    }


@api_router.put("/contributions/{contribution_id}/ambassador-validate")
async def ambassador_validate_contribution(contribution_id: str, request: Request):
    """Ambassador confirms or rejects a direct payment contribution"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    
    body = await request.json()
    action = body.get("action")  # "confirm" or "reject"
    notes = body.get("notes", "")
    
    if action not in ("confirm", "reject"):
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'confirm' ou 'reject'")
    
    contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")
    
    # Verify this ambassador owns the journey
    journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
    if not journey or journey.get("ambassador_user_id") != user.user_id:
        raise HTTPException(status_code=403, detail="Não tens permissão para validar esta contribuição")
    
    if contribution.get("status") != "awaiting_validation":
        raise HTTPException(status_code=400, detail="Esta contribuição não está à espera de validação")
    
    now = datetime.now(timezone.utc).isoformat()
    
    if action == "confirm":
        support_amount = contribution.get("support_amount") or contribution.get("amount", 0)
        
        await db.contributions.update_one(
            {"contribution_id": contribution_id},
            {"$set": {
                "status": "confirmed",
                "validated_by": f"ambassador:{user.user_id}",
                "validated_at": now,
                "ambassador_validation_notes": notes
            }}
        )
        
        # Update journey progress
        await db.journeys.update_one(
            {"journey_id": contribution["journey_id"]},
            {"$inc": {"current_amount": support_amount}}
        )
        
        # Apply revenue distribution
        await apply_revenue_distribution(contribution_id)
        
        # Update contributor stats
        contributor_id = contribution.get("user_id")
        if contributor_id:
            await db.users.update_one(
                {"user_id": contributor_id},
                {"$inc": {"total_contributed": contribution.get("amount", 0)}}
            )
            # Check progression
            if journey.get("is_main_trip"):
                await db.users.update_one(
                    {"user_id": contributor_id},
                    {"$set": {"contributed_to_main_trip": True}}
                )
            await recalculate_ambassador_status(contributor_id)
        
        # Check journey funding
        await check_and_update_journey_funding_status(contribution["journey_id"])
        await check_and_update_story_chapter(contribution["journey_id"])
        
        # Notify contributor
        if contribution.get("contributor_email"):
            asyncio.create_task(create_notification(
                contributor_id or "anonymous", "payment_confirmed",
                f"A tua contribuição de {support_amount}€ foi confirmada pelo Embaixador.",
                {"contribution_id": contribution_id}
            ))
            # Send confirmation email
            updated = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
            if updated:
                asyncio.create_task(send_contribution_email(updated, journey))
        
        return {"status": "confirmed", "message": "Pagamento confirmado com sucesso"}
    
    else:  # reject
        await db.contributions.update_one(
            {"contribution_id": contribution_id},
            {"$set": {
                "status": "rejected",
                "validated_by": f"ambassador:{user.user_id}",
                "validated_at": now,
                "ambassador_validation_notes": notes,
                "rejection_reason": notes
            }}
        )
        
        # Notify contributor
        contributor_id = contribution.get("user_id")
        asyncio.create_task(create_notification(
            contributor_id or "anonymous", "payment_rejected",
            f"O Embaixador não conseguiu confirmar a tua contribuição. Razão: {notes or 'Pagamento não recebido'}",
            {"contribution_id": contribution_id}
        ))
        
        return {"status": "rejected", "message": "Contribuição marcada como não recebida"}


@api_router.get("/ambassador/pending-validations")
async def get_ambassador_pending_validations(request: Request):
    """Get contributions awaiting validation by this ambassador"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    
    # Get ambassador's journeys
    journey_ids = await db.journeys.distinct("journey_id", {
        "ambassador_user_id": user.user_id,
        "is_active": True
    })
    
    # Get awaiting_validation contributions for those journeys
    contributions = await db.contributions.find(
        {
            "journey_id": {"$in": journey_ids},
            "status": "awaiting_validation"
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Also get recently validated (last 10)
    recent = await db.contributions.find(
        {
            "journey_id": {"$in": journey_ids},
            "status": {"$in": ["confirmed", "rejected"]},
            "validated_by": {"$regex": f"^ambassador:{user.user_id}"}
        },
        {"_id": 0}
    ).sort("validated_at", -1).limit(10).to_list(10)
    
    return {
        "pending": contributions,
        "pending_count": len(contributions),
        "recently_validated": recent
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
    
    # Count unique contributors for this journey
    journey_contributor_count = len(await db.contributions.distinct("contributor_email", {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}}))
    # Platform-wide count + seed offset
    platform_contributor_count = len(await db.contributions.distinct("contributor_email", {"status": {"$in": ["confirmed", "completed"]}}))
    contributor_display_count = platform_contributor_count + 57
    
    response = {
        "journey_id": journey_id,
        "current_amount": current_amount,
        "percentage": round(percentage, 1),
        "is_funded": is_funded,
        "funding_status": journey.get("funding_status", "active"),
        "is_main_trip": journey.get("is_main_trip", False),
        "is_ambassador_journey": journey.get("is_ambassador_journey", False),
        "status": journey.get("status", "active"),
        "target_date": journey.get("target_date"),
        "closing_message": "Financiamento total quase a fechar." if is_funded else None,
        "contributor_count": contributor_display_count,
        "journey_contributor_count": journey_contributor_count
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
    """Handle Stripe webhook events for PaymentIntent"""
    api_key = os.environ.get("STRIPE_API_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    stripe.api_key = api_key
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    try:
        # Verify webhook signature if secret is configured
        if webhook_secret:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        else:
            # Parse event without signature verification (development)
            import json
            event = stripe.Event.construct_from(json.loads(body), stripe.api_key)
        
        logger.info(f"Stripe webhook received: {event.type}")
        
        # Handle payment_intent.succeeded
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            payment_intent_id = payment_intent.id
            metadata = payment_intent.get("metadata", {})
            
            logger.info(f"PaymentIntent succeeded: {payment_intent_id}")
            
            # Find and update contribution
            contribution = await db.contributions.find_one(
                {"payment_intent_id": payment_intent_id},
                {"_id": 0}
            )
            
            if contribution:
                contribution_id = contribution["contribution_id"]
                journey_id = contribution["journey_id"]
                amount = contribution["amount"]
                user_id = contribution.get("user_id")
                
                # Update contribution status
                await db.contributions.update_one(
                    {"contribution_id": contribution_id},
                    {"$set": {
                        "status": "confirmed",
                        "validated_at": datetime.now(timezone.utc).isoformat(),
                        "validated_by": "stripe_webhook"
                    }}
                )
                
                # Update journey current_amount
                await db.journeys.update_one(
                    {"journey_id": journey_id},
                    {"$inc": {"current_amount": amount}}
                )
                
                # Update user total_contributed
                if user_id:
                    await db.users.update_one(
                        {"user_id": user_id},
                        {"$inc": {"total_contributed": amount}}
                    )
                
                # Check if journey is now funded
                await check_and_update_journey_funding_status(journey_id)
                
                # Check story chapter progression
                await check_and_update_story_chapter(journey_id)
                
                # Process user progression if logged in
                if user_id:
                    # Check if main trip contribution
                    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
                    if journey and journey.get("is_main_trip"):
                        await db.users.update_one(
                            {"user_id": user_id},
                            {"$set": {"contributed_to_main_trip": True}}
                        )
                    
                    # Recalculate ambassador status for contributor and sponsor
                    await recalculate_ambassador_status(user_id)
                    contributor_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "sponsor_id": 1})
                    if contributor_doc and contributor_doc.get("sponsor_id"):
                        await recalculate_ambassador_status(contributor_doc["sponsor_id"])
                
                # Send confirmation email
                updated_contribution = await db.contributions.find_one(
                    {"contribution_id": contribution_id},
                    {"_id": 0}
                )
                if updated_contribution and journey:
                    asyncio.create_task(send_contribution_email(updated_contribution, journey))
                
                logger.info(f"Contribution {contribution_id} confirmed via Stripe webhook")
            else:
                logger.warning(f"No contribution found for PaymentIntent: {payment_intent_id}")
        
        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            payment_intent_id = payment_intent.id
            logger.warning(f"PaymentIntent failed: {payment_intent_id}")
            
            # Update contribution status to rejected
            await db.contributions.update_one(
                {"payment_intent_id": payment_intent_id},
                {"$set": {"status": "rejected"}}
            )
        
        return {"status": "success"}
        
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

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

# ==================== AMBASSADOR SYSTEM ====================

AMBASSADOR_REQUIRED_REFERRALS = 3

async def recalculate_ambassador_status(user_id: str):
    """Recalculate ambassador status dynamically based on actual data.
    Conditions: 3+ unique invited users who each made a confirmed contribution to main trip."""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return False

    # Prevent recalculation if already ambassador
    if user.get("level") == "embaixador":
        return True

    # Get users invited by this user (sponsor_id = this user)
    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1, "email": 1}
    ).to_list(1000)

    if len(invited_users) < AMBASSADOR_REQUIRED_REFERRALS:
        return False

    # Get main trip journey
    main_journey = await db.journeys.find_one(
        {"is_main_trip": True, "is_active": True},
        {"_id": 0, "journey_id": 1}
    )
    if not main_journey:
        # Fallback: any active journey
        main_journey = await db.journeys.find_one(
            {"is_active": True, "status": "ativa"},
            {"_id": 0, "journey_id": 1}
        )
    if not main_journey:
        return False

    # Count unique invited users with confirmed contributions > 0€ to main trip
    invited_ids = [u["user_id"] for u in invited_users]
    valid_contributors = await db.contributions.distinct("user_id", {
        "user_id": {"$in": invited_ids},
        "journey_id": main_journey["journey_id"],
        "status": {"$in": ["confirmed", "completed"]},
        "amount": {"$gt": 0}
    })

    valid_count = len(valid_contributors)

    # Update the cached count
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"valid_referrals_count": valid_count}}
    )

    # Notify on progress milestones
    old_count = user.get("valid_referrals_count", 0)
    if valid_count > old_count and valid_count < AMBASSADOR_REQUIRED_REFERRALS:
        remaining = AMBASSADOR_REQUIRED_REFERRALS - valid_count
        if valid_count == 1:
            msg = "Um amigo teu contribuiu! Bom começo! Faltam 2 para seres Embaixador."
        elif valid_count == 2:
            msg = "Quase lá! Falta apenas 1 amigo para desbloquear o modo Embaixador!"
        else:
            msg = f"Já tens {valid_count}/{AMBASSADOR_REQUIRED_REFERRALS}! Faltam {remaining} amigo(s)."
        asyncio.create_task(create_notification(
            user_id, "referral_contributed", msg,
            {"valid_referrals": valid_count, "required": AMBASSADOR_REQUIRED_REFERRALS}
        ))

    # Check if ambassador threshold reached
    if valid_count >= AMBASSADOR_REQUIRED_REFERRALS:
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "level": "embaixador",
                "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        asyncio.create_task(send_ambassador_unlocked_email(user_id))
        asyncio.create_task(create_notification(
            user_id, "ambassador_unlocked",
            "Parabéns! És agora Embaixador 4Luis! Todas as funcionalidades premium estão desbloqueadas.",
            {"valid_referrals": valid_count}
        ))
        logger.info(f"User {user_id} promoted to ambassador with {valid_count} valid referrals")
        return True

    return False


@api_router.get("/ambassador/progress")
async def get_ambassador_progress(request: Request):
    """Get user's progress towards ambassador status with referral details."""
    user = await require_auth(request)
    user_id = user.user_id
    user_data = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})

    is_ambassador = user_data.get("level") == "embaixador"

    # Get main journey
    main_journey = await db.journeys.find_one(
        {"is_main_trip": True, "is_active": True},
        {"_id": 0, "journey_id": 1, "name": 1}
    )
    if not main_journey:
        main_journey = await db.journeys.find_one(
            {"is_active": True, "status": "ativa"},
            {"_id": 0, "journey_id": 1, "name": 1}
        )

    # Get invited users
    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1, "name": 1, "created_at": 1}
    ).to_list(1000)

    # For each invited user, check if they contributed
    referral_details = []
    valid_count = 0
    for inv in invited_users:
        has_contribution = False
        if main_journey:
            contrib = await db.contributions.find_one({
                "user_id": inv["user_id"],
                "journey_id": main_journey["journey_id"],
                "status": {"$in": ["confirmed", "completed"]},
                "amount": {"$gt": 0}
            })
            has_contribution = contrib is not None
        if has_contribution:
            valid_count += 1
        referral_details.append({
            "name": inv.get("name", "Utilizador"),
            "registered": True,
            "contributed": has_contribution,
            "registered_at": inv.get("created_at")
        })

    # Get or create sponsor link for sharing
    sponsor_link = await db.sponsor_links.find_one(
        {"user_id": user_id},
        {"_id": 0, "link_id": 1}
    )
    referral_code = sponsor_link["link_id"] if sponsor_link else None

    remaining = max(0, AMBASSADOR_REQUIRED_REFERRALS - valid_count)

    return {
        "is_ambassador": is_ambassador,
        "unlocked_at": user_data.get("embaixador_unlocked_at"),
        "valid_referrals": valid_count,
        "total_invited": len(invited_users),
        "required": AMBASSADOR_REQUIRED_REFERRALS,
        "remaining": remaining,
        "progress_pct": min(100, round((valid_count / AMBASSADOR_REQUIRED_REFERRALS) * 100)),
        "referral_code": referral_code,
        "referrals": referral_details,
        "premium_features": {
            "smart_map": is_ambassador,
            "secret_tips": is_ambassador,
            "enhanced_ctas": is_ambassador,
            "ai_assistant": is_ambassador,
            "premium_guide": is_ambassador,
        }
    }


@api_router.post("/ambassador/generate-referral")
async def generate_ambassador_referral(request: Request):
    """Generate a unique referral link for ambassador progression."""
    user = await require_auth(request)
    user_id = user.user_id

    # Anti-abuse: get main journey
    main_journey = await db.journeys.find_one(
        {"is_main_trip": True, "is_active": True},
        {"_id": 0, "journey_id": 1}
    )
    if not main_journey:
        main_journey = await db.journeys.find_one(
            {"is_active": True, "status": "ativa"},
            {"_id": 0, "journey_id": 1}
        )
    if not main_journey:
        raise HTTPException(status_code=404, detail="Nenhuma viagem ativa encontrada")

    # Check if link already exists
    existing = await db.sponsor_links.find_one(
        {"user_id": user_id, "journey_id": main_journey["journey_id"]},
        {"_id": 0}
    )
    if existing:
        return {
            "referral_code": existing["link_id"],
            "journey_id": main_journey["journey_id"]
        }

    # Create new sponsor link
    link = SponsorLink(user_id=user_id, journey_id=main_journey["journey_id"])
    doc = link.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.sponsor_links.insert_one(doc)

    return {
        "referral_code": doc["link_id"],
        "journey_id": main_journey["journey_id"]
    }


@api_router.get("/ambassador/features")
async def get_ambassador_features(request: Request):
    """Check which premium features are available. Works for both auth and anonymous."""
    user = await get_current_user(request)
    if not user:
        return {
            "is_ambassador": False,
            "features": {
                "smart_map": False,
                "secret_tips": False,
                "enhanced_ctas": False,
                "ai_assistant": False,
                "premium_guide": False,
            }
        }
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    is_amb = user_data.get("level") == "embaixador" if user_data else False
    return {
        "is_ambassador": is_amb,
        "features": {
            "smart_map": is_amb,
            "secret_tips": is_amb,
            "enhanced_ctas": is_amb,
            "ai_assistant": is_amb,
            "premium_guide": is_amb,
        }
    }


# ==================== AMBASSADOR CERTIFICATION ====================

@api_router.get("/ambassador/{user_id}/profile")
async def get_ambassador_certification_profile(user_id: str):
    """Get public ambassador profile with certification and stats"""
    user_data = await db.users.find_one(
        {"user_id": user_id, "level": "embaixador"},
        {"_id": 0, "password_hash": 0}
    )
    if not user_data:
        raise HTTPException(status_code=404, detail="Embaixador não encontrado")
    
    cert_level = user_data.get("certification_level", "embaixador")
    cert_info = CERTIFICATION_LEVELS.get(cert_level, CERTIFICATION_LEVELS["embaixador"])
    
    # Stats
    journeys = await db.journeys.find(
        {"ambassador_user_id": user_id},
        {"_id": 0, "journey_id": 1, "name": 1, "status": 1, "current_amount": 1, "goal_amount": 1}
    ).to_list(50)
    
    total_raised = sum(j.get("current_amount", 0) for j in journeys)
    total_supporters = await db.contributions.distinct("user_id", {
        "ambassador_user_id": user_id,
        "status": {"$in": ["confirmed", "completed"]}
    })
    
    display_name = user_data.get("name") if user_data.get("use_real_name", True) else user_data.get("anonymous_alias", "Embaixador")
    avatar = user_data.get("avatar") or user_data.get("anonymous_avatar")
    
    return {
        "user_id": user_id,
        "display_name": display_name,
        "avatar": avatar,
        "certification": {
            "level": cert_level,
            "label": cert_info["label"],
            "level_number": cert_info["level"],
            "verified_at": user_data.get("certification_verified_at"),
        },
        "stats": {
            "total_raised": total_raised,
            "total_supporters": len(total_supporters),
            "journeys_count": len(journeys),
            "journeys_funded": sum(1 for j in journeys if j.get("status") in ("financiada", "realizada")),
        },
        "journeys": journeys,
        "member_since": user_data.get("created_at"),
        "embaixador_since": user_data.get("embaixador_unlocked_at")
    }


@api_router.put("/admin/ambassador/{user_id}/certification")
async def update_ambassador_certification(user_id: str, request: Request):
    """Admin: Update ambassador certification level"""
    await require_admin(request)
    data = await request.json()
    new_level = data.get("certification_level")
    
    if new_level not in CERTIFICATION_LEVELS:
        raise HTTPException(status_code=400, detail=f"Nível inválido. Opções: {list(CERTIFICATION_LEVELS.keys())}")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user or user.get("level") != "embaixador":
        raise HTTPException(status_code=404, detail="Embaixador não encontrado")
    
    update = {
        "certification_level": new_level,
        "certification_updated_at": datetime.now(timezone.utc).isoformat()
    }
    if new_level in ("verificado", "confiavel"):
        update["certification_verified_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"user_id": user_id}, {"$set": update})
    
    # Notify ambassador
    label = CERTIFICATION_LEVELS[new_level]["label"]
    asyncio.create_task(create_notification(
        user_id, "certification_updated",
        f"O teu nível de certificação foi atualizado para: {label}",
        {"certification_level": new_level}
    ))
    
    return {"message": f"Certificação atualizada para {label}", "certification_level": new_level}


@api_router.post("/ambassador/report")
async def report_ambassador(request: Request):
    """Report an ambassador campaign (anti-fraud)"""
    data = await request.json()
    journey_id = data.get("journey_id")
    reason = data.get("reason", "")
    
    if not journey_id:
        raise HTTPException(status_code=400, detail="journey_id obrigatório")
    
    user = await get_current_user(request)
    reporter_id = user.user_id if user else None
    
    report_doc = {
        "report_id": f"report_{uuid.uuid4().hex[:12]}",
        "journey_id": journey_id,
        "reporter_user_id": reporter_id,
        "reason": reason,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.reports.insert_one(report_doc)
    
    # Notify admin
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0, "name": 1})
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "type": "campaign_reported",
        "title": "Campanha reportada",
        "message": f"A viagem '{journey.get('name', journey_id)}' foi reportada. Motivo: {reason[:100]}",
        "journey_id": journey_id,
        "for_admin": True,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Denúncia registada. A equipa irá analisar."}


@api_router.get("/journey/{journey_id}/payment-info")
async def get_journey_payment_info(journey_id: str):
    """Get payment info for a journey (direct mode returns ambassador payment methods)"""
    journey = await db.journeys.find_one({"journey_id": journey_id, "is_active": True}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    payment_mode = journey.get("payment_mode", "platform")
    
    result = {
        "payment_mode": payment_mode,
        "journey_id": journey_id,
        "is_ambassador_journey": journey.get("is_ambassador_journey", False),
    }
    
    if payment_mode == "direct" and journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "name": 1, "anonymous_alias": 1, "use_real_name": 1, "certification_level": 1}
        )
        amb_name = ambassador.get("name") if ambassador and ambassador.get("use_real_name", True) else ambassador.get("anonymous_alias", "Embaixador") if ambassador else "Embaixador"
        cert_level = ambassador.get("certification_level", "embaixador") if ambassador else "embaixador"
        
        result["ambassador_name"] = amb_name
        result["ambassador_certification"] = cert_level
        result["ambassador_certification_label"] = CERTIFICATION_LEVELS.get(cert_level, {}).get("label", "Embaixador 4Luis")
        result["ambassador_payment_methods"] = journey.get("ambassador_payment_methods", {})
        result["ambassador_payment_instructions"] = journey.get("ambassador_payment_instructions")
    
    return result



@api_router.get("/success-stories")
async def get_success_stories():
    """Get funded ambassador journeys for social proof (homepage section)"""
    journeys = await db.journeys.find(
        {
            "is_ambassador_journey": True,
            "status": {"$in": ["financiada", "realizada"]},
        },
        {"_id": 0, "journey_id": 1, "name": 1, "poetic_name": 1, "image_url": 1,
         "ambassador_name": 1, "ambassador_user_id": 1, "current_amount": 1, "goal_amount": 1,
         "status": 1, "created_at": 1}
    ).sort("updated_at", -1).limit(6).to_list(6)
    
    # Enrich with contributor count
    for j in journeys:
        count = await db.contributions.count_documents({
            "journey_id": j["journey_id"],
            "status": {"$in": ["confirmed", "completed"]}
        })
        j["contributor_count"] = count
        # Get ambassador avatar
        if j.get("ambassador_user_id"):
            amb = await db.users.find_one(
                {"user_id": j["ambassador_user_id"]},
                {"_id": 0, "avatar": 1, "anonymous_avatar": 1, "name": 1, "anonymous_alias": 1, "use_real_name": 1}
            )
            if amb:
                j["ambassador_avatar"] = amb.get("avatar") or amb.get("anonymous_avatar")
                j["ambassador_display_name"] = amb.get("name") if amb.get("use_real_name", True) else amb.get("anonymous_alias", "Embaixador")
    
    return {"stories": journeys}



@api_router.get("/ambassador/{user_id}/trust-indicators")
async def get_ambassador_trust_indicators(user_id: str):
    """Get trust indicators for an ambassador (confirmation rate, total confirmed, etc.)"""
    # Get ambassador's journeys
    journey_ids = await db.journeys.distinct("journey_id", {"ambassador_user_id": user_id})
    
    if not journey_ids:
        return {"confirmed_count": 0, "total_count": 0, "confirmation_rate": 0, "total_raised": 0}
    
    confirmed = await db.contributions.count_documents({
        "journey_id": {"$in": journey_ids},
        "status": {"$in": ["confirmed", "completed"]}
    })
    rejected = await db.contributions.count_documents({
        "journey_id": {"$in": journey_ids},
        "status": "rejected"
    })
    total = confirmed + rejected
    rate = round((confirmed / max(total, 1)) * 100) if total > 0 else 0
    
    # Total raised
    pipeline = [
        {"$match": {"journey_id": {"$in": journey_ids}, "status": {"$in": ["confirmed", "completed"]}}},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$support_amount", "$amount"]}}}}
    ]
    result = await db.contributions.aggregate(pipeline).to_list(1)
    total_raised = result[0]["total"] if result else 0
    
    # Average confirmation time (only if confirmed_count > 5)
    avg_confirmation_time = None
    avg_confirmation_label = None
    if confirmed > 5:
        time_pipeline = [
            {"$match": {
                "journey_id": {"$in": journey_ids},
                "status": {"$in": ["confirmed", "completed"]},
                "confirmed_by_user_at": {"$exists": True},
                "validated_at": {"$exists": True}
            }},
            {"$project": {
                "user_confirmed": "$confirmed_by_user_at",
                "validated": "$validated_at"
            }}
        ]
        time_docs = await db.contributions.aggregate(time_pipeline).to_list(200)
        
        deltas = []
        for doc in time_docs:
            try:
                t1 = datetime.fromisoformat(doc["user_confirmed"].replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(doc["validated"].replace("Z", "+00:00"))
                delta_hours = (t2 - t1).total_seconds() / 3600
                if 0 < delta_hours < 168:  # ignore outliers > 7 days
                    deltas.append(delta_hours)
            except Exception:
                continue
        
        if len(deltas) >= 3:
            avg_h = sum(deltas) / len(deltas)
            avg_confirmation_time = round(avg_h, 1)
            if avg_h < 1:
                avg_confirmation_label = f"~{round(avg_h * 60)}min"
            elif avg_h < 24:
                avg_confirmation_label = f"~{round(avg_h)}h"
            else:
                avg_confirmation_label = f"~{round(avg_h / 24)}d"
    
    return {
        "confirmed_count": confirmed,
        "total_count": total,
        "confirmation_rate": rate,
        "total_raised": total_raised,
        "avg_confirmation_time": avg_confirmation_time,
        "avg_confirmation_label": avg_confirmation_label
    }


# ==================== NOTIFICATIONS ====================

async def create_notification(user_id: str, ntype: str, message: str, data: dict = None):
    """Create a notification for a user."""
    doc = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": ntype,
        "message": message,
        "data": data or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(doc)
    return doc["notification_id"]


@api_router.get("/notifications")
async def get_notifications(request: Request):
    """Get user notifications (most recent first)."""
    user = await require_auth(request)
    notifs = await db.notifications.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    unread = sum(1 for n in notifs if not n.get("read"))
    return {"notifications": notifs, "unread_count": unread}


@api_router.post("/notifications/mark-read")
async def mark_notifications_read(request: Request):
    """Mark all notifications as read."""
    user = await require_auth(request)
    await db.notifications.update_many(
        {"user_id": user.user_id, "read": False},
        {"$set": {"read": True}}
    )
    return {"status": "ok"}

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
        {"_id": 0, "user_id": 1, "name": 1, "anonymous_alias": 1}
    ).to_list(1000)
    invited_user_ids = [u["user_id"] for u in invited_users]
    
    # Total contributed by invited users (these are the "valid referrals")
    invited_contributions = await db.contributions.find(
        {"user_id": {"$in": invited_user_ids}, "status": "completed"},
        {"_id": 0}
    ).to_list(10000)
    impact_amount = sum(c.get("amount", 0) for c in invited_contributions)
    
    # Build individual referral details
    referral_details = []
    for inv_user in invited_users:
        user_contribs = [c for c in invited_contributions if c.get("user_id") == inv_user["user_id"]]
        user_total = sum(c.get("amount", 0) for c in user_contribs)
        has_contributed = len(user_contribs) > 0
        display_name = inv_user.get("name") or inv_user.get("anonymous_alias") or "Amigo"
        referral_details.append({
            "name": display_name,
            "has_contributed": has_contributed,
            "amount": user_total
        })
    # Sort: contributors first
    referral_details.sort(key=lambda x: (-x["amount"], not x["has_contributed"], x["name"]))
    
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
            "sponsor_links": sponsor_links,
            "referral_details": referral_details
        },
        "main_journey": main_journey,
        "main_sponsor_link": main_sponsor_link,
        "user_alias": user_data.get("anonymous_alias") or user_data.get("name") or ""
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

# ==================== PUBLIC AMBASSADOR PROFILE ====================

@api_router.get("/ambassador/{user_id}/public-profile")
async def get_ambassador_public_profile(user_id: str):
    """Get public profile of an ambassador - accessible to everyone"""
    
    # Get user data
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0, "email": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    # Check if user is an ambassador (or has contributed - we show profiles for active community members)
    is_ambassador = user.get("level") == "embaixador"
    
    # Get display name based on privacy settings
    use_real_name = user.get("use_real_name", True)
    if use_real_name:
        display_name = user.get("name", "Sonhador")
        display_avatar = user.get("avatar") or f"https://api.dicebear.com/7.x/initials/svg?seed={user.get('name', 'S')}"
    else:
        display_name = user.get("anonymous_alias") or user.get("alias") or "Sonhador Anónimo"
        display_avatar = user.get("anonymous_avatar") or f"https://api.dicebear.com/7.x/shapes/svg?seed={user_id}"
    
    # === BASIC IDENTITY ===
    identity = {
        "display_name": display_name,
        "avatar": display_avatar,
        "level": user.get("level", "sonhador"),
        "is_ambassador": is_ambassador,
        "certification_level": user.get("certification_level", "embaixador") if is_ambassador else None,
        "certification_label": CERTIFICATION_LEVELS.get(user.get("certification_level", "embaixador"), {}).get("label") if is_ambassador else None,
        "country": user.get("country"),
        "bio": user.get("bio"),
        "member_since": user.get("created_at"),
        "embaixador_unlocked_at": user.get("embaixador_unlocked_at")
    }
    
    # === CURRENT JOURNEY (if ambassador) ===
    current_journey = None
    if is_ambassador:
        # Find their active journey
        journey = await db.journeys.find_one(
            {"ambassador_user_id": user_id, "status": {"$in": ["ativa", "aprovada", "candidatura"]}},
            {"_id": 0, "goal_amount": 0, "admin_notes": 0}
        )
        if journey:
            # Get progress
            full_journey = await db.journeys.find_one({"journey_id": journey["journey_id"]}, {"_id": 0})
            goal = full_journey.get("goal_amount", 1) if full_journey else 1
            current = journey.get("current_amount", 0)
            percentage = round((current / goal) * 100, 1) if goal > 0 else 0
            
            current_journey = {
                "journey_id": journey.get("journey_id"),
                "name": journey.get("name"),
                "poetic_name": journey.get("poetic_name"),
                "description": journey.get("description"),
                "image_url": journey.get("image_url"),
                "status": journey.get("status"),
                "country": journey.get("country"),
                "city": journey.get("city"),
                "progress_percentage": percentage,
                "current_amount": current
            }
    
    # === PREVIOUS CONTRIBUTIONS ===
    contributions = await db.contributions.find(
        {"user_id": user_id, "status": {"$in": ["confirmed", "completed"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    total_contributed = sum(c.get("amount", 0) for c in contributions)
    
    # Check if contributed to main journey
    main_journey = await db.journeys.find_one(
        {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]},
        {"_id": 0, "journey_id": 1}
    )
    contributed_to_main = False
    if main_journey:
        main_contribution = await db.contributions.find_one({
            "user_id": user_id,
            "journey_id": main_journey["journey_id"],
            "status": {"$in": ["confirmed", "completed"]}
        })
        contributed_to_main = main_contribution is not None
    
    contributions_summary = {
        "total_amount": total_contributed,
        "total_count": len(contributions),
        "contributed_to_main_journey": contributed_to_main,
        "has_crypto_contributions": any(c.get("payment_method") == "crypto" for c in contributions)
    }
    
    # === SOCIAL IMPACT ===
    # Get referral stats
    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1}
    ).to_list(1000)
    invited_user_ids = [u["user_id"] for u in invited_users]
    
    # Count contributions from invited users
    contributions_from_invites = 0
    amount_from_invites = 0
    if invited_user_ids:
        invite_contributions = await db.contributions.find(
            {"user_id": {"$in": invited_user_ids}, "status": {"$in": ["confirmed", "completed"]}},
            {"_id": 0}
        ).to_list(1000)
        contributions_from_invites = len(invite_contributions)
        amount_from_invites = sum(c.get("amount", 0) for c in invite_contributions)
    
    social_impact = {
        "people_invited": len(invited_users),
        "valid_referrals": user.get("valid_referrals_count", 0),
        "contributions_generated": contributions_from_invites,
        "amount_generated": amount_from_invites
    }
    
    # === REALIZED JOURNEYS (past journeys) ===
    realized_journeys = []
    if is_ambassador:
        past_journeys = await db.journeys.find(
            {"ambassador_user_id": user_id, "status": {"$in": ["financiada", "realizada", "encerrada"]}},
            {"_id": 0, "goal_amount": 0, "admin_notes": 0}
        ).sort("funded_at", -1).to_list(50)
        
        for j in past_journeys:
            realized_journeys.append({
                "journey_id": j.get("journey_id"),
                "name": j.get("name"),
                "image_url": j.get("image_url"),
                "country": j.get("country"),
                "status": j.get("status"),
                "story": j.get("story"),
                "photos": j.get("photos", []),
                "funded_at": j.get("funded_at"),
                "realized_at": j.get("realized_at")
            })
    
    # === TESTIMONIALS (future feature - placeholder) ===
    testimonials = []
    # TODO: Implement testimonials collection
    
    return {
        "identity": identity,
        "current_journey": current_journey,
        "contributions": contributions_summary,
        "social_impact": social_impact,
        "realized_journeys": realized_journeys,
        "testimonials": testimonials
    }

@api_router.put("/profile/public-info")
async def update_public_profile_info(request: Request):
    """Update public profile information (country, bio)"""
    user = await require_auth(request)
    data = await request.json()
    
    allowed_fields = ["country", "bio"]
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    
    if "bio" in updates and len(updates["bio"]) > 500:
        raise HTTPException(status_code=400, detail="Bio não pode exceder 500 caracteres")
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": updates}
    )
    
    return {"message": "Perfil atualizado com sucesso"}

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


@api_router.patch("/users/preferred-language")
async def update_preferred_language(request: Request):
    user = await require_auth(request)
    body = await request.json()
    lang = body.get("language", "pt")
    if lang not in ("pt", "en", "es", "fr", "de", "it"):
        raise HTTPException(status_code=400, detail="Idioma não suportado")
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"preferred_language": lang}}
    )
    return {"message": "Idioma atualizado", "preferred_language": lang}

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

@api_router.post("/admin/generate-contribution-descriptions")
async def generate_contribution_descriptions(request: Request):
    """Generate inspirational contribution descriptions using AI"""
    user = await require_admin(request)
    
    body = await request.json()
    journey_name = body.get("journey_name", "")
    poetic_name = body.get("poetic_name", "")
    description = body.get("description", "")
    
    if not journey_name:
        raise HTTPException(status_code=400, detail="Nome da viagem é obrigatório")
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA não configurada")
    
    context = f"Destino: {journey_name}"
    if poetic_name:
        context += f" — {poetic_name}"
    if description:
        context += f". {description}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"contrib_desc_{uuid.uuid4().hex[:8]}",
        system_message="""Gera descrições curtas e inspiradoras para valores de contribuição numa plataforma de crowdfunding de viagens.
Cada descrição deve evocar uma experiência concreta relacionada com o destino.
Responde APENAS com um JSON com as chaves "10", "20", "50", "100", "200", "500", "1000" e os valores são frases curtas em português.
Exemplo: {"10": "Um café com vista para a Torre Eiffel", "20": "Um almoço num bistrô parisiense", ...}
Sem explicações, apenas o JSON."""
    ).with_model("openai", "gpt-5.2")
    
    user_message = UserMessage(text=f"Gera descrições de contribuição para: {context}")
    
    try:
        response = await chat.send_message(user_message)
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        import json as json_mod
        descriptions = json_mod.loads(clean_response)
        return {"descriptions": descriptions}
    except Exception as e:
        logger.error(f"AI description generation error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar descrições com IA")


@api_router.post("/admin/generate-story-chapters")
async def generate_story_chapters(request: Request):
    """Generate 5 storytelling chapters using AI"""
    user = await require_admin(request)
    
    body = await request.json()
    journey_name = body.get("journey_name", "")
    poetic_name = body.get("poetic_name", "")
    description = body.get("description", "")
    
    if not journey_name:
        raise HTTPException(status_code=400, detail="Nome da viagem é obrigatório")
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA não configurada")
    
    context = f"Destino: {journey_name}"
    if poetic_name:
        context += f" — {poetic_name}"
    if description:
        context += f". {description}"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"story_gen_{uuid.uuid4().hex[:8]}",
        system_message="""Gera 5 capítulos de storytelling para uma campanha de crowdfunding de viagens.
Cada capítulo corresponde a um nível de financiamento:
1: 0%-25% (O sonho nasce)
2: 25%-50% (O sonho ganha forma)
3: 50%-75% (O sonho aproxima-se)
4: 75%-100% (O sonho quase real)
5: 100%+ (O sonho realizado)

Cada capítulo deve ter um título curto e 2-3 linhas de texto poético/emocional em português, relacionadas com o destino.
Responde APENAS com JSON no formato:
{"1": {"title": "...", "lines": ["linha1", "linha2"]}, "2": {...}, "3": {...}, "4": {...}, "5": {...}}
Sem explicações, apenas o JSON."""
    ).with_model("openai", "gpt-5.2")
    
    user_message = UserMessage(text=f"Gera 5 capítulos de storytelling para: {context}")
    
    try:
        response = await chat.send_message(user_message)
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        import json as json_mod
        chapters = json_mod.loads(clean_response)
        return {"chapters": chapters}
    except Exception as e:
        logger.error(f"AI story generation error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar capítulos com IA")


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
    frontend_url = FRONTEND_URL
    
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
    # Base offset: platform started with 67 dreamers before tracking
    total_dreamers += 67
    
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

@api_router.get("/admin/contributions/search")
async def search_contributions_by_reference(request: Request, ref: str = None):
    """Search contributions by payment reference"""
    await require_admin(request)
    
    if not ref:
        raise HTTPException(status_code=400, detail="Parâmetro 'ref' é obrigatório")
    
    # Search by payment_reference (case-insensitive)
    query = {"payment_reference": {"$regex": ref.upper(), "$options": "i"}}
    contributions = await db.contributions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with user and journey info
    for contrib in contributions:
        if contrib.get("user_id"):
            user = await db.users.find_one({"user_id": contrib["user_id"]}, {"_id": 0, "name": 1, "email": 1})
            contrib["user_name"] = user.get("name") if user else "Desconhecido"
            contrib["user_email"] = user.get("email") if user else ""
        else:
            contrib["user_name"] = contrib.get("contributor_name") or "Anónimo"
            contrib["user_email"] = contrib.get("contributor_email") or ""
        
        journey = await db.journeys.find_one({"journey_id": contrib["journey_id"]}, {"_id": 0, "name": 1})
        contrib["journey_name"] = journey.get("name") if journey else "Desconhecida"
    
    return {
        "count": len(contributions),
        "contributions": contributions
    }

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
            contrib["user_name"] = contrib.get("contributor_name") or "Anónimo"
            contrib["user_email"] = contrib.get("contributor_email") or ""
        
        journey = await db.journeys.find_one({"journey_id": contrib["journey_id"]}, {"_id": 0, "name": 1})
        contrib["journey_name"] = journey.get("name") if journey else "Desconhecida"
        
        # Ensure payment_reference is included
        if not contrib.get("payment_reference"):
            contrib["payment_reference"] = None
    
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
    
    # Update user total_contributed
    if contribution.get("user_id"):
        await db.users.update_one(
            {"user_id": contribution["user_id"]},
            {"$inc": {"total_contributed": contribution["amount"]}}
        )
    
    # Check if journey reached goal - update status automatically
    await check_and_update_journey_funding_status(contribution["journey_id"])
    
    # Check story chapter progression
    await check_and_update_story_chapter(contribution["journey_id"])
    
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
            {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]}, 
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
        # Notify contributor
        journey_name = (await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0, "name": 1})) or {}
        await create_notification(
            contribution["user_id"],
            "contribution",
            f"A tua contribuição de {contribution['amount']}€ para {journey_name.get('name', 'esta viagem')} foi confirmada.",
            {"journey_id": contribution.get("journey_id"), "amount": contribution.get("amount")}
        )
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

@api_router.post("/admin/test-email")
async def test_email_send(request: Request):
    """Test email sending - Admin only"""
    await require_admin(request)
    data = await request.json()
    
    test_email = data.get("to_email", data.get("email", ADMIN_EMAIL))
    
    # Create a simple test email
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Teste de Email 4Luis</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        Este é um email de teste para verificar a integração do Resend.
    </p>
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; text-align: center;">
        <p style="margin: 0; color: #2D2A26;">Timestamp: {datetime.now(timezone.utc).isoformat()}</p>
    </div>
    """
    
    html = get_email_base_template(content, "Teste Email - 4Luis")
    
    result = await send_email_resend(
        to_email=test_email,
        subject="🧪 Teste de Email - 4Luis",
        html_content=html
    )
    
    return {
        "message": f"Email de teste enviado para {test_email}",
        "result": result
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
        
        # Update user total_contributed
        if contribution.get("user_id"):
            await db.users.update_one(
                {"user_id": contribution["user_id"]},
                {"$inc": {"total_contributed": contribution["amount"]}}
            )
        
        # Check if journey reached goal - use helper function
        await check_and_update_journey_funding_status(contribution["journey_id"])
        
        # Check story chapter progression
        await check_and_update_story_chapter(contribution["journey_id"])
        
        # Send confirmation email to contributor
        journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
        if journey:
            try:
                await send_contribution_confirmed_email(contribution, journey)
                logger.info(f"Confirmation email sent for contribution {contribution_id}")
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {e}")
        
        # MOTOR EMBAIXADOR: Update user progression
        if contribution.get("user_id"):
            user = await db.users.find_one(
                {"user_id": contribution["user_id"]}, 
                {"_id": 0}
            )
            
            if user:
                # Mark contributed to main trip
                main_journey = await db.journeys.find_one(
                    {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]}, 
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
    
    if new_level not in ["sonhador", "verificado", "embaixador"]:
        raise HTTPException(status_code=400, detail="Nível inválido. Use: sonhador, verificado, embaixador")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    update_data = {"level": new_level}
    if new_level == "embaixador" and not user.get("embaixador_unlocked_at"):
        update_data["embaixador_unlocked_at"] = datetime.now(timezone.utc).isoformat()
    
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
    """Check if journey reached funding goal and update status based on journey type.
    - Main journey (is_main_trip): sets funding_status to 'pending_validation', notifies admin
    - Ambassador journeys: sets funding_status to 'completed' automatically (no manual validation)
    Both types continue to accept contributions after reaching 100%.
    """
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return None
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    current_funding_status = journey.get("funding_status", "active")
    
    # Skip if already completed or pending_validation
    if current_funding_status in ("completed", "pending_validation"):
        return current_funding_status
    
    # Check if funded (100%+)
    if current_amount >= goal_amount:
        now_iso = datetime.now(timezone.utc).isoformat()
        is_main = journey.get("is_main_trip", False)
        is_ambassador = journey.get("is_ambassador_journey", False)

        if is_main and not is_ambassador:
            # ── MAIN JOURNEY: pending admin validation ──
            new_status = "pending_validation"
            await db.journeys.update_one(
                {"journey_id": journey_id},
                {"$set": {
                    "funding_status": new_status,
                    "funded_at": now_iso,
                    "updated_at": now_iso
                    # NOTE: is_active stays True, contributions still accepted
                }}
            )
            # Notify admin
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "main_journey_funded",
                "title": "Viagem Principal atingiu 100%!",
                "message": f"A viagem principal '{journey.get('name')}' atingiu o objetivo. Aguarda a tua validação para ativar a celebração.",
                "journey_id": journey_id,
                "for_admin": True,
                "read": False,
                "created_at": now_iso
            })
            logger.info(f"Main journey {journey_id} reached 100% — set to pending_validation")
        else:
            # ── AMBASSADOR JOURNEY: auto-complete ──
            new_status = "completed"
            await db.journeys.update_one(
                {"journey_id": journey_id},
                {"$set": {
                    "funding_status": new_status,
                    "status": "financiada",
                    "funded_at": now_iso,
                    "is_active": False,
                    "updated_at": now_iso
                }}
            )
            # Notify admin
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "journey_funded",
                "title": "Viagem Financiada!",
                "message": f"A viagem '{journey.get('name')}' atingiu o objetivo de financiamento.",
                "journey_id": journey_id,
                "for_admin": True,
                "read": False,
                "created_at": now_iso
            })
            # Notify ambassador
            if journey.get("ambassador_user_id"):
                ambassador_user_id = journey["ambassador_user_id"]
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "type": "your_journey_funded",
                    "title": "A tua viagem foi financiada!",
                    "message": f"Parabéns! A tua viagem '{journey.get('name')}' atingiu o objetivo de financiamento.",
                    "journey_id": journey_id,
                    "user_id": ambassador_user_id,
                    "read": False,
                    "created_at": now_iso
                })
                ambassador = await db.users.find_one({"user_id": ambassador_user_id}, {"_id": 0})
                await send_journey_funded_emails(journey, ambassador, current_amount)
            else:
                await send_journey_funded_emails(journey, None, current_amount)

            # ── Create payout record for ambassador ──
            if journey.get("ambassador_user_id"):
                existing_payout = await db.payouts.find_one({"journey_id": journey_id}, {"_id": 0})
                if not existing_payout:
                    payout_id = f"payout_{uuid.uuid4().hex[:12]}"
                    await db.payouts.insert_one({
                        "payout_id": payout_id,
                        "journey_id": journey_id,
                        "journey_name": journey.get("name", ""),
                        "ambassador_user_id": journey["ambassador_user_id"],
                        "ambassador_name": journey.get("ambassador_name", ""),
                        "amount": float(current_amount),
                        "goal_amount": float(goal_amount),
                        "status": "pending",
                        "payment_method": None,
                        "payment_reference": None,
                        "admin_notes": None,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                        "completed_at": None
                    })
                    logger.info(f"Payout {payout_id} created for ambassador journey {journey_id}")

            logger.info(f"Ambassador journey {journey_id} auto-completed")
        
        return new_status
    
    return current_funding_status


# ==================== PAYOUT ENDPOINTS ====================

@api_router.get("/admin/payouts")
async def get_admin_payouts(request: Request, status: Optional[str] = None):
    """Get all payouts with optional status filter"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_data or not user_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso negado")

    query = {}
    if status:
        query["status"] = status
    
    payouts = await db.payouts.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Compute summary
    all_payouts = await db.payouts.find({}, {"_id": 0}).to_list(500)
    summary = {
        "total": len(all_payouts),
        "pending": sum(1 for p in all_payouts if p["status"] == "pending"),
        "processing": sum(1 for p in all_payouts if p["status"] == "processing"),
        "completed": sum(1 for p in all_payouts if p["status"] == "completed"),
        "total_pending_amount": sum(p["amount"] for p in all_payouts if p["status"] in ("pending", "processing")),
        "total_paid_amount": sum(p["amount"] for p in all_payouts if p["status"] == "completed")
    }
    
    return {"payouts": payouts, "summary": summary}


@api_router.put("/admin/payouts/{payout_id}/status")
async def update_payout_status(payout_id: str, request: Request):
    """Update payout status (pending → processing → completed)"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_data or not user_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso negado")

    body = await request.json()
    new_status = body.get("status")
    if new_status not in ("pending", "processing", "completed"):
        raise HTTPException(status_code=400, detail="Status inválido")

    payout = await db.payouts.find_one({"payout_id": payout_id}, {"_id": 0})
    if not payout:
        raise HTTPException(status_code=404, detail="Payout não encontrado")

    now_iso = datetime.now(timezone.utc).isoformat()
    update_fields = {
        "status": new_status,
        "updated_at": now_iso,
        "updated_by": user.user_id
    }
    
    if body.get("payment_method"):
        update_fields["payment_method"] = body["payment_method"]
    if body.get("payment_reference"):
        update_fields["payment_reference"] = body["payment_reference"]
    if body.get("admin_notes"):
        update_fields["admin_notes"] = body["admin_notes"]
    if new_status == "completed":
        update_fields["completed_at"] = now_iso

    await db.payouts.update_one(
        {"payout_id": payout_id},
        {"$set": update_fields}
    )
    
    # Notify ambassador when payout is completed
    if new_status == "completed" and payout.get("ambassador_user_id"):
        await db.notifications.insert_one({
            "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
            "type": "payout_completed",
            "title": "Pagamento processado!",
            "message": f"O pagamento da viagem '{payout.get('journey_name')}' foi processado com sucesso.",
            "user_id": payout["ambassador_user_id"],
            "read": False,
            "created_at": now_iso
        })

    logger.info(f"Payout {payout_id} updated to {new_status} by {user.user_id}")
    return {"status": new_status, "message": f"Payout atualizado para {new_status}"}


@api_router.post("/admin/journey/{journey_id}/approve-funding")
async def admin_approve_journey_funding(journey_id: str, request: Request):
    """Admin endpoint to approve main journey funding — moves from pending_validation to completed"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_data or not user_data.get("is_admin"):
        raise HTTPException(status_code=403, detail="Acesso negado")

    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    if journey.get("funding_status") != "pending_validation":
        raise HTTPException(status_code=400, detail=f"Esta viagem não está pendente de validação (status: {journey.get('funding_status', 'active')})")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {
            "funding_status": "completed",
            "status": "financiada",
            "is_active": False,
            "approved_at": now_iso,
            "approved_by": user.user_id,
            "updated_at": now_iso
        }}
    )
    
    # Send funded emails
    current_amount = journey.get("current_amount", 0)
    await send_journey_funded_emails(journey, None, current_amount)

    logger.info(f"Admin {user.user_id} approved funding for journey {journey_id}")
    return {"status": "completed", "message": "Financiamento aprovado. Celebração ativada!"}

def get_chapter_number(percentage: float) -> int:
    """Get story chapter number based on funding percentage"""
    if percentage >= 100:
        return 5
    if percentage >= 75:
        return 4
    if percentage >= 50:
        return 3
    if percentage >= 25:
        return 2
    return 1

DEFAULT_STORY_CHAPTERS = {
    "1": {"title": "O sonho nasce", "lines": ["Um sonho de atravessar terras distantes,", "de descobrir culturas e paisagens novas.", "", "Esta jornada começa aqui."]},
    "2": {"title": "O sonho ganha forma", "lines": ["Cada contribuição aproxima esta viagem da realidade.", "", "A comunidade já começou a construir este sonho."]},
    "3": {"title": "O sonho está a caminho", "lines": ["A jornada começa a ganhar forma.", "", "A rota começa a desenhar-se entre cidades", "e paisagens milenares."]},
    "4": {"title": "O sonho quase acontece", "lines": ["A viagem está cada vez mais próxima.", "", "Em breve esta história deixará de ser apenas um sonho."]},
    "5": {"title": "O sonho torna-se realidade", "lines": ["A comunidade tornou este sonho possível.", "", "Agora começa a verdadeira aventura."]}
}

async def check_and_update_story_chapter(journey_id: str):
    """Check if the journey has entered a new story chapter and send emails if needed"""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = (current_amount / goal_amount) * 100 if goal_amount > 0 else 0
    
    new_chapter = get_chapter_number(percentage)
    old_chapter = journey.get("current_chapter", 1)
    
    if new_chapter > old_chapter:
        # Check which milestone was crossed (25, 50, 75, 100)
        milestones = {2: "25", 3: "50", 4: "75", 5: "100"}
        milestone_key = milestones.get(new_chapter)
        
        # Check if email was already sent for this milestone
        chapters_sent = journey.get("chapters_emails_sent") or {}
        already_sent = chapters_sent.get(milestone_key, False) if milestone_key else False
        
        # Update the chapter and mark milestone as sent
        update_fields = {
            "current_chapter": new_chapter,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if milestone_key:
            update_fields[f"chapters_emails_sent.{milestone_key}"] = True
            update_fields["last_milestone_reached"] = int(milestone_key)
            update_fields["last_milestone_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.journeys.update_one(
            {"journey_id": journey_id},
            {"$set": update_fields}
        )
        
        logger.info(f"Journey {journey_id} moved from chapter {old_chapter} to {new_chapter}")
        
        # Send emails only if enabled AND not already sent for this milestone
        if journey.get("story_emails_enabled", True) and not already_sent:
            await send_chapter_change_emails(journey, new_chapter)
        elif already_sent:
            logger.info(f"Email for chapter {new_chapter} (milestone {milestone_key}%) already sent, skipping")

async def send_chapter_change_emails(journey: dict, chapter_num: int):
    """Send email to all users when a journey enters a new chapter"""
    chapters = journey.get("story_chapters") or DEFAULT_STORY_CHAPTERS
    chapter = chapters.get(str(chapter_num), DEFAULT_STORY_CHAPTERS.get(str(chapter_num)))
    
    if not chapter:
        return
    
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    journey_id = journey.get("journey_id", "")
    chapter_title = chapter.get("title", "")
    chapter_lines = chapter.get("lines", [])
    chapter_text = "<br>".join(line if line else "<br>" for line in chapter_lines)
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = round((current_amount / goal_amount) * 100, 1) if goal_amount > 0 else 0
    
    next_milestones = {1: 25, 2: 50, 3: 75, 4: 100}
    next_milestone = next_milestones.get(chapter_num)
    remaining_text = ""
    if next_milestone and percentage < next_milestone:
        remaining = round(next_milestone - percentage, 1)
        remaining_text = f'<p style="color: #FFBE98; font-size: 14px; font-style: italic; margin-top: 12px;">Faltam {remaining}% para o próximo capítulo do sonho.</p>'
    
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    subject = f'O sonho da {journey_name} entrou numa nova fase'
    
    html_content = get_email_base_template(_build_chapter_email_body(
        poetic_name, chapter_num, chapter_title, chapter_text,
        percentage, remaining_text, journey_url
    ), title=f"4Luis — Capítulo {chapter_num}")
    
    # Get all users with email
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    
    sent_count = 0
    for user_doc in users:
        email = user_doc.get("email", "")
        if email and "@" in email and not email.endswith("@test.com"):
            try:
                await send_email_resend(email, subject, html_content)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send chapter email to {email}: {e}")
    
    logger.info(f"Chapter {chapter_num} emails sent to {sent_count} users for journey {journey.get('journey_id')}")

def _build_chapter_email_body(poetic_name, chapter_num, chapter_title, chapter_text, percentage, remaining_text, journey_url):
    """Build the HTML body for chapter change emails"""
    pct_int = int(min(percentage, 100))
    filled_blocks = max(1, pct_int // 5)
    empty_blocks = 20 - filled_blocks
    progress_bar_text = "█" * filled_blocks + "░" * empty_blocks
    
    return f"""
        <div style="text-align: center; padding: 20px 0;">
            <p style="color: #6B6661; font-size: 16px; line-height: 1.6;">
                O sonho da viagem "<strong>{poetic_name}</strong>"<br>
                acabou de entrar numa nova fase.
            </p>
            <div style="background: #FFF8F3; border-radius: 16px; padding: 24px; margin: 24px 0; border-left: 4px solid #FFBE98;">
                <p style="color: #6B6661; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    Capítulo {chapter_num}
                </p>
                <p style="color: #FFBE98; font-size: 22px; font-style: italic; margin-bottom: 12px;">
                    {chapter_title}
                </p>
                <p style="color: #6B6661; font-size: 14px; line-height: 1.8;">
                    {chapter_text}
                </p>
            </div>
            <div style="background: #F5F5F4; border-radius: 16px; padding: 20px; margin: 20px 0;">
                <p style="color: #6B6661; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">
                    Progresso atual da viagem
                </p>
                <div style="background: #E7E5E4; border-radius: 8px; height: 12px; overflow: hidden; margin-bottom: 8px;">
                    <div style="background: linear-gradient(90deg, #FFBE98, #F2C94C); height: 100%; width: {pct_int}%; border-radius: 8px;"></div>
                </div>
                <p style="font-family: monospace; color: #6B6661; font-size: 12px; letter-spacing: 1px; margin-bottom: 4px;">
                    {progress_bar_text}
                </p>
                <p style="color: #2D2A26; font-size: 18px; font-weight: bold;">
                    {percentage}% financiado
                </p>
                {remaining_text}
            </div>
            <p style="color: #6B6661; font-size: 14px; margin-bottom: 20px;">
                Se quiseres ajudar a dar o próximo passo:
            </p>
            <a href="{journey_url}" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 14px 28px; border-radius: 12px; font-weight: bold; text-decoration: none; font-size: 16px;">
                Contribuir para este sonho
            </a>
        </div>
    """

@api_router.post("/admin/test-chapter-email/{journey_id}/{chapter_num}")
async def test_chapter_email(journey_id: str, chapter_num: int, request: Request):
    """Test chapter change email - sends to admin only"""
    await require_admin(request)
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    if chapter_num < 1 or chapter_num > 5:
        raise HTTPException(status_code=400, detail="Capítulo deve ser entre 1 e 5")
    
    chapters = journey.get("story_chapters") or DEFAULT_STORY_CHAPTERS
    chapter = chapters.get(str(chapter_num), DEFAULT_STORY_CHAPTERS.get(str(chapter_num)))
    
    if not chapter:
        raise HTTPException(status_code=404, detail="Capítulo não encontrado")
    
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    chapter_title = chapter.get("title", "")
    chapter_lines = chapter.get("lines", [])
    chapter_text = "<br>".join(line if line else "<br>" for line in chapter_lines)
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = round((current_amount / goal_amount) * 100, 1) if goal_amount > 0 else 0
    
    next_milestones = {1: 25, 2: 50, 3: 75, 4: 100}
    next_milestone = next_milestones.get(chapter_num)
    remaining_text = ""
    if next_milestone and percentage < next_milestone:
        remaining = round(next_milestone - percentage, 1)
        remaining_text = f'<p style="color: #FFBE98; font-size: 14px; font-style: italic; margin-top: 12px;">Faltam {remaining}% para o próximo capítulo do sonho.</p>'
    
    subject = f'O sonho da {journey_name} entrou numa nova fase'
    
    html_content = get_email_base_template(_build_chapter_email_body(
        poetic_name, chapter_num, chapter_title, chapter_text,
        percentage, remaining_text, journey_url
    ), title=f"4Luis — Capítulo {chapter_num}")
    
    # Send test email to admin only
    result = await send_email_resend("luis.canarias@gmail.com", subject, html_content)
    
    return {
        "message": f"Email de teste do capítulo {chapter_num} enviado",
        "chapter_title": chapter_title,
        "percentage": percentage,
        "result": result
    }

@api_router.post("/admin/emails/weekly-summary")
async def trigger_weekly_summary(request: Request):
    """Admin: Send weekly progress summary email to all users"""
    await require_admin(request)
    result = await send_weekly_summary_emails()
    return {"message": "Resumo semanal enviado", **result}

@api_router.get("/admin/emails/preview/weekly-summary")
async def preview_weekly_summary(request: Request):
    """Preview weekly summary email without sending"""
    await require_admin(request)
    
    active_journeys = await db.journeys.find(
        {"status": "ativa", "is_active": True}, {"_id": 0}
    ).to_list(50)
    
    journeys_html = ""
    for j in active_journeys:
        pct = round((j.get("current_amount", 0) / j.get("goal_amount", 1)) * 100, 1) if j.get("goal_amount", 0) > 0 else 0
        pct_int = int(min(pct, 100))
        journey_url = f"{FRONTEND_URL}/journey/{j['journey_id']}"
        journeys_html += f"""
        <div style="background: #FFF8F3; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <p style="color: #2D2A26; font-size: 18px; font-weight: bold; margin: 0 0 4px 0;">{j.get('name', '')}</p>
            <p style="color: #FFBE98; font-style: italic; font-size: 14px; margin: 0 0 12px 0;">{j.get('poetic_name', '')}</p>
            <div style="background: #E7E5E4; border-radius: 8px; height: 10px; overflow: hidden; margin-bottom: 8px;">
                <div style="background: linear-gradient(90deg, #FFBE98, #F2C94C); height: 100%; width: {pct_int}%; border-radius: 8px;"></div>
            </div>
            <p style="color: #2D2A26; font-size: 14px; font-weight: bold; margin: 0 0 12px 0;">{pct}% financiado</p>
            <a href="{journey_url}" style="color: #FFBE98; font-size: 14px; font-weight: bold; text-decoration: none;">Ver este sonho &rarr;</a>
        </div>
        """
    
    body = f"""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Resumo Semanal dos Sonhos</h1>
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 24px;">
            Aqui esta o progresso dos sonhos que estamos a construir juntos esta semana.
        </p>
        {journeys_html}
        {_build_email_cta_button(FRONTEND_URL, "Explorar todos os sonhos")}
    </div>
    """
    html = get_email_base_template(body, "Resumo Semanal - 4Luis")
    
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    recipient_count = sum(1 for u in users if u.get("email") and "@" in u["email"] and not u["email"].endswith("@test.com"))
    
    return {"subject": "Resumo semanal dos sonhos - 4Luis", "html": html, "recipient_count": recipient_count}

@api_router.get("/admin/emails/preview/dream-funded/{journey_id}")
async def preview_dream_funded(journey_id: str, request: Request):
    """Preview dream funded email without sending"""
    await require_admin(request)
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem nao encontrada")
    
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = round((current_amount / goal_amount) * 100, 1) if goal_amount > 0 else 100
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    contributors = await db.contributions.find({"journey_id": journey_id, "status": "completed"}, {"_id": 0}).to_list(500)
    
    body = _build_standard_email(
        title="Este sonho tornou-se realidade!",
        narrative=f"""A viagem &ldquo;<strong>{poetic_name or journey_name}</strong>&rdquo; acaba de ser totalmente financiada.<br><br>
        Gracas a <strong>{len(contributors)} sonhadores</strong> que acreditaram, este sonho vai acontecer.<br>
        Obrigado a todos os que ajudaram a transformar este sonho em realidade.""",
        percentage=percentage,
        cta_url=journey_url,
        cta_text="Ver este sonho realizado"
    )
    html = get_email_base_template(body, f"Sonho Realizado: {journey_name} - 4Luis")
    
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    recipient_count = sum(1 for u in users if u.get("email") and "@" in u["email"] and not u["email"].endswith("@test.com"))
    
    return {"subject": f"O sonho da {journey_name} tornou-se realidade!", "html": html, "recipient_count": recipient_count}

@api_router.get("/admin/emails/preview/new-journey/{journey_id}")
async def preview_new_journey(journey_id: str, request: Request):
    """Preview new journey announcement email without sending"""
    await require_admin(request)
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem nao encontrada")
    
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    description = journey.get("description", "")
    ambassador_name = journey.get("ambassador_name", "")
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    ambassador_line = f"<br>Sonho de <strong>{ambassador_name}</strong>" if ambassador_name else ""
    
    body = _build_standard_email(
        title=f"Novo sonho: {journey_name}",
        narrative=f"""Um novo sonho acabou de chegar a plataforma 4Luis.<br><br>
        &ldquo;<em>{poetic_name or description}</em>&rdquo;{ambassador_line}<br><br>
        Cada sonho comeca com um primeiro passo. Sera que este vai ser o teu?""",
        percentage=0,
        cta_url=journey_url,
        cta_text="Descobrir este sonho"
    )
    html = get_email_base_template(body, f"Novo Sonho: {journey_name} - 4Luis")
    
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    recipient_count = sum(1 for u in users if u.get("email") and "@" in u["email"] and not u["email"].endswith("@test.com"))
    
    return {"subject": f"Novo sonho na 4Luis: {journey_name}", "html": html, "recipient_count": recipient_count}



@api_router.post("/admin/emails/dream-funded/{journey_id}")
async def trigger_dream_funded_email(journey_id: str, request: Request):
    """Admin: Send dream funded announcement email to all users"""
    await require_admin(request)
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    # Mark journey as funded
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {
            "status": "financiada",
            "funded_at": datetime.now(timezone.utc).isoformat(),
            "funded_email_sent": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    result = await send_dream_funded_announcement(journey)
    return {"message": f"Email de sonho financiado enviado para {result['sent']} utilizadores", **result}

@api_router.post("/admin/emails/new-journey/{journey_id}")
async def trigger_new_journey_email(journey_id: str, request: Request):
    """Admin: Send new journey announcement email to all users"""
    await require_admin(request)
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    result = await send_new_journey_email(journey)
    
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {"announcement_email_sent": True}}
    )
    
    return {"message": f"Email de novo sonho enviado para {result['sent']} utilizadores", **result}

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
        "payment_mode": "direct",  # Ambassador journeys use direct payment by default
        "ambassador_payment_methods": data.get("payment_methods", {}),
        "ambassador_payment_instructions": data.get("payment_instructions"),
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

@api_router.get("/admin/ambassador-journeys/{journey_id}/details")
async def get_ambassador_journey_details(journey_id: str, request: Request):
    """Get full details of an ambassador journey application including ambassador history - Admin only"""
    await require_admin(request)
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    
    # Get ambassador details
    ambassador = None
    ambassador_history = {
        "contributions": [],
        "total_contributed": 0,
        "referrals": [],
        "valid_referrals_count": 0,
        "journeys_created": []
    }
    
    if journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "password_hash": 0}
        )
        
        if ambassador:
            # Get ambassador's contributions
            contributions = await db.contributions.find(
                {"user_id": journey["ambassador_user_id"], "status": {"$in": ["confirmed", "completed"]}},
                {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            
            ambassador_history["contributions"] = contributions
            ambassador_history["total_contributed"] = sum(c.get("amount", 0) for c in contributions)
            
            # Get ambassador's referrals
            referrals = await db.users.find(
                {"sponsor_id": journey["ambassador_user_id"]},
                {"_id": 0, "user_id": 1, "name": 1, "email": 1, "registered_at": 1}
            ).sort("registered_at", -1).to_list(50)
            
            # Check which referrals have contributed
            for ref in referrals:
                ref_contributions = await db.contributions.count_documents({
                    "user_id": ref["user_id"],
                    "status": {"$in": ["confirmed", "completed"]}
                })
                ref["has_contributed"] = ref_contributions > 0
            
            ambassador_history["referrals"] = referrals
            ambassador_history["valid_referrals_count"] = ambassador.get("valid_referrals_count", 0)
            
            # Get other journeys created by this ambassador
            other_journeys = await db.journeys.find(
                {"ambassador_user_id": journey["ambassador_user_id"], "journey_id": {"$ne": journey_id}},
                {"_id": 0, "journey_id": 1, "name": 1, "status": 1, "current_amount": 1, "goal_amount": 1, "created_at": 1}
            ).sort("created_at", -1).to_list(10)
            
            ambassador_history["journeys_created"] = other_journeys
    
    return {
        "journey": journey,
        "ambassador": ambassador,
        "ambassador_history": ambassador_history
    }

@api_router.put("/admin/ambassador-journeys/{journey_id}/status")
async def update_ambassador_journey_status(journey_id: str, request: Request):
    """Update ambassador journey status - Admin only
    
    Actions:
    - candidatura → aprovada: Approves the application
    - candidatura → ajustes_pedidos: Request adjustments from ambassador
    - ajustes_pedidos → candidatura: Ambassador resubmits (allow)
    - aprovada → ativa: Activates journey for fundraising, publishes in "Sonhos em materialização"
    - ativa → financiada: When fully funded (usually automatic)
    - financiada → realizada: Mark as completed
    - any → encerrada: Close/reject the journey
    """
    admin = await require_admin(request)
    data = await request.json()
    
    new_status = data.get("status")
    admin_notes = data.get("admin_notes")
    adjustment_request = data.get("adjustment_request")  # Message when requesting adjustments
    auto_activate = data.get("auto_activate", True)  # Auto-activate after approval
    
    if new_status not in JOURNEY_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Estados permitidos: {list(JOURNEY_STATUSES.keys())}")
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    # Get ambassador details for email
    ambassador = None
    if journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "email": 1, "name": 1}
        )
    
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Set timestamps and flags based on status
    if new_status == "aprovada":
        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
        update_data["approved_by"] = admin.user_id
        
        # If auto_activate is True, also activate immediately
        if auto_activate:
            update_data["status"] = "ativa"
            update_data["is_active"] = True
            update_data["activated_at"] = datetime.now(timezone.utc).isoformat()
            # Explicitly set visibility fields to default values (no automatic featuring or boost)
            update_data["is_featured"] = False
            update_data["visibility_boost"] = 0.0
            update_data["hide_from_listings"] = False
            # Initial visibility score for new journeys (newness bonus only)
            update_data["visibility_score"] = 10.0
            new_status = "ativa"  # Update for email and notification
            
    elif new_status == "ajustes_pedidos":
        update_data["adjustment_request"] = adjustment_request or admin_notes
        update_data["adjustment_requested_at"] = datetime.now(timezone.utc).isoformat()
        update_data["adjustment_requested_by"] = admin.user_id
        
    elif new_status == "ativa":
        update_data["is_active"] = True
        update_data["activated_at"] = datetime.now(timezone.utc).isoformat()
        # Explicitly set visibility fields to default values (no automatic featuring or boost)
        update_data["is_featured"] = False
        update_data["visibility_boost"] = 0.0
        update_data["hide_from_listings"] = False
        # Calculate initial visibility score based on journey attributes
        goal = journey.get("goal_amount", 1)
        current = journey.get("current_amount", 0)
        progress = (current / goal * 100) if goal > 0 else 0
        # Initial score: only based on newness (10% weight = 10 points max for new journeys)
        update_data["visibility_score"] = 10.0  # New journey starts with base score
        
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
    
    # Notify ambassador (in-app notification)
    status_messages = {
        "aprovada": "A tua candidatura de viagem foi aprovada! Vamos ativá-la para receber contribuições.",
        "ajustes_pedidos": f"O admin pediu ajustes à tua candidatura: {adjustment_request or admin_notes or 'Por favor revê os detalhes.'}",
        "ativa": "🎉 A tua viagem está agora ATIVA e visível na secção 'Sonhos em Materialização'! Partilha com a tua rede para começar a receber contribuições.",
        "financiada": "🎊 Parabéns! A tua viagem foi totalmente financiada! O teu sonho vai realizar-se!",
        "realizada": "A tua viagem foi marcada como realizada! Podes adicionar fotos e contar a tua história.",
        "encerrada": "A tua candidatura/viagem foi encerrada."
    }
    
    if journey.get("ambassador_user_id") and new_status in status_messages:
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
    
    # Send email to ambassador
    if ambassador and ambassador.get("email") and RESEND_API_KEY:
        email_subjects = {
            "aprovada": "🎉 A tua viagem foi aprovada - 4Luis",
            "ajustes_pedidos": "📝 Pedido de ajustes à tua candidatura - 4Luis",
            "ativa": "🚀 A tua viagem está ATIVA - 4Luis",
            "financiada": "🎊 A tua viagem foi FINANCIADA - 4Luis",
            "realizada": "✨ Viagem marcada como realizada - 4Luis",
            "encerrada": "Atualização sobre a tua viagem - 4Luis"
        }
        
        email_bodies = {
            "aprovada": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #FFBE98;">🎉 Parabéns, {ambassador.get('name', 'Embaixador')}!</h1>
                    <p>A tua candidatura para a viagem <strong>"{journey.get('name')}"</strong> foi aprovada!</p>
                    <p>A tua viagem está agora ativa e visível na secção <strong>"Sonhos em Materialização"</strong> da nossa homepage.</p>
                    <p>Começa já a partilhar o link da tua viagem com amigos e família para começares a receber contribuições!</p>
                    <a href="https://4luis.com/journeys/{journey_id}" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 16px;">Ver a minha viagem</a>
                    <p style="margin-top: 24px; color: #6B6661; font-size: 14px;">Com carinho,<br>Equipa 4Luis</p>
                </div>
            """,
            "ajustes_pedidos": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #F2C94C;">📝 Pedido de Ajustes</h1>
                    <p>Olá {ambassador.get('name', 'Embaixador')},</p>
                    <p>Analisámos a tua candidatura para a viagem <strong>"{journey.get('name')}"</strong> e precisamos de alguns ajustes antes de a aprovar.</p>
                    <div style="background: #FFF8E1; border-left: 4px solid #F2C94C; padding: 16px; margin: 16px 0;">
                        <strong>Feedback do Admin:</strong><br>
                        {adjustment_request or admin_notes or 'Por favor revê os detalhes da tua candidatura.'}
                    </div>
                    <p>Por favor acede ao teu painel e faz as alterações necessárias.</p>
                    <a href="https://4luis.com/dashboard" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 16px;">Ir para o Meu Painel</a>
                    <p style="margin-top: 24px; color: #6B6661; font-size: 14px;">Com carinho,<br>Equipa 4Luis</p>
                </div>
            """,
            "ativa": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #4CAF50;">🚀 A tua viagem está ATIVA!</h1>
                    <p>Olá {ambassador.get('name', 'Embaixador')},</p>
                    <p>A tua viagem <strong>"{journey.get('name')}"</strong> está agora ativa e a receber contribuições!</p>
                    <p>A viagem está visível na secção <strong>"Sonhos em Materialização"</strong> da nossa homepage.</p>
                    <p><strong>Próximos passos:</strong></p>
                    <ul>
                        <li>Partilha o link da tua viagem nas redes sociais</li>
                        <li>Envia para amigos e família</li>
                        <li>Mantém a tua comunidade atualizada sobre o progresso</li>
                    </ul>
                    <a href="https://4luis.com/journeys/{journey_id}" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 16px;">Ver a minha viagem</a>
                    <p style="margin-top: 24px; color: #6B6661; font-size: 14px;">Com carinho,<br>Equipa 4Luis</p>
                </div>
            """,
            "financiada": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #9C27B0;">🎊 O TEU SONHO VAI REALIZAR-SE!</h1>
                    <p>Olá {ambassador.get('name', 'Embaixador')},</p>
                    <p>Temos uma notícia incrível: A tua viagem <strong>"{journey.get('name')}"</strong> foi <strong>totalmente financiada</strong>!</p>
                    <p>Graças à generosidade da comunidade 4Luis, vais poder realizar este sonho.</p>
                    <p>Entraremos em contacto em breve para coordenar os próximos passos.</p>
                    <p>Obrigado por fazeres parte desta comunidade! 💜</p>
                    <p style="margin-top: 24px; color: #6B6661; font-size: 14px;">Com muito carinho,<br>Equipa 4Luis</p>
                </div>
            """
        }
        
        if new_status in email_subjects and new_status in email_bodies:
            try:
                resend.emails.send({
                    "from": SENDER_EMAIL,
                    "to": [ambassador["email"]],
                    "subject": email_subjects[new_status],
                    "html": email_bodies[new_status]
                })
            except Exception as e:
                logging.error(f"Failed to send email to ambassador: {e}")
    
    # Return response with activation info
    response_data = {
        "message": f"Estado atualizado para '{JOURNEY_STATUSES[new_status]['name']}'",
        "journey_id": journey_id,
        "new_status": new_status
    }
    
    if new_status == "ativa":
        response_data["is_now_live"] = True
        response_data["published_in"] = "Sonhos em Materialização"
        response_data["email_sent"] = bool(ambassador and ambassador.get("email") and RESEND_API_KEY)
    
    return response_data

# ==================== VISIBILITY & FEATURING SYSTEM ====================

async def calculate_journey_visibility_score(journey: dict) -> float:
    """
    Calculate visibility score for a journey based on multiple criteria.
    Score components (all normalized to 0-100):
    - Funding progress (30%): Higher progress = higher visibility
    - Recent activity (25%): More recent contributions = higher visibility
    - Number of contributions (20%): More contributions = higher visibility
    - Ambassador social impact (15%): More referrals = higher visibility
    - Recency bonus (10%): Newer journeys get a slight boost
    """
    journey_id = journey.get("journey_id")
    
    # 1. Funding Progress (30%)
    goal = journey.get("goal_amount", 1)
    current = journey.get("current_amount", 0)
    funding_percentage = min((current / goal) * 100, 100) if goal > 0 else 0
    funding_score = funding_percentage * 0.30
    
    # 2. Recent Activity (25%) - Contributions in last 7 days
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_contributions = await db.contributions.count_documents({
        "journey_id": journey_id,
        "status": {"$in": ["confirmed", "completed"]},
        "created_at": {"$gte": seven_days_ago}
    })
    activity_score = min(recent_contributions * 10, 100) * 0.25
    
    # 3. Total Contributions (20%)
    total_contributions = await db.contributions.count_documents({
        "journey_id": journey_id,
        "status": {"$in": ["confirmed", "completed"]}
    })
    contribution_score = min(total_contributions * 5, 100) * 0.20
    
    # 4. Ambassador Social Impact (15%)
    social_score = 0
    if journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "valid_referrals_count": 1}
        )
        if ambassador:
            referrals = ambassador.get("valid_referrals_count", 0)
            social_score = min(referrals * 10, 100) * 0.15
    
    # 5. Recency Bonus (10%) - Decays over 30 days
    created_at = journey.get("created_at")
    if created_at:
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        days_old = (datetime.now(timezone.utc) - created_at).days
        recency_factor = max(0, (30 - days_old) / 30)
        recency_score = recency_factor * 100 * 0.10
    else:
        recency_score = 0
    
    # Calculate total score
    base_score = funding_score + activity_score + contribution_score + social_score + recency_score
    
    # Apply admin boost (-100 to +100)
    admin_boost = journey.get("visibility_boost", 0)
    final_score = max(0, min(200, base_score + admin_boost))
    
    # Featured journeys get +100 bonus
    if journey.get("is_featured"):
        final_score += 100
    
    return round(final_score, 2)

@api_router.post("/admin/journeys/{journey_id}/update-visibility")
async def update_journey_visibility(journey_id: str, request: Request):
    """Update journey visibility settings - Admin only"""
    await require_admin(request)
    data = await request.json()
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    # Feature/Unfeature
    if "is_featured" in data:
        update_data["is_featured"] = data["is_featured"]
        if data["is_featured"]:
            update_data["featured_at"] = datetime.now(timezone.utc).isoformat()
        else:
            update_data["featured_at"] = None
    
    # Featured order
    if "featured_order" in data:
        update_data["featured_order"] = int(data["featured_order"])
    
    # Visibility boost (-100 to +100)
    if "visibility_boost" in data:
        boost = float(data["visibility_boost"])
        update_data["visibility_boost"] = max(-100, min(100, boost))
    
    # Hide from listings
    if "hide_from_listings" in data:
        update_data["hide_from_listings"] = data["hide_from_listings"]
    
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": update_data}
    )
    
    # Recalculate visibility score
    updated_journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    new_score = await calculate_journey_visibility_score(updated_journey)
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {"visibility_score": new_score}}
    )
    
    return {
        "message": "Visibilidade atualizada",
        "journey_id": journey_id,
        "is_featured": update_data.get("is_featured", journey.get("is_featured")),
        "visibility_boost": update_data.get("visibility_boost", journey.get("visibility_boost")),
        "new_visibility_score": new_score
    }

@api_router.post("/admin/recalculate-all-visibility")
async def recalculate_all_visibility_scores(request: Request):
    """Recalculate visibility scores for all active journeys - Admin only"""
    await require_admin(request)
    
    journeys = await db.journeys.find(
        {"status": {"$in": ["ativa", "financiada"]}},
        {"_id": 0}
    ).to_list(1000)
    
    updated = 0
    for journey in journeys:
        score = await calculate_journey_visibility_score(journey)
        await db.journeys.update_one(
            {"journey_id": journey["journey_id"]},
            {"$set": {"visibility_score": score}}
        )
        updated += 1
    
    return {
        "message": f"Visibilidade recalculada para {updated} viagens",
        "updated_count": updated
    }

@api_router.put("/admin/journeys/{journey_id}/show-goal")
async def toggle_journey_show_goal(journey_id: str, request: Request):
    """Toggle whether to show goal amount publicly - Admin only"""
    await require_admin(request)
    
    data = await request.json()
    show_goal = data.get("show_goal_amount")
    
    if show_goal is None:
        raise HTTPException(status_code=400, detail="show_goal_amount é obrigatório")
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {
            "show_goal_amount": bool(show_goal),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": f"Visibilidade do objetivo {'ativada' if show_goal else 'desativada'}",
        "journey_id": journey_id,
        "show_goal_amount": bool(show_goal)
    }

@api_router.get("/admin/journeys-visibility")
async def get_journeys_with_visibility(request: Request, status: Optional[str] = None):
    """Get all journeys with visibility data - Admin only"""
    await require_admin(request)
    
    query = {}
    if status:
        query["status"] = status
    
    journeys = await db.journeys.find(query, {"_id": 0}).sort("visibility_score", -1).to_list(100)
    
    # Recalculate scores on the fly for accuracy
    for journey in journeys:
        journey["calculated_score"] = await calculate_journey_visibility_score(journey)
    
    return {
        "count": len(journeys),
        "journeys": journeys
    }

@api_router.get("/journeys/featured")
async def get_featured_journeys():
    """Get featured journeys for public display"""
    journeys = await db.journeys.find(
        {
            "is_featured": True,
            "status": "ativa",
            "hide_from_listings": {"$ne": True}
        },
        {"_id": 0, "goal_amount": 0, "admin_notes": 0}
    ).sort("featured_order", 1).to_list(10)
    
    # Add progress percentage
    for journey in journeys:
        full = await db.journeys.find_one({"journey_id": journey["journey_id"]}, {"_id": 0, "goal_amount": 1})
        if full:
            goal = full.get("goal_amount", 1)
            current = journey.get("current_amount", 0)
            journey["progress_percentage"] = round((current / goal) * 100, 1) if goal > 0 else 0
    
    return {
        "count": len(journeys),
        "journeys": journeys
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


# ==================== DRAFTS / AUTOSAVE SYSTEM ====================

@api_router.put("/admin/drafts/{draft_type}/{reference_id}")
async def save_draft(draft_type: str, reference_id: str, request: Request):
    """Save or update a draft (autosave to server)"""
    user = await require_admin(request)
    body = await request.json()
    data = body.get("data", {})
    
    now = datetime.now(timezone.utc).isoformat()
    await db.drafts.update_one(
        {"user_id": user.user_id, "draft_type": draft_type, "reference_id": reference_id},
        {"$set": {
            "user_id": user.user_id,
            "draft_type": draft_type,
            "reference_id": reference_id,
            "data": data,
            "updated_at": now
        }, "$setOnInsert": {"created_at": now}},
        upsert=True
    )
    return {"status": "saved", "updated_at": now}

@api_router.get("/admin/drafts/{draft_type}/{reference_id}")
async def get_draft(draft_type: str, reference_id: str, request: Request):
    """Get a specific draft"""
    user = await require_admin(request)
    draft = await db.drafts.find_one(
        {"user_id": user.user_id, "draft_type": draft_type, "reference_id": reference_id},
        {"_id": 0}
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Rascunho nao encontrado")
    return draft

@api_router.delete("/admin/drafts/{draft_type}/{reference_id}")
async def delete_draft(draft_type: str, reference_id: str, request: Request):
    """Delete a draft after successful save"""
    user = await require_admin(request)
    await db.drafts.delete_one(
        {"user_id": user.user_id, "draft_type": draft_type, "reference_id": reference_id}
    )
    return {"status": "deleted"}

@api_router.get("/admin/drafts")
async def list_drafts(request: Request):
    """List all drafts for current admin"""
    user = await require_admin(request)
    drafts = await db.drafts.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(50)
    return {"drafts": drafts}


# ==================== OBJECT STORAGE ====================
import requests as sync_requests

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "4luis"
_storage_key = None

def init_storage():
    global _storage_key
    if _storage_key:
        return _storage_key
    resp = sync_requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    _storage_key = resp.json()["storage_key"]
    return _storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = sync_requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    key = init_storage()
    resp = sync_requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# ==================== SUPPORT TICKET SYSTEM ====================

PRIORITY_RULES = {
    "Pagamento": "Alta",
    "Problema tecnico": "Media",
    "Conta e acesso": "Media",
    "Reclamacao": "Alta",
    "Sugestao": "Baixa",
    "Convites e referrals": "Media",
    "Viagens e sonhos": "Media",
    "Outro": "Media"
}

async def generate_ticket_id():
    year = datetime.now(timezone.utc).year
    count = await db.support_tickets.count_documents({})
    return f"SUP-{year}-{str(count + 1).zfill(5)}"

# ---- Support Email Templates ----

async def get_support_cta_block():
    """Get CTA block for support emails linking to main journey"""
    main_journey = await db.journeys.find_one(
        {"is_active": True, "is_main_trip": True},
        {"journey_id": 1, "name": 1, "_id": 0}
    )
    if not main_journey:
        return ""
    journey_url = f"{FRONTEND_URL}/journey/{main_journey['journey_id']}"
    journey_name = main_journey.get('name', 'esta viagem')
    return f"""
        <div style="background: linear-gradient(135deg, #FFF8F3 0%, #FFF0E6 100%); border-radius: 16px; padding: 28px; margin: 32px 0 0; text-align: center; border: 1px solid #FFDFCA;">
            <p style="color: #6B6661; font-size: 13px; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 1px;">Antes de partires...</p>
            <p style="color: #2D2A26; font-size: 16px; line-height: 1.6; margin: 0 0 16px;">
                O sonho da viagem pela <strong>{journey_name}</strong> ja comecou.<br>
                Nao fiques fora do sonho,<br>
                <em>sonha connosco.</em>
            </p>
            <a href="{journey_url}" style="display: inline-block; padding: 12px 28px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 14px;">Contribuir para este sonho</a>
        </div>
    """

def get_support_email_html(content: str, title: str = "Suporte 4Luis") -> str:
    return get_email_base_template(content, title)

def get_ticket_confirmation_email(name: str, ticket_id: str, ticket_type: str, subject: str) -> str:
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">Recebemos o teu pedido</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Ola, {name}<br><br>
            Recebemos o teu pedido de suporte com sucesso.
        </p>
        <div style="background: #F5F0EB; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #6B6661;">
                <strong>Referencia do pedido:</strong> {ticket_id}<br>
                <strong>Tipo:</strong> {ticket_type}<br>
                <strong>Assunto:</strong> {subject}
            </p>
        </div>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            A nossa equipa ira analisar o teu pedido e atualizar-te assim que houver novidades.<br><br>
            Podes acompanhar o estado do pedido na tua area de Ajuda e Suporte.
        </p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{FRONTEND_URL}/support/{ticket_id}" style="display: inline-block; padding: 12px 32px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px;">Ver pedido</a>
        </div>
        <p style="color: #6B6661; font-size: 14px; font-style: italic; text-align: center; margin-top: 24px;">
            4Luis<br>Clube de Sonhadores<br>Sonha connosco
        </p>
    """
    return get_support_email_html(content)

async def get_admin_reply_email(name: str, ticket_id: str, status: str, reply_excerpt: str) -> str:
    cta = await get_support_cta_block()
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">Nova resposta ao teu pedido</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Ola, {name}<br><br>
            A equipa 4Luis respondeu ao teu pedido de suporte.
        </p>
        <div style="background: #F5F0EB; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #6B6661;">
                <strong>Referencia do pedido:</strong> {ticket_id}<br>
                <strong>Estado atual:</strong> {status}
            </p>
        </div>
        <div style="background: #FAFAF9; border-left: 3px solid #FFBE98; padding: 16px; margin: 16px 0; border-radius: 0 8px 8px 0;">
            <p style="margin: 0; font-size: 14px; color: #2D2A26; font-style: italic;">
                {reply_excerpt}
            </p>
        </div>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Podes continuar a conversa e acompanhar o estado do pedido na tua area de Ajuda e Suporte.
        </p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{FRONTEND_URL}/support/{ticket_id}" style="display: inline-block; padding: 12px 32px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px;">Ver pedido</a>
        </div>
        <p style="color: #6B6661; font-size: 14px; font-style: italic; text-align: center; margin-top: 24px;">
            4Luis<br>Clube de Sonhadores<br>Sonha connosco
        </p>
        {cta}
    """
    return get_support_email_html(content)

async def get_status_change_email(name: str, ticket_id: str, status: str) -> str:
    cta = await get_support_cta_block()
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">Estado do pedido atualizado</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Ola, {name}<br><br>
            O estado do teu pedido de suporte foi atualizado.
        </p>
        <div style="background: #F5F0EB; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #6B6661;">
                <strong>Referencia do pedido:</strong> {ticket_id}<br>
                <strong>Novo estado:</strong> {status}
            </p>
        </div>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Podes consultar todos os detalhes na tua area de Ajuda e Suporte.
        </p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{FRONTEND_URL}/support/{ticket_id}" style="display: inline-block; padding: 12px 32px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px;">Ver pedido</a>
        </div>
        <p style="color: #6B6661; font-size: 14px; font-style: italic; text-align: center; margin-top: 24px;">
            4Luis<br>Clube de Sonhadores<br>Sonha connosco
        </p>
        {cta}
    """
    return get_support_email_html(content)

async def get_ticket_resolved_email(name: str, ticket_id: str) -> str:
    cta = await get_support_cta_block()
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">Pedido resolvido</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Ola, {name}<br><br>
            O teu pedido de suporte foi marcado como resolvido.
        </p>
        <div style="background: #F5F0EB; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #6B6661;">
                <strong>Referencia do pedido:</strong> {ticket_id}
            </p>
        </div>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Se precisares, podes responder ao pedido caso a questao persista.<br>
            Se estiver tudo bem, o pedido podera ser fechado.
        </p>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{FRONTEND_URL}/support/{ticket_id}" style="display: inline-block; padding: 12px 32px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px;">Ver pedido</a>
        </div>
        <p style="color: #6B6661; font-size: 14px; font-style: italic; text-align: center; margin-top: 24px;">
            4Luis<br>Clube de Sonhadores<br>Sonha connosco
        </p>
        {cta}
    """
    return get_support_email_html(content)

async def get_ticket_closed_email(name: str, ticket_id: str) -> str:
    cta = await get_support_cta_block()
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">Pedido fechado</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Ola, {name}<br><br>
            O teu pedido de suporte foi fechado.
        </p>
        <div style="background: #F5F0EB; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #6B6661;">
                <strong>Referencia do pedido:</strong> {ticket_id}
            </p>
        </div>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Obrigado por entrares em contacto connosco.
        </p>
        <p style="color: #6B6661; font-size: 14px; font-style: italic; text-align: center; margin-top: 24px;">
            4Luis<br>Clube de Sonhadores<br>Sonha connosco
        </p>
        {cta}
    """
    return get_support_email_html(content)

def get_admin_notification_email(name: str, ticket_id: str, ticket_type: str, status: str) -> str:
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">Nova resposta do utilizador</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            O utilizador {name} adicionou uma nova resposta ao pedido {ticket_id}.
        </p>
        <div style="background: #F5F0EB; border-radius: 12px; padding: 20px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px; color: #6B6661;">
                <strong>Tipo:</strong> {ticket_type}<br>
                <strong>Estado atual:</strong> {status}
            </p>
        </div>
        <div style="text-align: center; margin: 24px 0;">
            <a href="{FRONTEND_URL}/admin" style="display: inline-block; padding: 12px 32px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px;">Abrir pedido no admin</a>
        </div>
    """
    return get_support_email_html(content)

# ---- Support File Upload ----

ALLOWED_SUPPORT_TYPES = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
MAX_SUPPORT_FILE_SIZE = 5 * 1024 * 1024  # 5MB

from fastapi import UploadFile, File, Form, Query, Header

@api_router.post("/support/upload")
async def upload_support_file(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    
    if file.content_type not in ALLOWED_SUPPORT_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de ficheiro nao suportado. Use png, jpg, jpeg, webp ou pdf.")
    
    data = await file.read()
    if len(data) > MAX_SUPPORT_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Ficheiro excede 5MB")
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    path = f"{APP_NAME}/support/{user.user_id}/{uuid.uuid4()}.{ext}"
    
    result = await asyncio.to_thread(put_object, path, data, file.content_type or "application/octet-stream")
    
    return {
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size": result.get("size", len(data))
    }

@api_router.get("/support/files/{path:path}")
async def download_support_file(path: str, auth: str = Query(None), authorization: str = Header(None)):
    token_str = None
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization[7:]
    elif auth:
        token_str = auth
    if not token_str:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    try:
        payload = jwt.decode(token_str, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalido")
    
    data, content_type = await asyncio.to_thread(get_object, path)
    return Response(content=data, media_type=content_type)

# ---- Support Ticket Endpoints (User) ----

@api_router.post("/support/tickets")
async def create_support_ticket(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    
    body = await request.json()
    ticket_type = body.get("ticket_type", "")
    subject = body.get("subject", "")
    description = body.get("description", "")
    attachment = body.get("attachment")  # {storage_path, original_filename, content_type, size}
    
    if ticket_type not in TICKET_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de pedido invalido")
    if not subject or not description:
        raise HTTPException(status_code=400, detail="Assunto e descricao sao obrigatorios")
    
    ticket_id = await generate_ticket_id()
    now = datetime.now(timezone.utc).isoformat()
    priority = PRIORITY_RULES.get(ticket_type, "Media")
    
    ticket = {
        "ticket_id": ticket_id,
        "user_id": user.user_id,
        "user_name": user.name,
        "user_email": user.email,
        "ticket_type": ticket_type,
        "subject": subject,
        "description": description,
        "status": "Aberto",
        "priority": priority,
        "attachment": attachment,
        "messages": [],
        "internal_notes": [],
        "created_at": now,
        "updated_at": now
    }
    
    await db.support_tickets.insert_one(ticket)
    
    # Send confirmation email
    try:
        html = get_ticket_confirmation_email(user.name, ticket_id, ticket_type, subject)
        await send_email_resend(user.email, f"Recebemos o teu pedido de suporte — {ticket_id}", html)
    except Exception as e:
        logger.error(f"Failed to send ticket confirmation email: {e}")
    
    # Notify admin
    try:
        admin_html = get_admin_notification_email(user.name, ticket_id, ticket_type, "Aberto")
        await send_email_resend(ADMIN_EMAIL, f"Novo pedido de suporte — {ticket_id}", admin_html)
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
    
    del ticket["_id"]
    return ticket

@api_router.get("/support/tickets")
async def list_user_tickets(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    
    tickets = await db.support_tickets.find(
        {"user_id": user.user_id},
        {"_id": 0, "internal_notes": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"tickets": tickets}

@api_router.get("/support/tickets/{ticket_id}")
async def get_user_ticket(ticket_id: str, request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    
    ticket = await db.support_tickets.find_one(
        {"ticket_id": ticket_id, "user_id": user.user_id},
        {"_id": 0, "internal_notes": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    return ticket

@api_router.post("/support/tickets/{ticket_id}/reply")
async def user_reply_ticket(ticket_id: str, request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    
    body = await request.json()
    message = body.get("message", "").strip()
    attachment = body.get("attachment")
    if not message:
        raise HTTPException(status_code=400, detail="Mensagem e obrigatoria")
    
    ticket = await db.support_tickets.find_one({"ticket_id": ticket_id, "user_id": user.user_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    
    now = datetime.now(timezone.utc).isoformat()
    new_message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "sender": "user",
        "sender_name": user.name,
        "message": message,
        "attachment": attachment,
        "created_at": now
    }
    
    # If resolved ticket gets a reply, reopen
    new_status = ticket["status"]
    if ticket["status"] in ("Resolvido", "Aberto", "A aguardar resposta"):
        new_status = "Em analise"
    
    await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$push": {"messages": new_message}, "$set": {"status": new_status, "updated_at": now}}
    )
    
    # Notify admin
    try:
        admin_html = get_admin_notification_email(user.name, ticket_id, ticket["ticket_type"], new_status)
        await send_email_resend(ADMIN_EMAIL, f"Nova resposta do utilizador — {ticket_id}", admin_html)
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
    
    return {"status": "ok", "message": new_message, "new_status": new_status}

# ---- Support Ticket Endpoints (Admin) ----

@api_router.get("/admin/support/tickets")
async def admin_list_tickets(request: Request, status: str = None, ticket_type: str = None, priority: str = None, search: str = None):
    await require_admin(request)
    
    query = {}
    if status:
        query["status"] = status
    if ticket_type:
        query["ticket_type"] = ticket_type
    if priority:
        query["priority"] = priority
    if search:
        query["$or"] = [
            {"ticket_id": {"$regex": search, "$options": "i"}},
            {"user_email": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}}
        ]
    
    tickets = await db.support_tickets.find(query, {"_id": 0}).sort("updated_at", -1).to_list(200)
    
    # Stats
    total = await db.support_tickets.count_documents({})
    open_count = await db.support_tickets.count_documents({"status": {"$in": ["Aberto", "Em analise", "A aguardar resposta"]}})
    
    # Detailed stats for admin dashboard
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_count = await db.support_tickets.count_documents({"created_at": {"$gte": today_start}})
    in_analysis = await db.support_tickets.count_documents({"status": "Em analise"})
    awaiting_reply = await db.support_tickets.count_documents({"status": "A aguardar resposta"})
    urgent_count = await db.support_tickets.count_documents({"priority": "Urgente", "status": {"$nin": ["Resolvido", "Fechado"]}})
    
    # Stats by type (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    type_pipeline = [
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$ticket_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    type_stats = await db.support_tickets.aggregate(type_pipeline).to_list(20)
    types_breakdown = {t["_id"]: t["count"] for t in type_stats}
    
    return {
        "tickets": tickets, "total": total, "open_count": open_count,
        "today_count": today_count, "in_analysis": in_analysis,
        "awaiting_reply": awaiting_reply, "urgent_count": urgent_count,
        "types_breakdown": types_breakdown
    }

@api_router.get("/admin/support/tickets/{ticket_id}")
async def admin_get_ticket(ticket_id: str, request: Request):
    await require_admin(request)
    ticket = await db.support_tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    return ticket

@api_router.post("/admin/support/tickets/{ticket_id}/reply")
async def admin_reply_ticket(ticket_id: str, request: Request):
    await require_admin(request)
    body = await request.json()
    message = body.get("message", "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Mensagem e obrigatoria")
    
    ticket = await db.support_tickets.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    
    now = datetime.now(timezone.utc).isoformat()
    new_message = {
        "message_id": f"msg_{uuid.uuid4().hex[:8]}",
        "sender": "admin",
        "sender_name": "Equipa 4Luis",
        "message": message,
        "attachment": None,
        "created_at": now
    }
    
    await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$push": {"messages": new_message}, "$set": {"updated_at": now}}
    )
    
    # Send email to user
    try:
        excerpt = message[:200] + ("..." if len(message) > 200 else "")
        html = await get_admin_reply_email(ticket["user_name"], ticket_id, ticket["status"], excerpt)
        await send_email_resend(ticket["user_email"], f"Nova resposta ao teu pedido — {ticket_id}", html)
    except Exception as e:
        logger.error(f"Failed to send reply email: {e}")
    
    # In-app notification
    await create_notification(
        ticket["user_id"],
        "support",
        f"A equipa 4Luis respondeu ao teu pedido de suporte.",
        {"ticket_id": ticket_id}
    )
    
    return {"status": "ok", "message": new_message}

@api_router.put("/admin/support/tickets/{ticket_id}/status")
async def admin_update_ticket_status(ticket_id: str, request: Request):
    await require_admin(request)
    body = await request.json()
    new_status = body.get("status", "")
    
    if new_status not in TICKET_STATUSES:
        raise HTTPException(status_code=400, detail="Estado invalido")
    
    ticket = await db.support_tickets.find_one({"ticket_id": ticket_id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    
    old_status = ticket["status"]
    now = datetime.now(timezone.utc).isoformat()
    
    await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"status": new_status, "updated_at": now}}
    )
    
    # Send appropriate email
    try:
        if new_status == "Resolvido":
            html = await get_ticket_resolved_email(ticket["user_name"], ticket_id)
            await send_email_resend(ticket["user_email"], f"O teu pedido foi resolvido — {ticket_id}", html)
        elif new_status == "Fechado":
            html = await get_ticket_closed_email(ticket["user_name"], ticket_id)
            await send_email_resend(ticket["user_email"], f"O teu pedido foi fechado — {ticket_id}", html)
        elif new_status != old_status:
            html = await get_status_change_email(ticket["user_name"], ticket_id, new_status)
            await send_email_resend(ticket["user_email"], f"O estado do teu pedido foi atualizado — {ticket_id}", html)
    except Exception as e:
        logger.error(f"Failed to send status change email: {e}")
    
    return {"status": "ok", "new_status": new_status}

@api_router.put("/admin/support/tickets/{ticket_id}/priority")
async def admin_update_ticket_priority(ticket_id: str, request: Request):
    await require_admin(request)
    body = await request.json()
    new_priority = body.get("priority", "")
    
    if new_priority not in TICKET_PRIORITIES:
        raise HTTPException(status_code=400, detail="Prioridade invalida")
    
    await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"priority": new_priority, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok", "new_priority": new_priority}

@api_router.post("/admin/support/tickets/{ticket_id}/note")
async def admin_add_internal_note(ticket_id: str, request: Request):
    await require_admin(request)
    body = await request.json()
    note = body.get("note", "").strip()
    if not note:
        raise HTTPException(status_code=400, detail="Nota e obrigatoria")
    
    now = datetime.now(timezone.utc).isoformat()
    new_note = {
        "note_id": f"note_{uuid.uuid4().hex[:8]}",
        "note": note,
        "created_at": now
    }
    
    await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$push": {"internal_notes": new_note}, "$set": {"updated_at": now}}
    )
    return {"status": "ok", "note": new_note}

# ==================== TESTIMONIAL SYSTEM ====================

def get_testimonial_auth_email(name: str, testimonial_text: str, auth_token: str) -> str:
    authorize_url = f"{FRONTEND_URL}/testimonial/authorize/{auth_token}"
    reject_url = f"{FRONTEND_URL}/testimonial/reject/{auth_token}"
    content = f"""
        <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px;">A tua experiencia pode inspirar outros</h2>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Ola, {name}<br><br>
            Gostariamos de partilhar a tua experiencia para ajudar outros utilizadores a confiar na plataforma.
        </p>
        <div style="background: #FFF8F3; border-left: 3px solid #FFBE98; padding: 20px; margin: 24px 0; border-radius: 0 12px 12px 0;">
            <p style="margin: 0; font-size: 15px; color: #2D2A26; font-style: italic; line-height: 1.6;">
                &ldquo;{testimonial_text}&rdquo;
            </p>
            <p style="margin: 8px 0 0; font-size: 13px; color: #6B6661;">— {name}</p>
        </div>
        <p style="color: #6B6661; font-size: 15px; line-height: 1.6;">
            Autorizas a publicacao deste testemunho na plataforma 4Luis?
        </p>
        <div style="text-align: center; margin: 28px 0;">
            <a href="{authorize_url}" style="display: inline-block; padding: 12px 32px; background: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px; margin-right: 12px;">Autorizar</a>
            <a href="{reject_url}" style="display: inline-block; padding: 12px 32px; background: #F5F0EB; color: #6B6661; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 15px;">Nao autorizar</a>
        </div>
        <p style="color: #6B6661; font-size: 14px; font-style: italic; text-align: center; margin-top: 24px;">
            4Luis<br>Clube de Sonhadores<br>Sonha connosco
        </p>
    """
    return get_support_email_html(content, "Testemunho 4Luis")

@api_router.post("/admin/support/tickets/{ticket_id}/testimonial")
async def create_testimonial_from_ticket(ticket_id: str, request: Request):
    """Mark ticket as potential testimonial and create draft"""
    await require_admin(request)
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Texto do testemunho e obrigatorio")
    
    ticket = await db.support_tickets.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    
    auth_token = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    
    user = await db.users.find_one({"user_id": ticket["user_id"]}, {"_id": 0})
    trust_level = user.get("trust_level", "Sonhador") if user else "Sonhador"
    
    testimonial = {
        "testimonial_id": f"test_{uuid.uuid4().hex[:8]}",
        "ticket_id": ticket_id,
        "user_id": ticket["user_id"],
        "user_name": ticket["user_name"],
        "user_email": ticket["user_email"],
        "text": text,
        "badge": trust_level,
        "status": "draft",  # draft -> pending_auth -> authorized -> published | rejected
        "auth_token": auth_token,
        "created_at": now,
        "updated_at": now
    }
    
    await db.testimonials.insert_one(testimonial)
    
    # Mark ticket
    await db.support_tickets.update_one(
        {"ticket_id": ticket_id},
        {"$set": {"has_testimonial": True, "updated_at": now}}
    )
    
    del testimonial["_id"]
    return testimonial

@api_router.put("/admin/testimonials/{testimonial_id}")
async def update_testimonial(testimonial_id: str, request: Request):
    """Update testimonial draft text"""
    await require_admin(request)
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Texto e obrigatorio")
    
    await db.testimonials.update_one(
        {"testimonial_id": testimonial_id},
        {"$set": {"text": text, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok"}

@api_router.post("/admin/testimonials/{testimonial_id}/request-auth")
async def request_testimonial_auth(testimonial_id: str, request: Request):
    """Send authorization email to user"""
    await require_admin(request)
    testimonial = await db.testimonials.find_one({"testimonial_id": testimonial_id}, {"_id": 0})
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testemunho nao encontrado")
    
    # Send email
    html = get_testimonial_auth_email(testimonial["user_name"], testimonial["text"], testimonial["auth_token"])
    await send_email_resend(
        testimonial["user_email"],
        "A tua experiencia pode inspirar outros — 4Luis",
        html
    )
    
    await db.testimonials.update_one(
        {"testimonial_id": testimonial_id},
        {"$set": {"status": "pending_auth", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok"}

@api_router.get("/testimonials/authorize/{auth_token}")
async def authorize_testimonial(auth_token: str):
    """Public endpoint - user authorizes testimonial via email link"""
    testimonial = await db.testimonials.find_one({"auth_token": auth_token})
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testemunho nao encontrado")
    
    await db.testimonials.update_one(
        {"auth_token": auth_token},
        {"$set": {"status": "authorized", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return RedirectResponse(url=f"{FRONTEND_URL}/testimonial/result?action=authorized")

@api_router.get("/testimonials/reject/{auth_token}")
async def reject_testimonial(auth_token: str):
    """Public endpoint - user rejects testimonial via email link"""
    testimonial = await db.testimonials.find_one({"auth_token": auth_token})
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testemunho nao encontrado")
    
    await db.testimonials.update_one(
        {"auth_token": auth_token},
        {"$set": {"status": "rejected", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return RedirectResponse(url=f"{FRONTEND_URL}/testimonial/result?action=rejected")

@api_router.post("/admin/testimonials/{testimonial_id}/publish")
async def publish_testimonial(testimonial_id: str, request: Request):
    """Publish an authorized testimonial"""
    await require_admin(request)
    testimonial = await db.testimonials.find_one({"testimonial_id": testimonial_id}, {"_id": 0})
    if not testimonial:
        raise HTTPException(status_code=404, detail="Testemunho nao encontrado")
    if testimonial["status"] != "authorized":
        raise HTTPException(status_code=400, detail="Testemunho nao autorizado")
    
    await db.testimonials.update_one(
        {"testimonial_id": testimonial_id},
        {"$set": {"status": "published", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"status": "ok"}

@api_router.delete("/admin/testimonials/{testimonial_id}")
async def delete_testimonial(testimonial_id: str, request: Request):
    await require_admin(request)
    await db.testimonials.delete_one({"testimonial_id": testimonial_id})
    return {"status": "ok"}

@api_router.get("/admin/testimonials")
async def admin_list_testimonials(request: Request):
    """List all testimonials for admin"""
    await require_admin(request)
    testimonials = await db.testimonials.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"testimonials": testimonials}

@api_router.get("/testimonials/published")
async def get_published_testimonials():
    """Public endpoint - get published testimonials for homepage/journey"""
    testimonials = await db.testimonials.find(
        {"status": "published"},
        {"_id": 0, "auth_token": 0, "user_email": 0, "user_id": 0}
    ).sort("created_at", -1).to_list(20)
    return {"testimonials": testimonials}


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
    # Find the main journey (is_main_trip=True or first active one) — must be active
    journey = await db.journeys.find_one(
        {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]},
        {"_id": 0, "admin_notes": 0}
    )
    
    if not journey:
        return {"journey": None, "progress": None, "contributions": [], "updates": []}
    
    journey_id = journey["journey_id"]
    
    # Get progress info
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = min((current_amount / goal_amount) * 100, 100) if goal_amount > 0 else 0
    show_goal = journey.get("show_goal_amount", False)
    
    progress = {
        "current_amount": current_amount,
        "percentage": round(percentage, 1),
        "is_funded": percentage >= 100,
        "show_goal_amount": show_goal
    }
    
    # Only include goal_amount if show_goal_amount is True
    if show_goal:
        progress["goal_amount"] = goal_amount
    
    # Remove goal_amount from journey if not showing
    if not show_goal:
        journey.pop("goal_amount", None)
    
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
    
    # Count unique contributors across the platform + seed offset
    platform_contributor_count = len(await db.contributions.distinct("contributor_email", {"status": {"$in": ["confirmed", "completed"]}}))
    contributor_display_count = platform_contributor_count + 57
    
    # Count unique contributors for this specific journey
    journey_contributor_count = len(await db.contributions.distinct("contributor_email", {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}}))
    
    return {
        "journey": journey,
        "progress": progress,
        "contributions": public_contributions,
        "updates": updates,
        "contributor_count": contributor_display_count,
        "journey_contributor_count": journey_contributor_count
    }

@api_router.get("/homepage/ambassador-journeys")
async def get_active_ambassador_journeys():
    """Get active ambassador journeys organized by region for 'Sonhos em Materialização' section"""
    # Query excludes hidden journeys - keep goal_amount and show_goal_amount for processing
    journeys = await db.journeys.find(
        {
            "is_ambassador_journey": True,
            "status": "ativa",
            "is_active": True,
            "hide_from_listings": {"$ne": True}
        },
        {"_id": 0, "admin_notes": 0, "application_message": 0}
    ).sort("visibility_score", -1).to_list(100)  # Sort by visibility score
    
    # Separate featured journeys
    featured = []
    regular = []
    
    for j in journeys:
        # Calculate progress percentage
        goal = j.get("goal_amount", 1)
        current = j.get("current_amount", 0)
        j["progress_percentage"] = round((current / goal) * 100, 1) if goal > 0 else 0
        
        # Handle show_goal_amount visibility
        show_goal = j.get("show_goal_amount", False)
        j["show_goal_amount"] = show_goal
        if not show_goal:
            j.pop("goal_amount", None)
        
        if j.get("is_featured"):
            featured.append(j)
        else:
            regular.append(j)
    
    # Sort featured by featured_order
    featured.sort(key=lambda x: x.get("featured_order", 0))
    
    # Organize regular journeys by region
    regions = {
        "europa": {"name": "Europa", "journeys": []},
        "asia": {"name": "Ásia", "journeys": []},
        "africa": {"name": "África", "journeys": []},
        "americas": {"name": "Américas", "journeys": []},
        "oceania": {"name": "Oceânia", "journeys": []},
        "outro": {"name": "Outros", "journeys": []}
    }
    
    for j in regular:
        region = j.get("region", "outro") or "outro"
        region = region.lower()
        if region not in regions:
            region = "outro"
        regions[region]["journeys"].append(j)
    
    # Filter out empty regions
    regions_filtered = {k: v for k, v in regions.items() if v["journeys"]}
    
    return {
        "total_count": len(journeys),
        "featured": featured,
        "regions": regions_filtered
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
            "image_url": "https://images.pexels.com/photos/4080520/pexels-photo-4080520.jpeg?auto=compress&cs=tinysrgb&w=800",
            "story": "Uma peregrinação de autodescoberta pelos caminhos ancestrais da Península Ibérica.",
            "is_curated": True
        },
        {
            "id": "curated_2",
            "name": "Montanhas do Nepal",
            "country": "Nepal",
            "region": "asia",
            "image_url": "https://images.unsplash.com/photo-1591602333477-618f471b5c01?w=800",
            "story": "Onde o céu encontra a terra, uma jornada de elevação espiritual nos Himalaias.",
            "is_curated": True
        },
        {
            "id": "curated_3",
            "name": "Costa Amalfitana",
            "country": "Itália",
            "region": "europa",
            "image_url": "https://images.unsplash.com/photo-1529914266944-527632c9ea58?w=800",
            "story": "Cores vibrantes e paisagens deslumbrantes no coração do Mediterrâneo.",
            "is_curated": True
        },
        {
            "id": "curated_4",
            "name": "Deserto do Sahara",
            "country": "Marrocos",
            "region": "africa",
            "image_url": "https://images.unsplash.com/photo-1769537145747-ff380b863f49?w=800",
            "story": "Noites estreladas e dunas infinitas, uma experiência de silêncio profundo.",
            "is_curated": True
        }
    ]
    
    return {
        "use_curated": True,
        "curated_dreams": curated_dreams,
        "message": "Estes são sonhos inspiracionais. Sê o primeiro a realizar o teu!"
    }


# ==================== IN-APP NOTIFICATIONS ====================

@api_router.get("/notifications")
async def get_notifications(request: Request):
    user = await require_auth(request)
    notifications = await db.notifications.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    unread_count = await db.notifications.count_documents({"user_id": user.user_id, "read": False})
    return {"notifications": notifications, "unread_count": unread_count}

@api_router.put("/notifications/read-all")
async def mark_all_notifications_read(request: Request):
    user = await require_auth(request)
    await db.notifications.update_many(
        {"user_id": user.user_id, "read": False},
        {"$set": {"read": True}}
    )
    return {"status": "ok"}

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, request: Request):
    user = await require_auth(request)
    await db.notifications.update_one(
        {"notification_id": notification_id, "user_id": user.user_id},
        {"$set": {"read": True}}
    )
    return {"status": "ok"}


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

# CORS middleware MUST be added BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Platform stats endpoint
@api_router.get("/platform/stats")
async def get_platform_stats():
    total_users = await db.users.count_documents({})
    total_contributions = await db.contributions.count_documents({})
    unique_contributors = len(await db.contributions.distinct("contributor_email"))
    return {
        "total_dreamers": max(total_users, unique_contributors),
        "total_contributions": total_contributions
    }

# Invite page endpoint - get inviter info by alias
@api_router.get("/invite/{alias:path}")
async def get_invite_page(alias: str):
    # Normalize: convert hyphens back to spaces for lookup
    normalized = alias.replace("-", " ")
    
    # Find user by anonymous_alias (try both original and normalized)
    user = await db.users.find_one(
        {"anonymous_alias": {"$in": [alias, normalized]}},
        {"_id": 0, "name": 1, "anonymous_alias": 1, "user_id": 1}
    )
    if not user:
        # Try by name
        user = await db.users.find_one(
            {"name": {"$in": [alias, normalized]}},
            {"_id": 0, "name": 1, "anonymous_alias": 1, "user_id": 1}
        )
    if not user:
        raise HTTPException(status_code=404, detail="Convite não encontrado")
    
    # Get main journey
    main_journey = await db.journeys.find_one(
        {"is_main_trip": True},
        {"_id": 0}
    )
    
    # Get sponsor link for this user + main journey
    sponsor_link = None
    if main_journey:
        sponsor_link = await db.sponsor_links.find_one(
            {"user_id": user["user_id"], "journey_id": main_journey["journey_id"]},
            {"_id": 0, "link_id": 1}
        )
    
    display_name = user.get("name") or user.get("anonymous_alias") or "Alguém"
    
    # Check if inviter has contributed to this journey
    inviter_has_contributed = False
    if main_journey:
        contrib = await db.contributions.find_one(
            {"user_id": user["user_id"], "journey_id": main_journey["journey_id"], "status": "confirmed"},
            {"_id": 0, "amount": 1}
        )
        inviter_has_contributed = contrib is not None
    
    return {
        "inviter_name": display_name,
        "inviter_has_contributed": inviter_has_contributed,
        "journey": main_journey,
        "sponsor_link_id": sponsor_link.get("link_id") if sponsor_link else None
    }




# ==================== AI TRAVEL PLANNER ====================

# Rate limiting: track requests per user
ai_travel_plan_cache = {}


@api_router.post("/ai/travel-plan/reset-limit")
async def reset_travel_plan_limit():
    """Reset rate limit cache (dev only)"""
    ai_travel_plan_cache.clear()
    return {"status": "cleared"}


@api_router.post("/ai/travel-plan")
async def generate_travel_plan(request: Request):
    """Generate a travel plan using hybrid architecture: templates + selective AI."""
    from destination_templates import match_destination, build_full_template_plan, adapt_cached_plan, match_template_type, build_type_plan
    
    data = await request.json()
    destination = data.get("destination", "").strip()[:200]
    start_date = data.get("start_date", "").strip()[:20]
    end_date = data.get("end_date", "").strip()[:20]
    trip_type = data.get("trip_type", "")
    if isinstance(trip_type, list):
        trip_type = ", ".join([str(t).strip()[:30] for t in trip_type[:6]])
    else:
        trip_type = str(trip_type).strip()[:100]
    
    if not destination or not start_date or not end_date:
        raise HTTPException(status_code=400, detail="Destino, data de inicio e data de fim sao obrigatorios")
    
    # Validate date format
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        num_days = max((end_dt - start_dt).days, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data invalido. Use AAAA-MM-DD.")
    
    logger.info(f"AI Travel Plan request: destination={destination}, dates={start_date} to {end_date}, type={trip_type}")
    
    # ── Rate limiting ──
    user = None
    try:
        user = await get_current_user(request)
    except Exception:
        pass
    
    user_key = user.user_id if user else request.client.host
    now = datetime.now(timezone.utc)
    
    is_premium = False
    if user:
        user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "is_admin": 1, "level": 1})
        if user_doc and (user_doc.get("is_admin") or user_doc.get("level") == "embaixador"):
            is_premium = True
    
    # Tiered rate limits: Free=3/h, Registered=5/h, Premium=15/h
    max_requests = 15 if is_premium else (5 if user else 3)
    
    if user_key in ai_travel_plan_cache:
        requests_list = ai_travel_plan_cache[user_key]
        requests_list = [t for t in requests_list if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
        ai_travel_plan_cache[user_key] = requests_list
        if len(requests_list) >= max_requests:
            raise HTTPException(status_code=429, detail="Ja criaste varios planos! Podes gerar um novo dentro de 1 hora.")
    
    if user_key not in ai_travel_plan_cache:
        ai_travel_plan_cache[user_key] = []
    ai_travel_plan_cache[user_key].append(now.isoformat())

    # ── Layer 1: Exact cache match (0 cost) ──
    cache_key = f"{destination}_{start_date}_{end_date}_{trip_type}".lower()
    cached = await db.travel_plans.find_one({"cache_key": cache_key}, {"_id": 0})
    if cached and cached.get("plan"):
        logger.info(f"Cache HIT (exact): {cache_key}")
        return {"plan": cached["plan"], "cached": True, "slug": cached.get("slug")}
    
    # ── Layer 2: Fuzzy cache — same destination, similar duration (0 cost) ──
    dest_lower = destination.lower().strip()
    fuzzy_cached = await db.travel_plans.find_one(
        {"destination": {"$regex": f"^{dest_lower[:20]}$", "$options": "i"}, "plan": {"$exists": True}},
        {"_id": 0}
    )
    if fuzzy_cached and fuzzy_cached.get("plan"):
        cached_plan = fuzzy_cached["plan"]
        cached_itinerary = cached_plan.get("itinerary", [])
        cached_days = len(cached_itinerary)
        # Only reuse if structure is complete and duration is close
        has_required = cached_plan.get("hotel_info") and cached_plan.get("airport_to_hotel")
        if has_required and abs(cached_days - num_days) <= 2:
            logger.info(f"Cache HIT (fuzzy): adapting {cached_days}d plan to {num_days}d")
            adapted = adapt_cached_plan(cached_plan, start_date, end_date)
            slug = f"{dest_lower.replace(' ', '-')[:20]}-{uuid.uuid4().hex[:6]}"
            await db.travel_plans.update_one(
                {"cache_key": cache_key},
                {"$set": {"cache_key": cache_key, "destination": destination, "plan": adapted, "slug": slug, "is_public": True, "user_id": user.user_id if user else None, "created_at": now.isoformat(), "updated_at": now.isoformat(), "source": "fuzzy_cache"}},
                upsert=True
            )
            return {"plan": adapted, "cached": True, "slug": slug}
    
    # ── Layer 3: Template engine for known destinations (0 cost) ──
    dest_data = match_destination(destination)
    if dest_data:
        logger.info(f"Template HIT: {dest_data['name']} ({num_days} days)")
        plan = build_full_template_plan(dest_data, destination, start_date, end_date)
        
        import re as _re
        def _slugify(text):
            s = text.lower().strip()
            s = _re.sub(r'[àáâãäå]', 'a', s)
            s = _re.sub(r'[èéêë]', 'e', s)
            s = _re.sub(r'[ìíîï]', 'i', s)
            s = _re.sub(r'[òóôõö]', 'o', s)
            s = _re.sub(r'[ùúûü]', 'u', s)
            s = _re.sub(r'[ç]', 'c', s)
            s = _re.sub(r'[^a-z0-9\s-]', '', s)
            s = _re.sub(r'[\s_]+', '-', s)
            s = _re.sub(r'-+', '-', s).strip('-')
            return s
        slug = f"{_slugify(destination)}-{uuid.uuid4().hex[:6]}"
        
        await db.travel_plans.update_one(
            {"cache_key": cache_key},
            {"$set": {"cache_key": cache_key, "destination": destination, "plan": plan, "slug": slug, "is_public": True, "user_id": user.user_id if user else None, "created_at": now.isoformat(), "updated_at": now.isoformat(), "source": "template"}},
            upsert=True
        )
        return {"plan": plan, "cached": False, "slug": slug}
    
    # ── Layer 4: Template TYPE fallback for unknown destinations (0 cost) ──
    template_type = match_template_type(destination, num_days)
    if template_type:
        logger.info(f"Template TYPE fallback for: {destination} ({num_days} days)")
        plan = build_type_plan(template_type, destination, start_date, end_date)
        
        import re as _re2
        def _slugify2(text):
            s = text.lower().strip()
            s = _re2.sub(r'[àáâãäå]', 'a', s)
            s = _re2.sub(r'[èéêë]', 'e', s)
            s = _re2.sub(r'[ìíîï]', 'i', s)
            s = _re2.sub(r'[òóôõö]', 'o', s)
            s = _re2.sub(r'[ùúûü]', 'u', s)
            s = _re2.sub(r'[ç]', 'c', s)
            s = _re2.sub(r'[^a-z0-9\s-]', '', s)
            s = _re2.sub(r'[\s_]+', '-', s)
            s = _re2.sub(r'-+', '-', s).strip('-')
            return s
        slug = f"{_slugify2(destination)}-{uuid.uuid4().hex[:6]}"
        
        await db.travel_plans.update_one(
            {"cache_key": cache_key},
            {"$set": {"cache_key": cache_key, "destination": destination, "plan": plan, "slug": slug, "is_public": True, "user_id": user.user_id if user else None, "created_at": now.isoformat(), "updated_at": now.isoformat(), "source": "template_type"}},
            upsert=True
        )
        return {"plan": plan, "cached": False, "slug": slug, "source": "template_type"}
    
    # ── Layer 5: Full AI generation for unknown destinations (LLM cost) ──
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA nao configurada")
    
    trip_type_text = f"Tipo de viagem: {trip_type}. " if trip_type else ""
    
    # Optimized prompt — smaller, focused only on what AI does best
    prompt = f"""Cria um plano de viagem para: {destination}, {start_date} a {end_date}. {trip_type_text}

Responde APENAS com JSON valido (sem markdown):
{{
  "destination": "{destination}",
  "dates": "{start_date} a {end_date}",
  "summary": "Resumo (1-2 frases)",
  "flight_info": {{"outbound": {{"flight_number": "Ex: TAP TP548", "departure_airport": "Partida", "departure_time": "08:30", "arrival_airport": "Chegada", "arrival_time": "Hora"}}, "return": {{"flight_number": "Regresso", "departure_airport": "Partida", "departure_time": "09:00", "arrival_airport": "Chegada", "arrival_time": "Hora"}}}},
  "hotel_info": {{"name": "Hotel real", "address": "Morada", "phone": null, "area": "Zona"}},
  "airport_to_hotel": {{"best_option": {{"mode": "Transporte", "details": "Descricao", "duration": "X min", "cost": "X EUR"}}, "alternative": {{"mode": "Taxi", "details": "Desc", "duration": "X min", "cost": "X EUR"}}, "tip": "Dica"}},
  "itinerary": [{{"day": 1, "title": "Titulo", "activities": ["Act 1", "Act 2 [CTA:activity:Ver bilhetes]"]}}],
  "weather": "Clima esperado",
  "packing": {{"clothing": ["item1", "item2", "item3"], "essentials": ["item1", "item2", "item3"]}},
  "checklist": {{"documents": ["item1"], "hygiene": ["item1"], "tech": ["item1"]}},
  "local_tips": ["Dica 1", "Dica 2 [CTA:activity:Reservar]"]
}}
CTAs: max 5, formato [CTA:tipo:texto]. Tipos: activity, hotel, flight, esim, transport, insurance."""

    chat = LlmChat(
        api_key=api_key,
        session_id=f"travel_plan_{uuid.uuid4().hex[:8]}",
        system_message="Es um agente de viagens. Responde APENAS com JSON valido, sem markdown."
    ).with_model("openai", "gpt-5.2")
    
    try:
        response = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=45)
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()
        
        plan = json.loads(clean)
        logger.info(f"AI Travel Plan success (full LLM): destination={destination}")
        
        import re as _re
        def _slugify(text):
            s = text.lower().strip()
            s = _re.sub(r'[àáâãäå]', 'a', s)
            s = _re.sub(r'[èéêë]', 'e', s)
            s = _re.sub(r'[ìíîï]', 'i', s)
            s = _re.sub(r'[òóôõö]', 'o', s)
            s = _re.sub(r'[ùúûü]', 'u', s)
            s = _re.sub(r'[ç]', 'c', s)
            s = _re.sub(r'[^a-z0-9\s-]', '', s)
            s = _re.sub(r'[\s_]+', '-', s)
            s = _re.sub(r'-+', '-', s).strip('-')
            return s
        slug = f"{_slugify(destination)}-{uuid.uuid4().hex[:6]}"

        await db.travel_plans.update_one(
            {"cache_key": cache_key},
            {"$set": {
                "cache_key": cache_key,
                "destination": destination,
                "plan": plan,
                "slug": slug,
                "is_public": True,
                "user_id": user.user_id if user else None,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "source": "ai_full"
            }},
            upsert=True
        )
        
        return {"plan": plan, "cached": False, "slug": slug}
    except asyncio.TimeoutError:
        logger.error(f"AI travel plan timeout: destination={destination}")
        raise HTTPException(status_code=504, detail="Nao foi possivel gerar o plano. Tente novamente.")
    except json.JSONDecodeError:
        logger.error(f"AI travel plan JSON parse error: {response[:500]}")
        raise HTTPException(status_code=500, detail="Nao foi possivel gerar o plano. Tente novamente.")
    except Exception as e:
        logger.error(f"AI travel plan error: {e}")
        raise HTTPException(status_code=500, detail="Nao foi possivel gerar o plano. Tente novamente.")



# ── Smart Map: Geocoding with Nominatim + Photon fallback + Cache ──
geocode_cache = {}

async def geocode_location(location_name: str, destination_context: str = "", bias_lat: float = None, bias_lng: float = None) -> dict:
    """Geocode a location using Photon with geo bias. Returns {lat, lng} or None."""
    cache_key = f"{location_name}|{destination_context}|{bias_lat}|{bias_lng}".lower().strip()
    if cache_key in geocode_cache:
        return geocode_cache[cache_key]

    cached = await db.geocode_cache.find_one({"cache_key": cache_key}, {"_id": 0})
    if cached:
        result = {"lat": cached["lat"], "lng": cached["lng"]}
        geocode_cache[cache_key] = result
        return result

    search_query = f"{location_name}, {destination_context}" if destination_context else location_name

    # Build Photon params with geographic bias
    photon_params = {"q": search_query, "limit": 5}
    if bias_lat is not None and bias_lng is not None:
        photon_params["lat"] = bias_lat
        photon_params["lon"] = bias_lng

    # Try Photon (Komoot) with bias
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://photon.komoot.io/api/",
                    params=photon_params,
                    headers={"User-Agent": "4Luis-TravelApp/1.0"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    features = data.get("features", [])
                    # Pick closest result to bias point — strict 1° threshold (~111km)
                    best = None
                    if features and bias_lat is not None:
                        import math
                        for f in features:
                            c = f["geometry"]["coordinates"]
                            dist = math.sqrt((c[1] - bias_lat)**2 + (c[0] - bias_lng)**2)
                            if dist < 1.0:  # ~111km — must be in/near the destination city
                                if best is None or dist < best[1]:
                                    best = (f, dist)
                        if best:
                            coords = best[0]["geometry"]["coordinates"]
                            result = {"lat": float(coords[1]), "lng": float(coords[0])}
                        else:
                            result = None
                    elif features:
                        coords = features[0]["geometry"]["coordinates"]
                        result = {"lat": float(coords[1]), "lng": float(coords[0])}
                    else:
                        result = None

                    if result:
                        geocode_cache[cache_key] = result
                        await db.geocode_cache.update_one(
                            {"cache_key": cache_key},
                            {"$set": {"cache_key": cache_key, "lat": result["lat"], "lng": result["lng"], "query": search_query}},
                            upsert=True
                        )
                        return result
                elif resp.status_code == 429 and attempt == 0:
                    await asyncio.sleep(1.5)
                    continue
        except Exception as e:
            logger.warning(f"Photon geocode attempt {attempt+1} failed for '{search_query}': {e}")
            if attempt == 0:
                await asyncio.sleep(1)
        break

    return None


@api_router.post("/ai/geocode-plan")
async def geocode_plan(request: Request):
    """Geocode all locations in a travel plan using Nominatim with caching."""
    try:
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")

    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "level": 1})
    if not user_doc or user_doc.get("level") != "embaixador":
        raise HTTPException(status_code=403, detail="Funcionalidade exclusiva para Embaixadores")

    data = await request.json()
    plan = data.get("plan")
    if not plan or not plan.get("itinerary"):
        raise HTTPException(status_code=400, detail="Plano com itinerario e obrigatorio")

    destination = plan.get("destination", "")
    locations_by_day = []
    logger.info(f"Geocoding plan for {destination}, {len(plan['itinerary'])} days")

    # Step 1: Geocode the destination itself for geographic bias
    dest_coords = await geocode_location(destination, "")
    bias_lat = dest_coords["lat"] if dest_coords else None
    bias_lng = dest_coords["lng"] if dest_coords else None
    logger.info(f"Destination bias: {bias_lat}, {bias_lng}")

    # Geocode all locations with concurrent batching per day
    for day in plan["itinerary"]:
        activities = day.get("activities", [])
        # Extract location names from activity strings
        location_names = []
        # Portuguese verbs/prepositions to strip for better geocoding
        strip_words = r'\b(visitar|explorar|passear|almoco|almocar|jantar|conhecer|ir|ver|fazer|tomar|comprar|experimentar|descobrir|subida|passeio|deslocacao|regresso|tempo|tarde|manha|livre|reservar|centro|historico|com|sem|ultima|visita|almoco|despedida)\b'
        # Skip non-geocodable activities
        skip_words = ['croissant', 'jantar ', 'almoco ', 'almocar', 'cafe ', 'falafel', 'gelato', 'crepe ', 'pizza ', 'ramen', 'sushi', 'churros', 'comida', 'degustacao', 'aperitivo', 'brunch ', 'check-out', 'check-in', 'transfer para', 'regresso', 'despedida', 'chegada e check', 'aeroporto e regresso', 'dia livre', 'tempo livre', 'cha turco num', 'cafe tradicional', 'cerveja artesanal', 'rooftop bar']
        for activity in activities:
            name = activity if isinstance(activity, str) else activity.get("title", activity.get("name", str(activity)))
            name_lower = name.lower()
            # Skip non-geocodable activities
            if any(sw in name_lower for sw in skip_words):
                continue

            raw = re.sub(r'\[CTA:\w+:[^\]]+\]', '', name).strip()
            raw = re.sub(r'^\d{1,2}[h:]\d{0,2}\s*[-–—]\s*', '', raw).strip()

            # BEFORE removing parentheses, extract potential geocoding name from them
            # Parentheses often contain the original/English/international name
            paren_geo_name = None
            paren_match = re.search(r'\(([^)]+)\)', raw)
            if paren_match:
                paren_text = paren_match.group(1)
                # Get the first meaningful part (before —, comma)
                first_part = re.split(r'[—,\-]', paren_text)[0].strip()
                # Check: has capitals, longer than 3 chars, not purely descriptive
                descriptive_words = ['gratis', 'entrada', 'reserva', 'obra', 'melhor', 'mais', 'menos', 'para', 'com vista', 'visita', 'preco', 'degraus', 'subterran', 'exterior', 'interior', 'obra-prima']
                if (first_part and len(first_part) > 3
                        and any(c.isupper() for c in first_part)
                        and not any(dw in first_part.lower() for dw in descriptive_words)):
                    paren_geo_name = first_part

            # Clean display name (without parentheses)
            clean = re.sub(r'\([^)]*\)', '', raw).strip()
            if ':' in clean:
                parts = clean.split(':')
                best = max(parts, key=lambda p: sum(1 for w in p.split() if w and w[0].isupper()))
                clean = best.strip()

            # Build geo name from clean text
            geo_name = re.sub(strip_words, '', clean, flags=re.IGNORECASE).strip()
            geo_name = re.sub(r'\s+', ' ', geo_name).strip(' -–—,')
            # Extract capitalized words (proper nouns = likely locations)
            proper_nouns = [w for w in geo_name.split() if w and w[0].isupper() and len(w) > 1]
            if proper_nouns:
                geo_name = ' '.join(proper_nouns[:5])
            elif len(geo_name) > 2:
                geo_name = ' '.join(geo_name.split()[:4])

            display = clean[:80]

            if paren_geo_name and len(paren_geo_name) > 3:
                location_names.append((display, paren_geo_name[:60], geo_name[:60] if len(geo_name) > 2 else None))
            elif len(geo_name) > 2:
                location_names.append((display, geo_name[:60], None))

        logger.info(f"Day {day.get('day')}: {len(activities)} activities -> {len(location_names)} geocodable names")

        # Geocode concurrently (batch of tasks)
        async def geocode_with_delay(display_name, primary_geo, fallback_geo, idx):
            await asyncio.sleep(idx * 0.4)
            # Strategy 1: primary name (often parenthetical/international) + destination
            result = await geocode_location(primary_geo, destination, bias_lat, bias_lng)
            # Strategy 2: fallback name (Portuguese clean) + destination
            if not result and fallback_geo and fallback_geo != primary_geo:
                result = await geocode_location(fallback_geo, destination, bias_lat, bias_lng)
            # Strategy 3: short name + destination
            if not result:
                short = ' '.join(primary_geo.split()[:2])
                if short != primary_geo and len(short) > 2:
                    result = await geocode_location(short, destination, bias_lat, bias_lng)
            return result

        tasks = [geocode_with_delay(display, primary, fallback, i) for i, (display, primary, fallback) in enumerate(location_names)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        day_locations = []
        for i, ((display_name, primary_geo, fallback_geo), coords) in enumerate(zip(location_names, results)):
            if isinstance(coords, Exception):
                logger.warning(f"Geocode exception for '{display_name}': {coords}")
            elif isinstance(coords, dict) and coords:
                day_locations.append({
                    "name": display_name,
                    "lat": coords["lat"],
                    "lng": coords["lng"],
                    "day": day.get("day", 1),
                    "day_title": day.get("title", f"Dia {day.get('day', 1)}")
                })

        locations_by_day.append({
            "day": day.get("day", 1),
            "title": day.get("title", f"Dia {day.get('day', 1)}"),
            "locations": day_locations
        })

    # Also geocode airport and hotel if present
    special_pins = {}
    flight_info = plan.get("flight_info")
    hotel_info = plan.get("hotel_info")

    if flight_info:
        arrival = flight_info.get("outbound", {}).get("arrival_airport", "")
        if arrival:
            airport_name = re.sub(r'\s*-\s*[A-Z]{3}$', '', arrival).strip()
            coords = await geocode_location(airport_name, "", bias_lat, bias_lng)
            if coords:
                special_pins["airport"] = {"name": arrival, "lat": coords["lat"], "lng": coords["lng"], "type": "airport"}

    if hotel_info:
        hotel_name = hotel_info.get("name", "")
        hotel_addr = hotel_info.get("address", "")
        if hotel_name:
            coords = await geocode_location(f"{hotel_name}, {hotel_addr}", destination, bias_lat, bias_lng)
            if not coords:
                coords = await geocode_location(hotel_name, destination, bias_lat, bias_lng)
            if coords:
                special_pins["hotel"] = {"name": hotel_name, "lat": coords["lat"], "lng": coords["lng"], "type": "hotel"}

    return {"days": locations_by_day, "destination": destination, "special_pins": special_pins}


@api_router.post("/ai/optimize-route")
async def optimize_route(request: Request):
    """AI-powered route optimization - reorder locations by proximity."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA nao configurada")

    try:
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")

    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "level": 1})
    if not user_doc or user_doc.get("level") != "embaixador":
        raise HTTPException(status_code=403, detail="Funcionalidade exclusiva para Embaixadores")

    data = await request.json()
    locations = data.get("locations", [])
    day = data.get("day")
    destination = data.get("destination", "")

    if not locations:
        raise HTTPException(status_code=400, detail="Locais sao obrigatorios")

    locs_text = "\n".join([f"- {l['name']} (lat:{l['lat']}, lng:{l['lng']})" for l in locations])

    prompt = f"""Otimiza a ordem de visita destes locais no Dia {day} em {destination} para minimizar deslocacoes.

LOCAIS ATUAIS (na ordem atual):
{locs_text}

REGRAS:
1. Reordena por proximidade geografica e logica de visita
2. Considera horarios tipicos (museus de manha, restaurantes ao almoco, etc)
3. Responde APENAS com JSON valido (sem markdown):

{{
  "optimized_order": ["Nome local 1", "Nome local 2", ...],
  "savings": "Descricao curta da melhoria (ex: 'Reduz 2km de deslocacoes')",
  "tips": ["Dica 1 sobre a rota", "Dica 2"]
}}"""

    chat = LlmChat(
        api_key=api_key,
        session_id=f"route_{user.user_id}_{uuid.uuid4().hex[:6]}",
        system_message="Es um otimizador de percursos turisticos. APENAS JSON valido."
    ).with_model("openai", "gpt-5.2")

    try:
        response = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=30)
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(clean)
        return result
    except Exception as e:
        logger.error(f"Route optimization error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao otimizar percurso. Tenta novamente.")


@api_router.post("/ai/improve-location")
async def improve_location(request: Request):
    """AI suggestions for improving a specific location visit."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA nao configurada")

    try:
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")

    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "level": 1})
    if not user_doc or user_doc.get("level") != "embaixador":
        raise HTTPException(status_code=403, detail="Funcionalidade exclusiva para Embaixadores")

    data = await request.json()
    location = data.get("location", "")
    improvement_type = data.get("type", "")  # "less_queues", "cheaper", "best_time"
    destination = data.get("destination", "")
    day = data.get("day", 1)

    type_labels = {
        "less_queues": "como evitar filas",
        "cheaper": "alternativas mais baratas",
        "best_time": "melhor horario para visitar",
        "what_to_see": "o que ver e nao perder neste local",
        "where_to_eat": "onde comer bem perto deste local (restaurantes reais, com precos)",
        "how_to_next": f"como chegar deste local ao proximo ponto do roteiro (transporte pratico)"
    }
    focus = type_labels.get(improvement_type, improvement_type)

    prompt = f"""Da sugestoes para melhorar a visita a "{location}" em {destination} (Dia {day}).
FOCO: {focus}

REGRAS:
1. Maximo 3 sugestoes, CURTAS e accionaveis
2. Inclui dicas locais quando possivel
3. Responde APENAS com JSON valido (sem markdown):

{{
  "response": "Frase resumo (1 linha)",
  "suggestions": ["Sugestao 1", "Sugestao 2", "Sugestao 3"],
  "can_apply": true,
  "apply_prompt": "Instrucao curta para atualizar '{location}' no Dia {day} com estas melhorias"
}}"""

    chat = LlmChat(
        api_key=api_key,
        session_id=f"improve_{user.user_id}_{uuid.uuid4().hex[:6]}",
        system_message="Es um consultor de viagem local. Respostas curtas e accionaveis. APENAS JSON valido."
    ).with_model("openai", "gpt-5.2")

    try:
        response = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=25)
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(clean)
        return result
    except Exception as e:
        logger.error(f"Improve location error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar sugestoes.")



@api_router.post("/ai/assistant")
async def ai_assistant(request: Request):
    """AI Assistant for premium ambassador users - contextual itinerary advice"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA nao configurada")

    # Verify ambassador status
    try:
        user = await get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Autenticacao necessaria")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Autenticacao necessaria")

    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "level": 1})
    if not user_doc or user_doc.get("level") != "embaixador":
        raise HTTPException(status_code=403, detail="Funcionalidade exclusiva para Embaixadores")

    data = await request.json()
    plan = data.get("plan")
    message = data.get("message", "").strip()[:500]
    history = data.get("history", [])[-6:]  # Keep last 6 messages for context

    if not plan or not message:
        raise HTTPException(status_code=400, detail="Plano e mensagem sao obrigatorios")

    plan_json = json.dumps(plan, ensure_ascii=False)

    history_text = ""
    if history:
        history_text = "\nHistorico de conversa:\n"
        for h in history:
            role = "Utilizador" if h.get("role") == "user" else "Assistente"
            history_text += f"{role}: {h.get('content', '')}\n"

    prompt = f"""Es o assistente pessoal de viagem premium da 4Luis. Analisa o plano de viagem e responde ao pedido do utilizador.

PLANO ATUAL:
{plan_json}

{history_text}
PEDIDO DO UTILIZADOR:
"{message}"

REGRAS OBRIGATORIAS:
1. Responde APENAS sobre o itinerario/viagem. Se a pergunta nao for relacionada, diz educadamente que so ajudas com a viagem.
2. Respostas CURTAS e ESTRUTURADAS - usa bullet points.
3. Maximo 4-6 bullet points por resposta.
4. Cada bullet deve ser ACCIONAVEL (algo que o viajante pode fazer).
5. Se o utilizador pedir para alterar o roteiro, gera sugestoes concretas.
6. Inclui dicas locais quando relevante ("dicas secretas").
7. Responde SEMPRE em portugues de Portugal.
8. NAO uses paragrafos longos. Cada ponto deve ter no maximo 1-2 frases.

Responde APENAS com JSON valido (sem markdown):
{{
  "response": "Frase resumo curta (1 linha)",
  "suggestions": ["Sugestao 1 accionavel", "Sugestao 2 accionavel", "Sugestao 3"],
  "can_apply": true ou false (se as sugestoes podem ser aplicadas ao roteiro),
  "apply_prompt": "Instrucao curta para o refine endpoint, se can_apply=true, senao null"
}}"""

    chat = LlmChat(
        api_key=api_key,
        session_id=f"assistant_{user.user_id}_{uuid.uuid4().hex[:6]}",
        system_message="Es um assistente de viagem premium. Respostas curtas, estruturadas, accionaveis. APENAS JSON valido."
    ).with_model("openai", "gpt-5.2")

    try:
        response = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=30)
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        result = json.loads(clean)
        return {
            "response": result.get("response", ""),
            "suggestions": result.get("suggestions", []),
            "can_apply": result.get("can_apply", False),
            "apply_prompt": result.get("apply_prompt")
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="O assistente demorou demasiado. Tenta novamente.")
    except json.JSONDecodeError:
        # Fallback: return raw text as single suggestion
        return {
            "response": clean[:200] if clean else "Nao consegui processar. Tenta reformular.",
            "suggestions": [],
            "can_apply": False,
            "apply_prompt": None
        }
    except Exception as e:
        logger.error(f"AI Assistant error: {e}")
        raise HTTPException(status_code=500, detail="Erro no assistente. Tenta novamente.")



@api_router.post("/ai/travel-plan/refine")
async def refine_travel_plan(request: Request):
    """Refine an existing AI travel plan with additional user instructions"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chave de IA nao configurada")

    data = await request.json()
    destination = data.get("destination", "").strip()[:200]
    start_date = data.get("start_date", "").strip()[:20]
    end_date = data.get("end_date", "").strip()[:20]
    trip_type = data.get("trip_type", "")
    if isinstance(trip_type, list):
        trip_type = ", ".join([str(t).strip()[:30] for t in trip_type[:6]])
    else:
        trip_type = str(trip_type).strip()[:100]
    previous_plan = data.get("previous_plan")
    refinement = data.get("refinement", "").strip()[:500]

    if not destination or not start_date or not end_date:
        raise HTTPException(status_code=400, detail="Destino e datas sao obrigatorios")
    if not previous_plan:
        raise HTTPException(status_code=400, detail="Plano anterior e obrigatorio")
    if not refinement:
        raise HTTPException(status_code=400, detail="Instrucoes de ajuste sao obrigatorias")

    logger.info(f"AI Travel Plan refine: destination={destination}, refinement={refinement[:100]}")

    # Rate limiting
    user = None
    try:
        user = await get_current_user(request)
    except Exception:
        pass

    user_key = user.user_id if user else request.client.host
    now = datetime.now(timezone.utc)

    if user_key in ai_travel_plan_cache:
        requests_list = ai_travel_plan_cache[user_key]
        requests_list = [t for t in requests_list if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
        ai_travel_plan_cache[user_key] = requests_list
        if len(requests_list) >= 5:
            raise HTTPException(status_code=429, detail="Já criaste vários planos! ✈️ Podes gerar um novo dentro de 1 hora.")

    # Increment rate limit counter BEFORE the AI call
    if user_key not in ai_travel_plan_cache:
        ai_travel_plan_cache[user_key] = []
    ai_travel_plan_cache[user_key].append(now.isoformat())

    trip_type_text = f"Tipo de viagem: {trip_type}. " if trip_type else ""
    previous_plan_json = json.dumps(previous_plan, ensure_ascii=False)

    prompt = f"""Tens um plano de viagem existente que o utilizador quer ajustar.

Dados da viagem:
Destino: {destination}
Datas: {start_date} a {end_date}
{trip_type_text}

Plano atual:
{previous_plan_json}

O utilizador pediu o seguinte ajuste:
"{refinement}"

REGRAS PARA CTAs CONTEXTUAIS:
- Nas atividades do itinerario e nas dicas locais, adiciona marcadores de CTA quando for util.
- Formato: [CTA:tipo:texto do botao]
- Tipos: activity, hotel, flight, esim, transport
- MAXIMO 4-6 CTAs no plano inteiro. NAO repitas o mesmo tipo mais de 2 vezes.
- Coloca no FIM da frase, de forma natural.

Gera uma versao melhorada do plano incorporando o pedido do utilizador. Mantém a mesma estrutura JSON.
Responde APENAS com um JSON valido com esta estrutura exata (sem markdown, sem ```):
{{
  "destination": "{destination}",
  "dates": "{start_date} a {end_date}",
  "summary": "Resumo curto da viagem (1-2 frases)",
  "itinerary": [
    {{
      "day": 1,
      "title": "Titulo do dia",
      "activities": ["Atividade 1", "Atividade 2 [CTA:activity:Ver bilhetes]", "Atividade 3"]
    }}
  ],
  "weather": "Descricao do clima esperado durante as datas",
  "packing": {{
    "clothing": ["item1", "item2", "item3"],
    "essentials": ["item1", "item2", "item3"]
  }},
  "checklist": {{
    "documents": ["item1", "item2"],
    "hygiene": ["item1", "item2"],
    "tech": ["item1", "item2"]
  }},
  "local_tips": ["Dica 1", "Dica 2 [CTA:activity:Ver atividades]", "Dica 3", "Dica 4"]
}}"""

    chat = LlmChat(
        api_key=api_key,
        session_id=f"travel_refine_{uuid.uuid4().hex[:8]}",
        system_message="Es um agente de viagens especialista. Ajusta planos de viagem com base no feedback do utilizador. Responde APENAS com JSON valido, sem markdown."
    ).with_model("openai", "gpt-5.2")

    try:
        response = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=45)
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.strip()

        plan = json.loads(clean)
        logger.info(f"AI Travel Plan refine success: destination={destination}")

        # Preserve flight/hotel/transport data from previous plan (not affected by refinements)
        for key in ("flight_info", "hotel_info", "airport_to_hotel"):
            if key not in plan and key in previous_plan:
                plan[key] = previous_plan[key]

        return {"plan": plan, "refined": True}
    except asyncio.TimeoutError:
        logger.error(f"AI travel refine timeout: destination={destination}")
        raise HTTPException(status_code=504, detail="Não foi possível gerar o plano. Tente novamente.")
    except json.JSONDecodeError:
        logger.error(f"AI travel refine JSON parse error: {response[:500]}")
        raise HTTPException(status_code=500, detail="Não foi possível gerar o plano. Tente novamente.")
    except Exception as e:
        logger.error(f"AI travel refine error: {e}")
        raise HTTPException(status_code=500, detail="Não foi possível gerar o plano. Tente novamente.")



# ==================== AFFILIATE SYSTEM ====================

# Centralized affiliate links config
# Replace ONLY the base URLs below when real affiliate links are available.
# Dynamic params (?destination=...&checkin=...&checkout=...) are appended by the frontend.
AFFILIATE_LINKS = {
    "skyscanner":   {"name": "Skyscanner",      "url": "https://www.skyscanner.pt/",                   "category": "flights",    "affiliate_id": "4luis"},
    "booking":      {"name": "Booking.com",      "url": "https://www.booking.com/searchresults.html",   "category": "hotels",     "affiliate_id": "4luis"},
    "hotels":       {"name": "Hotels.com",       "url": "https://pt.hotels.com/",                      "category": "hotels",     "affiliate_id": ""},
    "getyourguide": {"name": "GetYourGuide",     "url": "https://www.getyourguide.com/s/",             "category": "activities", "affiliate_id": "WFPE9ME"},
    "cars":         {"name": "DiscoverCars",     "url": "https://www.discovercars.com/",                "category": "transport",  "affiliate_id": ""},
    "airalo":       {"name": "Airalo",           "url": "https://www.airalo.com/",                     "category": "esim",       "affiliate_id": ""},
    "holafly":      {"name": "Holafly",          "url": "https://www.holafly.com/pt",                  "category": "esim",       "affiliate_id": ""},
    "insurance":    {"name": "IATI Seguros",     "url": "https://www.iatiseguros.com/",                "category": "insurance",  "affiliate_id": "4luis"},
    "googlemaps":   {"name": "Google Maps",      "url": "https://maps.google.com",                     "category": "map",        "affiliate_id": ""},
}

@api_router.get("/affiliate-links")
async def get_affiliate_links():
    """Public endpoint — returns affiliate links config for frontend"""
    return {k: {"url": v["url"], "name": v["name"], "affiliate_id": v.get("affiliate_id", "")} for k, v in AFFILIATE_LINKS.items()}

@api_router.post("/affiliate-click")
async def track_affiliate_click(request: Request):
    """Track affiliate link clicks for analytics"""
    data = await request.json()
    platform = data.get("platform")
    if not platform or platform not in AFFILIATE_LINKS:
        raise HTTPException(status_code=400, detail="Plataforma invalida")
    
    user = None
    try:
        user = await get_current_user(request)
    except Exception:
        pass
    
    click_doc = {
        "click_id": f"click_{uuid.uuid4().hex[:12]}",
        "platform": platform,
        "category": AFFILIATE_LINKS[platform]["category"],
        "user_id": user.user_id if user else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.affiliate_clicks.insert_one(click_doc)
    
    return {"status": "tracked"}

@api_router.post("/track-share")
async def track_share(request: Request):
    """Track share events for analytics"""
    data = await request.json()
    share_type = data.get("type")
    page = data.get("page")
    slug = data.get("slug")
    if not share_type or share_type not in ("whatsapp", "copy", "native", "link"):
        raise HTTPException(status_code=400, detail="Invalid share type")
    
    user = None
    try:
        user = await get_current_user(request)
    except Exception:
        pass
    
    share_doc = {
        "share_id": f"share_{uuid.uuid4().hex[:12]}",
        "type": share_type,
        "page": page or "",
        "slug": slug or "",
        "user_id": user.user_id if user else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.share_events.insert_one(share_doc)
    
    return {"status": "tracked"}

@api_router.get("/admin/affiliate-stats")
async def get_affiliate_stats(request: Request):
    """Admin endpoint — affiliate click analytics"""
    await require_admin(request)
    
    pipeline = [
        {"$group": {"_id": "$platform", "clicks": {"$sum": 1}}},
        {"$sort": {"clicks": -1}}
    ]
    stats = await db.affiliate_clicks.aggregate(pipeline).to_list(100)
    total = sum(s["clicks"] for s in stats)
    
    return {
        "total_clicks": total,
        "by_platform": {s["_id"]: s["clicks"] for s in stats}
    }

@api_router.get("/admin/share-stats")
async def get_share_stats(request: Request):
    """Admin endpoint — share event analytics"""
    await require_admin(request)
    
    pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    stats = await db.share_events.aggregate(pipeline).to_list(100)
    total = sum(s["count"] for s in stats)
    
    return {
        "total_shares": total,
        "by_type": {s["_id"]: s["count"] for s in stats}
    }

@api_router.get("/admin/referral-stats")
async def get_referral_stats(request: Request):
    """Admin endpoint — referral conversion analytics"""
    await require_admin(request)
    
    total_users = await db.users.count_documents({})
    ambassadors = await db.users.count_documents({"is_ambassador": True})
    
    pipeline = [
        {"$match": {"referred_by": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "total_referred": {"$sum": 1}}}
    ]
    referred = await db.users.aggregate(pipeline).to_list(1)
    total_referred = referred[0]["total_referred"] if referred else 0
    
    referral_pipeline = [
        {"$match": {"valid_referrals_count": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "total_valid_referrals": {"$sum": "$valid_referrals_count"},
            "referrers_count": {"$sum": 1}
        }}
    ]
    ref_stats = await db.users.aggregate(referral_pipeline).to_list(1)
    
    return {
        "total_users": total_users,
        "ambassadors": ambassadors,
        "total_referred_users": total_referred,
        "total_valid_referrals": ref_stats[0]["total_valid_referrals"] if ref_stats else 0,
        "active_referrers": ref_stats[0]["referrers_count"] if ref_stats else 0,
        "ambassador_conversion_rate": round(ambassadors / max(total_users, 1) * 100, 1)
    }

@api_router.get("/admin/analytics")
async def get_analytics_dashboard(request: Request):
    """Aggregated analytics dashboard — one call for the full picture"""
    await require_admin(request)
    
    # --- FUNNEL ---
    total_users = await db.users.count_documents({})
    ambassadors = await db.users.count_documents({"is_ambassador": True})
    total_contributions = await db.contributions.count_documents({})
    completed_contributions = await db.contributions.count_documents({"status": "completed"})
    pending_contributions = await db.contributions.count_documents({"status": {"$in": ["pending", "pending_validation"]}})
    
    amount_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    amount_result = await db.contributions.aggregate(amount_pipeline).to_list(1)
    total_raised = amount_result[0]["total"] if amount_result else 0
    
    # --- AFFILIATE PERFORMANCE ---
    aff_pipeline = [
        {"$group": {"_id": "$platform", "clicks": {"$sum": 1}}},
        {"$sort": {"clicks": -1}}
    ]
    aff_stats = await db.affiliate_clicks.aggregate(aff_pipeline).to_list(100)
    total_aff_clicks = sum(s["clicks"] for s in aff_stats)
    
    # --- SHARE METRICS ---
    share_pipeline = [
        {"$group": {"_id": "$type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    share_stats = await db.share_events.aggregate(share_pipeline).to_list(100)
    total_shares = sum(s["count"] for s in share_stats)
    
    # --- REFERRAL SYSTEM ---
    ref_pipeline = [
        {"$match": {"valid_referrals_count": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "total_valid": {"$sum": "$valid_referrals_count"},
            "referrers": {"$sum": 1}
        }}
    ]
    ref_result = await db.users.aggregate(ref_pipeline).to_list(1)
    total_valid_referrals = ref_result[0]["total_valid"] if ref_result else 0
    active_referrers = ref_result[0]["referrers"] if ref_result else 0
    avg_referrals = round(total_valid_referrals / max(active_referrers, 1), 1)
    
    # --- TOP PLANS (most shared, most clicked) ---
    top_shared_pipeline = [
        {"$match": {"slug": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": "$slug", "shares": {"$sum": 1}}},
        {"$sort": {"shares": -1}},
        {"$limit": 5}
    ]
    top_shared = await db.share_events.aggregate(top_shared_pipeline).to_list(5)
    
    # Enrich top plans with destination name
    top_plans = []
    for ts in top_shared:
        slug = ts["_id"]
        if not slug:
            continue
        plan = await db.travel_plans.find_one({"slug": slug}, {"_id": 0, "destination": 1})
        top_plans.append({
            "slug": slug,
            "destination": plan.get("destination", slug) if plan else slug,
            "shares": ts["shares"]
        })
    
    # Top affiliate plans
    top_aff_pipeline = [
        {"$match": {"slug": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": "$slug", "clicks": {"$sum": 1}}},
        {"$sort": {"clicks": -1}},
        {"$limit": 5}
    ]
    top_aff_plans = await db.affiliate_clicks.aggregate(top_aff_pipeline).to_list(5)
    top_affiliate_plans = []
    for ta in top_aff_plans:
        slug = ta["_id"]
        if not slug:
            continue
        plan = await db.travel_plans.find_one({"slug": slug}, {"_id": 0, "destination": 1})
        top_affiliate_plans.append({
            "slug": slug,
            "destination": plan.get("destination", slug) if plan else slug,
            "clicks": ta["clicks"]
        })
    
    # Top contributing journeys
    top_journey_pipeline = [
        {"$match": {"status": "completed"}},
        {"$group": {"_id": "$journey_id", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 5}
    ]
    top_journeys = await db.contributions.aggregate(top_journey_pipeline).to_list(5)
    top_converting = []
    for tj in top_journeys:
        jid = tj["_id"]
        journey = await db.journeys.find_one({"journey_id": jid}, {"_id": 0, "name": 1})
        top_converting.append({
            "journey_id": jid,
            "name": journey.get("name", jid) if journey else jid,
            "amount": tj["total"],
            "contributions": tj["count"]
        })
    
    return {
        "funnel": {
            "total_users": total_users,
            "total_contributions": total_contributions,
            "completed_contributions": completed_contributions,
            "pending_contributions": pending_contributions,
            "total_raised": total_raised,
            "ambassadors": ambassadors,
            "ambassador_rate": round(ambassadors / max(total_users, 1) * 100, 1)
        },
        "affiliates": {
            "total_clicks": total_aff_clicks,
            "by_platform": {s["_id"]: s["clicks"] for s in aff_stats}
        },
        "shares": {
            "total": total_shares,
            "by_type": {s["_id"]: s["count"] for s in share_stats}
        },
        "referrals": {
            "total_valid": total_valid_referrals,
            "active_referrers": active_referrers,
            "avg_per_referrer": avg_referrals,
            "ambassador_conversion": round(ambassadors / max(total_users, 1) * 100, 1)
        },
        "top_plans_shared": top_plans,
        "top_plans_affiliate": top_affiliate_plans,
        "top_converting_journeys": top_converting
    }


@api_router.get("/admin/platform-revenue")
async def get_platform_revenue(request: Request):
    """Get platform revenue analytics (tips and platform campaign support)"""
    await require_admin(request)
    
    # Total tips collected
    tip_pipeline = [
        {"$match": {"status": {"$in": ["confirmed", "completed"]}, "tip_amount": {"$gt": 0}}},
        {"$group": {
            "_id": None,
            "total_tips": {"$sum": "$tip_amount"},
            "tip_count": {"$sum": 1}
        }}
    ]
    tip_result = await db.contributions.aggregate(tip_pipeline).to_list(1)
    total_tips = tip_result[0]["total_tips"] if tip_result else 0
    tip_contributions = tip_result[0]["tip_count"] if tip_result else 0
    
    # Total contributions (to calculate tip conversion rate)
    total_confirmed = await db.contributions.count_documents({"status": {"$in": ["confirmed", "completed"]}})
    tip_conversion_rate = round((tip_contributions / max(total_confirmed, 1)) * 100, 1)
    
    # Platform campaign revenue (support_amount from non-ambassador journeys)
    platform_campaign_pipeline = [
        {"$match": {
            "status": {"$in": ["confirmed", "completed"]},
            "$or": [
                {"is_ambassador_journey": False},
                {"is_ambassador_journey": {"$exists": False}},
                {"ambassador_user_id": None},
                {"ambassador_user_id": {"$exists": False}}
            ]
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": {"$ifNull": ["$support_amount", "$amount"]}},
            "count": {"$sum": 1}
        }}
    ]
    platform_campaign_result = await db.contributions.aggregate(platform_campaign_pipeline).to_list(1)
    platform_campaign_revenue = platform_campaign_result[0]["total"] if platform_campaign_result else 0
    platform_campaign_count = platform_campaign_result[0]["count"] if platform_campaign_result else 0
    
    # Ambassador campaign support (goes to ambassadors, not platform)
    ambassador_pipeline = [
        {"$match": {
            "status": {"$in": ["confirmed", "completed"]},
            "is_ambassador_journey": True,
            "ambassador_user_id": {"$exists": True, "$ne": None}
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": {"$ifNull": ["$support_amount", "$amount"]}},
            "count": {"$sum": 1}
        }}
    ]
    ambassador_result = await db.contributions.aggregate(ambassador_pipeline).to_list(1)
    ambassador_support_total = ambassador_result[0]["total"] if ambassador_result else 0
    ambassador_contributions_count = ambassador_result[0]["count"] if ambassador_result else 0
    
    # Tips by amount breakdown
    tip_breakdown_pipeline = [
        {"$match": {"status": {"$in": ["confirmed", "completed"]}, "tip_amount": {"$gt": 0}}},
        {"$group": {
            "_id": "$tip_amount",
            "count": {"$sum": 1},
            "total": {"$sum": "$tip_amount"}
        }},
        {"$sort": {"_id": 1}}
    ]
    tip_breakdown = await db.contributions.aggregate(tip_breakdown_pipeline).to_list(10)
    
    # Include zero tips in breakdown for tracking
    zero_tip_count = await db.contributions.count_documents({
        "status": {"$in": ["confirmed", "completed"]},
        "$or": [{"tip_amount": 0}, {"tip_amount": {"$exists": False}}]
    })
    
    # Calculate average tip (only from contributors who gave tips)
    avg_tip = round(total_tips / max(tip_contributions, 1), 2)
    
    # Recent tips
    recent_tips = await db.contributions.find(
        {"status": {"$in": ["confirmed", "completed"]}, "tip_amount": {"$gt": 0}},
        {"_id": 0, "contribution_id": 1, "tip_amount": 1, "support_amount": 1, "amount": 1, "created_at": 1, "journey_id": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "summary": {
            "total_platform_revenue": total_tips + platform_campaign_revenue,
            "total_tips": total_tips,
            "total_platform_campaign_revenue": platform_campaign_revenue,
            "tip_contributions": tip_contributions,
            "platform_campaign_contributions": platform_campaign_count,
            "tip_conversion_rate": tip_conversion_rate,
            "average_tip": avg_tip,
            "zero_tip_count": zero_tip_count,
            "ambassador_support_total": ambassador_support_total,
            "ambassador_contributions_count": ambassador_contributions_count
        },
        "tip_breakdown": [
            {"amount": t["_id"], "count": t["count"], "total": t["total"]}
            for t in tip_breakdown
        ] + ([{"amount": 0, "count": zero_tip_count, "total": 0, "label": "Sem contribuição"}] if zero_tip_count > 0 else []),
        "recent_tips": recent_tips
    }


# ==================== OFFERS SYSTEM (ADMIN ONLY) ====================

@api_router.get("/admin/offers")
async def list_offers(request: Request, status: Optional[str] = None, user_id: Optional[str] = None):
    """List offers - Admin only"""
    await require_admin(request)
    query = {}
    if status:
        query["status"] = status
    if user_id:
        query["user_id"] = user_id
    offers = await db.offers.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return offers

@api_router.post("/admin/offers")
async def create_offer(request: Request):
    """Create a new offer - Admin only"""
    await require_admin(request)
    data = await request.json()
    
    user_id = data.get("user_id")
    offer_type = data.get("type")
    description = data.get("description")
    
    if not all([user_id, offer_type, description]):
        raise HTTPException(status_code=400, detail="user_id, type e description são obrigatórios")
    if offer_type not in ["voucher", "parceiro"]:
        raise HTTPException(status_code=400, detail="Tipo deve ser 'voucher' ou 'parceiro'")
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "user_id": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")
    
    offer_doc = {
        "offer_id": f"offer_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": offer_type,
        "description": description,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.offers.insert_one(offer_doc)
    offer_doc.pop("_id", None)
    return offer_doc

@api_router.patch("/admin/offers/{offer_id}")
async def update_offer_status(offer_id: str, request: Request):
    """Update offer status - Admin only"""
    await require_admin(request)
    data = await request.json()
    new_status = data.get("status")
    
    if new_status not in ["pending", "sent"]:
        raise HTTPException(status_code=400, detail="Status deve ser 'pending' ou 'sent'")
    
    result = await db.offers.update_one(
        {"offer_id": offer_id},
        {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Oferta não encontrada")
    
    return {"message": f"Oferta atualizada para {new_status}", "offer_id": offer_id}

@api_router.delete("/admin/offers/{offer_id}")
async def delete_offer(offer_id: str, request: Request):
    """Delete an offer - Admin only"""
    await require_admin(request)
    result = await db.offers.delete_one({"offer_id": offer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Oferta não encontrada")
    return {"message": "Oferta eliminada"}


# ==================== PDF GUIDE ENDPOINT ====================

@api_router.post("/ai/travel-plan/pdf")
async def generate_pdf_guide(request: Request):
    """Generate offline travel guide PDF — Ambassador only"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "level": 1})
    level = user_doc.get("level", "sonhador") if user_doc else "sonhador"
    if level != "embaixador" and not user.is_admin:
        raise HTTPException(status_code=403, detail="Funcionalidade exclusiva para Embaixadores")
    
    body = await request.json()
    plan = body.get("plan")
    if not plan:
        raise HTTPException(status_code=400, detail="Plano não fornecido")
    
    sections = body.get("sections", {
        "flights": True, "hotel": True, "map": True,
        "itinerary": True, "tips": True, "transport": True
    })
    geocode_data = body.get("geocode_data")
    
    from pdf_generator import generate_travel_guide_pdf
    
    # Get affiliate links for PDF
    aff_links = {}
    try:
        aff_response = await db.settings.find_one({"key": "affiliate_links"}, {"_id": 0})
        if aff_response:
            aff_links = aff_response.get("value", {})
        else:
            aff_links = AFFILIATE_LINKS
    except Exception:
        aff_links = AFFILIATE_LINKS
    
    try:
        # Generate OG image for PDF cover
        og_image_bytes = None
        slug = body.get("slug")
        if slug:
            try:
                import io as _io
                from PIL import Image as PILImage, ImageDraw, ImageFont
                plan_for_og = plan
                destination_name = plan_for_og.get("destination", "Viagem")
                dates_og = plan_for_og.get("dates", "")
                num_days_og = len(plan_for_og.get("itinerary", []))
                summary_og = plan_for_og.get("summary", "")[:100]

                w_og, h_og = 1200, 630
                img = PILImage.new("RGB", (w_og, h_og))
                draw = ImageDraw.Draw(img)
                for y in range(h_og):
                    ratio = y / h_og
                    r = int(45 + ratio * 40)
                    g = int(42 + ratio * 22)
                    b = int(38 + ratio * 15)
                    draw.line([(0, y), (w_og, y)], fill=(r, g, b))
                for y in range(4):
                    draw.line([(0, y), (w_og, y)], fill=(255, 190, 152))
                try:
                    f_big = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 64)
                    f_med = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 28)
                    f_sml = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 22)
                    f_logo = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)
                except Exception:
                    f_big = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 64)
                    f_med = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 28)
                    f_sml = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 22)
                    f_logo = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 26)
                draw.text((60, 36), "4Luis", fill=(255, 190, 152), font=f_logo)
                dest_y = h_og // 2 - 80
                draw.text((60, dest_y), destination_name, fill=(255, 255, 255), font=f_big)
                info_parts = []
                if num_days_og > 0:
                    info_parts.append(f"{num_days_og} dias")
                if dates_og:
                    info_parts.append(dates_og)
                if info_parts:
                    draw.text((60, dest_y + 80), "  ·  ".join(info_parts), fill=(255, 190, 152), font=f_med)
                if summary_og:
                    draw.text((60, dest_y + 125), summary_og, fill=(180, 178, 175), font=f_sml)
                draw.text((60, h_og - 50), "Guia de viagem criado com IA", fill=(255, 190, 152), font=f_sml)
                draw.text((w_og - 170, h_og - 50), "4luis.com", fill=(200, 200, 200), font=f_med)
                og_buf = _io.BytesIO()
                img.save(og_buf, format="PNG")
                og_image_bytes = og_buf.getvalue()
            except Exception as e:
                logger.warning(f"PDF cover image generation failed: {e}")

        buf = generate_travel_guide_pdf(plan, geocode_data=geocode_data, sections=sections, affiliate_links=aff_links, og_image_bytes=og_image_bytes)
        destination = plan.get("destination", "viagem").replace(" ", "-").lower()
        filename = f"guia-{destination}-4luis.pdf"
        
        return Response(
            content=buf.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar o guia PDF")


# ==================== SEO ENDPOINTS ====================

@api_router.get("/og-image/{slug}")
async def generate_og_image(slug: str):
    """Generate dynamic Open Graph image for social sharing + PDF cover"""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import io

    plan_doc = await db.travel_plans.find_one(
        {"slug": slug, "is_public": True},
        {"_id": 0, "destination": 1, "plan": 1}
    )
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    p = plan_doc.get("plan", {})
    destination = p.get("destination", plan_doc.get("destination", "Viagem"))
    dates = p.get("dates", "")
    num_days = len(p.get("itinerary", []))
    summary = p.get("summary", "")[:100]

    # Create OG image (1200x630 — Facebook/LinkedIn standard)
    w, h = 1200, 630
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    # Premium gradient: dark charcoal base with warm peach accent
    for y in range(h):
        ratio = y / h
        # Top: dark charcoal → mid: slightly warmer → bottom: dark with peach hint
        if ratio < 0.5:
            r = int(45 + ratio * 20)
            g = int(42 + ratio * 15)
            b = int(38 + ratio * 10)
        else:
            r = int(55 + (ratio - 0.5) * 60)
            g = int(49 + (ratio - 0.5) * 30)
            b = int(43 + (ratio - 0.5) * 20)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Decorative peach accent stripe (top)
    for y in range(4):
        draw.line([(0, y), (w, y)], fill=(255, 190, 152))

    # Load fonts
    try:
        font_dest = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 64)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 28)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 18)
        font_logo = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)
        font_badge = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 14)
    except Exception:
        font_dest = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 64)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 28)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 18)
        font_logo = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 26)
        font_badge = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 14)

    # Logo (top-left)
    draw.text((60, 36), "4Luis", fill=(255, 190, 152), font=font_logo)

    # AI badge (top-right area)
    badge_text = "AI Travel Planner"
    draw.rounded_rectangle([w - 260, 36, w - 60, 64], radius=14, fill=(255, 190, 152, 40), outline=(255, 190, 152, 80))
    draw.text((w - 245, 40), badge_text, fill=(255, 190, 152), font=font_badge)

    # Main destination text (centered vertically)
    dest_y = h // 2 - 80
    draw.text((60, dest_y), destination, fill=(255, 255, 255), font=font_dest)

    # Duration + dates
    info_parts = []
    if num_days > 0:
        info_parts.append(f"{num_days} dias")
    if dates:
        info_parts.append(dates)
    info_text = "  ·  ".join(info_parts)
    if info_text:
        draw.text((60, dest_y + 80), info_text, fill=(255, 190, 152), font=font_sub)

    # Summary
    if summary:
        draw.text((60, dest_y + 125), summary, fill=(180, 178, 175), font=font_body)

    # Bottom bar: gradient overlay
    for y in range(h - 80, h):
        alpha = int((y - (h - 80)) / 80 * 100)
        draw.line([(0, y), (w, y)], fill=(30, 28, 25))

    # Bottom labels
    draw.text((60, h - 50), "Planeia a tua viagem com IA", fill=(255, 190, 152), font=font_small)
    draw.text((w - 170, h - 50), "4luis.com", fill=(200, 200, 200), font=font_sub)

    # Export as PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png",
                    headers={"Cache-Control": "public, max-age=86400"})


@api_router.get("/plan/{slug}")
async def get_public_plan(slug: str):
    """Public endpoint — returns a travel plan by its slug for SEO pages"""
    plan_doc = await db.travel_plans.find_one(
        {"slug": slug, "is_public": True},
        {"_id": 0, "cache_key": 0}
    )
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan_doc


@api_router.get("/ssr/plano/{slug}")
async def ssr_public_plan(slug: str, request: Request):
    """Server-side rendered HTML for social crawlers and SEO bots"""
    plan_doc = await db.travel_plans.find_one(
        {"slug": slug, "is_public": True},
        {"_id": 0, "cache_key": 0}
    )
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    p = plan_doc.get("plan", {})
    destination = p.get("destination", plan_doc.get("destination", "Viagem"))
    num_days = len(p.get("itinerary", []))
    summary = p.get("summary", "")[:200]
    dates = p.get("dates", "")
    weather = p.get("weather", "")

    frontend_url = os.environ.get("FRONTEND_URL", str(request.base_url).rstrip("/"))
    base_url = frontend_url.replace(":3000", "").rstrip("/")
    canonical_url = f"{base_url}/plano/{slug}"
    og_image_url = f"{base_url}/api/og-image/{slug}"

    title = f"{destination} em {num_days} dias | 4Luis"
    description = summary or f"Plano de viagem para {destination} com {num_days} dias. Roteiro completo gerado por IA."

    # Build itinerary HTML
    itinerary_html = ""
    for day in p.get("itinerary", []):
        day_num = day.get("day", "?")
        day_title = day.get("title", "")
        activities = day.get("activities", [])
        itinerary_html += f'<div style="margin-bottom:16px"><h3 style="color:#FFBE98;font-size:14px;margin:0">Dia {day_num} — {day_title}</h3><ul style="margin:4px 0 0 0;padding-left:20px">'
        for a in activities:
            import re
            clean = re.sub(r'\[CTA:\w+:[^\]]+\]', '', str(a)).strip()
            itinerary_html += f'<li style="color:#6B6661;font-size:13px;line-height:1.5">{clean}</li>'
        itinerary_html += "</ul></div>"

    # Tips HTML
    tips_html = ""
    for tip in p.get("local_tips", [])[:5]:
        import re
        clean = re.sub(r'\[CTA:\w+:[^\]]+\]', '', str(tip)).strip()
        tips_html += f'<li style="color:#6B6661;font-size:13px;line-height:1.6">{clean}</li>'

    # Flight info
    flight_html = ""
    fi = p.get("flight_info", {})
    if fi.get("outbound"):
        ob = fi["outbound"]
        flight_html += f'<p style="font-size:13px;color:#2D2A26"><strong>Ida:</strong> {ob.get("flight_number","")} — {ob.get("departure_airport","")} → {ob.get("arrival_airport","")}</p>'

    # Hotel info
    hotel_html = ""
    hi = p.get("hotel_info", {})
    if hi.get("name"):
        hotel_html += f'<p style="font-size:13px;color:#2D2A26"><strong>Hotel:</strong> {hi["name"]}'
        if hi.get("address"):
            hotel_html += f' — {hi["address"]}'
        hotel_html += "</p>"

    # Schema.org structured data
    schema_json = {
        "@context": "https://schema.org",
        "@type": "TouristTrip",
        "name": f"Roteiro {destination} — {num_days} dias",
        "description": description,
        "touristType": "Cultural",
        "url": canonical_url,
        "image": og_image_url,
    }
    if dates:
        parts = dates.split(" a ")
        if len(parts) == 2:
            schema_json["startDate"] = parts[0].strip()
            schema_json["endDate"] = parts[1].strip()

    import json as json_mod
    schema_tag = f'<script type="application/ld+json">{json_mod.dumps(schema_json, ensure_ascii=False)}</script>'

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>{title}</title>
    <meta name="description" content="{description}"/>
    <link rel="canonical" href="{canonical_url}"/>
    <meta property="og:title" content="{title}"/>
    <meta property="og:description" content="{description}"/>
    <meta property="og:image" content="{og_image_url}"/>
    <meta property="og:image:width" content="1200"/>
    <meta property="og:image:height" content="630"/>
    <meta property="og:url" content="{canonical_url}"/>
    <meta property="og:type" content="article"/>
    <meta property="og:site_name" content="4Luis"/>
    <meta name="twitter:card" content="summary_large_image"/>
    <meta name="twitter:title" content="{title}"/>
    <meta name="twitter:description" content="{description}"/>
    <meta name="twitter:image" content="{og_image_url}"/>
    {schema_tag}
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #FAFAF9; color: #2D2A26; }}
        .hero {{ background: linear-gradient(to bottom, #2D2A26, #3D3A36, #FAFAF9); padding: 60px 24px 40px; }}
        .container {{ max-width: 640px; margin: 0 auto; padding: 0 16px 60px; }}
        .badge {{ display: inline-block; background: rgba(255,255,255,0.1); color: #FFBE98; font-size: 12px; padding: 4px 12px; border-radius: 999px; margin-bottom: 12px; }}
        h1 {{ color: white; font-size: 32px; margin: 0 0 8px; }}
        .meta {{ color: #FFBE98; font-size: 14px; margin: 0 0 8px; }}
        .summary {{ color: rgba(255,255,255,0.7); font-size: 14px; line-height: 1.5; margin: 0; }}
        .card {{ background: white; border-radius: 16px; border: 1px solid #E5E5E5; padding: 20px; margin-top: 12px; }}
        h2 {{ font-size: 16px; color: #2D2A26; margin: 24px 0 12px; }}
        .cta {{ display: inline-block; background: #FFBE98; color: #2D2A26; font-weight: bold; padding: 12px 24px; border-radius: 12px; text-decoration: none; margin-top: 16px; }}
        .cta:hover {{ background: #E6A07C; }}
        .footer {{ text-align: center; color: #6B6661; font-size: 12px; padding: 24px 0; }}
    </style>
</head>
<body>
    <div class="hero">
        <div style="max-width:640px;margin:0 auto">
            <span class="badge">Plano gerado por IA</span>
            <h1>{destination}</h1>
            <p class="meta">{num_days} dias{' | ' + dates if dates else ''}</p>
            {f'<p class="summary">{summary}</p>' if summary else ''}
        </div>
    </div>
    <div class="container">
        {f'<div class="card">{flight_html}{hotel_html}</div>' if flight_html or hotel_html else ''}
        {f'<div class="card"><p style="font-size:13px;color:#6B6661">{weather}</p></div>' if weather else ''}
        <div class="card">
            <h2>Roteiro dia a dia</h2>
            {itinerary_html}
        </div>
        {f'<div class="card"><h2>Dicas locais</h2><ul style="padding-left:20px">{tips_html}</ul></div>' if tips_html else ''}
        <div style="text-align:center;padding:24px 0">
            <a class="cta" href="{base_url}/travel-planner">Criar o meu roteiro com IA</a>
        </div>
        <p class="footer">Plano gerado por 4Luis AI Travel Planner — 4luis.com</p>
    </div>
    <script>window.location.href="{canonical_url}";</script>
</body>
</html>"""

    return Response(content=html, media_type="text/html",
                    headers={"Cache-Control": "public, max-age=3600"})

@api_router.patch("/plan/{slug}/visibility")
async def toggle_plan_visibility(slug: str, request: Request):
    """Toggle a plan's public visibility — owner or admin only"""
    user = await get_current_user(request)
    plan_doc = await db.travel_plans.find_one({"slug": slug}, {"_id": 0, "user_id": 1, "is_public": 1})
    if not plan_doc:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    if plan_doc.get("user_id") != user.user_id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Sem permissão")
    new_status = not plan_doc.get("is_public", True)
    await db.travel_plans.update_one({"slug": slug}, {"$set": {"is_public": new_status}})
    return {"is_public": new_status}


@api_router.get("/sitemap.xml")
async def sitemap_xml():
    """Generate sitemap.xml for SEO — includes public journeys and travel plans"""
    frontend_url = os.environ.get("FRONTEND_URL", FRONTEND_URL or "https://4luis.com")

    urls = [
        {"loc": frontend_url, "priority": "1.0"},
        {"loc": f"{frontend_url}/about", "priority": "0.6"},
        {"loc": f"{frontend_url}/plan-trip", "priority": "0.8"},
        {"loc": f"{frontend_url}/travel-planner", "priority": "0.8"},
    ]

    journeys = await db.journeys.find(
        {"status": {"$in": ["active", "funded"]}},
        {"_id": 0, "journey_id": 1, "updated_at": 1}
    ).to_list(500)
    for j in journeys:
        urls.append({
            "loc": f"{frontend_url}/journey/{j['journey_id']}",
            "lastmod": j.get("updated_at", ""),
            "priority": "0.7"
        })

    plans = await db.travel_plans.find(
        {"is_public": True, "slug": {"$exists": True}},
        {"_id": 0, "slug": 1, "updated_at": 1}
    ).to_list(500)
    for p in plans:
        urls.append({
            "loc": f"{frontend_url}/plano/{p['slug']}",
            "lastmod": p.get("updated_at", ""),
            "priority": "0.5"
        })

    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_parts.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        xml_parts.append("  <url>")
        xml_parts.append(f"    <loc>{u['loc']}</loc>")
        if u.get("lastmod"):
            xml_parts.append(f"    <lastmod>{u['lastmod'][:10]}</lastmod>")
        xml_parts.append(f"    <priority>{u['priority']}</priority>")
        xml_parts.append("  </url>")
    xml_parts.append("</urlset>")

    return Response(content="\n".join(xml_parts), media_type="application/xml")


# Include router
app.include_router(api_router)

@app.on_event("startup")
async def startup_event():
    """Seed admin user on startup and start background validation checker"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    admin_exists = await db.users.find_one({"email": ADMIN_EMAIL})
    if not admin_exists:
        admin_doc = {
            "user_id": f"admin_{uuid.uuid4().hex[:8]}",
            "email": ADMIN_EMAIL,
            "password_hash": pwd_context.hash(ADMIN_PASSWORD),
            "name": "Admin",
            "is_admin": True,
            "level": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_doc)
        logger.info(f"Admin user created: {ADMIN_EMAIL}")
    
    # Start background task for validation reminders
    asyncio.create_task(validation_reminder_loop())


async def validation_reminder_loop():
    """Background loop: remind ambassadors of pending validations and flag stale ones"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            now = datetime.now(timezone.utc)
            
            # 24h reminder: notify ambassador of unvalidated contributions
            cutoff_24h = (now - timedelta(hours=24)).isoformat()
            stale_24h = await db.contributions.find({
                "status": "awaiting_validation",
                "confirmed_by_user_at": {"$lt": cutoff_24h},
                "reminder_sent": {"$ne": True}
            }, {"_id": 0}).to_list(100)
            
            for c in stale_24h:
                journey = await db.journeys.find_one({"journey_id": c["journey_id"]}, {"_id": 0, "ambassador_user_id": 1, "name": 1})
                if journey and journey.get("ambassador_user_id"):
                    await create_notification(
                        journey["ambassador_user_id"], "validation_reminder",
                        f"Tens pagamentos por confirmar para '{journey.get('name', '')}'. Ajuda a manter o sonho a crescer.",
                        {"contribution_id": c["contribution_id"]}
                    )
                    await db.contributions.update_one(
                        {"contribution_id": c["contribution_id"]},
                        {"$set": {"reminder_sent": True}}
                    )
            
            # 7-day timeout: flag for admin
            cutoff_7d = (now - timedelta(days=7)).isoformat()
            stale_7d = await db.contributions.find({
                "status": "awaiting_validation",
                "confirmed_by_user_at": {"$lt": cutoff_7d},
                "flagged": {"$ne": True}
            }, {"_id": 0}).to_list(100)
            
            for c in stale_7d:
                await db.contributions.update_one(
                    {"contribution_id": c["contribution_id"]},
                    {"$set": {"flagged": True, "flagged_at": now.isoformat(), "flagged_reason": "7d_no_validation"}}
                )
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "type": "stale_contribution",
                    "title": "Contribuição sem validação há 7 dias",
                    "message": f"Contribuição {c['contribution_id']} ({c.get('amount', 0)}€) sem validação. Verificar.",
                    "for_admin": True,
                    "read": False,
                    "created_at": now.isoformat()
                })
                logger.warning(f"Flagged stale contribution: {c['contribution_id']}")
        except Exception as e:
            logger.error(f"Validation reminder loop error: {e}")
            await asyncio.sleep(60)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
