"""
Journey routes — Phase 1 (read-only) + Phase 2 (CRUD) + Phase 3 (states/visibility/ambassador).
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import random
import logging
import resend

from config import (
    db, logger, CERTIFICATION_LEVELS,
    JOURNEY_STATUSES, FRONTEND_URL,
    RESEND_API_KEY, SENDER_EMAIL
)
from models import Journey, JourneyCreate, JourneyUpdate
from auth import get_current_user, require_admin, require_auth
from email_service import (
    get_email_base_template, send_email_resend,
    send_journey_funded_emails
)
from services.journey_service import (
    DEFAULT_STORY_CHAPTERS, get_chapter_number,
    _build_chapter_email_body,
    calculate_journey_visibility_score
)
from services.audit_service import log_admin_action

router = APIRouter()


# ==================== PUBLIC JOURNEY ENDPOINTS ====================

@router.get("/journeys", response_model=List[dict])
async def get_journeys():
    journeys = await db.journeys.find({"is_active": True}, {"_id": 0}).to_list(100)
    return journeys


@router.get("/journeys/featured")
async def get_featured_journeys():
    journeys = await db.journeys.find(
        {"is_active": True, "is_featured": True},
        {"_id": 0}
    ).sort("featured_order", 1).to_list(20)
    return journeys


@router.get("/journeys/realized")
async def get_realized_journeys():
    journeys = await db.journeys.find(
        {"status": {"$in": ["financiada", "realizada"]}},
        {"_id": 0}
    ).sort("funded_at", -1).to_list(50)
    return journeys


@router.get("/journeys/active")
async def get_active_journeys():
    journeys = await db.journeys.find(
        {"is_active": True, "status": "ativa"},
        {"_id": 0}
    ).to_list(100)
    return journeys


@router.get("/journeys/{journey_id}")
async def get_journey(journey_id: str):
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    if journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "password_hash": 0, "email": 0}
        )
        if ambassador:
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


@router.get("/journeys/{journey_id}/progress")
async def get_journey_progress(journey_id: str, request: Request):
    """Get journey progress - percentage is public, goal amount is admin-only"""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = (current_amount / goal_amount) * 100 if goal_amount > 0 else 0
    is_funded = percentage >= 100
    
    is_admin = False
    try:
        user = await get_current_user(request)
        if user:
            user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
            is_admin = user_data.get("is_admin", False) if user_data else False
    except:
        pass
    
    journey_contributor_count = len(await db.contributions.distinct("contributor_email", {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}}))
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
    
    if is_admin:
        response["goal_amount"] = goal_amount
    
    return response


@router.get("/journeys/{journey_id}/contributions")
async def get_journey_contributions(journey_id: str):
    contributions = await db.contributions.find(
        {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    public = []
    for c in contributions:
        if c.get("show_name", True) and c.get("contributor_name"):
            display_name = c["contributor_name"]
        else:
            display_name = "Sonhador Anónimo"
        public.append({
            "display_name": display_name,
            "amount": c.get("amount"),
            "message": c.get("public_message"),
            "is_crypto": c.get("payment_method") == "crypto",
            "crypto_type": c.get("crypto_type") if c.get("payment_method") == "crypto" else None,
            "created_at": c.get("created_at")
        })
    
    return {"contributions": public, "total": len(public)}


@router.get("/journey/{journey_id}/payment-info")
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


@router.get("/success-stories")
async def get_success_stories():
    """Get funded journeys for social proof."""
    journeys = await db.journeys.find(
        {"status": {"$in": ["financiada", "realizada"]}, "funding_status": "completed"},
        {"_id": 0, "journey_id": 1, "name": 1, "poetic_name": 1, "image_url": 1,
         "ambassador_name": 1, "ambassador_user_id": 1, "current_amount": 1, "goal_amount": 1,
         "status": 1, "is_main_trip": 1, "is_ambassador_journey": 1,
         "completed_contributor_count": 1, "created_at": 1, "approved_at": 1}
    ).sort("approved_at", -1).limit(6).to_list(6)
    
    for j in journeys:
        if not j.get("completed_contributor_count"):
            count = await db.contributions.count_documents({
                "journey_id": j["journey_id"], "status": {"$in": ["confirmed", "completed"]}
            })
            j["contributor_count"] = count
        else:
            j["contributor_count"] = j.pop("completed_contributor_count", 0)
        
        if j.get("ambassador_user_id"):
            amb = await db.users.find_one(
                {"user_id": j["ambassador_user_id"]},
                {"_id": 0, "avatar": 1, "anonymous_avatar": 1, "name": 1, "anonymous_alias": 1, "use_real_name": 1}
            )
            if amb:
                j["ambassador_avatar"] = amb.get("avatar") or amb.get("anonymous_avatar")
                j["ambassador_display_name"] = amb.get("name") if amb.get("use_real_name", True) else amb.get("anonymous_alias", "Embaixador")
    
    return {"stories": journeys}


# ==================== HOMEPAGE ENDPOINTS ====================

@router.get("/homepage/main-journey")
async def get_main_journey_details():
    """Get the main journey with full details for homepage"""
    journey = await db.journeys.find_one(
        {"is_active": True, "$or": [{"is_main_trip": True}, {"status": "ativa"}]},
        {"_id": 0, "admin_notes": 0}
    )
    
    if not journey:
        return {"journey": None, "progress": None, "contributions": [], "updates": []}
    
    journey_id = journey["journey_id"]
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
    if show_goal:
        progress["goal_amount"] = goal_amount
    if not show_goal:
        journey.pop("goal_amount", None)
    
    contributions = await db.contributions.find(
        {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
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
    
    platform_contributor_count = len(await db.contributions.distinct("contributor_email", {"status": {"$in": ["confirmed", "completed"]}}))
    contributor_display_count = platform_contributor_count + 57
    journey_contributor_count = len(await db.contributions.distinct("contributor_email", {"journey_id": journey_id, "status": {"$in": ["confirmed", "completed"]}}))
    
    return {
        "journey": journey,
        "progress": progress,
        "contributions": public_contributions,
        "updates": [],
        "contributor_count": contributor_display_count,
        "journey_contributor_count": journey_contributor_count
    }


@router.get("/homepage/ambassador-journeys")
async def get_active_ambassador_journeys():
    """Get active ambassador journeys for homepage"""
    journeys = await db.journeys.find(
        {
            "is_ambassador_journey": True,
            "status": "ativa",
            "is_active": True,
            "hide_from_listings": {"$ne": True}
        },
        {"_id": 0, "admin_notes": 0, "application_message": 0}
    ).sort("visibility_score", -1).to_list(100)
    
    featured = []
    regular = []
    
    for j in journeys:
        goal = j.get("goal_amount", 1)
        current = j.get("current_amount", 0)
        j["progress_percentage"] = round((current / goal) * 100, 1) if goal > 0 else 0
        show_goal = j.get("show_goal_amount", False)
        j["show_goal_amount"] = show_goal
        if not show_goal:
            j.pop("goal_amount", None)
        
        if j.get("is_featured"):
            featured.append(j)
        else:
            regular.append(j)
    
    featured.sort(key=lambda x: x.get("featured_order", 0))
    
    regions = {
        "europa": {"name": "Europa", "journeys": []},
        "asia": {"name": "Ásia", "journeys": []},
        "africa": {"name": "África", "journeys": []},
        "americas": {"name": "Américas", "journeys": []},
        "oceania": {"name": "Oceânia", "journeys": []},
        "outro": {"name": "Outros", "journeys": []}
    }
    
    for j in regular:
        region = (j.get("region", "outro") or "outro").lower()
        if region not in regions:
            region = "outro"
        regions[region]["journeys"].append(j)
    
    regions_filtered = {k: v for k, v in regions.items() if v["journeys"]}
    
    return {
        "total_count": len(journeys),
        "featured": featured,
        "regions": regions_filtered
    }


@router.get("/homepage/realized-journeys")
async def get_realized_journeys_for_homepage():
    """Get realized journeys for 'Sonhos Realizados' section"""
    journeys = await db.journeys.find(
        {"status": {"$in": ["financiada", "realizada"]}},
        {"_id": 0, "goal_amount": 0, "admin_notes": 0, "application_message": 0}
    ).sort("funded_at", -1).to_list(100)
    
    countries = {}
    for j in journeys:
        country = j.get("country") or j.get("name", "Destino").split(",")[-1].strip() or "Desconhecido"
        if country not in countries:
            countries[country] = {"name": country, "region": j.get("region"), "journeys": []}
        countries[country]["journeys"].append(j)
    
    sorted_countries = dict(sorted(countries.items()))
    return {"total_count": len(journeys), "countries": sorted_countries}


@router.get("/homepage/curated-dreams")
async def get_curated_dreams():
    """Get curated content for Sonhos Realizados section when no real cases exist"""
    real_count = await db.journeys.count_documents({"status": {"$in": ["financiada", "realizada"]}})
    
    if real_count > 0:
        return {"use_curated": False, "curated_dreams": []}
    
    curated_dreams = [
        {
            "id": "curated_1", "name": "Caminho de Santiago", "country": "Espanha", "region": "europa",
            "image_url": "https://images.pexels.com/photos/4080520/pexels-photo-4080520.jpeg?auto=compress&cs=tinysrgb&w=800",
            "story": "Uma peregrinação de autodescoberta pelos caminhos ancestrais da Península Ibérica.", "is_curated": True
        },
        {
            "id": "curated_2", "name": "Montanhas do Nepal", "country": "Nepal", "region": "asia",
            "image_url": "https://images.unsplash.com/photo-1591602333477-618f471b5c01?w=800",
            "story": "Onde o céu encontra a terra, uma jornada de elevação espiritual nos Himalaias.", "is_curated": True
        },
        {
            "id": "curated_3", "name": "Costa Amalfitana", "country": "Itália", "region": "europa",
            "image_url": "https://images.unsplash.com/photo-1529914266944-527632c9ea58?w=800",
            "story": "Cores vibrantes e paisagens deslumbrantes no coração do Mediterrâneo.", "is_curated": True
        },
        {
            "id": "curated_4", "name": "Deserto do Sahara", "country": "Marrocos", "region": "africa",
            "image_url": "https://images.unsplash.com/photo-1769537145747-ff380b863f49?w=800",
            "story": "Noites estreladas e dunas infinitas, uma experiência de silêncio profundo.", "is_curated": True
        }
    ]
    
    return {
        "use_curated": True,
        "curated_dreams": curated_dreams,
        "message": "Estes são sonhos inspiracionais. Sê o primeiro a realizar o teu!"
    }


# ==================== PHASE 2: JOURNEY CRUD (ADMIN) ====================

@router.post("/admin/journeys")
async def create_journey(journey_data: JourneyCreate, request: Request):
    user = await require_admin(request)
    
    journey = Journey(**journey_data.model_dump())
    doc = journey.model_dump()
    doc["owner_user_id"] = user.user_id
    doc["status"] = "ativa"
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.journeys.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/admin/journeys/{journey_id}")
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


@router.delete("/admin/journeys/{journey_id}")
async def delete_journey(journey_id: str, request: Request):
    await require_admin(request)
    result = await db.journeys.delete_one({"journey_id": journey_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    return {"message": "Viagem eliminada com sucesso"}


@router.get("/admin/journeys", response_model=List[dict])
async def get_all_journeys_admin(request: Request):
    await require_admin(request)
    journeys = await db.journeys.find({}, {"_id": 0}).to_list(100)
    
    for j in journeys:
        if j.get("is_ambassador_journey") and j.get("ambassador_user_id"):
            amb = await db.users.find_one({"user_id": j["ambassador_user_id"]}, {"_id": 0, "name": 1})
            j["ambassador_name"] = amb.get("name", "Embaixador") if amb else "Embaixador"
    
    return journeys


# ==================== PHASE 3: JOURNEY STATES & LOGIC ====================

@router.post("/admin/journey/{journey_id}/approve-funding")
async def admin_approve_journey_funding(journey_id: str, request: Request):
    """Admin endpoint to approve main journey funding — moves from pending_validation to completed."""
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
    
    contributor_count = await db.contributions.count_documents({
        "journey_id": journey_id,
        "status": {"$in": ["confirmed", "completed"]}
    })
    
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {
            "funding_status": "completed",
            "status": "realizada",
            "is_active": False,
            "approved_at": now_iso,
            "approved_by": user.user_id,
            "completed_contributor_count": contributor_count,
            "updated_at": now_iso
        }}
    )
    
    current_amount = journey.get("current_amount", 0)
    await send_journey_funded_emails(journey, None, current_amount)

    logger.info(f"Admin {user.user_id} approved funding for journey {journey_id} — marked as realizada")
    await log_admin_action(user.user_id, "journey_funding_approved", "journey", journey_id, {
        "contributor_count": contributor_count, "current_amount": current_amount
    })
    return {"status": "completed", "message": "Viagem fechada com sucesso. Agora aparece na secção 'Sonhos realizados'."}


@router.post("/admin/test-chapter-email/{journey_id}/{chapter_num}")
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
    
    result = await send_email_resend("luis.canarias@gmail.com", subject, html_content)
    
    return {
        "message": f"Email de teste do capítulo {chapter_num} enviado",
        "chapter_title": chapter_title,
        "percentage": percentage,
        "result": result
    }


# ==================== AMBASSADOR JOURNEY ENDPOINTS ====================

@router.post("/ambassador/journey/apply")
async def apply_for_ambassador_journey(request: Request):
    """Submit an application for an ambassador journey"""
    user = await require_auth(request)
    
    user_data = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    if not user_data or user_data.get("level") != "embaixador":
        raise HTTPException(status_code=403, detail="Apenas embaixadores podem candidatar-se a criar viagens")
    
    data = await request.json()
    
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
        "is_active": False,
        "is_main_trip": False,
        "status": "candidatura",
        "is_ambassador_journey": True,
        "ambassador_user_id": user.user_id,
        "ambassador_name": user_data.get("name"),
        "payment_mode": "direct",
        "ambassador_payment_methods": data.get("payment_methods", {}),
        "ambassador_payment_instructions": data.get("payment_instructions"),
        "application_message": data["application_message"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journeys.insert_one(journey_doc)
    
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


@router.get("/ambassador/my-journeys")
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


@router.get("/admin/ambassador-journeys")
async def get_ambassador_journeys(request: Request, status: Optional[str] = None):
    """Get all ambassador journeys - Admin only"""
    await require_admin(request)
    
    query = {"is_ambassador_journey": True}
    if status:
        query["status"] = status
    
    journeys = await db.journeys.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    by_status = {}
    for s in JOURNEY_STATUSES:
        by_status[s] = [j for j in journeys if j.get("status") == s]
    
    return {
        "total": len(journeys),
        "by_status": by_status,
        "journeys": journeys
    }


@router.get("/admin/ambassador-journeys/{journey_id}/details")
async def get_ambassador_journey_details(journey_id: str, request: Request):
    """Get full details of an ambassador journey application including ambassador history - Admin only"""
    await require_admin(request)
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    
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
            contributions = await db.contributions.find(
                {"user_id": journey["ambassador_user_id"], "status": {"$in": ["confirmed", "completed"]}},
                {"_id": 0}
            ).sort("created_at", -1).to_list(50)
            
            ambassador_history["contributions"] = contributions
            ambassador_history["total_contributed"] = sum(c.get("amount", 0) for c in contributions)
            
            referrals = await db.users.find(
                {"sponsor_id": journey["ambassador_user_id"]},
                {"_id": 0, "user_id": 1, "name": 1, "email": 1, "registered_at": 1}
            ).sort("registered_at", -1).to_list(50)
            
            for ref in referrals:
                ref_contributions = await db.contributions.count_documents({
                    "user_id": ref["user_id"],
                    "status": {"$in": ["confirmed", "completed"]}
                })
                ref["has_contributed"] = ref_contributions > 0
            
            ambassador_history["referrals"] = referrals
            ambassador_history["valid_referrals_count"] = ambassador.get("valid_referrals_count", 0)
            
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


@router.put("/admin/ambassador-journeys/{journey_id}/status")
async def update_ambassador_journey_status(journey_id: str, request: Request):
    """Update ambassador journey status - Admin only"""
    admin = await require_admin(request)
    data = await request.json()
    
    new_status = data.get("status")
    admin_notes = data.get("admin_notes")
    adjustment_request = data.get("adjustment_request")
    auto_activate = data.get("auto_activate", True)
    
    if new_status not in JOURNEY_STATUSES:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Estados permitidos: {list(JOURNEY_STATUSES.keys())}")
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
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
    
    if new_status == "aprovada":
        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
        update_data["approved_by"] = admin.user_id
        
        if auto_activate:
            update_data["status"] = "ativa"
            update_data["is_active"] = True
            update_data["activated_at"] = datetime.now(timezone.utc).isoformat()
            update_data["is_featured"] = False
            update_data["visibility_boost"] = 0.0
            update_data["hide_from_listings"] = False
            update_data["visibility_score"] = 10.0
            new_status = "ativa"
            
    elif new_status == "ajustes_pedidos":
        update_data["adjustment_request"] = adjustment_request or admin_notes
        update_data["adjustment_requested_at"] = datetime.now(timezone.utc).isoformat()
        update_data["adjustment_requested_by"] = admin.user_id
        
    elif new_status == "ativa":
        update_data["is_active"] = True
        update_data["activated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["is_featured"] = False
        update_data["visibility_boost"] = 0.0
        update_data["hide_from_listings"] = False
        update_data["visibility_score"] = 10.0
        
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
        "ativa": "A tua viagem está agora ATIVA e visível na secção 'Sonhos em Materialização'! Partilha com a tua rede para começar a receber contribuições.",
        "financiada": "Parabéns! A tua viagem foi totalmente financiada! O teu sonho vai realizar-se!",
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
            "aprovada": "A tua viagem foi aprovada - 4Luis",
            "ajustes_pedidos": "Pedido de ajustes à tua candidatura - 4Luis",
            "ativa": "A tua viagem está ATIVA - 4Luis",
            "financiada": "A tua viagem foi FINANCIADA - 4Luis",
            "realizada": "Viagem marcada como realizada - 4Luis",
            "encerrada": "Atualização sobre a tua viagem - 4Luis"
        }
        
        email_bodies = {
            "aprovada": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #FFBE98;">Parabéns, {ambassador.get('name', 'Embaixador')}!</h1>
                    <p>A tua candidatura para a viagem <strong>"{journey.get('name')}"</strong> foi aprovada!</p>
                    <p>A tua viagem está agora ativa e visível na secção <strong>"Sonhos em Materialização"</strong> da nossa homepage.</p>
                    <p>Começa já a partilhar o link da tua viagem com amigos e família para começares a receber contribuições!</p>
                    <a href="https://4luis.com/journeys/{journey_id}" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 16px;">Ver a minha viagem</a>
                    <p style="margin-top: 24px; color: #6B6661; font-size: 14px;">Com carinho,<br>Equipa 4Luis</p>
                </div>
            """,
            "ajustes_pedidos": f"""
                <div style="font-family: system-ui, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #F2C94C;">Pedido de Ajustes</h1>
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
                    <h1 style="color: #4CAF50;">A tua viagem está ATIVA!</h1>
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
                    <h1 style="color: #9C27B0;">O TEU SONHO VAI REALIZAR-SE!</h1>
                    <p>Olá {ambassador.get('name', 'Embaixador')},</p>
                    <p>Temos uma notícia incrível: A tua viagem <strong>"{journey.get('name')}"</strong> foi <strong>totalmente financiada</strong>!</p>
                    <p>Graças à generosidade da comunidade 4Luis, vais poder realizar este sonho.</p>
                    <p>Entraremos em contacto em breve para coordenar os próximos passos.</p>
                    <p>Obrigado por fazeres parte desta comunidade!</p>
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
    
    response_data = {
        "message": f"Estado atualizado para '{JOURNEY_STATUSES[new_status]['name']}'",
        "journey_id": journey_id,
        "new_status": new_status
    }
    
    if new_status == "ativa":
        response_data["is_now_live"] = True
        response_data["published_in"] = "Sonhos em Materialização"
        response_data["email_sent"] = bool(ambassador and ambassador.get("email") and RESEND_API_KEY)
    
    await log_admin_action(admin.user_id, "journey_status_changed", "journey", journey_id, {
        "old_status": journey.get("status"), "new_status": new_status
    })

    return response_data


# ==================== VISIBILITY & FEATURING SYSTEM ====================

@router.post("/admin/journeys/{journey_id}/update-visibility")
async def update_journey_visibility(journey_id: str, request: Request):
    """Update journey visibility settings - Admin only"""
    await require_admin(request)
    data = await request.json()
    
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    upd = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if "is_featured" in data:
        upd["is_featured"] = data["is_featured"]
        if data["is_featured"]:
            upd["featured_at"] = datetime.now(timezone.utc).isoformat()
        else:
            upd["featured_at"] = None
    
    if "featured_order" in data:
        upd["featured_order"] = int(data["featured_order"])
    
    if "visibility_boost" in data:
        boost = float(data["visibility_boost"])
        upd["visibility_boost"] = max(-100, min(100, boost))
    
    if "hide_from_listings" in data:
        upd["hide_from_listings"] = data["hide_from_listings"]
    
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": upd}
    )
    
    updated_journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    new_score = await calculate_journey_visibility_score(updated_journey)
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {"visibility_score": new_score}}
    )
    
    return {
        "message": "Visibilidade atualizada",
        "journey_id": journey_id,
        "is_featured": upd.get("is_featured", journey.get("is_featured")),
        "visibility_boost": upd.get("visibility_boost", journey.get("visibility_boost")),
        "new_visibility_score": new_score
    }


@router.post("/admin/recalculate-all-visibility")
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


@router.put("/admin/journeys/{journey_id}/show-goal")
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


@router.get("/admin/journeys-visibility")
async def get_journeys_with_visibility(request: Request, status: Optional[str] = None):
    """Get all journeys with visibility data - Admin only"""
    await require_admin(request)
    
    query = {}
    if status:
        query["status"] = status
    
    journeys = await db.journeys.find(query, {"_id": 0}).sort("visibility_score", -1).to_list(100)
    
    for journey in journeys:
        journey["calculated_score"] = await calculate_journey_visibility_score(journey)
    
    return {
        "count": len(journeys),
        "journeys": journeys
    }


# ==================== RAFFLE SYSTEM ====================

@router.get("/admin/journeys-ready-for-raffle")
async def get_journeys_ready_for_raffle(request: Request):
    """Get all journeys that have reached their funding goal and are ready for raffle"""
    await require_admin(request)
    
    journeys = await db.journeys.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    ready_journeys = []
    for journey in journeys:
        if journey.get("current_amount", 0) >= journey.get("goal_amount", float('inf')):
            existing_raffle = await db.raffle_results.find_one(
                {"journey_id": journey["journey_id"]},
                {"_id": 0}
            )
            
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


@router.get("/admin/raffle/{journey_id}")
async def get_raffle_participants(journey_id: str, request: Request):
    """Get all participants (users with points) for a journey raffle"""
    await require_admin(request)
    
    points = await db.points.find({"journey_id": journey_id}, {"_id": 0}).to_list(10000)
    
    user_points = {}
    for point in points:
        user_id = point["user_id"]
        if user_id not in user_points:
            user_points[user_id] = {"total_points": 0, "entries": []}
        user_points[user_id]["total_points"] += point.get("points_value", 1)
        user_points[user_id]["entries"].append(point["point_id"])
    
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
    
    participants.sort(key=lambda x: x["total_points"], reverse=True)
    
    existing_raffle = await db.raffle_results.find_one({"journey_id": journey_id}, {"_id": 0})
    
    return {
        "journey_id": journey_id,
        "total_participants": len(participants),
        "total_points": sum(p["total_points"] for p in participants),
        "participants": participants,
        "raffle_done": existing_raffle is not None,
        "raffle_result": existing_raffle
    }


@router.post("/admin/raffle/{journey_id}/draw")
async def draw_raffle_winner(journey_id: str, request: Request):
    """Draw a random winner from participants (weighted by points)"""
    await require_admin(request)
    
    existing_raffle = await db.raffle_results.find_one({"journey_id": journey_id}, {"_id": 0})
    if existing_raffle:
        raise HTTPException(status_code=400, detail="Sorteio já foi realizado para esta viagem")
    
    points = await db.points.find({"journey_id": journey_id}, {"_id": 0}).to_list(10000)
    
    if not points:
        raise HTTPException(status_code=400, detail="Não há participantes para este sorteio")
    
    winning_point = random.choice(points)
    
    user = await db.users.find_one({"user_id": winning_point["user_id"]}, {"_id": 0})
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    
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


# ==================== SEED & MIGRATION ====================

@router.post("/seed-journeys")
async def seed_journeys():
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
            "image_url": "https://customer-assets.emergentagent.com/job_comeback-point/artifacts/cjyrr4fo_Imagem%20China%202.avif",
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


@router.post("/admin/migrate-journey-status")
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


@router.post("/admin/set-main-journey/{journey_id}")
async def set_main_journey(journey_id: str, request: Request):
    """Set a journey as the main platform journey"""
    await require_admin(request)
    
    await db.journeys.update_many(
        {"is_main_trip": True},
        {"$set": {"is_main_trip": False}}
    )
    
    result = await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {"is_main_trip": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    
    return {"message": f"Journey {journey_id} set as main trip"}
