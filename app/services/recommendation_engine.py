from dataclasses import dataclass, field
from datetime import date
import re

from app.core.config import settings
from app.db.models import (
    Opportunity,
    ProfileOpportunityStatus,
    ProfileOpportunityStatusValue,
    ResearcherProfile,
    ResearcherProfileDetails,
)
from app.schemas.recommendations import RecommendationScoreBreakdown
from app.services.embeddings import cosine_similarity, ensure_opportunity_embedding, ensure_profile_embedding
from app.services.requirements import extract_opportunity_requirements
from app.services.serialization import normalize_terms, unpack_list


@dataclass
class RecommendationScore:
    final_score: int
    reasons: list[str]
    breakdown: RecommendationScoreBreakdown


@dataclass
class UserHistorySignals:
    saved_keywords: set[str] = field(default_factory=set)
    ignored_keywords: set[str] = field(default_factory=set)
    saved_countries: set[str] = field(default_factory=set)
    ignored_countries: set[str] = field(default_factory=set)
    saved_types: set[str] = field(default_factory=set)
    ignored_types: set[str] = field(default_factory=set)


def score_opportunity(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None = None,
    profile_status: ProfileOpportunityStatus | None = None,
    history_signals: UserHistorySignals | None = None,
) -> RecommendationScore:
    reasons: list[str] = []
    semantic = _semantic_score(profile, opportunity, details, reasons)
    eligibility = _eligibility_score(profile, opportunity, details, reasons)
    deadline = _deadline_score(opportunity, reasons)
    user_history = _history_score(opportunity, profile_status, history_signals or UserHistorySignals(), reasons)

    final = round(
        semantic * settings.semantic_score_weight
        + eligibility * settings.eligibility_score_weight
        + deadline * settings.deadline_score_weight
        + user_history * settings.user_history_score_weight
    )

    if not reasons:
        reasons.append("Low metadata overlap; review manually")

    breakdown = RecommendationScoreBreakdown(
        semantic=semantic,
        eligibility=eligibility,
        deadline=deadline,
        user_history=user_history,
        final=max(0, min(100, final)),
    )
    return RecommendationScore(final_score=breakdown.final, reasons=reasons, breakdown=breakdown)


def build_history_signals(
    statuses: list[ProfileOpportunityStatus],
    opportunities_by_id: dict[int, Opportunity],
) -> UserHistorySignals:
    signals = UserHistorySignals()
    positive = {
        ProfileOpportunityStatusValue.saved,
        ProfileOpportunityStatusValue.planned,
        ProfileOpportunityStatusValue.applied,
        ProfileOpportunityStatusValue.accepted,
    }
    for status in statuses:
        opportunity = opportunities_by_id.get(status.opportunity_id)
        if opportunity is None:
            continue
        keywords = normalize_terms(unpack_list(opportunity.keywords))
        countries = normalize_terms(unpack_list(opportunity.countries))
        if status.status in positive:
            signals.saved_keywords.update(keywords)
            signals.saved_countries.update(countries)
            signals.saved_types.add(opportunity.opportunity_type.value)
        elif status.status == ProfileOpportunityStatusValue.ignored:
            signals.ignored_keywords.update(keywords)
            signals.ignored_countries.update(countries)
            signals.ignored_types.add(opportunity.opportunity_type.value)
    return signals


def _semantic_score(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
    reasons: list[str],
) -> int:
    profile_vector = ensure_profile_embedding(profile, details)
    opportunity_vector = ensure_opportunity_embedding(opportunity)
    similarity = cosine_similarity(profile_vector, opportunity_vector)
    semantic_score = max(0, min(100, round(similarity * 100)))
    if semantic_score >= 55:
        reasons.append(f"Semantic similarity to your profile is strong ({semantic_score}%)")
    elif semantic_score >= 30:
        reasons.append(f"Semantic similarity to your profile is moderate ({semantic_score}%)")
    return semantic_score


