from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.db.models import ResearcherProfile, ResearcherProfileDetails, User
from app.integrations.openalex.client import OpenAlexClient
from app.integrations.openalex.mapper import extract_openalex_profile
from app.schemas.openalex import OpenAlexImportPreview, OpenAlexImportRequest
from app.services.results import OpenAlexProfileImportResult
from app.services.serialization import pack_list, unpack_list


def import_openalex_profile(
    db: Session,
    payload: OpenAlexImportRequest,
    current_user: User | None,
    client: OpenAlexClient | None = None,
) -> OpenAlexProfileImportResult:
    profile = db.get(ResearcherProfile, payload.profile_id)
    if profile is None:
        raise NotFoundError("Profile not found")
    if profile.user_id is not None and (current_user is None or current_user.id != profile.user_id):
        raise ForbiddenError("Profile access denied")

    orcid_id = payload.orcid_id or profile.orcid_id
    if not payload.openalex_author_id and not orcid_id:
        raise BadRequestError("Provide an OpenAlex author id or a profile with ORCID")

    source_client = client or OpenAlexClient()
    author = source_client.read_author(author_id=payload.openalex_author_id, orcid_id=orcid_id)
    if not author:
        raise NotFoundError("OpenAlex author not found")
    author_id = author.get("id") or payload.openalex_author_id
    works = source_client.read_works(author_id, payload.max_works) if author_id else []
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
    preview = OpenAlexImportPreview(
        display_name=extracted["display_name"],
        concepts=extracted["concepts"],
        works=extracted["works"],
        openalex_author_id=extracted["openalex_author_id"],
    )
    return OpenAlexProfileImportResult(profile=profile, details=details, preview=preview)
