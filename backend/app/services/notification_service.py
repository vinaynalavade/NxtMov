from typing import Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification

def create_notification(
    db: Session,
    organization_id: int,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "INFO",
    link_url: Optional[str] = None
) -> Notification:
    notif = Notification(
        organization_id=organization_id,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
