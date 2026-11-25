from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from db.session import get_db
from schemas.patients import PatientCreate, PatientOut
from services import booking

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def register_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    return booking.register_patient(db, payload.full_name, payload.phone, payload.email)


@router.get("/{phone}", response_model=PatientOut)
def get_patient(phone: str, db: Session = Depends(get_db)):
    return booking.identify_user(db, phone)
