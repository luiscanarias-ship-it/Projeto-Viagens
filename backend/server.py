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
import stripe

# Import shared modules
from config import (
    db, client, logger, JWT_SECRET, JWT_ALGORITHM, ADMIN_PASSWORD, ADMIN_EMAIL,
    STRIPE_API_KEY, STRIPE_SONHADOR_PRICE_ID, STRIPE_WEBHOOK_SECRET, FRONTEND_URL,
    FIXED_CONTRIBUTION_AMOUNTS, PAYMENT_METHODS, CRYPTO_TYPES, JOURNEY_STATUSES,
    TICKET_TYPES, TICKET_STATUSES, TICKET_PRIORITIES
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
    _build_email_progress_bar, _build_email_cta_button, _build_standard_email
)

app = FastAPI(title="4Luis API")
api_router = APIRouter(prefix="/api")

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
        "total_contributed": 0,  # Soma de todas as contribuições confirmadas
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
    """Create a new contribution with payment reference for external payments"""
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
    
    # Validate payment method (Stripe temporarily disabled)
    valid_methods = ["crypto", "mbway", "paypal", "revolut", "wise"]
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
        "amount": amount,
        "currency": "EUR",
        "payment_method": payment_method,
        "crypto_type": crypto_type if payment_method == "crypto" else None,
        "payment_reference": payment_reference,
        "status": "pending",  # Requires admin confirmation
        "is_main_trip": journey.get("is_main_trip", False),
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
        "amount": amount,
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
                sponsor_link_id = contribution.get("sponsor_link_id")
                
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
                    
                    # Process sponsor referral
                    if sponsor_link_id:
                        sponsor_link = await db.sponsor_links.find_one(
                            {"link_id": sponsor_link_id},
                            {"_id": 0}
                        )
                        if sponsor_link:
                            sponsor_user_id = sponsor_link["user_id"]
                            # Increment successful referrals
                            await db.sponsor_links.update_one(
                                {"link_id": sponsor_link_id},
                                {"$inc": {"successful_referrals": 1}}
                            )
                            # Update sponsor's valid_referrals_count
                            await db.users.update_one(
                                {"user_id": sponsor_user_id},
                                {"$inc": {"valid_referrals_count": 1}}
                            )
                            
                            # Check if sponsor becomes ambassador
                            sponsor_user = await db.users.find_one(
                                {"user_id": sponsor_user_id},
                                {"_id": 0}
                            )
                            if sponsor_user:
                                valid_refs = sponsor_user.get("valid_referrals_count", 0) + 1
                                contributed = sponsor_user.get("contributed_to_main_trip", False)
                                if contributed and valid_refs >= 3 and sponsor_user.get("level") != "embaixador":
                                    await db.users.update_one(
                                        {"user_id": sponsor_user_id},
                                        {"$set": {
                                            "level": "embaixador",
                                            "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                                        }}
                                    )
                                    # Send email
                                    asyncio.create_task(send_ambassador_unlocked_email(sponsor_user_id))
                
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
            "Contribuição confirmada",
            f"A tua contribuição de {contribution['amount']}€ para {journey_name.get('name', 'esta viagem')} foi confirmada.",
            f"/journey/{contribution['journey_id']}",
            "contribution"
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
            
            # Send emails to ambassador and admin
            ambassador = await db.users.find_one({"user_id": ambassador_user_id}, {"_id": 0})
            await send_journey_funded_emails(journey, ambassador, current_amount)
        else:
            # Just send email to admin for non-ambassador journeys
            await send_journey_funded_emails(journey, None, current_amount)
        
        logger.info(f"Journey {journey_id} automatically moved to 'financiada' status")
        return "financiada"
    
    return current_status

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
        "Nova resposta ao teu pedido",
        f"A equipa 4Luis respondeu ao teu pedido de suporte.",
        f"/support/{ticket_id}",
        "support"
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

async def create_notification(user_id: str, title: str, message: str, link: str = None, notif_type: str = "info"):
    notification = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "title": title,
        "message": message,
        "link": link,
        "type": notif_type,
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    return notification


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


# Include router
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
