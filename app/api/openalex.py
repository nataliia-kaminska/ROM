from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.api.profiles import _details_to_read, _to_read
from app.db.models import ResearcherProfile, ResearcherProfileDetails
from app.db.session import get_db
from app.schemas.openalex import OpenAlexImportPreview, OpenAlexImportRequest, OpenAlexImportResult
from app.services.openalex import OpenAlexClient, extract_openalex_profile
from app.services.serialization import pack_list, unpack_list


router = APIRouter(prefix="/integrations/openalex", tags=["integrations"])


@router.post("/import", response_model=OpenAlexImportResult)
def import_openalex_profile(
    payload: OpenAlexImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> OpenAlexImportResult:
    profile = ensure_profile_access(db.get(ResearcherProfile, payload.profile_id), current_user)
    orcid_id = payload.orcid_id or profile.orcid_id
    if not payload.openalex_author_id and not orcid_id:
        raise HTTPException(status_code=400, detail="Provide an OpenAlex author id or a profile with ORCID")

    client = OpenAlexClient()
    author = client.read_author(author_id=payload.openalex_author_id, orcid_id=orcid_id)
    if not author:
        raise HTTPException(status_code=404, detail="OpenAlex author not found")
    author_id = author.get("id") or payload.openalex_author_id
    works = client.read_works(author_id, payload.max_works) if author_id else []
    extracted = extract_openalex_profile(author, works)

    existing_keywords = set(unpack_list(profile.keywords))
    profile.keywords = pack_list(sorted(existing_keywords | set(extracted["concepts"][:12])))

    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    if details is None:
        details = ResearcherProfileDetails(profile_id=profile.id)
        db.add(details)
    existing_publications = set(unpack_list(details.publications))
    details.publications = pack_list(sorted(existing_publications | set(extracted["works"])))
    existing_interests = set(unpack_list(details.funding_interests))
    details.funding_interests = pack_list(sorted(existing_interests | set(extracted["concepts"][:8])))
    if extracted["summary"] and not details.research_summary:
        details.research_summary = extracted["summary"]
    details.profile_embedding = ""

    db.commit()
    db.refresh(profile)
    db.refresh(details)
    return OpenAlexImportResult(
        profile=_to_read(profile),
        details=_details_to_read(details),
        preview=OpenAlexImportPreview(
            display_name=extracted["display_name"],
            concepts=extracted["concepts"],
            works=extracted["works"],
            openalex_author_id=extracted["openalex_author_id"],
        ),
    )
