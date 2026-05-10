from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Opportunity, OpportunityType
from app.services.serialization import unpack_list


def get_opportunity(db: Session, opportunity_id: int) -> Opportunity | None:
    return db.get(Opportunity, opportunity_id)


def get_opportunity_by_url(db: Session, url: str) -> Opportunity | None:
    return db.query(Opportunity).filter(Opportunity.url == url).first()


def list_opportunities(
    db: Session,
    source: str | None = None,
    opportunity_type: OpportunityType | str | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Opportunity]:
    query = db.query(Opportunity)
    sources = _split_terms(source)
    opportunity_types = _opportunity_types(opportunity_type)
    keywords = _split_terms(keyword)
    countries = _split_terms(country)
    career_stages = _split_terms(career_stage)
    if sources:
        query = query.filter(Opportunity.source.in_(sources))
    if opportunity_types:
        query = query.filter(Opportunity.opportunity_type.in_(opportunity_types))
    if keywords:
        keyword_filters = []
        for keyword_item in keywords:
            pattern = f"%{keyword_item}%"
            keyword_filters.append(
                Opportunity.title.ilike(pattern)
                | Opportunity.summary.ilike(pattern)
                | Opportunity.eligibility.ilike(pattern)
                | Opportunity.keywords.ilike(pattern)
                | Opportunity.disciplines.ilike(pattern)
            )
        query = query.filter(or_(*keyword_filters))
    if active_only:
        query = query.filter((Opportunity.deadline.is_(None)) | (Opportunity.deadline >= date.today()))

    opportunities = query.order_by(Opportunity.deadline.asc().nullslast()).all()
    if countries:
        opportunities = [item for item in opportunities if _contains_any_term(item.countries, countries)]
    if career_stages:
        opportunities = [item for item in opportunities if _contains_any_term(item.career_stages, career_stages)]
    return opportunities[offset : offset + limit]


def _split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _opportunity_types(value: OpportunityType | str | None) -> list[OpportunityType]:
    if isinstance(value, OpportunityType):
        return [value]
    types = []
    for item in _split_terms(value):
        normalized = item.strip().casefold().replace(" ", "_")
        try:
            types.append(OpportunityType(normalized))
        except ValueError:
            continue
    return types


def _contains_any_term(value: str, terms: list[str]) -> bool:
    normalized_values = {item.casefold() for item in unpack_list(value)}
    return any(term.strip().casefold() in normalized_values for term in terms)
