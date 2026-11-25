from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.constants import AppointmentStatus, Department
from core.exceptions import InvalidRequestError, NotFoundError, SlotUnavailableError
from models import Appointment, Patient
from services.notifications import schedule_reminders
from services.slots import fetch_slots


def identify_user(db: Session, phone: str) -> Patient:
    patient = db.scalar(select(Patient).where(Patient.phone == phone))
    if patient is None:
        raise NotFoundError(f"No patient registered with phone {phone}")
    return patient


def register_patient(db: Session, full_name: str, phone: str, email: str | None = None) -> Patient:
    if db.scalar(select(Patient).where(Patient.phone == phone)) is not None:
        raise InvalidRequestError(f"Phone {phone} is already registered")
    patient = Patient(full_name=full_name, phone=phone, email=email)
    db.add(patient)
    db.flush()
    return patient


def _ensure_bookable(db: Session, department: str, slot_date: date, slot_time: time) -> None:
    if datetime.combine(slot_date, slot_time) <= datetime.now(timezone.utc):
        raise InvalidRequestError("Appointments can only be booked in the future")
    if slot_time not in fetch_slots(db, slot_date, department):
        raise SlotUnavailableError(f"{department} slot {slot_date} {slot_time:%H:%M} is not available")


def book_appointment(
    db: Session,
    phone: str,
    department: Department | str,
    slot_date: date,
    slot_time: time,
    reason: str | None = None,
) -> Appointment:
    patient = identify_user(db, phone)
    department = Department(department).value
    _ensure_bookable(db, department, slot_date, slot_time)
    appointment = Appointment(
        patient=patient,
        department=department,
        slot_date=slot_date,
        slot_time=slot_time,
        reason=reason,
    )
    db.add(appointment)
    db.flush()
    schedule_reminders(db, appointment)
    return appointment


def retrieve_appointments(db: Session, phone: str, include_cancelled: bool = False) -> list[Appointment]:
    patient = identify_user(db, phone)
    query = select(Appointment).where(Appointment.patient_id == patient.id)
    if not include_cancelled:
        query = query.where(Appointment.status == AppointmentStatus.BOOKED.value)
    return list(db.scalars(query.order_by(Appointment.slot_date, Appointment.slot_time)))


def _get_active(db: Session, appointment_id: int) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if appointment is None or appointment.status != AppointmentStatus.BOOKED.value:
        raise NotFoundError(f"Active appointment {appointment_id} not found")
    return appointment


def cancel_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = _get_active(db, appointment_id)
    appointment.status = AppointmentStatus.CANCELLED.value
    db.flush()
    return appointment


def modify_appointment(db: Session, appointment_id: int, slot_date: date, slot_time: time) -> Appointment:
    appointment = _get_active(db, appointment_id)
    _ensure_bookable(db, appointment.department, slot_date, slot_time)
    appointment.slot_date = slot_date
    appointment.slot_time = slot_time
    db.flush()
    schedule_reminders(db, appointment)
    return appointment
