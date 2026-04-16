"""
Referral service — sponsor links, referral tracking, ambassador progression.
"""
from datetime import datetime, timezone
from config import db, logger


async def recalculate_ambassador_status(user_id: str):
    """
    Recalculate if a user qualifies for ambassador level.
    Requirements:
    1. Has contributed to main trip
    2. Has 3+ valid referrals (referrals who also contributed to main trip)
    """
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user or user.get("level") == "embaixador":
        return False
    
    has_contribution = user.get("contributed_to_main_trip", False)
    
    # Count valid referrals: users sponsored by this user who contributed to main trip
    referred_users = await db.users.find(
        {"sponsor_id": user_id}, {"_id": 0, "user_id": 1, "contributed_to_main_trip": 1}
    ).to_list(100)
    
    valid_count = sum(1 for u in referred_users if u.get("contributed_to_main_trip"))
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"valid_referrals_count": valid_count}}
    )
    
    if has_contribution and valid_count >= 3:
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "level": "embaixador",
                "certification_level": "embaixador",
                "embaixador_unlocked_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        logger.info(f"User {user_id} promoted to ambassador!")
        return True
    
    return False


async def get_referral_progress(user_id: str) -> dict:
    """Get referral progress for ambassador requirements."""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        return {}
    
    has_contribution = user.get("contributed_to_main_trip", False)
    valid_referrals = user.get("valid_referrals_count", 0)
    is_ambassador = user.get("level") == "embaixador"
    
    return {
        "has_contribution": has_contribution,
        "valid_referrals": valid_referrals,
        "referrals_needed": max(0, 3 - valid_referrals),
        "is_ambassador": is_ambassador,
        "percentage": min(100, round(((1 if has_contribution else 0) + valid_referrals) / 4 * 100))
    }
