from datetime import date, datetime

from pydantic import BaseModel

from app.db.models import ReminderStatus


class OpportunityReminderCreate(BaseModel):
    opportunity_id: int
    remind_on: date
    message: str = ""


class OpportunityReminderRead(BaseModel):
    id: int
    profile_id: int
    opportunity_id: int
    remind_on: date
    message: str
    status: ReminderStatus
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}

