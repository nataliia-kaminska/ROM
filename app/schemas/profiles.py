from pydantic import BaseModel, EmailStr, HttpUrl

from app.db.models import CareerStage


class ResearcherProfileBase(BaseModel):
    full_name: str
    email: EmailStr | None = None
    career_stage: CareerStage
    country: str | None = None
    disciplines: list[str] = []
    keywords: list[str] = []
    preferred_countries: list[str] = []
    orcid_id: str | None = None
    google_scholar_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None


class ResearcherProfileCreate(ResearcherProfileBase):
    pass


class ResearcherProfileRead(ResearcherProfileBase):
    id: int
    user_id: int | None = None

    model_config = {"from_attributes": True}
