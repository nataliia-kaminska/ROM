import logging
from typing import Any

import httpx

from app.core.config import settings
from app.db.models import Opportunity
from app.services.serialization import unpack_list


logger = logging.getLogger(__name__)


class ElasticsearchOpportunitySearch:
    def __init__(
        self,
        base_url: str | None = None,
        index_name: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (base_url or settings.elasticsearch_url).rstrip("/")
        self.index_name = index_name or settings.elasticsearch_opportunity_index
        self.client = client or httpx.Client(timeout=5)

    def search_opportunity_ids(
        self,
        keyword: str,
        limit: int,
        offset: int = 0,
        filters: dict[str, str] | None = None,
    ) -> list[int]:
        must: list[dict[str, Any]] = [
            {
                "multi_match": {
                    "query": keyword,
                    "fields": ["title^3", "summary^2", "eligibility", "keywords", "disciplines"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]
        filter_clauses = []
        for field, value in (filters or {}).items():
            if value:
                filter_clauses.append({"term": {field: value}})

        logger.debug("elasticsearch search index=%s keyword=%s filters=%s", self.index_name, keyword, filters)
        response = self.client.post(
            f"{self.base_url}/{self.index_name}/_search",
            json={
                "from": offset,
                "size": limit,
                "_source": ["id"],
                "query": {"bool": {"must": must, "filter": filter_clauses}},
            },
        )
        response.raise_for_status()
        hits = response.json().get("hits", {}).get("hits", [])
        ids = [int(hit["_source"]["id"]) for hit in hits if hit.get("_source", {}).get("id") is not None]
        logger.debug("elasticsearch search complete index=%s hits=%s", self.index_name, len(ids))
        return ids

    def index_opportunity(self, opportunity: Opportunity) -> None:
        logger.debug("elasticsearch index opportunity index=%s opportunity_id=%s", self.index_name, opportunity.id)
        response = self.client.put(
            f"{self.base_url}/{self.index_name}/_doc/{opportunity.id}",
            json=_opportunity_document(opportunity),
        )
        response.raise_for_status()


def _opportunity_document(opportunity: Opportunity) -> dict[str, Any]:
    return {
        "id": opportunity.id,
        "title": opportunity.title,
        "opportunity_type": opportunity.opportunity_type.value,
        "source": opportunity.source,
        "summary": opportunity.summary,
        "eligibility": opportunity.eligibility,
        "disciplines": unpack_list(opportunity.disciplines),
        "keywords": unpack_list(opportunity.keywords),
        "countries": unpack_list(opportunity.countries),
        "career_stages": unpack_list(opportunity.career_stages),
        "deadline": opportunity.deadline.isoformat() if opportunity.deadline else None,
    }


def search_enabled() -> bool:
    return settings.elasticsearch_enabled
