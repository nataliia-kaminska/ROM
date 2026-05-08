from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_optional_current_user, get_recommendation_use_case
from app.application.use_cases.recommendations import ListRecommendationsUseCase
from app.schemas.recommendations import RecommendationRead
from app.services.recommendations import RecommendationQuery


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{profile_id}", response_model=list[RecommendationRead])
def get_recommendations(
    profile_id: int,
    include_ignored: bool = False,
    min_score: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_optional_current_user),
    use_case: ListRecommendationsUseCase = Depends(get_recommendation_use_case),
) -> list[RecommendationRead]:
    return use_case.execute(
        profile_id,
        current_user,
        RecommendationQuery(
            include_ignored=include_ignored,
            min_score=min_score,
            limit=limit,
            offset=offset,
        ),
    )
