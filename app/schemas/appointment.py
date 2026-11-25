from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field

from core.constants import Department


class SlotQuery(BaseModel):
    department: Department
    slot_date: date


class SlotOut(BaseModel):
    department: Department
    slot_date: date
    available: list[time]


class AppointmentCreate(BaseModel):
    patient_phone: str = Field(..., pattern=r"^\+?\d{10,13}$")
    department: Department
    slot_date: date
    slot_time: time
    reason: Optional[str] = Field(default=None, max_length=255)


class AppointmentModify(BaseModel):
    slot_date: date
    slot_time: time


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    department: Department
    slot_date: date
    slot_time: time
    status: str
    reason: Optional[str] = None
