from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError
from app.db.models import ResearcherProfile, User
from app.integrations.orcid.client import OrcidClient
from app.integrations.orcid.mapper import extract_profile_payload
from app.schemas.orcid import OrcidImportPreview, OrcidImportRequest
from app.services.results import OrcidProfileImportResult
from app.services.serialization import pack_list, unpack_list


def import_orcid_profile(
    db: Session,
    payload: OrcidImportRequest,
    current_user: User | None,
    client: OrcidClient | None = None,
) -> OrcidProfileImportResult:
    record = (client or OrcidClient()).read_public_record(payload.orcid_id)
    extracted = extract_profile_payload(payload.orcid_id, record)
    profile = db.query(ResearcherProfile).filter(ResearcherProfile.orcid_id == payload.orcid_id).first()
    imported = False

    if profile is None:
        profile = ResearcherProfile(
            user_id=current_user.id if current_user else None,
            full_name=extracted["full_name"],
            email=payload.email,
            career_stage=payload.career_stage,
            country=extracted["country"],
            disciplines=pack_list(payload.disciplines),
            keywords=pack_list(extracted["keywords"]),
            preferred_countries=pack_list(payload.preferred_countries),
            orcid_id=payload.orcid_id,
            google_scholar_url=extracted["google_scholar_url"],
            linkedin_url=extracted["linkedin_url"],
        )
        db.add(profile)
        imported = True
    else:
        if profile.user_id is not None and (current_user is None or profile.user_id != current_user.id):
            raise ForbiddenError("Profile access denied")
        existing_keywords = set(unpack_list(profile.keywords))
        profile.keywords = pack_list(sorted(existing_keywords | set(extracted["keywords"])))
        profile.country = profile.country or extracted["country"]
        profile.google_scholar_url = profile.google_scholar_url or extracted["google_scholar_url"]
        profile.linkedin_url = profile.linkedin_url or extracted["linkedin_url"]

    db.commit()
    db.refresh(profile)

    preview = OrcidImportPreview(
        full_name=extracted["full_name"],
        country=extracted["country"],
        keywords=extracted["keywords"],
        google_scholar_url=extracted["google_scholar_url"],
        linkedin_url=extracted["linkedin_url"],
        external_urls=extracted["external_urls"],
    )
    return OrcidProfileImportResult(profile=profile, preview=preview, imported=imported)
