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
from services.notification_service import create_notification
from services.journey_service import (
    check_and_update_journey_funding_status,
    check_and_update_story_chapter,
    DEFAULT_STORY_CHAPTERS, get_chapter_number,
    _build_chapter_email_body,
    calculate_journey_visibility_score
)
from services.payment_service import (
    apply_revenue_distribution,
    generate_points_for_user
)
from services.referral_service import recalculate_ambassador_status, AMBASSADOR_REQUIRED_REFERRALS
from routes.auth_routes import router as auth_router

app = FastAPI(title="4Luis API")
api_router = APIRouter(prefix="/api")

# Register modular route files
api_router.include_router(auth_router)

from routes.journey_routes import router as journey_router
api_router.include_router(journey_router)

from routes.payment_routes import router as payment_router
api_router.include_router(payment_router)

# Revenue distribution moved to services/payment_service.py
# ==================== ROUTES MOVED TO routes/ ====================
# Auth: routes/auth_routes.py
# Journeys (read-only, CRUD, states, visibility, ambassador, raffle, seed): routes/journey_routes.py

# Contributions & Payments moved to routes/payment_routes.py

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

# recalculate_ambassador_status moved to services/referral_service.py

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


# payment-info and success-stories moved to routes/journey_routes.py


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

# generate_points_for_user moved to services/payment_service.py

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

# my-contributions moved to routes/payment_routes.py

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

# Admin contributions management moved to routes/payment_routes.py

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

# ==================== AMBASSADOR JOURNEYS (moved to routes/journey_routes.py + services/journey_service.py) ====================

# ==================== PAYOUT ENDPOINTS ====================

# Admin payouts moved to routes/payment_routes.py

# approve-funding, chapter functions, test-chapter-email moved to routes/journey_routes.py + services/journey_service.py

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

# Ambassador journeys, visibility, raffle moved to routes/journey_routes.py

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


# ==================== SEED DATA (moved to routes/journey_routes.py) ====================
# ==================== HOMEPAGE ENDPOINTS (moved to routes/journey_routes.py) ====================


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
# migrate-journey-status, set-main-journey moved to routes/journey_routes.py

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
