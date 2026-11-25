from fastapi import APIRouter

from api.routes import appointments, assistant, health, notifications, patients

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(patients.router)
api_router.include_router(appointments.router)
api_router.include_router(notifications.router)
api_router.include_router(assistant.router)
