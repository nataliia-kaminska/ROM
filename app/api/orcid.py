from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.db.session import get_db
from app.integrations.orcid.client import OrcidClient
from app.integrations.orcid.service import import_orcid_profile as import_orcid_profile_service
from app.modules.profiles.mappers import to_profile_read
from app.schemas.orcid import OrcidImportRequest, OrcidImportResult


router = APIRouter(prefix="/integrations/orcid", tags=["integrations"])


@router.post("/import", response_model=OrcidImportResult)
def import_orcid_profile(
    payload: OrcidImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> OrcidImportResult:
    result = import_orcid_profile_service(
        db,
        payload,
        current_user,
        client=OrcidClient(),
    )
    return OrcidImportResult(imported=result.imported, profile=to_profile_read(result.profile), preview=result.preview)
