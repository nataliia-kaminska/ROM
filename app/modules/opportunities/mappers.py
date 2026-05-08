from dataclasses import asdict

from app.db.models import Opportunity
from app.schemas.opportunities import OpportunityPreview, OpportunityRead
from app.services.requirements import extract_opportunity_requirements
from app.services.serialization import unpack_list


def to_opportunity_read(opportunity: Opportunity) -> OpportunityRead:
    return OpportunityRead(
        id=opportunity.id,
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type,
        source=opportunity.source,
        url=opportunity.url,
        summary=opportunity.summary,
        eligibility=opportunity.eligibility,
        disciplines=unpack_list(opportunity.disciplines),
        keywords=unpack_list(opportunity.keywords),
        countries=unpack_list(opportunity.countries),
        career_stages=unpack_list(opportunity.career_stages),
        deadline=opportunity.deadline,
        extracted_requirements=asdict(extract_opportunity_requirements(opportunity)),
        requirements_confidence=opportunity.requirements_confidence,
    )


def to_opportunity_preview(opportunity: Opportunity) -> OpportunityPreview:
    return OpportunityPreview(
        id=opportunity.id,
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type,
        source=opportunity.source,
        url=opportunity.url,
        summary=opportunity.summary,
        eligibility=opportunity.eligibility,
        disciplines=unpack_list(opportunity.disciplines),
        keywords=unpack_list(opportunity.keywords),
        countries=unpack_list(opportunity.countries),
        career_stages=unpack_list(opportunity.career_stages),
        deadline=opportunity.deadline,
        requirements_confidence=opportunity.requirements_confidence,
    )
