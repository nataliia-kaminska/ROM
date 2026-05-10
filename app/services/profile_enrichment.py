import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ResearcherProfile, ResearcherProfileDetails
from app.integrations.openalex.client import OpenAlexClient
from app.integrations.openalex.mapper import extract_openalex_profile
from app.services.embeddings import persist_profile_embedding_vector
from app.services.serialization import pack_list, unpack_list

logger = logging.getLogger(__name__)


@dataclass
class ProfileTermEnrichment:
    disciplines: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    funding_interests: list[str] = field(default_factory=list)
    provider: str = "deterministic"


DISCIPLINE_HINTS = {
    "Artificial Intelligence": ["artificial intelligence", "machine learning", "deep learning", "computer vision", "natural language processing"],
    "Bioinformatics": ["bioinformatics", "genomics", "computational biology"],
    "Biology": ["biology", "molecular biology", "ecology"],
    "Chemistry": ["chemistry", "chemical"],
    "Climate Science": ["climate", "climate change"],
    "Computer Science": ["computer science", "software engineering", "algorithms", "data science"],
    "Economics": ["economics", "econometrics"],
    "Engineering": ["engineering", "robotics"],
    "Environmental Science": ["environmental science", "sustainability"],
    "Mathematics": ["mathematics", "statistics"],
    "Medicine": ["medicine", "medical", "clinical", "healthcare"],
    "Neuroscience": ["neuroscience"],
    "Physics": ["physics", "quantum"],
    "Political Science": ["political science", "public policy"],
    "Psychology": ["psychology"],
    "Public Health": ["public health", "epidemiology", "health equity"],
    "Social Sciences": ["sociology", "anthropology", "social science"],
}


def enrich_profile_from_openalex(
    db: Session,
    profile: ResearcherProfile,
    openalex_author_id: str | None = None,
    orcid_id: str | None = None,
    max_works: int | None = None,
    client: OpenAlexClient | None = None,
) -> tuple[ResearcherProfileDetails, dict[str, Any]] | None:
    source_client = client or OpenAlexClient()
    author = source_client.read_author(author_id=openalex_author_id, orcid_id=orcid_id or profile.orcid_id)
    if not author:
        return None
    author_id = author.get("id") or openalex_author_id
    works = source_client.read_works(author_id, max_works or settings.profile_enrichment_max_works) if author_id else []
    extracted = extract_openalex_profile(author, works)
    details = apply_openalex_enrichment(db, profile, extracted)
    logger.info("profile enriched from openalex profile_id=%s works=%s concepts=%s", profile.id, len(extracted["works"]), len(extracted["concepts"]))
    return details, extracted


def apply_openalex_enrichment(
    db: Session,
    profile: ResearcherProfile,
    extracted: dict[str, Any],
) -> ResearcherProfileDetails:
    concepts = [item for item in extracted.get("concepts", []) if isinstance(item, str)]
    works = [item for item in extracted.get("works", []) if isinstance(item, str)]
    normalized = normalize_profile_concepts(concepts)

    profile.disciplines = pack_list(_merge(unpack_list(profile.disciplines), normalized.disciplines))
    profile.keywords = pack_list(_merge(unpack_list(profile.keywords), normalized.keywords))

    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    if details is None:
        details = ResearcherProfileDetails(profile_id=profile.id)
        db.add(details)

    details.publications = pack_list(_merge(unpack_list(details.publications), works, limit=80))
    details.funding_interests = pack_list(_merge(unpack_list(details.funding_interests), normalized.funding_interests))
    if extracted.get("summary") and not details.research_summary:
        details.research_summary = str(extracted["summary"])
    details.profile_embedding = ""
    db.flush()
    persist_profile_embedding_vector(db, profile, details)
    logger.info(
        "profile metadata normalized provider=%s profile_id=%s disciplines=%s keywords=%s funding_interests=%s publications=%s",
        normalized.provider,
        profile.id,
        len(normalized.disciplines),
        len(normalized.keywords),
        len(normalized.funding_interests),
        len(works),
    )
    return details


def normalize_profile_concepts(concepts: list[str]) -> ProfileTermEnrichment:
    deterministic = _deterministic_concept_enrichment(concepts)
    provider = settings.profile_enrichment_provider.strip().lower()
    if provider == "groq":
        ai_result = _normalize_with_chat_completion(
            provider="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=settings.profile_enrichment_model or settings.groq_model,
            concepts=concepts,
        )
    elif provider == "local":
        ai_result = _normalize_with_chat_completion(
            provider="local",
            base_url=settings.advisor_local_base_url.rstrip("/"),
            api_key="local",
            model=settings.profile_enrichment_model or settings.advisor_local_model,
            concepts=concepts,
        )
    else:
        ai_result = None
    if ai_result is None:
        return deterministic
    return ProfileTermEnrichment(
        disciplines=_merge(deterministic.disciplines, ai_result.disciplines),
        keywords=_merge(deterministic.keywords, ai_result.keywords),
        funding_interests=_merge(deterministic.funding_interests, ai_result.funding_interests),
        provider=ai_result.provider,
    )


def _deterministic_concept_enrichment(concepts: list[str]) -> ProfileTermEnrichment:
    disciplines = []
    for concept in concepts:
        lower = concept.casefold()
        for discipline, hints in DISCIPLINE_HINTS.items():
            if any(hint in lower for hint in hints):
                disciplines.append(discipline)
    return ProfileTermEnrichment(
        disciplines=_merge(disciplines),
        keywords=_merge(concepts, limit=24),
        funding_interests=_merge(concepts, limit=16),
    )


def _normalize_with_chat_completion(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    concepts: list[str],
) -> ProfileTermEnrichment | None:
    if provider == "groq" and not api_key:
        return None
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0,
                "max_tokens": 350,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Normalize OpenAlex concepts into researcher profile metadata. Return only JSON with "
                            "disciplines, keywords, and funding_interests arrays. Use concise academic terms."
                        ),
                    },
                    {"role": "user", "content": json.dumps({"concepts": concepts[:40]}, ensure_ascii=False)},
                ],
            },
            timeout=settings.profile_enrichment_timeout_seconds,
        )
        response.raise_for_status()
        payload = json.loads(response.json()["choices"][0]["message"]["content"])
        return ProfileTermEnrichment(
            disciplines=_clean_terms(payload.get("disciplines", [])),
            keywords=_clean_terms(payload.get("keywords", []), limit=24),
            funding_interests=_clean_terms(payload.get("funding_interests", []), limit=16),
            provider=provider,
        )
    except Exception as exc:
        logger.warning("profile enrichment provider=%s failed; using deterministic fallback: %s", provider, exc)
        return None


def _merge(*groups: list[str], limit: int = 24) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for item in _clean_terms(group, limit=limit):
            key = item.casefold()
            if key not in seen:
                seen.add(key)
                result.append(item)
    return sorted(result)[:limit]


def _clean_terms(values: object, limit: int = 24) -> list[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = " ".join(value.strip().split())
        if 2 < len(cleaned) <= 70 and not cleaned.lower().startswith("http"):
            result.append(cleaned)
    return result[:limit]
