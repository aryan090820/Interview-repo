from enum import Enum


class Department(str, Enum):
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    GENERAL_MEDICINE = "general_medicine"
    ORTHOPEDICS = "orthopedics"
    PEDIATRICS = "pediatrics"


class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
