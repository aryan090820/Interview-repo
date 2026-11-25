from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appointment_id: int
    title: str
    body: str
    send_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
