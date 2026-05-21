import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Opportunity
from app.infrastructure.search.elasticsearch import ElasticsearchOpportunitySearch
from app.repositories import opportunities as opportunity_repository


logger = logging.getLogger(__name__)


def list_opportunities_with_search(
    db: Session,
    source: str | None = None,
    opportunity_type: str | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
    sort_by: str = "deadline",
    sort_order: str = "asc",
    limit: int = 50,
    offset: int = 0,
) -> list[Opportunity]:
    has_multi_value_filters = any(_has_multiple_values(value) for value in [keyword, source, opportunity_type, country, career_stage])
    if keyword and settings.elasticsearch_enabled and not has_multi_value_filters and sort_by == "relevance":
        try:
            logger.info(
                "search opportunities using elasticsearch keyword=%s source=%s type=%s limit=%s offset=%s",
                keyword,
                source,
                opportunity_type,
                limit,
                offset,
            )
            filters = {
                "source": source or "",
                "opportunity_type": opportunity_type or "",
            }
            ids = ElasticsearchOpportunitySearch().search_opportunity_ids(keyword, limit=limit, offset=offset, filters=filters)
            if ids:
                logger.info("elasticsearch returned opportunities count=%s", len(ids))
                by_id = {item.id: item for item in db.query(Opportunity).filter(Opportunity.id.in_(ids)).all()}
                opportunities = [by_id[item_id] for item_id in ids if item_id in by_id]
                if country:
                    opportunities = [item for item in opportunities if country.casefold() in item.countries.casefold()]
                if career_stage:
                    opportunities = [item for item in opportunities if career_stage.casefold() in item.career_stages.casefold()]
                return opportunities
            logger.info("elasticsearch returned no opportunities keyword=%s", keyword)
        except Exception:
            logger.exception("elasticsearch opportunity search failed; falling back to database search")

    logger.info(
        "search opportunities using database keyword=%s source=%s type=%s active_only=%s limit=%s offset=%s",
        keyword,
        source,
        opportunity_type,
        active_only,
        limit,
        offset,
    )
    return opportunity_repository.list_opportunities(
        db,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        keyword=keyword,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


def count_opportunities_with_search(
    db: Session,
    source: str | None = None,
    opportunity_type: str | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
) -> int:
    return opportunity_repository.count_opportunities(
        db,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        keyword=keyword,
        active_only=active_only,
    )


def _has_multiple_values(value: str | None) -> bool:
    return bool(value and "," in value)


def index_opportunity_for_search(opportunity: Opportunity) -> None:
    if not settings.elasticsearch_enabled or not settings.elasticsearch_index_on_import or opportunity.id is None:
        logger.debug(
            "skip elasticsearch indexing opportunity_id=%s enabled=%s index_on_import=%s",
            opportunity.id,
            settings.elasticsearch_enabled,
            settings.elasticsearch_index_on_import,
        )
        return
    try:
        ElasticsearchOpportunitySearch().index_opportunity(opportunity)
        logger.info("indexed opportunity in elasticsearch opportunity_id=%s source=%s", opportunity.id, opportunity.source)
    except Exception:
        logger.exception("failed to index opportunity in elasticsearch")
