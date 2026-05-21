from typing import Any

import httpx


GRANTS_GOV_SEARCH_URL = "https://api.grants.gov/v1/api/search2"


class GrantsGovClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http_client = http_client or httpx.Client(timeout=20)

    def search(self, keyword: str, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        payload = {"keyword": keyword, "rows": limit, "startRecordNum": offset}
        response = self.http_client.post(GRANTS_GOV_SEARCH_URL, json=payload)
        response.raise_for_status()
        body = response.json()
        return _extract_hits(body)[:limit]


def _extract_hits(body: dict[str, Any]) -> list[dict[str, Any]]:
    data = body.get("data", body)
    for key in ("oppHits", "opportunities", "results", "hits"):
        value = data.get(key) if isinstance(data, dict) else None
        if isinstance(value, list):
            return value
    if isinstance(data, list):
        return data
    return []
