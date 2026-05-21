from datetime import date

from app.db.models import Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.schemas.application_assistant import ApplicationAssistantRead
from app.services.advisor_provider import AdvisorFacts, get_advisor_provider
from app.services.requirements import build_gap_analysis, extract_opportunity_requirements
from app.services.serialization import unpack_list
from app.services.web_research import research_opportunity_web


def build_application_assistant(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
) -> ApplicationAssistantRead:
    retrieved_context = _retrieve_context(profile, opportunity, details)
    missing_fields = _missing_fields(profile, details)
    warnings = _eligibility_warnings(profile, opportunity, details)
    gaps = build_gap_analysis(profile, opportunity, details)
    checklist = _checklist(opportunity, warnings, retrieved_context)
    outline = _motivation_outline(profile, opportunity)
    fit_statement = _fit_statement(profile, opportunity, details, retrieved_context)
    web_research = research_opportunity_web(opportunity)
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
            retrieved_context=retrieved_context,
            web_research=web_research,
            checklist=checklist,
            motivation_outline=outline,
            fit_statement=fit_statement,
        )
    )
    notes = _export_notes(profile, opportunity, retrieved_context, checklist, outline, fit_statement, missing_fields, warnings, gaps, advisor_memo)
    return ApplicationAssistantRead(
        opportunity_id=opportunity.id,
        profile_id=profile.id,
        profile_name=profile.full_name,
        opportunity_title=opportunity.title,
        retrieved_context=retrieved_context,
        web_research=web_research,
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


def _checklist(opportunity: Opportunity, warnings: list[str], retrieved_context: list[str]) -> list[str]:
    requirements = extract_opportunity_requirements(opportunity)
    items = []
    if warnings:
        items.append("Open the official eligibility rules and resolve the highest-risk warning before drafting.")
    if opportunity.deadline:
        days_left = (opportunity.deadline - date.today()).days
        if days_left >= 0:
            items.append(f"Block review and submission time before {opportunity.deadline.isoformat()} ({days_left} days left).")
        else:
            items.append(f"Confirm whether the deadline has been extended after {opportunity.deadline.isoformat()}.")
    if requirements.required_degree:
        items.append("Prepare a degree or qualification proof file and compare it against the call wording.")
    if requirements.languages:
        items.append("Prepare language evidence or a short note explaining how language requirements are satisfied.")
    requirement_snippets = [snippet for snippet in retrieved_context if snippet.startswith("Opportunity eligibility") or snippet.startswith("Extracted requirement")]
    if requirement_snippets:
        items.append("Turn the extracted requirement snippets into a short document checklist.")
    if requirements.publication_expectation:
        items.append("Select the strongest publication or output evidence before writing the motivation paragraph.")
    items.append("Draft one fit paragraph using the Evidence to use card as the proof source.")
    items.append("Confirm submission documents, budget rules, and portal steps on the official call page.")
    if opportunity.url:
        items.append("Open the saved source link and verify that the page is the specific call, not a general search page.")
    return items


def _motivation_outline(profile: ResearcherProfile, opportunity: Opportunity) -> list[str]:
    disciplines = ", ".join(unpack_list(profile.disciplines)[:3]) or "your research area"
    keywords = ", ".join(unpack_list(profile.keywords)[:4]) or "your current research priorities"
    requirements = extract_opportunity_requirements(opportunity)
    opportunity_topics = ", ".join((unpack_list(opportunity.keywords) + unpack_list(opportunity.disciplines))[:4]) or opportunity.opportunity_type.value
    countries = ", ".join((unpack_list(opportunity.countries) or requirements.countries)[:3])
    required_degree = requirements.required_degree or "the required qualification"
    language_text = ", ".join(requirements.languages[:3])
    mobility_text = requirements.mobility or (f"host country/region: {countries}" if countries else "")
    return [
        f"Opening: name {opportunity.title} and frame {profile.full_name}'s goal in {disciplines}.",
        f"Fit argument: connect profile keywords ({keywords}) to opportunity themes ({opportunity_topics}).",
        f"Eligibility proof: explicitly address {required_degree}{f' and {language_text} language ability' if language_text else ''}.",
        f"Evidence paragraph: cite the strongest publication, project, or OpenAlex-imported work linked to {opportunity_topics}.",
        f"Impact paragraph: explain what this {opportunity.opportunity_type.value} enables for the host/community{f' and {mobility_text}' if mobility_text else ''}.",
        "Close: state availability, readiness, and the next concrete application step.",
    ]


def _fit_statement(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
    retrieved_context: list[str],
) -> str:
    profile_topics = unpack_list(profile.keywords) or unpack_list(profile.disciplines)
    opportunity_topics = unpack_list(opportunity.keywords) or unpack_list(opportunity.disciplines)
    topic_text = ", ".join((profile_topics + opportunity_topics)[:5]) or "the opportunity priorities"
    summary = details.research_summary if details and details.research_summary else ""
    if summary:
        return (
            f"{profile.full_name}'s work is a strong fit for {opportunity.title} because their profile centers on "
            f"{topic_text}. Their research summary shows relevant direction: {summary[:260]} "
            f"Retrieved evidence to cite: {_compact_snippet(retrieved_context[0]) if retrieved_context else 'add source-specific evidence before submission'}."
        )
    return (
        f"{profile.full_name}'s background in {topic_text} can be positioned as a fit for {opportunity.title}. "
        "A stronger statement should add concrete publications, methods, and expected outcomes."
    )


def _retrieve_context(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
) -> list[str]:
    query_terms = {
        *[item.lower() for item in unpack_list(profile.disciplines)],
        *[item.lower() for item in unpack_list(profile.keywords)],
        *[item.lower() for item in unpack_list(opportunity.disciplines)],
        *[item.lower() for item in unpack_list(opportunity.keywords)],
        profile.career_stage.value.lower(),
        (profile.country or "").lower(),
    }
    candidates = [
        ("Opportunity summary", opportunity.summary),
        ("Opportunity eligibility", opportunity.eligibility),
        ("Opportunity disciplines", ", ".join(unpack_list(opportunity.disciplines))),
        ("Opportunity keywords", ", ".join(unpack_list(opportunity.keywords))),
        ("Opportunity countries", ", ".join(unpack_list(opportunity.countries))),
        ("Opportunity career stages", ", ".join(unpack_list(opportunity.career_stages))),
    ]
    requirements = extract_opportunity_requirements(opportunity)
    candidates.extend(
        [
            ("Extracted requirement countries", ", ".join(requirements.countries)),
            ("Extracted requirement career stages", ", ".join(requirements.career_stages)),
            ("Extracted requirement languages", ", ".join(requirements.languages)),
            ("Extracted requirement snippets", " | ".join(requirements.snippets)),
        ]
    )
    if details:
        candidates.extend(
            [
                ("Profile research summary", details.research_summary),
                ("Profile publications", ", ".join(unpack_list(details.publications))),
                ("Profile degrees", ", ".join(unpack_list(details.degrees))),
                ("Profile languages", ", ".join(unpack_list(details.languages))),
                ("Profile funding interests", ", ".join(unpack_list(details.funding_interests))),
            ]
        )
        for publication in _publication_evidence(details, opportunity):
            candidates.append(("Publication evidence", publication))
    scored = []
    for label, text in candidates:
        clean = " ".join((text or "").split())
        if not clean:
            continue
        score = sum(1 for term in query_terms if term and term in clean.lower())
        if label.startswith("Opportunity") or label.startswith("Extracted requirement"):
            score += 1
        scored.append((score, f"{label}: {_compact_snippet(clean)}"))
    return [snippet for _, snippet in sorted(scored, key=lambda item: item[0], reverse=True)[:8]]


def _publication_evidence(details: ResearcherProfileDetails, opportunity: Opportunity) -> list[str]:
    opportunity_text = " ".join(
        [
            opportunity.title,
            opportunity.summary,
            opportunity.eligibility,
            opportunity.keywords,
            opportunity.disciplines,
        ]
    ).lower()
    evidence = []
    for publication in unpack_list(details.publications):
        publication_terms = [term for term in publication.lower().replace("-", " ").split() if len(term) > 4]
        if any(term in opportunity_text for term in publication_terms):
            evidence.append(publication)
    return evidence[:3]


def _compact_snippet(value: str, limit: int = 260) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else f"{text[:limit].rstrip()}..."


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
        languages = {item.lower() for item in unpack_list(details.languages)}
        required_languages = {item.lower() for item in requirements.languages}
        missing_languages = required_languages - languages
        if missing_languages:
            warnings.append(f"Required language evidence may be missing: {', '.join(sorted(missing_languages))}.")
        if requirements.publication_expectation and not unpack_list(details.publications):
            warnings.append(f"Publication evidence is expected: {requirements.publication_expectation}")
    if requirements.required_degree:
        degree_text = " ".join(unpack_list(details.degrees)).lower() if details else ""
        if requirements.required_degree.lower() not in degree_text and requirements.required_degree.lower() not in profile.career_stage.value.lower():
            warnings.append(f"Required degree may need proof: {requirements.required_degree}.")
    if requirements.citizenship:
        citizenship_text = requirements.citizenship.lower()
        profile_country = (profile.country or "").lower()
        if profile_country and profile_country not in citizenship_text and "any" not in citizenship_text and "global" not in citizenship_text:
            warnings.append(f"Citizenship/residency condition needs manual check: {requirements.citizenship}.")
    if requirements.mobility:
        warnings.append(f"Mobility rule needs confirmation: {requirements.mobility}.")
    if opportunity.deadline and opportunity.deadline < date.today():
        warnings.append("The listed deadline has passed.")
    return _dedupe(warnings)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _export_notes(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    retrieved_context: list[str],
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
        "## Retrieved Context",
        *[f"- {item}" for item in (retrieved_context or ["No retrieved snippets available"])],
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
