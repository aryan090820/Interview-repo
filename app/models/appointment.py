from __future__ import annotations

import datetime as dt

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.constants import AppointmentStatus
from db.base import Base
from models.patient import Patient


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index(
            "uq_active_slot",
            "slot_date",
            "slot_time",
            "department",
            unique=True,
            sqlite_where=text("status = 'booked'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    department: Mapped[str] = mapped_column(String(50))
    slot_date: Mapped[dt.date]
    slot_time: Mapped[dt.time]
    reason: Mapped[str | None] = mapped_column(String(255), default=None)
    status: Mapped[str] = mapped_column(String(20), default=AppointmentStatus.BOOKED.value)
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now(dt.timezone.utc))

    patient: Mapped[Patient] = relationship(back_populates="appointment")

    @property
    def starts_at(self) -> dt.datetime:
        return dt.datetime.combine(self.slot_date, self.slot_time)
