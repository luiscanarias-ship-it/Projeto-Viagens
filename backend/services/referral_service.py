"""
Referral service — sponsor links, referral tracking, ambassador progression.
"""
from datetime import datetime, timezone
import asyncio

from config import db, logger
from services.notification_service import create_notification
from email_service import send_ambassador_unlocked_email

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
