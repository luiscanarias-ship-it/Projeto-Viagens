"""
Ambassador routes — sponsor links, progression, certification, trust indicators, public profiles.
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
import uuid
import asyncio

from config import (
    db, logger, CERTIFICATION_LEVELS,
    TRUSTED_AMBASSADOR_MIN_SUPPORTERS, TRUSTED_AMBASSADOR_MIN_RAISED
)
from models import SponsorLink
from auth import get_current_user, require_auth, require_admin
from services.notification_service import create_notification
from services.referral_service import AMBASSADOR_REQUIRED_REFERRALS
from services.audit_service import log_admin_action

router = APIRouter()


# ==================== SPONSOR LINKS ====================

@router.post("/sponsor-links/create")
async def create_sponsor_link(request: Request):
    user = await require_auth(request)
    data = await request.json()
    journey_id = data.get("journey_id")

    existing = await db.sponsor_links.find_one(
        {"user_id": user.user_id, "journey_id": journey_id}, {"_id": 0}
    )
    if existing:
        return existing

    link = SponsorLink(user_id=user.user_id, journey_id=journey_id)
    doc = link.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.sponsor_links.insert_one(doc)
    return {
        "link_id": doc["link_id"],
        "user_id": doc["user_id"],
        "journey_id": doc["journey_id"],
        "referral_count": doc["referral_count"],
        "successful_referrals": doc["successful_referrals"],
        "created_at": doc["created_at"]
    }


@router.get("/sponsor-links/my-links")
async def get_my_sponsor_links(request: Request):
    user = await require_auth(request)
    links = await db.sponsor_links.find({"user_id": user.user_id}, {"_id": 0}).to_list(100)
    return links


@router.get("/sponsor-links/{link_id}")
async def get_sponsor_link(link_id: str):
    link = await db.sponsor_links.find_one({"link_id": link_id}, {"_id": 0})
    if not link:
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return link


@router.post("/sponsor-links/{link_id}/track")
async def track_sponsor_referral(link_id: str):
    result = await db.sponsor_links.update_one(
        {"link_id": link_id},
        {"$inc": {"referral_count": 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return {"message": "Referência registada"}


# ==================== AMBASSADOR SYSTEM ====================

@router.get("/ambassador/progress")
async def get_ambassador_progress(request: Request):
    """Get user's progress towards ambassador status with referral details."""
    user = await require_auth(request)
    user_id = user.user_id
    user_data = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})

    is_ambassador = user_data.get("level") == "embaixador"

    main_journey = await db.journeys.find_one(
        {"is_main_trip": True, "is_active": True},
        {"_id": 0, "journey_id": 1, "name": 1}
    )
    if not main_journey:
        main_journey = await db.journeys.find_one(
            {"is_active": True, "status": "ativa"},
            {"_id": 0, "journey_id": 1, "name": 1}
        )

    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1, "name": 1, "created_at": 1}
    ).to_list(1000)

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


@router.post("/ambassador/generate-referral")
async def generate_ambassador_referral(request: Request):
    """Generate a unique referral link for ambassador progression."""
    user = await require_auth(request)
    user_id = user.user_id

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

    existing = await db.sponsor_links.find_one(
        {"user_id": user_id, "journey_id": main_journey["journey_id"]},
        {"_id": 0}
    )
    if existing:
        return {"referral_code": existing["link_id"], "journey_id": main_journey["journey_id"]}

    link = SponsorLink(user_id=user_id, journey_id=main_journey["journey_id"])
    doc = link.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.sponsor_links.insert_one(doc)

    return {"referral_code": doc["link_id"], "journey_id": main_journey["journey_id"]}


