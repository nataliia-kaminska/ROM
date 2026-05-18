from sqlalchemy.orm import Session
import logging

from app.db.models import ResearcherProfile, ResearcherProfileDetails, User
from app.repositories import profiles as profile_repository
from app.schemas.profile_details import ResearcherProfileDetailsUpsert
from app.schemas.profiles import ResearcherProfileCreate
from app.services.serialization import pack_list

logger = logging.getLogger(__name__)


def create_profile(
    db: Session,
    payload: ResearcherProfileCreate,
    current_user: User | None,
) -> ResearcherProfile:
    profile = ResearcherProfile(
        user_id=current_user.id if current_user else None,
        full_name=payload.full_name,
        email=payload.email,
        career_stage=payload.career_stage,
        country=payload.country,
        disciplines=pack_list(payload.disciplines),
        keywords=pack_list(payload.keywords),
        preferred_countries=pack_list(payload.preferred_countries),
        orcid_id=payload.orcid_id,
        google_scholar_url=str(payload.google_scholar_url) if payload.google_scholar_url else None,
        linkedin_url=str(payload.linkedin_url) if payload.linkedin_url else None,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    db.add(ResearcherProfileDetails(profile_id=profile.id))
    db.commit()
    logger.info("created profile embedding cache row profile_id=%s", profile.id)
    return profile


def update_profile(
    db: Session,
    profile: ResearcherProfile,
    payload: ResearcherProfileCreate,
) -> ResearcherProfile:
    profile.full_name = payload.full_name
    profile.email = payload.email
    profile.career_stage = payload.career_stage
    profile.country = payload.country
    profile.disciplines = pack_list(payload.disciplines)
    profile.keywords = pack_list(payload.keywords)
    profile.preferred_countries = pack_list(payload.preferred_countries)
    profile.orcid_id = payload.orcid_id
    profile.google_scholar_url = str(payload.google_scholar_url) if payload.google_scholar_url else None
    profile.linkedin_url = str(payload.linkedin_url) if payload.linkedin_url else None
    db.commit()
    db.refresh(profile)
    details = profile_repository.get_profile_details(db, profile.id)
    if details is not None:
        details.profile_embedding = ""
        details.embedding_model = ""
        db.commit()
        logger.info("invalidated profile embedding cache profile_id=%s reason=profile_update", profile.id)
    return profile


def upsert_profile_details(
    db: Session,
    profile_id: int,
    payload: ResearcherProfileDetailsUpsert,
) -> ResearcherProfileDetails:
    details = profile_repository.get_or_create_profile_details(db, profile_id)
    details.research_summary = payload.research_summary
    details.publications = pack_list(payload.publications)
    details.degrees = pack_list(payload.degrees)
    details.languages = pack_list(payload.languages)
    details.funding_interests = pack_list(payload.funding_interests)
    details.unavailable_countries = pack_list(payload.unavailable_countries)
    details.preferred_opportunity_types = pack_list([item.value for item in payload.preferred_opportunity_types])
    details.min_duration_months = payload.min_duration_months
    details.max_duration_months = payload.max_duration_months
    details.profile_embedding = ""
    details.embedding_model = ""
    db.commit()
    db.refresh(details)
    logger.info("invalidated profile embedding cache profile_id=%s reason=details_update", profile_id)
    return details
