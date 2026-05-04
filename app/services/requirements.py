import json
import re
from dataclasses import asdict, dataclass, field

from app.db.models import Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.services.serialization import normalize_terms, unpack_list


@dataclass
class ExtractedRequirements:
    career_stages: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    required_degree: str = ""
    languages: list[str] = field(default_factory=list)
    publication_expectation: str = ""
    mobility: str = ""
    citizenship: str = ""
    years_since_phd: int | None = None
    snippets: list[str] = field(default_factory=list)
    confidence: int = 0


@dataclass
class GapAnalysis:
    readiness_score: int
    strengths: list[str]
    gaps: list[str]


COUNTRY_PATTERNS = {
    "Germany": r"\bgermany|german\b",
    "France": r"\bfrance|french\b",
    "United States": r"\bunited states|usa|u\.s\.\b",
    "Ukraine": r"\bukraine|ukrainian\b",
    "European Union": r"\beuropean union|eu\b",
    "Global": r"\bglobal|worldwide|all countries\b",
}

STAGE_PATTERNS = {
    "bachelor": r"\bbachelor",
    "master": r"\bmaster",
    "phd": r"\bphd|doctoral|doctorate",
    "postdoc": r"\bpostdoc|postdoctoral",
    "early_career": r"\bearly[- ]career",
    "senior": r"\bsenior|principal investigator|pi\b",
}

LANGUAGE_PATTERNS = {
    "English": r"\benglish\b",
    "German": r"\bgerman\b",
    "French": r"\bfrench\b",
}


def extract_requirements_text(title: str, summary: str, eligibility: str) -> ExtractedRequirements:
    text = " ".join([title, summary, eligibility])
    lower = text.lower()
    requirements = ExtractedRequirements()
    requirements.career_stages = _matches(lower, STAGE_PATTERNS)
    requirements.countries = _matches(lower, COUNTRY_PATTERNS)
    requirements.languages = _matches(lower, LANGUAGE_PATTERNS)
    requirements.required_degree = _degree(lower)
    requirements.publication_expectation = _snippet(text, r"publications?|papers?|publication record")
    requirements.mobility = _snippet(text, r"mobility|relocat|secondment|host institution")
    requirements.citizenship = _snippet(text, r"citizenship|resident|residency|nationality")
    requirements.years_since_phd = _years_since_phd(lower)
    requirements.snippets = _evidence_snippets(text)
    signals = [
        requirements.career_stages,
        requirements.countries,
        requirements.required_degree,
        requirements.languages,
        requirements.publication_expectation,
        requirements.mobility,
        requirements.citizenship,
        requirements.years_since_phd,
    ]
    requirements.confidence = min(95, 20 + 10 * sum(1 for signal in signals if signal))
    return requirements


def extract_opportunity_requirements(opportunity: Opportunity) -> ExtractedRequirements:
    stored = getattr(opportunity, "extracted_requirements", "") or ""
    if stored:
        try:
            payload = json.loads(stored)
            return ExtractedRequirements(**payload)
        except (TypeError, ValueError):
            pass
    return extract_requirements_text(opportunity.title, opportunity.summary, opportunity.eligibility)


def serialize_requirements(requirements: ExtractedRequirements) -> str:
    return json.dumps(asdict(requirements), sort_keys=True)


def refresh_opportunity_requirements(opportunity: Opportunity) -> ExtractedRequirements:
    requirements = extract_requirements_text(opportunity.title, opportunity.summary, opportunity.eligibility)
    opportunity.extracted_requirements = serialize_requirements(requirements)
    opportunity.requirements_confidence = requirements.confidence
    return requirements


def build_gap_analysis(
    profile: ResearcherProfile,
    opportunity: Opportunity,
    details: ResearcherProfileDetails | None,
) -> GapAnalysis:
    requirements = extract_opportunity_requirements(opportunity)
    strengths: list[str] = []
    gaps: list[str] = []
    score = 45

    profile_stage = profile.career_stage.value
    stages = normalize_terms(requirements.career_stages or unpack_list(opportunity.career_stages))
    if stages:
        if profile_stage in stages:
            score += 15
            strengths.append(f"Career stage matches requirement: {profile_stage}.")
        else:
            score -= 18
            gaps.append(f"Career stage may not match: requires {', '.join(sorted(stages))}.")

    countries = normalize_terms(requirements.countries or unpack_list(opportunity.countries))
    if countries and "global" not in countries:
        profile_country = (profile.country or "").strip().lower()
        if profile_country and profile_country in countries:
            score += 10
            strengths.append("Country or residency appears aligned.")
        else:
            score -= 10
            gaps.append(f"Country or residency should be checked against: {', '.join(sorted(countries))}.")

    if requirements.required_degree:
        degree_terms = normalize_terms(unpack_list(details.degrees) if details else [])
        if requirements.required_degree in degree_terms or (requirements.required_degree == "phd" and profile_stage in {"phd", "postdoc", "senior"}):
            score += 10
            strengths.append(f"Degree signal appears compatible with {requirements.required_degree}.")
        else:
            gaps.append(f"Add evidence for required degree: {requirements.required_degree}.")

    if requirements.publication_expectation:
        publications = unpack_list(details.publications) if details else []
        if publications:
            score += 8
            strengths.append("Publication evidence is present for a publication-sensitive call.")
        else:
            score -= 8
            gaps.append("Add publication highlights because the call mentions publication expectations.")

    if requirements.languages:
        profile_languages = normalize_terms(unpack_list(details.languages) if details else [])
        missing_languages = [language for language in requirements.languages if language.lower() not in profile_languages]
        if missing_languages:
            gaps.append(f"Add or verify language evidence: {', '.join(missing_languages)}.")
        else:
            score += 6
            strengths.append("Language requirements appear covered.")

    topic_overlap = normalize_terms(unpack_list(profile.keywords) + unpack_list(profile.disciplines)) & normalize_terms(
        unpack_list(opportunity.keywords) + unpack_list(opportunity.disciplines)
    )
    if topic_overlap:
        score += 10
        strengths.append(f"Topic overlap: {', '.join(sorted(topic_overlap)[:4])}.")
    else:
        gaps.append("Add clearer topic fit between profile keywords and opportunity metadata.")

    return GapAnalysis(readiness_score=max(0, min(100, score)), strengths=strengths, gaps=gaps)


def _matches(text: str, patterns: dict[str, str]) -> list[str]:
    return [label for label, pattern in patterns.items() if re.search(pattern, text)]


def _degree(text: str) -> str:
    if re.search(r"\bphd|doctoral|doctorate", text):
        return "phd"
    if re.search(r"\bmaster", text):
        return "master"
    if re.search(r"\bbachelor", text):
        return "bachelor"
    return ""


def _years_since_phd(text: str) -> int | None:
    match = re.search(r"(\d+)\s+(?:years?|yrs?)\s+(?:since|after)\s+phd", text)
    return int(match.group(1)) if match else None


def _snippet(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - 80)
    end = min(len(text), match.end() + 120)
    return " ".join(text[start:end].split())


def _evidence_snippets(text: str) -> list[str]:
    snippets = []
    for pattern in (r"eligible[^.]*\.", r"required[^.]*\.", r"must[^.]*\.", r"open to[^.]*\."):
        snippets.extend(" ".join(match.group(0).split()) for match in re.finditer(pattern, text, re.IGNORECASE))
    return snippets[:5]
