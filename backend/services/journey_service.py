"""
Journey service — progress calculation, funding status, story chapters.
"""
from datetime import datetime, timezone
from config import db, logger


async def calculate_progress(journey_id: str) -> dict:
    """Calculate journey funding progress."""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return {}
    
    current = journey.get("current_amount", 0)
    goal = journey.get("goal_amount", 1)
    percentage = round((current / goal) * 100) if goal > 0 else 0
    is_funded = percentage >= 100
    
    contributor_count = await db.contributions.count_documents({
        "journey_id": journey_id,
        "status": {"$in": ["confirmed", "completed"]}
    })
    
    return {
        "current_amount": current,
        "goal_amount": goal,
        "percentage": min(percentage, 999),
        "is_funded": is_funded,
        "funding_status": journey.get("funding_status", "active"),
        "contributor_count": contributor_count
    }


async def check_funding_status(journey_id: str):
    """Check if journey has reached funding goal and update status."""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return
    
    current = journey.get("current_amount", 0)
    goal = journey.get("goal_amount", 0)
    
    if goal > 0 and current >= goal and journey.get("funding_status") != "completed":
        await db.journeys.update_one(
            {"journey_id": journey_id},
            {"$set": {
                "funding_status": "pending_validation",
                "funded_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"Journey {journey_id} reached funding goal! Pending admin validation.")
