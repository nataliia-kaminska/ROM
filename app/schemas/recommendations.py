from pydantic import BaseModel, Field

from app.schemas.opportunities import OpportunityRead


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
    score_breakdown: RecommendationScoreBreakdown = Field(default_factory=RecommendationScoreBreakdown)
    reasons: list[str]
    readiness_score: int = 0
    gaps: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    user_status: str | None = None
