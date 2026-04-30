from pydantic import BaseModel

from app.db.models import ProfileOpportunityStatusValue


class ProfileOpportunityStatusCreate(BaseModel):
    status: ProfileOpportunityStatusValue
    notes: str = ""


class ProfileOpportunityStatusRead(BaseModel):
    id: int
    profile_id: int
    opportunity_id: int
    status: ProfileOpportunityStatusValue
    notes: str

    model_config = {"from_attributes": True}

