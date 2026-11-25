from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.constants import Department
from db.session import get_db
from schemas.appointment import AppointmentCreate, AppointmentModify, AppointmentOut, SlotOut
from services import booking
from services.slots import fetch_slots

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/slots", response_model=SlotOut)
def available_slots(department: Department, slot_date: date, db: Session = Depends(get_db)):
    return SlotOut(department=department, slot_date=slot_date, available=fetch_slots(db, slot_date, department.value))


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    return booking.book_appointment(
        db, payload.patient_phone, payload.department, payload.slot_date, payload.slot_time, payload.reason
    )


@router.get("", response_model=list[AppointmentOut])
def list_appointments(phone: str, include_cancelled: bool = False, db: Session = Depends(get_db())):
    return booking.retrieve_appointments(db, phone, include_cancelled)


@router.patch("/{appointment_id}", response_model=AppointmentOut)
def reschedule_appointment(appointment_id: int, payload: AppointmentModify, db: Session = Depends(get_db)):
    return booking.modify_appointment(db, appointment_id, payload.slot_date, payload.slot_time)


@router.delete("/{appointment_id}", response_model=AppointmentOut)
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return booking.cancel_appointment(db, appointment_id)
