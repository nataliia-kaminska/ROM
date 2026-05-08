from sqlalchemy.orm import Session

from app.db.models import Notification, NotificationType, Opportunity, OpportunityReminder, ResearcherProfile, User


def create_deadline_notification(
    db: Session,
    reminder: OpportunityReminder,
    profile: ResearcherProfile | None,
    opportunity: Opportunity | None,
) -> Notification:
    subject = f"Deadline reminder: {opportunity.title if opportunity else 'Opportunity'}"
    notification = Notification(
        user_id=profile.user_id if profile else None,
        profile_id=reminder.profile_id,
        opportunity_id=reminder.opportunity_id,
        reminder_id=reminder.id,
        notification_type=NotificationType.deadline_reminder,
        recipient=profile.email if profile and profile.email else "",
        subject=subject,
        body=reminder.message or subject,
    )
    db.add(notification)
    db.flush()
    return notification


def create_digest_notification(
    db: Session,
    user: User,
    profile: ResearcherProfile | None,
    subject: str,
    body: str,
    notification_type: NotificationType,
) -> Notification:
    notification = Notification(
        user_id=user.id,
        profile_id=profile.id if profile else None,
        notification_type=notification_type,
        recipient=user.email,
        subject=subject,
        body=body,
    )
    db.add(notification)
    db.flush()
    return notification
