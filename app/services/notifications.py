import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from core.exceptions import NotFoundError
from models import Appointment, Notification, NotificationTemplate

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES = [
    {
        "code": "reminder_24h",
        "title": "Appointment tomorrow",
        "body": "Hi {patient_name}, your {department} appointment is on {slot_date} at {slot_time}.",
        "offset_minutes": 24 * 60,
    },
    {
        "code": "reminder_1h",
        "title": "Appointment in one hour",
        "body": "Hi {patient_name}, see you at {slot_time} for your {department} visit.",
        "offset_minutes": 60,
    },
]


def ensure_templates(db: Session) -> None:
    existing = set(db.scalars(select(NotificationTemplate.code)))
    for template in DEFAULT_TEMPLATES:
        if template["code"] not in existing:
            db.add(NotificationTemplate(**template))
    db.flush()


def schedule_reminders(db: Session, appointment: Appointment) -> list[Notification]:
    db.execute(
        delete(Notification).where(
            Notification.appointment_id == appointment.id,
            Notification.sent_at.is_(None),
        )
    )
    created = []
    for template in db.scalars(select(NotificationTemplate)):
        context = {
            "patient_name": appointment.patient.full_name,
            "department": appointment.department.replace("_", " "),
            "slot_date": appointment.slot_date.isoformat(),
            "slot_time": appointment.slot_time.strftime("%H:%M"),
        }
        notification = Notification(
            patient_id=appointment.patient_id,
            appointment_id=appointment.id,
            template_id=template.id,
            title=template.title,
            body=template.body.format(**context),
            send_at=appointment.starts_at - timedelta(minutes=template.offset_minutes),
        )
        db.add(notification)
        created.append(notification)
    db.flush()
    return created


def mark_read(db: Session, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise NotFoundError(f"Notification {notification_id} not found")
    if notification.read_at is None:
        notification.read_at = datetime.now()
    return notification


class NotificationScheduler:
    def __init__(self, session_factory: sessionmaker, poll_seconds: int):
        self._session_factory = session_factory
        self._poll_seconds = poll_seconds
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        asyncio.run(self._warmup())
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    async def _warmup(self) -> None:
        with self._session_factory() as db:
            ensure_templates(db)
            db.commit()
        logger.info("Notification templates ready")

    async def _run(self) -> None:
        while True:
            try:
                sent = self.dispatch_due()
                if sent:
                    logger.info("Dispatched %d notifications", sent)
            except Exception:
                logger.exception("Notification dispatch failed")
            await asyncio.sleep(self._poll_seconds)

    def dispatch_due(self) -> int:
        now = datetime.now()
        with self._session_factory() as db:
            due = db.scalars(
                select(Notification).where(Notification.sent_at.is_(None), Notification.send_at <= now)
            ).all()
            for notification in due:
                notification.sent_at = now
            db.commit()
            return len(due)
