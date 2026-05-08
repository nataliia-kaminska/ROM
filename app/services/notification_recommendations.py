from sqlalchemy.orm import Session

from app.db.models import Opportunity, ProfileOpportunityStatus, ResearcherProfile, ResearcherProfileDetails
from app.services.recommendation_engine import build_history_signals, score_opportunity


def top_recommendation_matches(db: Session, profile: ResearcherProfile, limit: int) -> list[dict]:
    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile.id).first()
    statuses = db.query(ProfileOpportunityStatus).filter(ProfileOpportunityStatus.profile_id == profile.id).all()
    opportunities = db.query(Opportunity).all()
    opportunities_by_id = {opportunity.id: opportunity for opportunity in opportunities}
    statuses_by_id = {status.opportunity_id: status for status in statuses}
    history = build_history_signals(statuses, opportunities_by_id)
    scored = []
    for opportunity in opportunities:
        result = score_opportunity(profile, opportunity, details, statuses_by_id.get(opportunity.id), history)
        scored.append(
            {
                "title": opportunity.title,
                "score": result.final_score,
                "reason": result.reasons[0] if result.reasons else "Recommended match",
            }
        )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
