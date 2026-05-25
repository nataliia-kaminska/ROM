from typing import Any


def extract_profile_payload(orcid_id: str, record: dict[str, Any]) -> dict[str, Any]:
    person = record.get("person") or {}
    name = person.get("name") or {}
    biography = person.get("biography") or {}
    keywords = person.get("keywords") or {}
    addresses = person.get("addresses") or {}
    researcher_urls = person.get("researcher-urls") or {}
    emails = person.get("emails") or {}

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
        "email": _extract_email(emails),
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


def _extract_email(source: dict[str, Any]) -> str | None:
    for item in source.get("email", []):
        value = _nested_value(item, "email")
        if value:
            return value.lower()
    return None
