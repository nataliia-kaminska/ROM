from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_optional_current_user, get_recommendation_use_case
from app.application.use_cases.recommendations import ListRecommendationsUseCase
from app.schemas.recommendations import RecommendationListResponse, RecommendationRead
from app.services.recommendations import RecommendationQuery


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{profile_id}", response_model=None)
def get_recommendations(
    profile_id: int,
    include_ignored: bool = False,
    min_score: int = Query(default=0, ge=0, le=100),
    keyword: str | None = None,
    source: str | None = None,
    opportunity_type: str | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    active_only: bool = True,
    sort_by: str = Query(default="match_score", pattern="^(match_score|semantic_score|readiness_score|deadline|created_at|title|source)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_total: bool = False,
    current_user=Depends(get_optional_current_user),
    use_case: ListRecommendationsUseCase = Depends(get_recommendation_use_case),
) -> list[RecommendationRead] | RecommendationListResponse:
    query = RecommendationQuery(
        include_ignored=include_ignored,
        min_score=min_score,
        keyword=keyword,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
        exact_total=include_total,
    )
    if include_total:
        return use_case.execute_page(profile_id, current_user, query)
    return use_case.execute(profile_id, current_user, query)
