from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import get_settings
from core.constants import AppointmentStatus
from models import Appointment


def generate_day_slots() -> list[time]
    settings = get_settings()
    current = datetime.combine(date.today(), time(hour=settings.clinic_open_hour))
    closing = datetime.combine(date.today(), time(hour=settings.clinic_close_hour))
    step = timedelta(minutes=settings.slot_duration_minutes)
    slots = []
    while current < closing:
        slots.append(current.time())
        current += step
    return slots


def fetch_slots(db: Session, slot_date: date, department: str) -> list[time]:
    booked = db.scalars(
        select(Appointment).where(
            Appointment.slot_date == slot_date,
            Appointment.department == department,
            Appointment.status == AppointmentStatus.BOOKED.value,
        )
    )
    taken = {appointment.slot_time.strftime("%H:%M") for appointment in booked}
    return [slot for slot in generate_day_slots() if slot not in taken]
