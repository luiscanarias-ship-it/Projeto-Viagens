"""
Payment routes — Phase 1 (read-only) + Phase 2 (validation) + Phase 3 (integrations) + Admin.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timezone
from collections import defaultdict
import uuid
import os
import asyncio
import stripe
import httpx

from config import (
    db, logger,
    FIXED_CONTRIBUTION_AMOUNTS, PAYMENT_METHODS, CRYPTO_TYPES,
    TIP_OPTIONS, DEFAULT_TIP_AMOUNT,
    PAYPAL_CLIENT_ID, PAYPAL_MODE, PAYPAL_API_URL,
    ADMIN_EMAIL
)
from models import generate_payment_reference
from auth import get_current_user, require_auth, require_admin
from email_service import (
    get_email_base_template, send_email_resend,
    send_contribution_email, send_contribution_pending_email,
    send_contribution_confirmed_email, send_referral_contribution_emails,
    send_ambassador_unlocked_email, send_tip_thank_you_email
)
from services.notification_service import create_notification
from services.journey_service import (
    check_and_update_journey_funding_status,
    check_and_update_story_chapter
)
from services.payment_service import (
    apply_revenue_distribution,
    get_paypal_access_token,
    generate_points_for_user
)
from services.referral_service import recalculate_ambassador_status
from services.audit_service import log_admin_action

router = APIRouter()


# ==================== PHASE 1: READ-ONLY ENDPOINTS ====================

@router.get("/contributions/config")
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


@router.get("/contributions/payment-info")
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


@router.get("/stripe/config")
async def get_stripe_config():
    """Get Stripe publishable key for frontend"""
    publishable_key = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    return {"publishable_key": publishable_key}


@router.get("/paypal/config")
async def get_paypal_config():
    """Get PayPal client ID for frontend SDK"""
    return {"client_id": PAYPAL_CLIENT_ID, "mode": PAYPAL_MODE}


@router.get("/contributions/checkout-status/{session_id}")
async def get_checkout_status(session_id: str, request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout

    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)

    status = await stripe_checkout.get_checkout_status(session_id)

    if status.payment_status == "paid":
        existing = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        if existing and existing.get("payment_status") != "completed":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "completed", "updated_at": datetime.now(timezone.utc).isoformat()}}
            )

            contribution = await db.contributions.find_one({"session_id": session_id}, {"_id": 0})
            if contribution:
                points_count = int(contribution["amount"] / 5)

                await db.contributions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "completed", "points_count": points_count}}
                )

                await db.journeys.update_one(
                    {"journey_id": contribution["journey_id"]},
                    {"$inc": {"current_amount": contribution["amount"]}}
                )

                if contribution.get("user_id"):
                    await generate_points_for_user(
                        contribution["user_id"], contribution["journey_id"],
                        contribution["contribution_id"], points_count, contribution.get("is_crypto", False)
                    )

    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }


@router.get("/contributions/my-contributions")
async def get_my_contributions(request: Request):
    """Get all contributions for the authenticated user"""
    user = await require_auth(request)
    contributions = await db.contributions.find(
        {"user_id": user.user_id, "status": "completed"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)

    total_amount = sum(c.get("amount", 0) for c in contributions)
    total_count = len(contributions)
    last_contribution = contributions[0] if contributions else None

    return {
        "contributions": contributions,
        "total_amount": total_amount,
        "total_count": total_count,
        "last_contribution": last_contribution
    }


@router.get("/ambassador/pending-validations")
async def get_ambassador_pending_validations(request: Request):
    """Get contributions awaiting validation by this ambassador"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")

    journey_ids = await db.journeys.distinct("journey_id", {
        "ambassador_user_id": user.user_id,
        "is_active": True
    })

    contributions = await db.contributions.find(
        {
            "journey_id": {"$in": journey_ids},
            "status": "awaiting_validation"
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)

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


# ==================== PHASE 2: VALIDATION / STATE TRANSITIONS ====================

@router.post("/contributions/create")
async def create_contribution(request: Request):
    """Create a new contribution with payment reference for external payments"""
    data = await request.json()
    support_amount = data.get("support_amount")
    tip_amount = data.get("tip_amount", 0)
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    journey_id = data.get("journey_id")
    sponsor_code = data.get("sponsor_code")
    contributor_name = data.get("contributor_name")
    contributor_email = data.get("contributor_email")

    if support_amount is None:
        support_amount = amount
        tip_amount = 0

    total_amount = support_amount + tip_amount

    if support_amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(
            status_code=400,
            detail=f"Montante inválido. Valores permitidos: {FIXED_CONTRIBUTION_AMOUNTS}"
        )

    valid_tip_values = [opt["value"] for opt in TIP_OPTIONS]
    if tip_amount not in valid_tip_values:
        raise HTTPException(
            status_code=400,
            detail=f"Valor de contribuição para a plataforma inválido. Valores permitidos: {valid_tip_values}"
        )

    valid_methods = ["crypto", "paypal", "mbway"]
    if payment_method not in valid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Método de pagamento inválido. Métodos permitidos: {valid_methods}"
        )

    journey = await db.journeys.find_one({"journey_id": journey_id, "is_active": True}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada ou inativa")

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

    payment_reference = generate_payment_reference()
    while await db.contributions.find_one({"payment_reference": payment_reference}):
        payment_reference = generate_payment_reference()

    contribution_doc = {
        "contribution_id": contribution_id,
        "journey_id": journey_id,
        "user_id": user_id,
        "amount": total_amount,
        "support_amount": support_amount,
        "tip_amount": tip_amount,
        "currency": "EUR",
        "payment_method": payment_method,
        "crypto_type": crypto_type if payment_method == "crypto" else None,
        "payment_reference": payment_reference,
        "status": "pending",
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


@router.post("/contributions/manual")
async def record_manual_contribution(request: Request):
    data = await request.json()
    journey_id = data.get("journey_id")
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    is_crypto = data.get("is_crypto", False)
    sponsor_code = data.get("sponsor_code")
    name = data.get("name")
    surname = data.get("surname")
    email = data.get("email")

    if amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(status_code=400, detail=f"Montante inválido. Valores permitidos: {FIXED_CONTRIBUTION_AMOUNTS}")

    user = await get_current_user(request)

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


@router.put("/contributions/{contribution_id}/confirm-details")
async def confirm_contribution_details(contribution_id: str, request: Request):
    """User confirms they made the payment and optionally provides name/email"""
    body = await request.json()
    contributor_name = body.get("contributor_name")
    contributor_email = body.get("contributor_email")
    proof_image_url = body.get("proof_image_url")

    if not contributor_email:
        raise HTTPException(status_code=400, detail="Email é obrigatório")

    contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")

    journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
    is_direct = journey and journey.get("payment_mode") == "direct"

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

    updated_contribution = {**contribution, **update_fields}
    if journey:
        try:
            await send_contribution_pending_email(updated_contribution, journey)
        except Exception as e:
            logger.error(f"Failed to send pending email: {e}")

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


@router.put("/contributions/{contribution_id}/ambassador-validate")
async def ambassador_validate_contribution(contribution_id: str, request: Request):
    """Ambassador confirms or rejects a direct payment contribution"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Autenticação necessária")

    body = await request.json()
    action = body.get("action")
    notes = body.get("notes", "")

    if action not in ("confirm", "reject"):
        raise HTTPException(status_code=400, detail="Ação inválida. Use 'confirm' ou 'reject'")

    contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")

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

        await db.journeys.update_one(
            {"journey_id": contribution["journey_id"]},
            {"$inc": {"current_amount": support_amount}}
        )

        await apply_revenue_distribution(contribution_id)

        contributor_id = contribution.get("user_id")
        if contributor_id:
            await db.users.update_one(
                {"user_id": contributor_id},
                {"$inc": {"total_contributed": contribution.get("amount", 0)}}
            )
            if journey.get("is_main_trip"):
                await db.users.update_one(
                    {"user_id": contributor_id},
                    {"$set": {"contributed_to_main_trip": True}}
                )
            await recalculate_ambassador_status(contributor_id)

        await check_and_update_journey_funding_status(contribution["journey_id"])
        await check_and_update_story_chapter(contribution["journey_id"])

        if contribution.get("contributor_email"):
            asyncio.create_task(create_notification(
                contributor_id or "anonymous", "payment_confirmed",
                f"A tua contribuição de {support_amount}€ foi confirmada pelo Embaixador.",
                {"contribution_id": contribution_id}
            ))
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

        contributor_id = contribution.get("user_id")
        asyncio.create_task(create_notification(
            contributor_id or "anonymous", "payment_rejected",
            f"O Embaixador não conseguiu confirmar a tua contribuição. Razão: {notes or 'Pagamento não recebido'}",
            {"contribution_id": contribution_id}
        ))

        return {"status": "rejected", "message": "Contribuição marcada como não recebida"}


# ==================== PHASE 3: INTEGRATIONS (PayPal, Stripe) ====================

@router.post("/paypal/create-order")
async def paypal_create_order(request: Request):
    """Create a PayPal order for a contribution with optional platform tip"""
    data = await request.json()
    support_amount = data.get("support_amount")
    tip_amount = data.get("tip_amount", 0)
    amount = data.get("amount")
    journey_id = data.get("journey_id")

    if support_amount is None:
        support_amount = amount
        tip_amount = 0

    total_amount = support_amount + tip_amount

    if support_amount not in FIXED_CONTRIBUTION_AMOUNTS:
        raise HTTPException(status_code=400, detail=f"Montante invalido: {FIXED_CONTRIBUTION_AMOUNTS}")

    valid_tip_values = [opt["value"] for opt in TIP_OPTIONS]
    if tip_amount not in valid_tip_values:
        raise HTTPException(status_code=400, detail="Valor de contribuição para a plataforma inválido")

    journey = await db.journeys.find_one({"journey_id": journey_id, "is_active": True}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem nao encontrada ou inativa")

    user = await get_current_user(request)
    user_id = user.user_id if user else None
    contributor_name = data.get("contributor_name") or (user.name if user else None)
    contributor_email = data.get("contributor_email") or (user.email if user else None)
    sponsor_code = data.get("sponsor_code")

    contribution_id = f"contrib_{uuid.uuid4().hex[:12]}"
    payment_reference = generate_payment_reference()
    while await db.contributions.find_one({"payment_reference": payment_reference}):
        payment_reference = generate_payment_reference()

    access_token = await get_paypal_access_token()

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

    contribution_doc = {
        "contribution_id": contribution_id,
        "journey_id": journey_id,
        "user_id": user_id,
        "amount": total_amount,
        "support_amount": support_amount,
        "tip_amount": tip_amount,
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


@router.post("/paypal/capture-order/{order_id}")
async def paypal_capture_order(order_id: str, request: Request):
    """Capture a PayPal order after user approval — marks contribution as completed"""
    contribution = await db.contributions.find_one(
        {"paypal_order_id": order_id},
        {"_id": 0}
    )
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuicao nao encontrada")

    if contribution["status"] in ("completed", "confirmed"):
        return {
            "status": "ALREADY_CAPTURED",
            "contribution_id": contribution["contribution_id"],
            "message": "Pagamento ja confirmado"
        }

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

    distribution = await apply_revenue_distribution(contribution_id)

    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$inc": {"current_amount": support_amount}}
    )

    if user_id:
        await db.users.update_one(
            {"user_id": user_id},
            {"$inc": {"total_contributed": amount}}
        )

    await check_and_update_journey_funding_status(journey_id)
    await check_and_update_story_chapter(journey_id)

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
                await recalculate_ambassador_status(user_id)

            if user_doc.get("sponsor_id"):
                await recalculate_ambassador_status(user_doc["sponsor_id"])

        journey_name = (await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0, "name": 1})) or {}
        await create_notification(
            user_id,
            "contribution",
            f"A tua contribuicao de {amount}EUR para {journey_name.get('name', 'esta viagem')} foi confirmada automaticamente.",
            {"journey_id": journey_id, "amount": amount}
        )

    journey_doc = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    updated_contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if journey_doc and updated_contribution:
        asyncio.create_task(send_contribution_email(updated_contribution, journey_doc))
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


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events for PaymentIntent"""
    api_key = os.environ.get("STRIPE_API_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    stripe.api_key = api_key

    body = await request.body()
    signature = request.headers.get("Stripe-Signature")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        else:
            import json
            event = stripe.Event.construct_from(json.loads(body), stripe.api_key)

        logger.info(f"Stripe webhook received: {event.type}")

        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            payment_intent_id = payment_intent.id

            logger.info(f"PaymentIntent succeeded: {payment_intent_id}")

            contribution = await db.contributions.find_one(
                {"payment_intent_id": payment_intent_id},
                {"_id": 0}
            )

            if contribution:
                contribution_id = contribution["contribution_id"]
                journey_id = contribution["journey_id"]
                amount = contribution["amount"]
                user_id = contribution.get("user_id")

                await db.contributions.update_one(
                    {"contribution_id": contribution_id},
                    {"$set": {
                        "status": "confirmed",
                        "validated_at": datetime.now(timezone.utc).isoformat(),
                        "validated_by": "stripe_webhook"
                    }}
                )

                await db.journeys.update_one(
                    {"journey_id": journey_id},
                    {"$inc": {"current_amount": amount}}
                )

                if user_id:
                    await db.users.update_one(
                        {"user_id": user_id},
                        {"$inc": {"total_contributed": amount}}
                    )

                await check_and_update_journey_funding_status(journey_id)
                await check_and_update_story_chapter(journey_id)

                if user_id:
                    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
                    if journey and journey.get("is_main_trip"):
                        await db.users.update_one(
                            {"user_id": user_id},
                            {"$set": {"contributed_to_main_trip": True}}
                        )

                    await recalculate_ambassador_status(user_id)
                    contributor_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "sponsor_id": 1})
                    if contributor_doc and contributor_doc.get("sponsor_id"):
                        await recalculate_ambassador_status(contributor_doc["sponsor_id"])

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


# ==================== ADMIN CONTRIBUTION MANAGEMENT ====================

@router.get("/admin/contributions/search")
async def search_contributions_by_reference(request: Request, ref: str = None):
    """Search contributions by payment reference"""
    await require_admin(request)

    if not ref:
        raise HTTPException(status_code=400, detail="Parâmetro 'ref' é obrigatório")

    query = {"payment_reference": {"$regex": ref.upper(), "$options": "i"}}
    contributions = await db.contributions.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)

    for contrib in contributions:
        if contrib.get("user_id"):
            u = await db.users.find_one({"user_id": contrib["user_id"]}, {"_id": 0, "name": 1, "email": 1})
            contrib["user_name"] = u.get("name") if u else "Desconhecido"
            contrib["user_email"] = u.get("email") if u else ""
        else:
            contrib["user_name"] = contrib.get("contributor_name") or "Anónimo"
            contrib["user_email"] = contrib.get("contributor_email") or ""

        j = await db.journeys.find_one({"journey_id": contrib["journey_id"]}, {"_id": 0, "name": 1})
        contrib["journey_name"] = j.get("name") if j else "Desconhecida"

    return {"count": len(contributions), "contributions": contributions}


