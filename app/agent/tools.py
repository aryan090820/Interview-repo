import logging
from datetime import date, time
from typing import Any, Callable

from sqlalchemy.orm import Session

from services import booking
from services.slots import fetch_slots

logger = logging.getLogger(__name__)

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {}

REQUIRED_TOOLS = (
    "identify_user",
    "fetch_slots",
    "book_appointment",
    "retrieve_appointments",
    "cancel_appointment",
    "modify_appointment",
    "end_conversation",
)


def register_tool(name: str):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        TOOL_REGISTRY[name] = func
        return func

    return decorator


def _serialize(appointment) -> dict:
    return {
        "id": appointment.id,
        "department": appointment.department,
        "slot_date": appointment.slot_date.isoformat(),
        "slot_time": appointment.slot_time.strftime("%H:%M"),
        "status": appointment.status,
    }


@register_tool("identify_user")
def identify_user(db: Session, phone: str) -> dict:
    patient = booking.identify_user(db, phone)
    return {"patient_id": patient.id, "full_name": patient.full_name}


@register_tool("fetch_slots")
def fetch_available_slots(db: Session, department: str, slot_date: str) -> dict:
    slots = fetch_slots(db, date.fromisoformat(slot_date), department)
    return {"department": department, "slot_date": slot_date, "available": [s.strftime("%H:%M") for s in slots]}


@register_tool("book_appointment")
def book_appointment(db: Session, phone: str, department: str, slot_date: str, slot_time: str, reason: str | None = None) -> dict:
    appointment = booking.book_appointment(
        db, phone, department, date.fromisoformat(slot_date), time.fromisoformat(slot_time), reason
    )
    return _serialize(appointment)


@register_tool("retrieve_appointments")
def retrieve_appointments(db: Session, phone: str) -> dict:
    return {"appointments": [_serialize(a) for a in booking.retrieve_appointments(db, phone)]}


@register_tool("cancel_appointment")
def cancel_appointment(db: Session, appointment_id: int) -> dict:
    return _serialize(booking.cancel_appointment(db, int(appointment_id)))


@register_tool("modify_appointment")
def modify_appointment(db: Session, appointment_id: int, slot_date: str, slot_time: str) -> dict:
    appointment = booking.modify_appointment(
        db, int(appointment_id), date.fromisoformat(slot_date), time.fromisoformat(slot_time)
    )
    return _serialize(appointment)


@register_tool
def end_conversation(db: Session, summary: str = "") -> dict:
    logger.info("Conversation ended: %s", summary or "no summary")
    return {"ended": True}


def validate_registry() -> None:
    missing = [name for name in REQUIRED_TOOLS if name not in TOOL_REGISTRY]
    if missing:
        raise RuntimeError(f"Agent tools not registered: {missing}")


def invoke_tool(db: Session, name: str, arguments: dict[str, Any]) -> Any:
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        raise KeyError(name)
    return tool(db, **arguments)
