import json
import logging
import re
from dataclasses import asdict, dataclass, field

import httpx

from app.core.config import settings
from app.db.models import Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.services.serialization import normalize_terms, pack_list, unpack_list
from app.services.source_quality import is_generic_provider_reference

logger = logging.getLogger(__name__)


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
class ExtractedOpportunityMetadata:
    title: str = ""
    summary: str = ""
    eligibility: str = ""
    disciplines: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    career_stages: list[str] = field(default_factory=list)
    requirements: ExtractedRequirements = field(default_factory=ExtractedRequirements)
    provider: str = "deterministic"


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


def extract_opportunity_metadata(opportunity: Opportunity, page_preview: str = "") -> ExtractedOpportunityMetadata:
    deterministic = ExtractedOpportunityMetadata(
        title=opportunity.title,
        summary=opportunity.summary,
        eligibility=opportunity.eligibility,
        disciplines=unpack_list(opportunity.disciplines),
        keywords=unpack_list(opportunity.keywords),
        countries=unpack_list(opportunity.countries),
        career_stages=unpack_list(opportunity.career_stages),
        requirements=extract_requirements_text(opportunity.title, opportunity.summary, opportunity.eligibility),
    )
    provider = settings.opportunity_extraction_provider.strip().lower()
    if provider == "groq":
        ai_result = _extract_with_chat_completion(
            provider="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=settings.opportunity_extraction_model or settings.groq_model,
            opportunity=opportunity,
            page_preview=page_preview,
        )
    elif provider == "local":
        ai_result = _extract_with_chat_completion(
            provider="local",
            base_url=settings.advisor_local_base_url.rstrip("/"),
            api_key="local",
            model=settings.opportunity_extraction_model or settings.advisor_local_model,
            opportunity=opportunity,
            page_preview=page_preview,
        )
    else:
        ai_result = None
    if ai_result is None:
        return deterministic
    return ExtractedOpportunityMetadata(
        title=_best_public_text(ai_result.title, deterministic.title, field_name="title", opportunity=opportunity),
        summary=_best_public_text(ai_result.summary, deterministic.summary, field_name="summary", opportunity=opportunity),
        eligibility=_best_public_text(ai_result.eligibility, deterministic.eligibility, field_name="eligibility", opportunity=opportunity),
        disciplines=_merge_terms(deterministic.disciplines, ai_result.disciplines),
        keywords=_merge_terms(deterministic.keywords, ai_result.keywords),
        countries=_merge_terms(deterministic.countries, ai_result.countries),
        career_stages=_merge_terms(deterministic.career_stages, ai_result.career_stages),
        requirements=_merge_requirements(deterministic.requirements, ai_result.requirements),
        provider=ai_result.provider,
    )


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


def refresh_opportunity_requirements(opportunity: Opportunity, page_preview: str = "") -> ExtractedRequirements:
    metadata = extract_opportunity_metadata(opportunity, page_preview=page_preview)
    opportunity.title = metadata.title or opportunity.title
    opportunity.summary = metadata.summary or opportunity.summary
    opportunity.eligibility = metadata.eligibility or opportunity.eligibility
    opportunity.disciplines = pack_list(metadata.disciplines)
    opportunity.keywords = pack_list(metadata.keywords)
    opportunity.countries = pack_list(metadata.countries)
    opportunity.career_stages = pack_list(metadata.career_stages)
    opportunity.extracted_requirements = serialize_requirements(metadata.requirements)
    opportunity.requirements_confidence = metadata.requirements.confidence
    logger.info(
        "extracted opportunity metadata provider=%s title=%s confidence=%s disciplines=%s keywords=%s countries=%s stages=%s",
        metadata.provider,
        opportunity.title,
        metadata.requirements.confidence,
        len(metadata.disciplines),
        len(metadata.keywords),
        len(metadata.countries),
        len(metadata.career_stages),
    )
    return metadata.requirements


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


