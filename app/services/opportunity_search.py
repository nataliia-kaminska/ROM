import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Opportunity, OpportunityType
from app.infrastructure.search.elasticsearch import ElasticsearchOpportunitySearch
from app.repositories import opportunities as opportunity_repository


logger = logging.getLogger(__name__)


def list_opportunities_with_search(
    db: Session,
    source: str | None = None,
    opportunity_type: OpportunityType | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Opportunity]:
    if keyword and settings.elasticsearch_enabled:
        try:
            filters = {
                "source": source or "",
                "opportunity_type": opportunity_type.value if opportunity_type else "",
            }
            ids = ElasticsearchOpportunitySearch().search_opportunity_ids(keyword, limit=limit, offset=offset, filters=filters)
            if ids:
                by_id = {item.id: item for item in db.query(Opportunity).filter(Opportunity.id.in_(ids)).all()}
                opportunities = [by_id[item_id] for item_id in ids if item_id in by_id]
                if country:
                    opportunities = [item for item in opportunities if country.casefold() in item.countries.casefold()]
                if career_stage:
                    opportunities = [item for item in opportunities if career_stage.casefold() in item.career_stages.casefold()]
                return opportunities
        except Exception:
            logger.exception("elasticsearch opportunity search failed; falling back to database search")

    return opportunity_repository.list_opportunities(
        db,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        keyword=keyword,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )


def index_opportunity_for_search(opportunity: Opportunity) -> None:
    if not settings.elasticsearch_enabled or opportunity.id is None:
        return
    try:
        ElasticsearchOpportunitySearch().index_opportunity(opportunity)
    except Exception:
        logger.exception("failed to index opportunity in elasticsearch")
