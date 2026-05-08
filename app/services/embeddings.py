import hashlib
import json
import math
import re
from datetime import datetime
from functools import lru_cache
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

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


class EmbeddingProvider(Protocol):
    name: str
    model_name: str
    dimensions: int

    def embed(self, text: str) -> list[float]:
        ...


class HashEmbeddingProvider:
    name = "hash"

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions
        self.model_name = f"hash-{dimensions}"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for term in _terms(text):
            digest = hashlib.sha256(term.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        return _normalize(vector)


class SentenceTransformerEmbeddingProvider:
    name = "sentence_transformers"

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install with `pip install -e .[embeddings]` "
                "or set EMBEDDING_PROVIDER=hash."
            ) from exc
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimensions = int(self.model.get_sentence_embedding_dimension())

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text or "", normalize_embeddings=True)
        return [float(value) for value in vector]


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower().strip()
    if provider in {"sentence_transformers", "local_model", "local"}:
        return SentenceTransformerEmbeddingProvider(settings.embedding_model_name)
    return HashEmbeddingProvider(settings.embedding_dimensions)


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
    if dimensions is not None:
        return HashEmbeddingProvider(dimensions).embed(text)
    return get_embedding_provider().embed(text)


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
    provider = get_embedding_provider()
    if details is None:
        return embed_text(profile_embedding_text(profile))
    existing = deserialize_embedding(details.profile_embedding)
    if existing and details.embedding_model == provider.model_name:
        return existing
    vector = embed_text(profile_embedding_text(profile, details))
    details.profile_embedding = serialize_embedding(vector)
    details.embedding_model = provider.model_name
    details.embedding_updated_at = datetime.utcnow()
    return vector


def ensure_opportunity_embedding(opportunity: Opportunity) -> list[float]:
    provider = get_embedding_provider()
    existing = deserialize_embedding(opportunity.opportunity_embedding)
    if existing and opportunity.embedding_model == provider.model_name:
        return existing
    vector = embed_text(opportunity_embedding_text(opportunity))
    opportunity.opportunity_embedding = serialize_embedding(vector)
    opportunity.embedding_model = provider.model_name
    opportunity.embedding_updated_at = datetime.utcnow()
    return vector


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def refresh_opportunity_embeddings(db: Session) -> dict:
    opportunities = db.query(Opportunity).all()
    for opportunity in opportunities:
        opportunity.opportunity_embedding = ""
        vector = ensure_opportunity_embedding(opportunity)
        if db.bind and db.bind.dialect.name == "postgresql":
            db.execute(
                text(
                    "UPDATE opportunities "
                    "SET opportunity_embedding_vector = CAST(:vector AS vector) "
                    "WHERE id = :id"
                ),
                {"vector": vector_literal(vector), "id": opportunity.id},
            )
    db.commit()
    return {"opportunity_count": len(opportunities)}


def refresh_profile_embeddings(db: Session) -> dict:
    details_records = db.query(ResearcherProfileDetails).all()
    refreshed = 0
    for details in details_records:
        profile = db.get(ResearcherProfile, details.profile_id)
        if profile is None:
            continue
        details.profile_embedding = ""
        vector = ensure_profile_embedding(profile, details)
        if db.bind and db.bind.dialect.name == "postgresql":
            db.execute(
                text(
                    "UPDATE researcher_profile_details "
                    "SET profile_embedding_vector = CAST(:vector AS vector) "
                    "WHERE id = :id"
                ),
                {"vector": vector_literal(vector), "id": details.id},
            )
        refreshed += 1
    db.commit()
    return {"profile_count": refreshed}


def refresh_all_embeddings(db: Session) -> dict:
    return {
        "profiles": refresh_profile_embeddings(db),
        "opportunities": refresh_opportunity_embeddings(db),
    }


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
