from sqlalchemy.orm import Session

from app.application.ports.repositories import OpportunityRepository, ProfileRepository, WorkflowRepository
from app.db.models import Opportunity, OpportunityReminder, ProfileOpportunityStatus, ResearcherProfile, ResearcherProfileDetails, User
from app.domain.enums import OpportunityType
from app.repositories import opportunities as opportunity_repository
from app.repositories import profiles as profile_repository
from app.repositories import workflow as workflow_repository


class SqlAlchemyProfileRepository(ProfileRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, profile_id: int) -> ResearcherProfile | None:
        return profile_repository.get_profile(self.db, profile_id)

    def list_for_user(self, user: User) -> list[ResearcherProfile]:
        return profile_repository.list_profiles_for_user(self.db, user)

    def get_details(self, profile_id: int) -> ResearcherProfileDetails | None:
        return profile_repository.get_profile_details(self.db, profile_id)


class SqlAlchemyOpportunityRepository(OpportunityRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, opportunity_id: int) -> Opportunity | None:
        return opportunity_repository.get_opportunity(self.db, opportunity_id)

    def get_by_url(self, url: str) -> Opportunity | None:
        return opportunity_repository.get_opportunity_by_url(self.db, url)

    def list(
        self,
        source: str | None = None,
        opportunity_type: OpportunityType | None = None,
        country: str | None = None,
        career_stage: str | None = None,
        keyword: str | None = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Opportunity]:
        return opportunity_repository.list_opportunities(
            self.db,
            source=source,
            opportunity_type=opportunity_type,
            country=country,
            career_stage=career_stage,
            keyword=keyword,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )


class SqlAlchemyWorkflowRepository(WorkflowRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_profile_statuses(self, profile_id: int) -> list[ProfileOpportunityStatus]:
        return workflow_repository.list_profile_statuses(self.db, profile_id)

    def list_profile_reminders(
        self,
        profile_id: int,
        include_completed: bool = False,
        due_only: bool = False,
    ) -> list[OpportunityReminder]:
        return workflow_repository.list_profile_reminders(
            self.db,
            profile_id=profile_id,
            include_completed=include_completed,
            due_only=due_only,
        )
