from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.db.models import ResearcherProfile, ResearcherProfileDetails
from app.db.session import get_db
from app.schemas.profile_details import ResearcherProfileDetailsRead, ResearcherProfileDetailsUpsert
from app.schemas.profiles import ResearcherProfileCreate, ResearcherProfileRead
from app.services.serialization import pack_list, unpack_list


router = APIRouter(prefix="/profiles", tags=["profiles"])


def _to_read(profile: ResearcherProfile) -> ResearcherProfileRead:
    return ResearcherProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        email=profile.email,
        career_stage=profile.career_stage,
        country=profile.country,
        disciplines=unpack_list(profile.disciplines),
        keywords=unpack_list(profile.keywords),
        preferred_countries=unpack_list(profile.preferred_countries),
        orcid_id=profile.orcid_id,
        google_scholar_url=profile.google_scholar_url,
        linkedin_url=profile.linkedin_url,
    )


def _details_to_read(details: ResearcherProfileDetails) -> ResearcherProfileDetailsRead:
    return ResearcherProfileDetailsRead(
        id=details.id,
        profile_id=details.profile_id,
        research_summary=details.research_summary,
        publications=unpack_list(details.publications),
        degrees=unpack_list(details.degrees),
        languages=unpack_list(details.languages),
        funding_interests=unpack_list(details.funding_interests),
        unavailable_countries=unpack_list(details.unavailable_countries),
        preferred_opportunity_types=unpack_list(details.preferred_opportunity_types),
        min_duration_months=details.min_duration_months,
        max_duration_months=details.max_duration_months,
    )


@router.post("", response_model=ResearcherProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ResearcherProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileRead:
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
    return _to_read(profile)


@router.get("/me", response_model=list[ResearcherProfileRead])
def list_my_profiles(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> list[ResearcherProfileRead]:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    profiles = db.query(ResearcherProfile).filter(ResearcherProfile.user_id == current_user.id).all()
    return [_to_read(profile) for profile in profiles]


@router.get("/{profile_id}", response_model=ResearcherProfileRead)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileRead:
    profile = ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)
    return _to_read(profile)


@router.put("/{profile_id}", response_model=ResearcherProfileRead)
def update_profile(
    profile_id: int,
    payload: ResearcherProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileRead:
    profile = ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)
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
    return _to_read(profile)


@router.put("/{profile_id}/details", response_model=ResearcherProfileDetailsRead)
def upsert_profile_details(
    profile_id: int,
    payload: ResearcherProfileDetailsUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileDetailsRead:
    ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)

    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile_id).first()
    if details is None:
        details = ResearcherProfileDetails(profile_id=profile_id)
        db.add(details)

    details.research_summary = payload.research_summary
    details.publications = pack_list(payload.publications)
    details.degrees = pack_list(payload.degrees)
    details.languages = pack_list(payload.languages)
    details.funding_interests = pack_list(payload.funding_interests)
    details.unavailable_countries = pack_list(payload.unavailable_countries)
    details.preferred_opportunity_types = pack_list([item.value for item in payload.preferred_opportunity_types])
    details.min_duration_months = payload.min_duration_months
    details.max_duration_months = payload.max_duration_months

    db.commit()
    db.refresh(details)
    return _details_to_read(details)


@router.get("/{profile_id}/details", response_model=ResearcherProfileDetailsRead)
def get_profile_details(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileDetailsRead:
    ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)
    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile_id).first()
    if details is None:
        raise HTTPException(status_code=404, detail="Profile details not found")
    return _details_to_read(details)
