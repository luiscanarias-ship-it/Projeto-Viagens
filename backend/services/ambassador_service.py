"""
Ambassador service — certification, trust indicators, profile management.
"""
from datetime import datetime, timezone
from config import db, logger, CERTIFICATION_LEVELS


async def get_trust_indicators(user_id: str) -> dict:
    """Get trust indicators for an ambassador."""
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
    
    # Average confirmation time
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


async def update_certification(user_id: str, new_level: str, admin_user_id: str = None) -> dict:
    """Update ambassador certification level."""
    if new_level not in CERTIFICATION_LEVELS:
        raise ValueError(f"Invalid level: {new_level}")
    
    update = {
        "certification_level": new_level,
        "certification_updated_at": datetime.now(timezone.utc).isoformat()
    }
    if new_level in ("verificado", "confiavel"):
        update["certification_verified_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one({"user_id": user_id}, {"$set": update})
    label = CERTIFICATION_LEVELS[new_level]["label"]
    logger.info(f"Ambassador {user_id} certification updated to {new_level} by {admin_user_id}")
    return {"label": label, "level": new_level}
