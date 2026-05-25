from pydantic import BaseModel, HttpUrl

from app.schemas.profile_details import ResearcherProfileDetailsRead
from app.schemas.profiles import ResearcherProfileRead


class ProfileDiscoveryCandidate(BaseModel):
    title: str
    url: HttpUrl
    snippet: str = ""
    source: str = ""
    confidence: int = 0


class ProfileDiscoveryApplyRequest(BaseModel):
    title: str
    url: HttpUrl
    snippet: str = ""


class ProfileDiscoveryApplyResult(BaseModel):
    profile: ResearcherProfileRead
    details: ResearcherProfileDetailsRead
    candidate: ProfileDiscoveryCandidate
    applied_fields: list[str]
