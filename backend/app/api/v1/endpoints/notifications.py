from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationListResponse

router = APIRouter()

@router.get("", response_model=NotificationListResponse, summary="Get Server-Side Notifications for Current User")
def get_notifications(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    notifs = db.query(Notification).filter(
        Notification.organization_id == ctx.organization.id,
        Notification.user_id == ctx.user.id
    ).order_by(Notification.id.desc()).limit(50).all()

    unread_count = db.query(Notification).filter(
        Notification.organization_id == ctx.organization.id,
        Notification.user_id == ctx.user.id,
        Notification.is_read == False
    ).count()

    return NotificationListResponse(
        unread_count=unread_count,
        notifications=[NotificationResponse.model_validate(n) for n in notifs]
    )

@router.patch("/{id}/read", response_model=NotificationResponse, summary="Mark Single Notification as Read")
def mark_notification_read(
    id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    notif = db.query(Notification).filter(
        Notification.organization_id == ctx.organization.id,
        Notification.user_id == ctx.user.id,
        Notification.id == id
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return NotificationResponse.model_validate(notif)

@router.post("/read-all", summary="Mark All Notifications as Read")
def mark_all_read(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    db.query(Notification).filter(
        Notification.organization_id == ctx.organization.id,
        Notification.user_id == ctx.user.id,
        Notification.is_read == False
    ).update({"is_read": True})

    db.commit()
    return {"message": "All notifications marked as read."}