def _extract_with_chat_completion(
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
    opportunity: Opportunity,
    page_preview: str = "",
) -> ExtractedOpportunityMetadata | None:
    if provider == "groq" and not api_key:
        logger.warning("opportunity extraction provider=groq skipped because GROQ_API_KEY is empty")
        return None
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0,
                "max_tokens": 900,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Extract structured academic opportunity metadata. Return only valid JSON. "
                            "Use short canonical values. Improve title, summary, and eligibility only from the "
                            "provided evidence. Do not invent facts. Do not include funder names, agencies, offices, "
                            "URLs, or source names as keywords or disciplines."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "schema": {
                                    "title": "concise official opportunity title",
                                    "summary": "1-3 sentence user-facing description",
                                    "eligibility": "concise eligibility requirements",
                                    "disciplines": ["Computer Science"],
                                    "keywords": ["machine learning"],
                                    "countries": ["Germany"],
                                    "career_stages": ["phd", "postdoc"],
                                    "required_degree": "phd",
                                    "languages": ["English"],
                                    "publication_expectation": "short evidence string",
                                    "mobility": "short evidence string",
                                    "citizenship": "short evidence string",
                                    "years_since_phd": 8,
                                    "snippets": ["evidence snippet"],
                                    "confidence": 80,
                                },
                                "allowed_career_stages": ["bachelor", "master", "phd", "postdoc", "early_career", "senior"],
                                "opportunity": {
                                    "title": opportunity.title,
                                    "type": opportunity.opportunity_type.value,
                                    "source": opportunity.source,
                                    "summary": opportunity.summary,
                                    "eligibility": opportunity.eligibility,
                                    "disciplines": unpack_list(opportunity.disciplines),
                                    "keywords": unpack_list(opportunity.keywords),
                                    "countries": unpack_list(opportunity.countries),
                                    "career_stages": unpack_list(opportunity.career_stages),
                                },
                                "page_preview": page_preview,
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            },
            timeout=settings.opportunity_extraction_timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        requirements = ExtractedRequirements(
            career_stages=_clean_terms(payload.get("career_stages", [])),
            countries=_clean_terms(payload.get("countries", [])),
            required_degree=_clean_scalar(payload.get("required_degree", "")),
            languages=_clean_terms(payload.get("languages", [])),
            publication_expectation=_clean_scalar(payload.get("publication_expectation", "")),
            mobility=_clean_scalar(payload.get("mobility", "")),
            citizenship=_clean_scalar(payload.get("citizenship", "")),
            years_since_phd=payload.get("years_since_phd") if isinstance(payload.get("years_since_phd"), int) else None,
            snippets=_clean_terms(payload.get("snippets", []), max_items=5, max_length=180),
            confidence=max(0, min(95, int(payload.get("confidence", 0) or 0))),
        )
        return ExtractedOpportunityMetadata(
            title=_clean_scalar(payload.get("title", ""), max_length=180),
            summary=_clean_scalar(payload.get("summary", ""), max_length=900),
            eligibility=_clean_scalar(payload.get("eligibility", ""), max_length=900),
            disciplines=_clean_terms(payload.get("disciplines", [])),
            keywords=_clean_terms(payload.get("keywords", [])),
            countries=requirements.countries,
            career_stages=requirements.career_stages,
            requirements=requirements,
            provider=provider,
        )
    except Exception as exc:
        logger.warning("opportunity extraction provider=%s failed; using deterministic fallback: %s", provider, exc)
        return None


def _merge_requirements(left: ExtractedRequirements, right: ExtractedRequirements) -> ExtractedRequirements:
    return ExtractedRequirements(
        career_stages=_merge_terms(left.career_stages, right.career_stages),
        countries=_merge_terms(left.countries, right.countries),
        required_degree=right.required_degree or left.required_degree,
        languages=_merge_terms(left.languages, right.languages),
        publication_expectation=right.publication_expectation or left.publication_expectation,
        mobility=right.mobility or left.mobility,
        citizenship=right.citizenship or left.citizenship,
        years_since_phd=right.years_since_phd if right.years_since_phd is not None else left.years_since_phd,
        snippets=_merge_terms(left.snippets, right.snippets, max_items=5),
        confidence=max(left.confidence, right.confidence),
    )


def _best_public_text(candidate: str, current: str, field_name: str, opportunity: Opportunity) -> str:
    cleaned_candidate = _clean_scalar(candidate, max_length=900 if field_name != "title" else 180)
    cleaned_current = _clean_scalar(current, max_length=900 if field_name != "title" else 180)
    if not cleaned_candidate:
        return cleaned_current
    if field_name == "title" and is_generic_provider_reference(opportunity.source, cleaned_candidate, opportunity.url):
        return cleaned_current
    if field_name == "title":
        return cleaned_candidate if _looks_more_specific_title(cleaned_candidate, cleaned_current) else cleaned_current
    if _is_placeholder_text(cleaned_current):
        return cleaned_candidate
    if len(cleaned_candidate) >= max(80, len(cleaned_current) + 30):
        return cleaned_candidate
    return cleaned_current


def _looks_more_specific_title(candidate: str, current: str) -> bool:
    if _is_placeholder_text(current):
        return True
    candidate_words = [word for word in candidate.split() if len(word) > 2]
    current_words = [word for word in current.split() if len(word) > 2]
    return len(candidate_words) >= 3 and len(candidate_words) >= len(current_words)


def _is_placeholder_text(value: str) -> bool:
    normalized = value.casefold().strip(" .:-")
    return normalized in {"", "see call page", "see opportunity page", "details to be confirmed", "no summary available"} or len(normalized) < 20


def _merge_terms(*groups: list[str], max_items: int = 12) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for group in groups:
        for item in _clean_terms(group):
            key = item.casefold()
            if key not in seen:
                seen.add(key)
                result.append(item)
    return result[:max_items]


def _clean_terms(values: object, max_items: int = 12, max_length: int = 60) -> list[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        cleaned = _clean_scalar(value, max_length=max_length)
        if cleaned:
            result.append(cleaned)
    return result[:max_items]


def _clean_scalar(value: object, max_length: int = 180) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = " ".join(value.strip().split())
    if len(cleaned) > max_length:
        return cleaned[:max_length].rstrip()
    return cleaned
