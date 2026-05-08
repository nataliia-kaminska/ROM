from enum import Enum


class UserRole(str, Enum):
    researcher = "researcher"
    admin = "admin"


class CareerStage(str, Enum):
    bachelor = "bachelor"
    master = "master"
    phd = "phd"
    postdoc = "postdoc"
    early_career = "early_career"
    senior = "senior"


class OpportunityType(str, Enum):
    grant = "grant"
    exchange = "exchange"
    fellowship = "fellowship"
    internship = "internship"
    research_position = "research_position"
    training = "training"


class IngestionBatchStatus(str, Enum):
    dry_run = "dry_run"
    success = "success"
    failed = "failed"


class ProfileOpportunityStatusValue(str, Enum):
    saved = "saved"
    ignored = "ignored"
    planned = "planned"
    applied = "applied"
    rejected = "rejected"
    accepted = "accepted"


class ReminderStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class NotificationStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    skipped = "skipped"
    read = "read"


class NotificationType(str, Enum):
    deadline_reminder = "deadline_reminder"
    weekly_digest = "weekly_digest"
    high_match_alert = "high_match_alert"