@router.get("/admin/contributions")
async def get_all_contributions(request: Request):
    """Get all contributions for admin management"""
    await require_admin(request)
    contributions = await db.contributions.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)

    for contrib in contributions:
        if contrib.get("user_id"):
            u = await db.users.find_one({"user_id": contrib["user_id"]}, {"_id": 0, "name": 1, "email": 1})
            contrib["user_name"] = u.get("name") if u else "Desconhecido"
            contrib["user_email"] = u.get("email") if u else ""
        else:
            contrib["user_name"] = contrib.get("contributor_name") or "Anónimo"
            contrib["user_email"] = contrib.get("contributor_email") or ""

        j = await db.journeys.find_one({"journey_id": contrib["journey_id"]}, {"_id": 0, "name": 1})
        contrib["journey_name"] = j.get("name") if j else "Desconhecida"

        if not contrib.get("payment_reference"):
            contrib["payment_reference"] = None

    return contributions


@router.put("/admin/contributions/{contribution_id}/confirm")
async def confirm_contribution(contribution_id: str, request: Request):
    """Confirm a manual payment contribution"""
    await require_admin(request)

    contribution = await db.contributions.find_one({"contribution_id": contribution_id}, {"_id": 0})
    if not contribution:
        raise HTTPException(status_code=404, detail="Contribuição não encontrada")

    if contribution["status"] == "completed":
        return {"message": "Contribuição já confirmada"}

    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "status": "completed",
            "confirmed": True,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    await db.journeys.update_one(
        {"journey_id": contribution["journey_id"]},
        {"$inc": {"current_amount": contribution["amount"]}}
    )

    if contribution.get("user_id"):
        await db.users.update_one(
            {"user_id": contribution["user_id"]},
            {"$inc": {"total_contributed": contribution["amount"]}}
        )

    await check_and_update_journey_funding_status(contribution["journey_id"])
    await check_and_update_story_chapter(contribution["journey_id"])

    if contribution.get("sponsor_link_id"):
        await db.sponsor_links.update_one(
            {"link_id": contribution["sponsor_link_id"]},
            {"$inc": {"successful_referrals": 1}}
        )

    # MOTOR EMBAIXADOR v2
    if contribution.get("user_id"):
        contributing_user = await db.users.find_one({"user_id": contribution["user_id"]}, {"_id": 0})

        main_journey = await db.journeys.find_one(
            {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]},
            {"_id": 0}
        )
        is_main_trip = main_journey and contribution["journey_id"] == main_journey.get("journey_id")

        if is_main_trip and contributing_user:
            await db.users.update_one(
                {"user_id": contribution["user_id"]},
                {"$set": {"contributed_to_main_trip": True}}
            )

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
                await send_ambassador_unlocked_email(contribution["user_id"])

        if contributing_user and contributing_user.get("sponsor_id"):
            sponsor_user_id = contributing_user["sponsor_id"]

            await db.users.update_one(
                {"user_id": sponsor_user_id},
                {"$inc": {"valid_referrals_count": 1}}
            )

            sponsor = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0})
            if sponsor:
                valid_refs = sponsor.get("valid_referrals_count", 0)
                contributed = sponsor.get("contributed_to_main_trip", False)
                current_level = sponsor.get("level", "sonhador")

                was_already_ambassador = current_level == "embaixador"
                if contributed and valid_refs >= 3 and not was_already_ambassador:
                    await db.users.update_one(
                        {"user_id": sponsor_user_id},
                        {"$set": {
                            "level": "embaixador",
                            "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    await send_ambassador_unlocked_email(sponsor_user_id)

                journey_for_email = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
                if journey_for_email:
                    sponsor_updated = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0})
                    await send_referral_contribution_emails(
                        contribution=contribution,
                        journey=journey_for_email,
                        contributor_user=contributing_user,
                        sponsor_user=sponsor_updated
                    )

    if contribution.get("user_id"):
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

    journey = await db.journeys.find_one({"journey_id": contribution["journey_id"]}, {"_id": 0})
    if journey:
        await send_contribution_email(contribution, journey)

    await log_admin_action(
        (await get_current_user(request)).user_id if await get_current_user(request) else "system",
        "contribution_confirmed", "contribution", contribution_id, {"amount": contribution.get("amount")}
    )

    return {"message": "Contribuição confirmada com sucesso"}


@router.put("/admin/contributions/{contribution_id}/reject")
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

    await log_admin_action(admin.user_id, "contribution_rejected", "contribution", contribution_id, {})

    return {"message": "Contribuição rejeitada"}


@router.get("/admin/contributions/reports")
async def get_contribution_reports(request: Request):
    """Get comprehensive contribution reports for admin"""
    await require_admin(request)

    all_contributions = await db.contributions.find(
        {"status": "confirmed"},
        {"_id": 0}
    ).to_list(10000)

    completed_contributions = await db.contributions.find(
        {"status": "completed"},
        {"_id": 0}
    ).to_list(10000)

    contributions = all_contributions + completed_contributions

    by_amount = {}
    for c in contributions:
        amt = c.get("amount", 0)
        if amt not in by_amount:
            by_amount[amt] = {"count": 0, "total": 0}
        by_amount[amt]["count"] += 1
        by_amount[amt]["total"] += amt

    amount_report = [
        {"amount": amt, "count": data["count"], "total": data["total"]}
        for amt, data in sorted(by_amount.items())
    ]

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

    temporal = defaultdict(lambda: {"count": 0, "total": 0})
    for c in contributions:
        created_at = c.get("created_at", "")
        if isinstance(created_at, str):
            day = created_at[:10]
        else:
            day = created_at.strftime("%Y-%m-%d")
        temporal[day]["count"] += 1
        temporal[day]["total"] += c.get("amount", 0)

    temporal_report = [
        {"date": day, "count": data["count"], "total": data["total"]}
        for day, data in sorted(temporal.items(), reverse=True)[:30]
    ]

    total_amount = sum(c.get("amount", 0) for c in contributions)
    total_count = len(contributions)
    avg_contribution = total_amount / total_count if total_count > 0 else 0

    pending = await db.contributions.find({"status": "pending"}, {"_id": 0}).to_list(1000)
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


@router.get("/admin/contributions/pending")
async def get_pending_contributions(request: Request):
    """Get all pending contributions that need admin validation"""
    await require_admin(request)

    pending = await db.contributions.find(
        {"status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)

    for contrib in pending:
        if contrib.get("user_id"):
            u = await db.users.find_one(
                {"user_id": contrib["user_id"]},
                {"_id": 0, "name": 1, "email": 1}
            )
            contrib["user_name"] = u.get("name") if u else contrib.get("contributor_name", "Desconhecido")
            contrib["user_email"] = u.get("email") if u else contrib.get("contributor_email", "")
        else:
            contrib["user_name"] = contrib.get("contributor_name", "Anónimo")
            contrib["user_email"] = contrib.get("contributor_email", "")

        j = await db.journeys.find_one(
            {"journey_id": contrib["journey_id"]},
            {"_id": 0, "name": 1}
        )
        contrib["journey_name"] = j.get("name") if j else "Desconhecida"

    return {"count": len(pending), "contributions": pending}


@router.put("/admin/contributions/{contribution_id}/validate")
async def validate_contribution(contribution_id: str, request: Request):
    """Validate (confirm or reject) a contribution with notes"""
    admin = await require_admin(request)
    data = await request.json()

    action = data.get("action")
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

    if action == "confirm":
        await db.journeys.update_one(
            {"journey_id": contribution["journey_id"]},
            {"$inc": {"current_amount": contribution["amount"]}}
        )

        if contribution.get("user_id"):
            await db.users.update_one(
                {"user_id": contribution["user_id"]},
                {"$inc": {"total_contributed": contribution["amount"]}}
            )

        await check_and_update_journey_funding_status(contribution["journey_id"])
        await check_and_update_story_chapter(contribution["journey_id"])

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

                    valid_refs = user.get("valid_referrals_count", 0)
                    if valid_refs >= 3 and user.get("level") != "embaixador":
                        await db.users.update_one(
                            {"user_id": contribution["user_id"]},
                            {"$set": {
                                "level": "embaixador",
                                "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )

                if user.get("sponsor_id"):
                    sponsor_id = user["sponsor_id"]
                    await db.users.update_one(
                        {"user_id": sponsor_id},
                        {"$inc": {"valid_referrals_count": 1}}
                    )

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


# ==================== ADMIN PAYOUTS ====================

@router.get("/admin/payouts")
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


@router.put("/admin/payouts/{payout_id}/status")
async def update_payout_status(payout_id: str, request: Request):
    """Update payout status (pending -> processing -> completed)"""
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
