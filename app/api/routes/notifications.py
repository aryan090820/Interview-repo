from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from models import Notification
from schemas.notification import NotificationOut
from services import booking
from services.notifications import mark_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[Notification])
def list_notifications(phone: str, unread_only: bool = False, db: Session = Depends(get_db)):
    patient = booking.identify_user(db, phone)
    query = select(Notification).where(Notification.patient_id == patient.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    return list(db.scalars(query.order_by(Notification.send_at)))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_notification(notification_id: int, db: Session = Depends(get_db)):
    return mark_read(db, notification_id)
