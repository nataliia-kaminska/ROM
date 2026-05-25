from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.db.session import get_db
from app.modules.profiles.mappers import to_profile_details_read, to_profile_read
from app.repositories import profiles as profile_repository
from app.schemas.profile_discovery import ProfileDiscoveryApplyRequest, ProfileDiscoveryApplyResult, ProfileDiscoveryCandidate
from app.schemas.profile_details import ResearcherProfileDetailsRead, ResearcherProfileDetailsUpsert
from app.schemas.profiles import ResearcherProfileCreate, ResearcherProfileRead
from app.services import profile_discovery
from app.services import profiles as profile_service


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ResearcherProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ResearcherProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileRead:
    return to_profile_read(profile_service.create_profile(db, payload, current_user))


@router.get("/me", response_model=list[ResearcherProfileRead])
def list_my_profiles(
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> list[ResearcherProfileRead]:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    profiles = profile_repository.list_profiles_for_user(db, current_user)
    return [to_profile_read(profile) for profile in profiles]


@router.get("/{profile_id}", response_model=ResearcherProfileRead)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileRead:
    profile = ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return to_profile_read(profile)


@router.put("/{profile_id}", response_model=ResearcherProfileRead)
def update_profile(
    profile_id: int,
    payload: ResearcherProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileRead:
    profile = ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return to_profile_read(profile_service.update_profile(db, profile, payload))


@router.put("/{profile_id}/details", response_model=ResearcherProfileDetailsRead)
def upsert_profile_details(
    profile_id: int,
    payload: ResearcherProfileDetailsUpsert,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileDetailsRead:
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return to_profile_details_read(profile_service.upsert_profile_details(db, profile_id, payload))


@router.get("/{profile_id}/details", response_model=ResearcherProfileDetailsRead)
def get_profile_details(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ResearcherProfileDetailsRead:
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    details = profile_repository.get_profile_details(db, profile_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Profile details not found")
    return to_profile_details_read(details)


@router.get("/{profile_id}/discovery", response_model=list[ProfileDiscoveryCandidate])
def discover_profile_evidence(
    profile_id: int,
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> list[ProfileDiscoveryCandidate]:
    profile = ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return profile_discovery.discover_profile_candidates(profile, limit)


@router.post("/{profile_id}/discovery/apply", response_model=ProfileDiscoveryApplyResult)
def apply_profile_evidence(
    profile_id: int,
    payload: ProfileDiscoveryApplyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ProfileDiscoveryApplyResult:
    profile = ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return profile_discovery.apply_profile_candidate(db, profile, payload)
