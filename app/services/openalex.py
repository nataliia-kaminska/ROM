from typing import Any

import httpx

from app.core.config import settings


class OpenAlexClient:
    def __init__(self, http_client: httpx.Client | None = None, base_url: str | None = None) -> None:
        self.http_client = http_client or httpx.Client(timeout=20, follow_redirects=True)
        self.base_url = (base_url or settings.openalex_base_url).rstrip("/")

    def read_author(self, author_id: str | None = None, orcid_id: str | None = None) -> dict[str, Any]:
        if author_id:
            response = self.http_client.get(f"{self.base_url}/authors/{_normalize_author_id(author_id)}")
        elif orcid_id:
            response = self.http_client.get(f"{self.base_url}/authors", params={"filter": f"orcid:{orcid_id}"})
        else:
            raise ValueError("openalex_author_id or orcid_id is required")
        response.raise_for_status()
        body = response.json()
        if "results" in body:
            results = body.get("results") or []
            return results[0] if results else {}
        return body

    def read_works(self, author_id: str, limit: int = 10) -> list[dict[str, Any]]:
        response = self.http_client.get(
            f"{self.base_url}/works",
            params={"filter": f"authorships.author.id:{_full_author_url(author_id)}", "per-page": limit},
        )
        response.raise_for_status()
        body = response.json()
        return body.get("results", []) if isinstance(body, dict) else []


def extract_openalex_profile(author: dict[str, Any], works: list[dict[str, Any]]) -> dict[str, Any]:
    author_id = author.get("id")
    concepts = [
        item.get("display_name")
        for item in author.get("x_concepts", [])
        if isinstance(item, dict) and item.get("display_name")
    ]
    work_titles = [
        work.get("display_name") or work.get("title")
        for work in works
        if isinstance(work, dict) and (work.get("display_name") or work.get("title"))
    ]
    work_concepts = []
    for work in works:
        for concept in work.get("concepts", []) if isinstance(work, dict) else []:
            name = concept.get("display_name") if isinstance(concept, dict) else None
            if name:
                work_concepts.append(name)
    return {
        "display_name": author.get("display_name") or "",
        "openalex_author_id": author_id,
        "concepts": sorted(set(concepts + work_concepts)),
        "works": work_titles,
        "summary": _summary(author, concepts, work_titles),
    }


def _summary(author: dict[str, Any], concepts: list[str], works: list[str]) -> str:
    name = author.get("display_name") or "This researcher"
    concept_text = ", ".join(concepts[:5])
    count = author.get("works_count")
    if concept_text and count:
        return f"{name} has {count} OpenAlex-indexed works with activity in {concept_text}."
    if concept_text:
        return f"{name} has OpenAlex-indexed activity in {concept_text}."
    if works:
        return f"{name} has OpenAlex-indexed publications including {works[0]}."
    return ""


def _normalize_author_id(author_id: str) -> str:
    return author_id.rstrip("/").split("/")[-1]


def _full_author_url(author_id: str) -> str:
    normalized = _normalize_author_id(author_id)
    return f"https://openalex.org/{normalized}"
