"""
Journey routes — Phase 1: Read-only public endpoints.
GET /journeys, GET /journeys/{id}, GET /journeys/{id}/progress,
GET /journeys/featured, GET /journeys/realized, GET /journeys/active,
GET /homepage/main-journey, GET /homepage/ambassador-journeys,
GET /homepage/realized-journeys, GET /homepage/curated-dreams,
GET /journey/{id}/payment-info, GET /success-stories
"""
from fastapi import APIRouter, HTTPException, Request
from typing import List
from datetime import datetime, timezone

from config import (
    db, logger, CERTIFICATION_LEVELS
)
from auth import get_current_user

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
