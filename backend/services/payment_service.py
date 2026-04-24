"""
Payment processing service — revenue distribution, points generation, PayPal auth.
"""
from datetime import datetime, timezone
import base64
import httpx

from config import (
    db, logger,
    FIXED_CONTRIBUTION_AMOUNTS, TIP_OPTIONS,
    PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_API_URL
)
from fastapi import HTTPException


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


async def get_paypal_access_token():
    """Get PayPal OAuth2 access token"""
    auth_str = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()).decode()
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.post(
            f"{PAYPAL_API_URL}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_str}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data="grant_type=client_credentials"
        )
        if resp.status_code != 200:
            logger.error(f"PayPal auth failed: {resp.text}")
            raise HTTPException(status_code=500, detail="Erro ao autenticar com PayPal")
        return resp.json()["access_token"]


async def generate_points_for_user(user_id: str, journey_id: str, contribution_id: str,
                                    points_count: int, is_crypto: bool):
    """Generate points for a user based on their contribution — uses insert_many"""
    link = await db.sponsor_links.find_one(
        {"user_id": user_id, "journey_id": journey_id}, {"_id": 0}
    )

    if not link or link.get("successful_referrals", 0) < 3:
        return

    if points_count <= 0:
        return

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    name_initial = (user.get("name", "X")[0]).upper() if user else "X"
    surname_initial = (user.get("surname", "X")[0]).upper() if user and user.get("surname") else "X"

    existing_count = await db.points.count_documents({"journey_id": journey_id})
    now_iso = datetime.now(timezone.utc).isoformat()

    docs = []
    for i in range(points_count):
        registration_number = existing_count + i + 1
        point_id = f"{name_initial}{surname_initial}1{str(registration_number).zfill(7)}"
        docs.append({
            "point_id": point_id,
            "user_id": user_id,
            "journey_id": journey_id,
            "contribution_id": contribution_id,
            "points_value": 1,
            "created_at": now_iso
        })

    if docs:
        await db.points.insert_many(docs)


def validate_contribution_amount(amount: int) -> bool:
    """Validate that amount is in allowed list."""
    return amount in FIXED_CONTRIBUTION_AMOUNTS


def validate_tip_amount(tip_amount: int) -> bool:
    """Validate that tip is one of the allowed values."""
    valid_values = [opt["value"] for opt in TIP_OPTIONS]
    return tip_amount in valid_values