@router.get("/ambassador/features")
async def get_ambassador_features(request: Request):
    """Check which premium features are available."""
    user = await get_current_user(request)
    if not user:
        return {
            "is_ambassador": False,
            "features": {
                "smart_map": False, "secret_tips": False,
                "enhanced_ctas": False, "ai_assistant": False, "premium_guide": False,
            }
        }
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    is_amb = user_data.get("level") == "embaixador" if user_data else False
    return {
        "is_ambassador": is_amb,
        "features": {
            "smart_map": is_amb, "secret_tips": is_amb,
            "enhanced_ctas": is_amb, "ai_assistant": is_amb, "premium_guide": is_amb,
        }
    }


# ==================== AMBASSADOR CERTIFICATION ====================

@router.get("/ambassador/{user_id}/profile")
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


@router.put("/admin/ambassador/{user_id}/certification")
async def update_ambassador_certification(user_id: str, request: Request):
    """Admin: Update ambassador certification level"""
    admin = await require_admin(request)
    data = await request.json()
    new_level = data.get("certification_level")

    if new_level not in CERTIFICATION_LEVELS:
        raise HTTPException(status_code=400, detail=f"Nível inválido. Opções: {list(CERTIFICATION_LEVELS.keys())}")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user or user.get("level") != "embaixador":
        raise HTTPException(status_code=404, detail="Embaixador não encontrado")

    old_level = user.get("certification_level", "embaixador")
    update = {
        "certification_level": new_level,
        "certification_updated_at": datetime.now(timezone.utc).isoformat()
    }
    if new_level in ("verificado", "confiavel"):
        update["certification_verified_at"] = datetime.now(timezone.utc).isoformat()

    await db.users.update_one({"user_id": user_id}, {"$set": update})

    label = CERTIFICATION_LEVELS[new_level]["label"]
    asyncio.create_task(create_notification(
        user_id, "certification_updated",
        f"O teu nível de certificação foi atualizado para: {label}",
        {"certification_level": new_level}
    ))

    await log_admin_action(admin.user_id, "certification_changed", "user", user_id, {
        "old_level": old_level, "new_level": new_level
    })

    return {"message": f"Certificação atualizada para {label}", "certification_level": new_level}


@router.post("/ambassador/report")
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


