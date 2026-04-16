"""
Payment processing service — centralizes all payment and contribution logic.
"""
from datetime import datetime, timezone
from config import (
    db, logger, FIXED_CONTRIBUTION_AMOUNTS, TIP_OPTIONS,
    CERTIFICATION_LEVELS
)


async def calculate_revenue_distribution(contribution: dict) -> dict:
    """
    Calculate revenue distribution for a contribution.
    
    Rules:
    - Ambassador campaign: 100% support_amount -> ambassador, tip_amount -> platform
    - Platform campaign: 100% support_amount -> platform, tip_amount -> platform
    """
    support_amount = contribution.get("support_amount") or contribution.get("amount", 0)
    tip_amount = contribution.get("tip_amount", 0)
    is_ambassador_journey = contribution.get("is_ambassador_journey", False)
    ambassador_user_id = contribution.get("ambassador_user_id")
    
    if is_ambassador_journey and ambassador_user_id:
        return {
            "ambassador_revenue": support_amount,
            "platform_revenue": tip_amount,
            "ambassador_user_id": ambassador_user_id
        }
    else:
        return {
            "ambassador_revenue": 0,
            "platform_revenue": support_amount + tip_amount,
            "ambassador_user_id": None
        }


async def apply_revenue_distribution(contribution_id: str):
    """Apply revenue distribution after payment is confirmed."""
    contribution = await db.contributions.find_one(
        {"contribution_id": contribution_id}, {"_id": 0}
    )
    if not contribution:
        return
    
    distribution = await calculate_revenue_distribution(contribution)
    
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "ambassador_revenue": distribution["ambassador_revenue"],
            "platform_revenue": distribution["platform_revenue"]
        }}
    )
    
    if distribution["ambassador_user_id"] and distribution["ambassador_revenue"] > 0:
        await db.users.update_one(
            {"user_id": distribution["ambassador_user_id"]},
            {"$inc": {"ambassador_earnings": distribution["ambassador_revenue"]}}
        )
    
    logger.info(f"Revenue distribution applied for {contribution_id}: ambassador={distribution['ambassador_revenue']}€, platform={distribution['platform_revenue']}€")
    return distribution


def validate_contribution_amount(amount: int) -> bool:
    """Validate that amount is in allowed list."""
    return amount in FIXED_CONTRIBUTION_AMOUNTS


def validate_tip_amount(tip_amount: int) -> bool:
    """Validate that tip is one of the allowed values."""
    valid_values = [opt["value"] for opt in TIP_OPTIONS]
    return tip_amount in valid_values


def calculate_total_payment(support_amount: int, tip_amount: int = 0) -> int:
    """Calculate total payment amount."""
    return support_amount + tip_amount
