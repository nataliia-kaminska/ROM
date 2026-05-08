from sqlalchemy.orm import Session

from app.db.models import ResearcherProfile, ResearcherProfileDetails, User


def get_profile(db: Session, profile_id: int) -> ResearcherProfile | None:
    return db.get(ResearcherProfile, profile_id)


def list_profiles_for_user(db: Session, user: User) -> list[ResearcherProfile]:
    return db.query(ResearcherProfile).filter(ResearcherProfile.user_id == user.id).all()


def get_profile_details(db: Session, profile_id: int) -> ResearcherProfileDetails | None:
    return db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile_id).first()


def get_or_create_profile_details(db: Session, profile_id: int) -> ResearcherProfileDetails:
    details = get_profile_details(db, profile_id)
    if details is not None:
        return details
    details = ResearcherProfileDetails(profile_id=profile_id)
    db.add(details)
    return details