@router.get("/ambassador/{user_id}/trust-indicators")
async def get_ambassador_trust_indicators(user_id: str):
    """Get trust indicators for an ambassador"""
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

    pipeline = [
        {"$match": {"journey_id": {"$in": journey_ids}, "status": {"$in": ["confirmed", "completed"]}}},
        {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$support_amount", "$amount"]}}}}
    ]
    result = await db.contributions.aggregate(pipeline).to_list(1)
    total_raised = result[0]["total"] if result else 0

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
            {"$project": {"user_confirmed": "$confirmed_by_user_at", "validated": "$validated_at"}}
        ]
        time_docs = await db.contributions.aggregate(time_pipeline).to_list(200)

        deltas = []
        for doc in time_docs:
            try:
                t1 = datetime.fromisoformat(doc["user_confirmed"].replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(doc["validated"].replace("Z", "+00:00"))
                delta_hours = (t2 - t1).total_seconds() / 3600
                if 0 < delta_hours < 168:
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


# ==================== PUBLIC AMBASSADOR PROFILE ====================

@router.get("/ambassador/{user_id}/public-profile")
async def get_ambassador_public_profile(user_id: str):
    """Get public profile of an ambassador"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0, "email": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    is_ambassador = user.get("level") == "embaixador"
    use_real_name = user.get("use_real_name", True)
    if use_real_name:
        display_name = user.get("name", "Sonhador")
        display_avatar = user.get("avatar") or f"https://api.dicebear.com/7.x/initials/svg?seed={user.get('name', 'S')}"
    else:
        display_name = user.get("anonymous_alias") or user.get("alias") or "Sonhador Anónimo"
        display_avatar = user.get("anonymous_avatar") or f"https://api.dicebear.com/7.x/shapes/svg?seed={user_id}"

    identity = {
        "display_name": display_name, "avatar": display_avatar,
        "level": user.get("level", "sonhador"), "is_ambassador": is_ambassador,
        "certification_level": user.get("certification_level", "embaixador") if is_ambassador else None,
        "certification_label": CERTIFICATION_LEVELS.get(user.get("certification_level", "embaixador"), {}).get("label") if is_ambassador else None,
        "country": user.get("country"), "bio": user.get("bio"),
        "member_since": user.get("created_at"),
        "embaixador_unlocked_at": user.get("embaixador_unlocked_at")
    }

    current_journey = None
    if is_ambassador:
        journey = await db.journeys.find_one(
            {"ambassador_user_id": user_id, "status": {"$in": ["ativa", "aprovada", "candidatura"]}},
            {"_id": 0, "goal_amount": 0, "admin_notes": 0}
        )
        if journey:
            full_journey = await db.journeys.find_one({"journey_id": journey["journey_id"]}, {"_id": 0})
            goal = full_journey.get("goal_amount", 1) if full_journey else 1
            current = journey.get("current_amount", 0)
            percentage = round((current / goal) * 100, 1) if goal > 0 else 0
            current_journey = {
                "journey_id": journey.get("journey_id"), "name": journey.get("name"),
                "poetic_name": journey.get("poetic_name"), "description": journey.get("description"),
                "image_url": journey.get("image_url"), "status": journey.get("status"),
                "country": journey.get("country"), "city": journey.get("city"),
                "progress_percentage": percentage, "current_amount": current
            }

    contributions = await db.contributions.find(
        {"user_id": user_id, "status": {"$in": ["confirmed", "completed"]}}, {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    total_contributed = sum(c.get("amount", 0) for c in contributions)

    main_journey = await db.journeys.find_one(
        {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]}, {"_id": 0, "journey_id": 1}
    )
    contributed_to_main = False
    if main_journey:
        mc = await db.contributions.find_one({
            "user_id": user_id, "journey_id": main_journey["journey_id"],
            "status": {"$in": ["confirmed", "completed"]}
        })
        contributed_to_main = mc is not None

    contributions_summary = {
        "total_amount": total_contributed, "total_count": len(contributions),
        "contributed_to_main_journey": contributed_to_main,
        "has_crypto_contributions": any(c.get("payment_method") == "crypto" for c in contributions)
    }

    invited_users = await db.users.find({"sponsor_id": user_id}, {"_id": 0, "user_id": 1}).to_list(1000)
    invited_user_ids = [u["user_id"] for u in invited_users]
    contributions_from_invites = 0
    amount_from_invites = 0
    if invited_user_ids:
        invite_contribs = await db.contributions.find(
            {"user_id": {"$in": invited_user_ids}, "status": {"$in": ["confirmed", "completed"]}}, {"_id": 0}
        ).to_list(1000)
        contributions_from_invites = len(invite_contribs)
        amount_from_invites = sum(c.get("amount", 0) for c in invite_contribs)

    social_impact = {
        "people_invited": len(invited_users), "valid_referrals": user.get("valid_referrals_count", 0),
        "contributions_generated": contributions_from_invites, "amount_generated": amount_from_invites
    }

    realized_journeys = []
    if is_ambassador:
        past = await db.journeys.find(
            {"ambassador_user_id": user_id, "status": {"$in": ["financiada", "realizada", "encerrada"]}},
            {"_id": 0, "goal_amount": 0, "admin_notes": 0}
        ).sort("funded_at", -1).to_list(50)
        for j in past:
            realized_journeys.append({
                "journey_id": j.get("journey_id"), "name": j.get("name"),
                "image_url": j.get("image_url"), "country": j.get("country"),
                "status": j.get("status"), "story": j.get("story"),
                "photos": j.get("photos", []), "funded_at": j.get("funded_at"),
                "realized_at": j.get("realized_at")
            })

    return {
        "identity": identity, "current_journey": current_journey,
        "contributions": contributions_summary, "social_impact": social_impact,
        "realized_journeys": realized_journeys, "testimonials": []
    }
