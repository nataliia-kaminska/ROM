from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.application.access_control import require_owned_or_public_resource
from app.db.models import User
from app.repositories import profiles as profile_repository
from app.schemas.recommendations import RecommendationListResponse, RecommendationRead
from app.services.recommendations import RecommendationQuery, list_recommendations, list_recommendations_page


@dataclass
class ListRecommendationsUseCase:
    db: Session

    def execute(
        self,
        profile_id: int,
        current_user: User | None,
        query: RecommendationQuery,
    ) -> list[RecommendationRead]:
        profile = require_owned_or_public_resource(
            profile_repository.get_profile(self.db, profile_id),
            current_user,
            "Profile",
        )
        return list_recommendations(self.db, profile, query)

    def execute_page(
        self,
        profile_id: int,
        current_user: User | None,
        query: RecommendationQuery,
    ) -> RecommendationListResponse:
        profile = require_owned_or_public_resource(
            profile_repository.get_profile(self.db, profile_id),
            current_user,
            "Profile",
        )
        page = list_recommendations_page(self.db, profile, query)
        return RecommendationListResponse(items=page.items, total=page.total, limit=query.limit, offset=query.offset)
