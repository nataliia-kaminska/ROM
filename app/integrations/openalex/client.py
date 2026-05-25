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
            params={"filter": f"authorships.author.id:{_full_author_url(author_id)}", "per-page": limit, "sort": "publication_date:desc"},
        )
        response.raise_for_status()
        body = response.json()
        return body.get("results", []) if isinstance(body, dict) else []


def _normalize_author_id(author_id: str) -> str:
    return author_id.rstrip("/").split("/")[-1]


def _full_author_url(author_id: str) -> str:
    normalized = _normalize_author_id(author_id)
    return f"https://openalex.org/{normalized}"
