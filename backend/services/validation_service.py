"""
Validation service — contribution status management and anti-fraud.
"""
from datetime import datetime, timezone
from config import db, logger


async def transition_contribution_status(contribution_id: str, new_status: str, 
                                          validated_by: str = None, notes: str = None):
    """
    Manage contribution status transitions.
    Valid transitions:
      pending -> awaiting_validation (user confirms payment for direct mode)
      pending -> confirmed (admin confirms for platform mode)
      awaiting_validation -> confirmed (ambassador confirms)
      awaiting_validation -> rejected (ambassador rejects)
      any -> flagged (system timeout after 7 days)
    """
    valid_statuses = ["pending", "awaiting_validation", "confirmed", "rejected", "flagged"]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}")
    
    update = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if validated_by:
        update["validated_by"] = validated_by
        update["validated_at"] = datetime.now(timezone.utc).isoformat()
    if notes:
        update["ambassador_validation_notes"] = notes
    
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": update}
    )
    logger.info(f"Contribution {contribution_id} transitioned to {new_status}")


async def check_pending_limit(contributor_email: str, exclude_id: str = None) -> int:
    """Check how many pending contributions an email has. Max 3 allowed."""
    query = {
        "contributor_email": contributor_email,
        "status": {"$in": ["pending", "awaiting_validation"]}
    }
    if exclude_id:
        query["contribution_id"] = {"$ne": exclude_id}
    return await db.contributions.count_documents(query)


async def flag_stale_contribution(contribution_id: str, reason: str = "7d_no_validation"):
    """Flag a stale contribution for admin review."""
    await db.contributions.update_one(
        {"contribution_id": contribution_id},
        {"$set": {
            "flagged": True,
            "flagged_at": datetime.now(timezone.utc).isoformat(),
            "flagged_reason": reason
        }}
    )
    logger.warning(f"Flagged stale contribution: {contribution_id} ({reason})")
