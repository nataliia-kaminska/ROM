from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.db.models import ResearcherProfile, ResearcherProfileDetails, User
from app.integrations.openalex.client import OpenAlexClient
from app.integrations.openalex.mapper import extract_openalex_profile
from app.schemas.openalex import OpenAlexImportPreview, OpenAlexImportRequest
from app.services.profile_enrichment import apply_openalex_enrichment, normalize_profile_concepts
from app.services.results import OpenAlexProfileImportResult
from app.services.serialization import unpack_list


def import_openalex_profile(
    db: Session,
    payload: OpenAlexImportRequest,
    current_user: User | None,
    client: OpenAlexClient | None = None,
) -> OpenAlexProfileImportResult:
    profile, extracted = _load_openalex_profile_data(db, payload, current_user, client)
    existing_details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    preview = build_openalex_preview(profile, existing_details, extracted)
    details = apply_openalex_enrichment(db, profile, extracted)

    db.commit()
    db.refresh(profile)
    db.refresh(details)
    return OpenAlexProfileImportResult(profile=profile, details=details, preview=preview)


def preview_openalex_profile(
    db: Session,
    payload: OpenAlexImportRequest,
    current_user: User | None,
    client: OpenAlexClient | None = None,
) -> OpenAlexImportPreview:
    profile, extracted = _load_openalex_profile_data(db, payload, current_user, client)
    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    return build_openalex_preview(profile, details, extracted)


def build_openalex_preview(
    profile: ResearcherProfile,
    details,
    extracted: dict,
) -> OpenAlexImportPreview:
    concepts = [item for item in extracted.get("concepts", []) if isinstance(item, str)]
    works = [item for item in extracted.get("works", []) if isinstance(item, str)]
    normalized = normalize_profile_concepts(concepts, extracted.get("concept_records", []))
    existing_publications = set(unpack_list(details.publications)) if details is not None else set()
    new_publications = [work for work in works if work not in existing_publications]
    return OpenAlexImportPreview(
        display_name=extracted.get("display_name", ""),
        summary=extracted.get("summary", ""),
        concepts=concepts,
        works=works,
        openalex_author_id=extracted.get("openalex_author_id"),
        suggested_disciplines=normalized.disciplines,
        suggested_keywords=normalized.keywords,
        suggested_funding_interests=normalized.funding_interests,
        new_publications=new_publications,
        existing_publications=len(existing_publications),
        works_count=len(works),
    )


def _load_openalex_profile_data(
    db: Session,
    payload: OpenAlexImportRequest,
    current_user: User | None,
    client: OpenAlexClient | None,
) -> tuple[ResearcherProfile, dict]:
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
    return profile, extract_openalex_profile(author, works)
