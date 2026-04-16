"""
Audit service — logs administrative actions for accountability and traceability.
"""
from datetime import datetime, timezone
import uuid

from config import db, logger


async def log_admin_action(
    admin_id: str,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict = None
):
    """Log an administrative action for audit trail.

    Args:
        admin_id: User ID of the admin performing the action
        action: Action type (e.g., 'journey_approved', 'status_changed', 'user_level_changed')
        target_type: Entity type (e.g., 'journey', 'contribution', 'user')
        target_id: ID of the affected entity
        metadata: Additional context about the action
    """
    doc = {
        "audit_id": f"audit_{uuid.uuid4().hex[:12]}",
        "admin_id": admin_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(doc)
    logger.info(f"AUDIT: {action} on {target_type}/{target_id} by {admin_id}")


async def get_audit_logs(limit: int = 100, target_type: str = None, admin_id: str = None):
    """Retrieve audit logs with optional filters."""
    query = {}
    if target_type:
        query["target_type"] = target_type
    if admin_id:
        query["admin_id"] = admin_id

    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return logs
