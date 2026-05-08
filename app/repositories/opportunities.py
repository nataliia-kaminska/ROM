from datetime import date

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
    opportunity_type: OpportunityType | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Opportunity]:
    query = db.query(Opportunity)
    if source:
        query = query.filter(Opportunity.source == source)
    if opportunity_type:
        query = query.filter(Opportunity.opportunity_type == opportunity_type)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            Opportunity.title.ilike(pattern)
            | Opportunity.summary.ilike(pattern)
            | Opportunity.keywords.ilike(pattern)
            | Opportunity.disciplines.ilike(pattern)
        )
    if active_only:
        query = query.filter((Opportunity.deadline.is_(None)) | (Opportunity.deadline >= date.today()))

    opportunities = query.order_by(Opportunity.deadline.asc().nullslast()).all()
    if country:
        opportunities = [item for item in opportunities if _contains_term(item.countries, country)]
    if career_stage:
        opportunities = [item for item in opportunities if _contains_term(item.career_stages, career_stage)]
    return opportunities[offset : offset + limit]


def _contains_term(value: str, term: str) -> bool:
    normalized = term.strip().casefold()
    return normalized in {item.casefold() for item in unpack_list(value)}
