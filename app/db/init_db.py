import logging
from datetime import date, timedelta

from sqlalchemy import func, select

import models
from core.constants import Department
from db.base import Base
from db.session import SessionLocal, engine
from services import booking
from services.notifications import ensure_templates
from services.slots import fetch_slots

logger = logging.getLogger(__name__)

SEED_PATIENTS = [
    {"full_name": "Aarav Mehta", "phone": "+919800000001", "email": "aarav@example.com"},
    {"full_name": "Diya Sharma", "phone": "+919800000002", "email": "diya@example.com"},
    {"full_name": "Rohan Verma", "phone": "+919800000003", "email": None},
]

SEED_BOOKINGS = [
    ("+919800000001", Department.CARDIOLOGY, "Chest pain follow-up"),
    ("+919800000002", Department.CARDIOLOGY, "Routine ECG"),
    ("+919800000003", Department.DERMATOLOGY, "Skin allergy"),
]


def seed(db) -> None:
    if db.scalar(select(func.count()).select_from(models.Patient)):
        return
    ensure_templates(db)
    for patient in SEED_PATIENTS:
        booking.register_patient(db, **patient)
    seed_date = date.today() + timedelta(days=2)
    for phone, department, reason in SEED_BOOKINGS:
        next_slot = fetch_slots(db, seed_date, department.value)[0]
        booking.book_appointment(db, phone, department, seed_date, next_slot, reason)
    logger.info("Seeded %d patients and %d appointments", len(SEED_PATIENTS), len(SEED_BOOKINGS))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
        db.commit()
