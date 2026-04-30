from app.schemas.opportunities import OpportunityRead

from pydantic import BaseModel


class RecommendationRead(BaseModel):
    opportunity: OpportunityRead
    match_score: int
    reasons: list[str]
    user_status: str | None = None
