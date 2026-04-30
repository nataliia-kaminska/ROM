from typing import Any

import httpx

from app.core.config import settings


class OrcidClient:
    def __init__(self, http_client: httpx.Client | None = None, base_url: str | None = None) -> None:
        self.http_client = http_client or httpx.Client(timeout=20)
        self.base_url = (base_url or settings.orcid_base_url).rstrip("/")

    def read_public_record(self, orcid_id: str) -> dict[str, Any]:
        response = self.http_client.get(
            f"{self.base_url}/{orcid_id}/record",
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()


def extract_profile_payload(orcid_id: str, record: dict[str, Any]) -> dict[str, Any]:
    person = record.get("person") or {}
    name = person.get("name") or {}
    biography = person.get("biography") or {}
    keywords = person.get("keywords") or {}
    addresses = person.get("addresses") or {}
    researcher_urls = person.get("researcher-urls") or {}

    given = _nested_value(name, "given-names", "value")
    family = _nested_value(name, "family-name", "value")
    credit_name = _nested_value(name, "credit-name", "value")
    full_name = " ".join(part for part in (given, family) if part).strip() or credit_name or f"ORCID {orcid_id}"

    extracted_keywords = [
        keyword.get("content")
        for keyword in keywords.get("keyword", [])
        if isinstance(keyword, dict) and keyword.get("content")
    ]

    country = None
    address_items = addresses.get("address", [])
    if address_items:
        country = _nested_value(address_items[0], "country", "value")

    urls = _extract_researcher_urls(researcher_urls)

    return {
        "full_name": full_name,
        "country": country,
        "keywords": extracted_keywords,
        "summary": _nested_value(biography, "content"),
        "orcid_id": orcid_id,
        "google_scholar_url": _find_url(urls, "scholar.google"),
        "linkedin_url": _find_url(urls, "linkedin.com"),
        "external_urls": urls,
    }


def _nested_value(source: dict[str, Any], *keys: str) -> str | None:
    current: Any = source
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return str(current).strip() if current else None


def _extract_researcher_urls(source: dict[str, Any]) -> list[str]:
    urls = []
    for item in source.get("researcher-url", []):
        value = _nested_value(item, "url", "value")
        if value:
            urls.append(value)
    return urls


def _find_url(urls: list[str], needle: str) -> str | None:
    for url in urls:
        if needle in url.lower():
            return url
    return None

