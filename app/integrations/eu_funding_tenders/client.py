import json
from typing import Any

import httpx


EU_FUNDING_TENDERS_SEARCH_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

OPEN_OR_FORTHCOMING_STATUS_CODES = ["31094501", "31094502"]

DISPLAY_FIELDS = [
    "type",
    "identifier",
    "reference",
    "callccm2Id",
    "title",
    "status",
    "caName",
    "startDate",
    "description",
    "deadlineDate",
    "deadlineModel",
    "frameworkProgramme",
    "programmePeriod",
    "typesOfAction",
]


class EUFundingTendersClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http_client = http_client or httpx.Client(timeout=25)

    def search(
        self,
        keyword: str,
        limit: int = 10,
        programme: str | None = None,
        page_number: int = 1,
        page_size: int | None = None,
    ) -> list[dict[str, Any]]:
        query = _query()
        search_text = " ".join(part for part in [keyword, programme or ""] if part).strip() or "***"
        page_size = page_size or limit
        files = {
            "sort": ("blob", json.dumps({"order": "DESC", "field": "startDate"}), "application/json"),
            "query": ("blob", json.dumps(query), "application/json"),
            "languages": ("blob", json.dumps(["en"]), "application/json"),
            "displayFields": ("blob", json.dumps(DISPLAY_FIELDS), "application/json"),
        }
        response = self.http_client.post(
            EU_FUNDING_TENDERS_SEARCH_URL,
            params={"apiKey": "SEDIA", "text": search_text, "pageSize": str(page_size), "pageNumber": str(page_number)},
            files=files,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://ec.europa.eu",
                "Referer": "https://ec.europa.eu/",
                "User-Agent": "Mozilla/5.0",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        response.raise_for_status()
        return _extract_hits(response.json())[:limit]


def _query() -> dict[str, Any]:
    must: list[dict[str, Any]] = [
        {"terms": {"type": ["1", "2", "8"]}},
        {"terms": {"status": OPEN_OR_FORTHCOMING_STATUS_CODES}},
        {"term": {"programmePeriod": "2021 - 2027"}},
    ]
    return {"bool": {"must": must}}


def _extract_hits(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if not isinstance(body, dict):
        return []
    for key in ("results", "hits", "items", "data"):
        value = body.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _extract_hits(value)
            if nested:
                return nested
    nested_hits = body.get("hits")
    if isinstance(nested_hits, dict):
        value = nested_hits.get("hits")
        if isinstance(value, list):
            return [item.get("_source", item) for item in value if isinstance(item, dict)]
    return []
