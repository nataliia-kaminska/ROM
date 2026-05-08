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
