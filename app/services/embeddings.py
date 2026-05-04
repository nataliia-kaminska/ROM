import hashlib
import json
import math
import re
from datetime import datetime

from app.core.config import settings
from app.db.models import Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.services.serialization import unpack_list


STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "for",
    "from",
    "into",
    "open",
    "that",
    "the",
    "this",
    "with",
    "your",
}


def profile_embedding_text(profile: ResearcherProfile, details: ResearcherProfileDetails | None = None) -> str:
    parts = [
        profile.full_name,
        profile.career_stage.value,
        profile.country or "",
        *unpack_list(profile.disciplines),
        *unpack_list(profile.keywords),
        *unpack_list(profile.preferred_countries),
    ]
    if details:
        parts.extend(
            [
                details.research_summary,
                *unpack_list(details.publications),
                *unpack_list(details.degrees),
                *unpack_list(details.languages),
                *unpack_list(details.funding_interests),
                *unpack_list(details.preferred_opportunity_types),
            ]
        )
    return " ".join(parts)


def opportunity_embedding_text(opportunity: Opportunity) -> str:
    return " ".join(
        [
            opportunity.title,
            opportunity.opportunity_type.value,
            opportunity.source,
            opportunity.summary,
            opportunity.eligibility,
            *unpack_list(opportunity.disciplines),
            *unpack_list(opportunity.keywords),
            *unpack_list(opportunity.countries),
            *unpack_list(opportunity.career_stages),
        ]
    )


def embed_text(text: str, dimensions: int | None = None) -> list[float]:
    size = dimensions or settings.embedding_dimensions
    vector = [0.0] * size
    for term in _terms(text):
        digest = hashlib.sha256(term.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % size
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    return _normalize(vector)


def serialize_embedding(vector: list[float]) -> str:
    return json.dumps([round(value, 6) for value in vector], separators=(",", ":"))


def deserialize_embedding(value: str | None) -> list[float]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [float(item) for item in parsed if isinstance(item, int | float)]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def ensure_profile_embedding(profile: ResearcherProfile, details: ResearcherProfileDetails | None) -> list[float]:
    if details is None:
        return embed_text(profile_embedding_text(profile))
    existing = deserialize_embedding(details.profile_embedding)
    if existing:
        return existing
    vector = embed_text(profile_embedding_text(profile, details))
    details.profile_embedding = serialize_embedding(vector)
    details.embedding_updated_at = datetime.utcnow()
    return vector


def ensure_opportunity_embedding(opportunity: Opportunity) -> list[float]:
    existing = deserialize_embedding(opportunity.opportunity_embedding)
    if existing:
        return existing
    vector = embed_text(opportunity_embedding_text(opportunity))
    opportunity.opportunity_embedding = serialize_embedding(vector)
    opportunity.embedding_updated_at = datetime.utcnow()
    return vector


def _terms(text: str) -> list[str]:
    return [
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", text.lower())
        if term not in STOP_WORDS
    ]


def _normalize(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in vector))
    if not length:
        return vector
    return [value / length for value in vector]
