from app.schemas.opportunities import OpportunityRead

from pydantic import BaseModel


class RecommendationScoreBreakdown(BaseModel):
    semantic: int = 0
    eligibility: int = 0
    deadline: int = 0
    user_history: int = 0
    final: int = 0


class RecommendationRead(BaseModel):
    opportunity: OpportunityRead
    match_score: int
    semantic_score: int = 0
    score_breakdown: RecommendationScoreBreakdown = RecommendationScoreBreakdown()
    reasons: list[str]
    user_status: str | None = None
