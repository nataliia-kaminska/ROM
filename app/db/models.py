"""Compatibility exports for ORM models.

Domain model definitions live under app.modules.*.models. Existing imports from
app.db.models remain supported while the backend moves toward feature modules.
"""

from app.modules.admin.models import AdminAuditLog
from app.modules.auth.models import User, UserRole
from app.modules.ingestion.models import IngestionBatch, IngestionBatchStatus, IngestionError, OpportunitySource
from app.modules.notifications.models import Notification, NotificationPreference, NotificationStatus, NotificationType
from app.modules.opportunities.models import Opportunity, OpportunityType
from app.modules.profiles.models import CareerStage, ResearcherProfile, ResearcherProfileDetails
from app.modules.workflow.models import (
    OpportunityReminder,
    ProfileOpportunityStatus,
    ProfileOpportunityStatusValue,
    ReminderStatus,
)

__all__ = [
    "AdminAuditLog",
    "CareerStage",
    "IngestionBatch",
    "IngestionBatchStatus",
    "IngestionError",
    "Notification",
    "NotificationPreference",
    "NotificationStatus",
    "NotificationType",
    "Opportunity",
    "OpportunityReminder",
    "OpportunitySource",
    "OpportunityType",
    "ProfileOpportunityStatus",
    "ProfileOpportunityStatusValue",
    "ReminderStatus",
    "ResearcherProfile",
    "ResearcherProfileDetails",
    "User",
    "UserRole",
]
