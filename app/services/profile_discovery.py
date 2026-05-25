import html
import logging
import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ResearcherProfile, ResearcherProfileDetails
from app.modules.profiles.mappers import to_profile_details_read, to_profile_read
from app.schemas.profile_discovery import ProfileDiscoveryApplyRequest, ProfileDiscoveryApplyResult, ProfileDiscoveryCandidate
from app.services.embeddings import persist_profile_embedding_vector
from app.services.external_fetch import ExternalSourceClient
from app.services.profile_enrichment import extract_profile_metadata_from_text
from app.services.serialization import pack_list, unpack_list
from app.services.web_research import duckduckgo_search_results

logger = logging.getLogger(__name__)


def discover_profile_candidates(profile: ResearcherProfile, limit: int | None = None) -> list[ProfileDiscoveryCandidate]:
    if not settings.profile_discovery_enabled:
        return []
    max_results = min(limit or settings.profile_discovery_max_results, settings.profile_discovery_max_results)
    name = profile.full_name.strip()
    if not name:
        return []
    query = _discovery_query(profile)
    results = duckduckgo_search_results(query, max_results * 2)
    candidates: list[ProfileDiscoveryCandidate] = []
    seen_urls: set[str] = set()
    for result in results:
        url = result.get("href", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        confidence = _confidence(name, result.get("title", ""), result.get("body", ""), url)
        if confidence < 35:
            continue
        candidates.append(
            ProfileDiscoveryCandidate(
                title=result.get("title", "")[:180],
                url=url,
                snippet=result.get("body", "")[:500],
                source=_source_label(url),
                confidence=confidence,
            )
        )
        if len(candidates) >= max_results:
            break
    logger.info("profile discovery complete profile_id=%s query=%s candidates=%s", profile.id, query, len(candidates))
    return candidates


def apply_profile_candidate(
    db: Session,
    profile: ResearcherProfile,
    payload: ProfileDiscoveryApplyRequest,
    client: ExternalSourceClient | None = None,
) -> ProfileDiscoveryApplyResult:
    source_client = client or ExternalSourceClient()
    page_text = _plain_text(source_client.fetch(str(payload.url)))
    candidate_text = " ".join([payload.title, payload.snippet, page_text[: settings.profile_discovery_page_max_chars]])
    metadata = extract_profile_metadata_from_text(profile.full_name, payload.title, str(payload.url), candidate_text)
    details = _get_or_create_details(db, profile.id)
    applied_fields = _apply_metadata(profile, details, str(payload.url), metadata)
    details.profile_embedding = ""
    details.embedding_model = ""
    db.flush()
    persist_profile_embedding_vector(db, profile, details)
    db.commit()
    db.refresh(profile)
    db.refresh(details)
    logger.info("profile discovery applied profile_id=%s url=%s fields=%s", profile.id, payload.url, ",".join(applied_fields))
    return ProfileDiscoveryApplyResult(
        profile=to_profile_read(profile),
        details=to_profile_details_read(details),
        candidate=ProfileDiscoveryCandidate(
            title=payload.title,
            url=payload.url,
            snippet=payload.snippet,
            source=_source_label(str(payload.url)),
            confidence=_confidence(profile.full_name, payload.title, payload.snippet, str(payload.url)),
        ),
        applied_fields=applied_fields,
    )


def _discovery_query(profile: ResearcherProfile) -> str:
    topics = " ".join(unpack_list(profile.disciplines)[:3] + unpack_list(profile.keywords)[:3])
    return f'"{profile.full_name}" researcher profile publications {topics}'.strip()


def _confidence(name: str, title: str, snippet: str, url: str) -> int:
    haystack = f"{title} {snippet} {url}".casefold()
    name_parts = [part for part in name.casefold().split() if len(part) > 1]
    score = 20
    if name.casefold() in haystack:
        score += 45
    else:
        score += min(30, sum(12 for part in name_parts if part in haystack))
    host = urlparse(url).netloc.casefold()
    if any(marker in host for marker in ("orcid", "openalex", "scholar.google", "linkedin", "researchgate", "academia", "edu")):
        score += 15
    if any(marker in haystack for marker in ("publication", "research", "profile", "scholar", "university", "orcid")):
        score += 10
    return min(score, 95)


def _source_label(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _plain_text(raw_html: str) -> str:
    without_scripts = re.sub(r"<(script|style).*?</\1>", " ", raw_html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(html.unescape(without_tags).split())


def _get_or_create_details(db: Session, profile_id: int) -> ResearcherProfileDetails:
    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile_id).first()
    if details is None:
        details = ResearcherProfileDetails(profile_id=profile_id)
        db.add(details)
        db.flush()
    return details


def _apply_metadata(profile: ResearcherProfile, details: ResearcherProfileDetails, url: str, metadata: dict) -> list[str]:
    applied: list[str] = []
    profile.disciplines = pack_list(_merge(unpack_list(profile.disciplines), metadata.get("disciplines", []), limit=18))
    profile.keywords = pack_list(_merge(unpack_list(profile.keywords), metadata.get("keywords", []), limit=28))
    applied.extend(["disciplines", "keywords"])
    if "linkedin.com" in urlparse(url).netloc.lower():
        profile.linkedin_url = url
        applied.append("linkedin_url")
    if "scholar.google" in urlparse(url).netloc.lower():
        profile.google_scholar_url = url
        applied.append("google_scholar_url")
    summary = str(metadata.get("research_summary") or "").strip()
    if summary:
        details.research_summary = _merge_summary(details.research_summary, summary)
        applied.append("research_summary")
    details.publications = pack_list(_merge(unpack_list(details.publications), metadata.get("publications", []), limit=80))
    details.degrees = pack_list(_merge(unpack_list(details.degrees), metadata.get("degrees", []), limit=16))
    details.languages = pack_list(_merge(unpack_list(details.languages), metadata.get("languages", []), limit=12))
    details.funding_interests = pack_list(_merge(unpack_list(details.funding_interests), metadata.get("funding_interests", []), limit=20))
    applied.extend(["publications", "degrees", "languages", "funding_interests"])
    return sorted(set(applied))


def _merge_summary(current: str | None, addition: str) -> str:
    if not current:
        return addition
    if addition.casefold() in current.casefold():
        return current
    return f"{current}\n\nConfirmed public profile evidence: {addition}"


def _merge(existing: list[str], incoming: object, limit: int) -> list[str]:
    values = incoming if isinstance(incoming, list) else []
    seen: set[str] = set()
    result: list[str] = []
    for value in [*existing, *values]:
        if not isinstance(value, str):
            continue
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result[:limit]
