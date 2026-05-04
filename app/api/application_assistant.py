from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.db.models import Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.db.session import get_db
from app.schemas.application_assistant import ApplicationAssistantRead, ApplicationAssistantRequest
from app.services.application_assistant import build_application_assistant


router = APIRouter(prefix="/application-assistant", tags=["application assistant"])


@router.post("", response_model=ApplicationAssistantRead)
def create_application_assistant_notes(
    payload: ApplicationAssistantRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ApplicationAssistantRead:
    profile = ensure_profile_access(db.get(ResearcherProfile, payload.profile_id), current_user)
    opportunity = db.get(Opportunity, payload.opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    return build_application_assistant(profile, opportunity, details)
