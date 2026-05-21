from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.db.session import get_db
from app.integrations.openalex.client import OpenAlexClient
from app.integrations.openalex.service import import_openalex_profile as import_openalex_profile_service
from app.integrations.openalex.service import preview_openalex_profile as preview_openalex_profile_service
from app.modules.profiles.mappers import to_profile_details_read, to_profile_read
from app.schemas.openalex import OpenAlexImportPreview, OpenAlexImportRequest, OpenAlexImportResult


router = APIRouter(prefix="/integrations/openalex", tags=["integrations"])


@router.post("/import", response_model=OpenAlexImportResult)
def import_openalex_profile(
    payload: OpenAlexImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> OpenAlexImportResult:
    result = import_openalex_profile_service(
        db,
        payload,
        current_user,
        client=OpenAlexClient(),
    )
    return OpenAlexImportResult(
        profile=to_profile_read(result.profile),
        details=to_profile_details_read(result.details),
        preview=result.preview,
    )


@router.post("/preview", response_model=OpenAlexImportPreview)
def preview_openalex_profile(
    payload: OpenAlexImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    return preview_openalex_profile_service(
        db,
        payload,
        current_user,
        client=OpenAlexClient(),
    )
