from datetime import date

from app.db.models import Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.schemas.application_assistant import ApplicationAssistantRead
from app.services.advisor_provider import AdvisorFacts, get_advisor_provider
from app.services.requirements import build_gap_analysis, extract_opportunity_requirements
from app.services.serialization import unpack_list


def build_application_assistant(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
) -> ApplicationAssistantRead:
    missing_fields = _missing_fields(profile, details)
    warnings = _eligibility_warnings(profile, opportunity, details)
    gaps = build_gap_analysis(profile, opportunity, details)
    checklist = _checklist(opportunity, warnings)
    outline = _motivation_outline(profile, opportunity)
    fit_statement = _fit_statement(profile, opportunity, details)
    advisor_provider = get_advisor_provider()
    advisor_memo = advisor_provider.generate_memo(
        AdvisorFacts(
            profile_name=profile.full_name,
            opportunity_title=opportunity.title,
            opportunity_type=opportunity.opportunity_type.value,
            deadline=opportunity.deadline.isoformat() if opportunity.deadline else "",
            readiness_score=gaps.readiness_score,
            strengths=gaps.strengths,
            gaps=gaps.gaps,
            warnings=warnings,
            missing_fields=missing_fields,
            checklist=checklist,
            motivation_outline=outline,
            fit_statement=fit_statement,
        )
    )
    notes = _export_notes(profile, opportunity, checklist, outline, fit_statement, missing_fields, warnings, gaps, advisor_memo)
    return ApplicationAssistantRead(
        opportunity_id=opportunity.id,
        profile_id=profile.id,
        application_checklist=checklist,
        motivation_letter_outline=outline,
        research_fit_statement=fit_statement,
        missing_profile_fields=missing_fields,
        eligibility_warnings=warnings,
        readiness_score=gaps.readiness_score,
        gap_analysis=gaps.gaps,
        strengths=gaps.strengths,
        advisor_provider=advisor_provider.name,
        advisor_memo=advisor_memo,
        exported_notes=notes,
    )


def _checklist(opportunity: Opportunity, warnings: list[str]) -> list[str]:
    items = [
        "Confirm eligibility requirements against the official source.",
        "Prepare an updated academic CV.",
        "Draft a one-page research fit statement.",
        "Collect publication highlights relevant to this opportunity.",
        "Identify referees or host contacts if required.",
        "Review budget, mobility, or duration requirements.",
    ]
    if opportunity.deadline:
        items.insert(0, f"Submit before {opportunity.deadline.isoformat()}.")
    if opportunity.url:
        items.append(f"Open and verify application instructions: {opportunity.url}")
    if warnings:
        items.insert(0, "Resolve eligibility warnings before investing in the full application.")
    return items


def _motivation_outline(profile: ResearcherProfile, opportunity: Opportunity) -> list[str]:
    disciplines = ", ".join(unpack_list(profile.disciplines)[:3]) or "your research area"
    keywords = ", ".join(unpack_list(profile.keywords)[:4]) or "your current research priorities"
    return [
        f"Opening: introduce {profile.full_name} and the opportunity, {opportunity.title}.",
        f"Research fit: connect {disciplines} and {keywords} to the opportunity goals.",
        "Evidence: cite two or three publications, projects, or outcomes that show readiness.",
        "Impact: explain what the funding, mobility, training, or position would make possible.",
        "Close: restate fit, availability, and next-step readiness.",
    ]


def _fit_statement(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
) -> str:
    profile_topics = unpack_list(profile.keywords) or unpack_list(profile.disciplines)
    opportunity_topics = unpack_list(opportunity.keywords) or unpack_list(opportunity.disciplines)
    topic_text = ", ".join((profile_topics + opportunity_topics)[:5]) or "the opportunity priorities"
    summary = details.research_summary if details and details.research_summary else ""
    if summary:
        return (
            f"{profile.full_name}'s work is a strong fit for {opportunity.title} because their profile centers on "
            f"{topic_text}. Their research summary shows relevant direction: {summary[:260]}"
        )
    return (
        f"{profile.full_name}'s background in {topic_text} can be positioned as a fit for {opportunity.title}. "
        "A stronger statement should add concrete publications, methods, and expected outcomes."
    )


def _missing_fields(profile: ResearcherProfile, details: ResearcherProfileDetails | None) -> list[str]:
    missing = []
    if not profile.email:
        missing.append("email")
    if not profile.country:
        missing.append("country")
    if not unpack_list(profile.disciplines):
        missing.append("disciplines")
    if not unpack_list(profile.keywords):
        missing.append("keywords")
    if details is None:
        missing.extend(["research summary", "publications", "degrees", "languages"])
        return missing
    if not details.research_summary:
        missing.append("research summary")
    if not unpack_list(details.publications):
        missing.append("publications")
    if not unpack_list(details.degrees):
        missing.append("degrees")
    if not unpack_list(details.languages):
        missing.append("languages")
    return missing


def _eligibility_warnings(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
) -> list[str]:
    warnings = []
    requirements = extract_opportunity_requirements(opportunity)
    stages = {item.lower() for item in unpack_list(opportunity.career_stages)}
    stages = stages or {item.lower() for item in requirements.career_stages}
    if stages and profile.career_stage.value.lower() not in stages:
        warnings.append(f"Career stage is {profile.career_stage.value}, while opportunity lists {', '.join(sorted(stages))}.")
    countries = {item.lower() for item in unpack_list(opportunity.countries)}
    countries = countries or {item.lower() for item in requirements.countries}
    if profile.country and countries and profile.country.lower() not in countries and "global" not in countries:
        warnings.append(f"Profile country {profile.country} is not explicitly listed in opportunity countries.")
    if details:
        unavailable = {item.lower() for item in unpack_list(details.unavailable_countries)}
        conflict = countries & unavailable
        if conflict:
            warnings.append(f"Opportunity conflicts with unavailable country or region: {', '.join(sorted(conflict))}.")
    if opportunity.deadline and opportunity.deadline < date.today():
        warnings.append("The listed deadline has passed.")
    return warnings


def _export_notes(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    checklist: list[str],
    outline: list[str],
    fit_statement: str,
    missing: list[str],
    warnings: list[str],
    gaps,
    advisor_memo: str,
) -> str:
    sections = [
        f"# Application Notes: {opportunity.title}",
        f"Profile: {profile.full_name}",
        "",
        "## Checklist",
        *[f"- {item}" for item in checklist],
        "",
        "## Motivation Letter Outline",
        *[f"- {item}" for item in outline],
        "",
        "## Research Fit Statement",
        fit_statement,
        "",
        "## Missing Profile Fields",
        *[f"- {item}" for item in (missing or ["None flagged"])],
        "",
        "## Eligibility Warnings",
        *[f"- {item}" for item in (warnings or ["None flagged"])],
        "",
        "## Readiness and Gaps",
        f"Readiness score: {gaps.readiness_score}",
        *[f"- Strength: {item}" for item in (gaps.strengths or ["None flagged"])],
        *[f"- Gap: {item}" for item in (gaps.gaps or ["None flagged"])],
        "",
        "## Advisor Memo",
        advisor_memo,
    ]
    return "\n".join(sections)