def _eligibility_score(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
    reasons: list[str],
) -> int:
    score = 20
    profile_disciplines = normalize_terms(unpack_list(profile.disciplines))
    profile_keywords = normalize_terms(unpack_list(profile.keywords))
    preferred_countries = normalize_terms(unpack_list(profile.preferred_countries))

    opportunity_disciplines = normalize_terms(unpack_list(opportunity.disciplines))
    opportunity_keywords = normalize_terms(unpack_list(opportunity.keywords))
    opportunity_countries = normalize_terms(unpack_list(opportunity.countries))
    opportunity_stages = normalize_terms(unpack_list(opportunity.career_stages))
    extracted = extract_opportunity_requirements(opportunity)
    opportunity_countries = opportunity_countries or normalize_terms(extracted.countries)
    opportunity_stages = opportunity_stages or normalize_terms(extracted.career_stages)

    discipline_matches = profile_disciplines & opportunity_disciplines
    keyword_matches = profile_keywords & opportunity_keywords

    if discipline_matches:
        score += 25
        reasons.append(f"Matches disciplines: {', '.join(sorted(discipline_matches))}")
    if keyword_matches:
        score += min(25, 8 * len(keyword_matches))
        reasons.append(f"Matches research keywords: {', '.join(sorted(keyword_matches))}")

    if profile.career_stage.value in opportunity_stages:
        score += 20
        reasons.append(f"Eligible career stage: {profile.career_stage.value}")
    elif opportunity_stages:
        score -= 15
        reasons.append("Career stage may need manual eligibility review")
    else:
        score += 8

    if preferred_countries and preferred_countries & opportunity_countries:
        score += 10
        reasons.append("Available in a preferred country or region")
    elif profile.country and profile.country.strip().lower() in opportunity_countries:
        score += 8
        reasons.append("Available for your country")
    elif not opportunity_countries:
        score += 5

    if details:
        score = _score_details(score, reasons, details, opportunity, opportunity_countries)

    return max(0, min(100, score))


def _deadline_score(opportunity: Opportunity, reasons: list[str]) -> int:
    if opportunity.deadline is None:
        return 55
    days_left = (opportunity.deadline - date.today()).days
    if days_left < 0:
        reasons.append("Deadline has passed")
        return 0
    reasons.append(f"Deadline in {days_left} days")
    if days_left <= 14:
        return 75
    if days_left <= 45:
        return 100
    if days_left <= 120:
        return 80
    return 60


def _history_score(
    opportunity: Opportunity,
    profile_status: ProfileOpportunityStatus | None,
    signals: UserHistorySignals,
    reasons: list[str],
) -> int:
    score = 50
    opportunity_keywords = normalize_terms(unpack_list(opportunity.keywords))
    opportunity_countries = normalize_terms(unpack_list(opportunity.countries))
    opportunity_type = opportunity.opportunity_type.value

    positive_keywords = opportunity_keywords & signals.saved_keywords
    ignored_keywords = opportunity_keywords & signals.ignored_keywords
    positive_countries = opportunity_countries & signals.saved_countries
    ignored_countries = opportunity_countries & signals.ignored_countries

    if positive_keywords:
        score += 15
        reasons.append(f"Ranks higher because you saved/applied to similar topics: {', '.join(sorted(positive_keywords)[:3])}")
    if ignored_keywords:
        score -= 18
        reasons.append(f"Ranks lower because you ignored similar topics: {', '.join(sorted(ignored_keywords)[:3])}")
    if positive_countries:
        score += 8
        reasons.append("Ranks higher because you engaged with this country or region before")
    if ignored_countries:
        score -= 10
        reasons.append("Ranks lower because you ignored this country or region before")
    if opportunity_type in signals.saved_types:
        score += 8
        reasons.append(f"Ranks higher because you engaged with {opportunity_type} opportunities")
    if opportunity_type in signals.ignored_types:
        score -= 8
        reasons.append(f"Ranks lower because you ignored {opportunity_type} opportunities")

    if profile_status:
        if profile_status.status in {ProfileOpportunityStatusValue.saved, ProfileOpportunityStatusValue.planned}:
            score += 12
            reasons.append(f"Previously marked as {profile_status.status.value}")
        elif profile_status.status == ProfileOpportunityStatusValue.applied:
            score += 5
            reasons.append("Already marked as applied")
        elif profile_status.status == ProfileOpportunityStatusValue.ignored:
            score -= 30

    return max(0, min(100, score))


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
