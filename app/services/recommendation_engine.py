from datetime import date
import re

from app.db.models import (
    Opportunity,
    ProfileOpportunityStatus,
    ProfileOpportunityStatusValue,
    ResearcherProfile,
    ResearcherProfileDetails,
)
from app.services.serialization import normalize_terms, unpack_list


def score_opportunity(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None = None,
    profile_status: ProfileOpportunityStatus | None = None,
) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    profile_disciplines = normalize_terms(unpack_list(profile.disciplines))
    profile_keywords = normalize_terms(unpack_list(profile.keywords))
    preferred_countries = normalize_terms(unpack_list(profile.preferred_countries))

    opportunity_disciplines = normalize_terms(unpack_list(opportunity.disciplines))
    opportunity_keywords = normalize_terms(unpack_list(opportunity.keywords))
    opportunity_countries = normalize_terms(unpack_list(opportunity.countries))
    opportunity_stages = normalize_terms(unpack_list(opportunity.career_stages))

    discipline_matches = profile_disciplines & opportunity_disciplines
    keyword_matches = profile_keywords & opportunity_keywords

    if discipline_matches:
        score += 30
        reasons.append(f"Matches disciplines: {', '.join(sorted(discipline_matches))}")

    if keyword_matches:
        score += min(30, 10 * len(keyword_matches))
        reasons.append(f"Matches research keywords: {', '.join(sorted(keyword_matches))}")

    if profile.career_stage.value in opportunity_stages:
        score += 20
        reasons.append(f"Eligible career stage: {profile.career_stage.value}")
    elif opportunity_stages:
        score -= 10
        reasons.append("Career stage may need manual eligibility review")

    if preferred_countries and preferred_countries & opportunity_countries:
        score += 10
        reasons.append("Available in a preferred country or region")
    elif profile.country and profile.country.strip().lower() in opportunity_countries:
        score += 8
        reasons.append("Available for your country")

    if details:
        score = _score_details(score, reasons, details, opportunity, opportunity_countries)

    if opportunity.deadline:
        days_left = (opportunity.deadline - date.today()).days
        if days_left >= 0:
            score += 10 if days_left <= 45 else 5
            reasons.append(f"Deadline in {days_left} days")
        else:
            score -= 25
            reasons.append("Deadline has passed")

    if profile_status:
        if profile_status.status in {ProfileOpportunityStatusValue.saved, ProfileOpportunityStatusValue.planned}:
            score += 5
            reasons.append(f"Previously marked as {profile_status.status.value}")
        elif profile_status.status == ProfileOpportunityStatusValue.applied:
            score -= 5
            reasons.append("Already marked as applied")

    if not reasons:
        reasons.append("Low metadata overlap; review manually")

    return max(0, min(100, score)), reasons


def _score_details(
    score: int,
    reasons: list[str],
    details: ResearcherProfileDetails,
    opportunity: Opportunity,
    opportunity_countries: set[str],
) -> int:
    unavailable_countries = normalize_terms(unpack_list(details.unavailable_countries))
    if unavailable_countries & opportunity_countries:
        score -= 35
        reasons.append("Conflicts with an unavailable country or region")

    preferred_types = normalize_terms(unpack_list(details.preferred_opportunity_types))
    if preferred_types and opportunity.opportunity_type.value in preferred_types:
        score += 8
        reasons.append(f"Matches preferred opportunity type: {opportunity.opportunity_type.value}")

    funding_interest_matches = normalize_terms(unpack_list(details.funding_interests)) & normalize_terms(
        unpack_list(opportunity.keywords)
    )
    if funding_interest_matches:
        score += min(15, 5 * len(funding_interest_matches))
        reasons.append(f"Matches funding interests: {', '.join(sorted(funding_interest_matches))}")

    text_matches = _text_overlap_terms(details, opportunity)
    if text_matches:
        score += min(12, 3 * len(text_matches))
        reasons.append(f"Profile text overlaps with opportunity: {', '.join(text_matches[:4])}")

    return score


def _text_overlap_terms(details: ResearcherProfileDetails, opportunity: Opportunity) -> list[str]:
    profile_text = " ".join(
        [
            details.research_summary,
            details.publications,
            details.degrees,
            details.funding_interests,
        ]
    )
    opportunity_text = " ".join(
        [
            opportunity.title,
            opportunity.summary,
            opportunity.eligibility,
            opportunity.keywords,
            opportunity.disciplines,
        ]
    )
    profile_terms = _meaningful_terms(profile_text)
    opportunity_terms = _meaningful_terms(opportunity_text)
    return sorted(profile_terms & opportunity_terms)


def _meaningful_terms(text: str) -> set[str]:
    stop_words = {
        "about",
        "after",
        "also",
        "and",
        "for",
        "from",
        "into",
        "open",
        "that",
        "the",
        "this",
        "with",
    }
    return {term for term in re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", text.lower()) if term not in stop_words}
