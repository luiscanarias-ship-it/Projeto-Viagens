"""
Notification service — centralized notification creation.
Used by all route modules.
"""
from datetime import datetime, timezone
import uuid
from config import db


async def create_notification(user_id: str, ntype: str, message: str, data: dict = None):
    """Create a notification for a user."""
    doc = {
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "type": ntype,
        "message": message,
        "data": data or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(doc)
    return doc["notification_id"]
