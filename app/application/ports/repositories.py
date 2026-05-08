from typing import Protocol

from app.db.models import Opportunity, OpportunityReminder, ProfileOpportunityStatus, ResearcherProfile, ResearcherProfileDetails, User
from app.domain.enums import OpportunityType


class ProfileRepository(Protocol):
    def get(self, profile_id: int) -> ResearcherProfile | None:
        ...

    def list_for_user(self, user: User) -> list[ResearcherProfile]:
        ...

    def get_details(self, profile_id: int) -> ResearcherProfileDetails | None:
        ...


class OpportunityRepository(Protocol):
    def get(self, opportunity_id: int) -> Opportunity | None:
        ...

    def get_by_url(self, url: str) -> Opportunity | None:
        ...

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
        ...


class WorkflowRepository(Protocol):
    def list_profile_statuses(self, profile_id: int) -> list[ProfileOpportunityStatus]:
        ...

    def list_profile_reminders(
        self,
        profile_id: int,
        include_completed: bool = False,
        due_only: bool = False,
    ) -> list[OpportunityReminder]:
        ...
