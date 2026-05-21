from dataclasses import dataclass
import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AdvisorFacts:
    profile_name: str
    opportunity_title: str
    opportunity_type: str
    deadline: str
    readiness_score: int
    strengths: list[str]
    gaps: list[str]
    warnings: list[str]
    missing_fields: list[str]
    retrieved_context: list[str]
    web_research: list[str]
    checklist: list[str]
    motivation_outline: list[str]
    fit_statement: str


class AdvisorProvider:
    name = "deterministic"

    def generate_memo(self, facts: AdvisorFacts) -> str:
        return deterministic_advisor_memo(facts)


class GroqAdvisorProvider(AdvisorProvider):
    name = "groq"

    def generate_memo(self, facts: AdvisorFacts) -> str:
        if not settings.groq_api_key:
            return deterministic_advisor_memo(facts)
        return _chat_completion(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            facts=facts,
            fallback_provider=self.name,
        )


class LocalAdvisorProvider(AdvisorProvider):
    name = "local"

    def generate_memo(self, facts: AdvisorFacts) -> str:
        return _chat_completion(
            base_url=settings.advisor_local_base_url.rstrip("/"),
            api_key="local",
            model=settings.advisor_local_model,
            facts=facts,
            fallback_provider=self.name,
        )


def get_advisor_provider() -> AdvisorProvider:
    provider = settings.advisor_provider.strip().lower()
    if provider == "groq":
        return GroqAdvisorProvider()
    if provider == "local":
        return LocalAdvisorProvider()
    return AdvisorProvider()


def deterministic_advisor_memo(facts: AdvisorFacts) -> str:
    urgency = f" The deadline is {facts.deadline}, so the strategy should stay practical and evidence-led." if facts.deadline else ""
    profile_summary = _context_value(facts.retrieved_context, "Profile research summary")
    publication_evidence = _context_value(facts.retrieved_context, "Publication evidence")
    opportunity_summary = _context_value(facts.retrieved_context, "Opportunity summary")
    opportunity_eligibility = _context_value(facts.retrieved_context, "Opportunity eligibility")
    topic_signal = _compact_sentence(publication_evidence or profile_summary or facts.fit_statement)
    opportunity_signal = _compact_sentence(opportunity_summary or opportunity_eligibility or facts.opportunity_title)
    strongest_signal = _compact_sentence(facts.strengths[0] if facts.strengths else topic_signal)
    top_concerns = (facts.warnings + facts.gaps + [f"Missing profile evidence: {field}." for field in facts.missing_fields])[:4]
    if not top_concerns:
        top_concerns = [f"The main risk is making {facts.opportunity_title} sound generic instead of tying {facts.profile_name}'s evidence to the call wording."]
    evidence_source = facts.web_research[0] if facts.web_research else (facts.retrieved_context[0] if facts.retrieved_context else "")
    profile_gap = facts.missing_fields[0] if facts.missing_fields else "the weakest evidence point"
    opportunity_kind = facts.opportunity_type.replace("_", " ")
    reviewer_question = top_concerns[0].rstrip(".")
    return "\n".join(
        [
            "Best angle:",
            f"- Position {facts.profile_name} as a researcher who can use this {opportunity_kind} to turn {topic_signal} into a concrete contribution for {facts.opportunity_title}.",
            f"- Connect that story to the call through this programme signal: {opportunity_signal}",
            f"- Lead with one precise research problem, then show why this opportunity is the right mechanism for solving it.{urgency}",
            "",
            "Reviewer concerns:",
            *[f"- {item}" for item in top_concerns],
            "",
            "How to answer:",
            f"- Answer the likely reviewer question directly: '{reviewer_question}?' Use one sentence in the application, not a hidden assumption.",
            f"- Add a concrete proof point for {profile_gap}: document, publication, language evidence, host confirmation, or CV line.",
            f"- Anchor the first paragraph in {facts.profile_name}'s actual evidence ({topic_signal}) before describing broader impact.",
            "",
            "Draft snippets:",
            f"- Opening: I am applying to {facts.opportunity_title} to develop a focused research plan grounded in {topic_signal}.",
            f"- Fit sentence: My profile fits this call because {strongest_signal}",
            f"- Reviewer reassurance: I will explicitly document eligibility, availability, and required evidence before submission{f', starting from this source lead: {evidence_source}' if evidence_source else ''}.",
            "",
            "Do not overclaim:",
            f"- Do not claim that {facts.profile_name} is fully eligible until country, career-stage, host, and document rules are checked on the official page.",
            "- Do not mention publications, language proof, institutional support, or mobility availability unless that evidence is already in the profile or attached documents.",
        ]
    )


def _chat_completion(base_url: str, api_key: str, model: str, facts: AdvisorFacts, fallback_provider: str) -> str:
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.35,
                "max_tokens": 950,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an academic application strategist and reviewer. Use only the provided JSON facts. "
                            "Do not invent eligibility requirements, deadlines, publications, countries, or scores. "
                            "Ground your advice in retrieved_context snippets when possible. "
                            "Do not summarize the other UI cards. Create new strategic value: positioning, reviewer concerns, "
                            "how to answer concerns, draftable snippets, and cautions against overclaiming. "
                            "Use short sections with bullet points. Avoid long paragraphs."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Create a compact Advisor memo from these facts. Do not repeat score counts, generic checklist wording, "
                            "or the exact next-action checklist. Focus on program-specific strategy. Include exactly these sections: "
                            "Best angle, Reviewer concerns, How to answer, Draft snippets, Do not overclaim. "
                            "Use 2-4 bullets per section. Draft snippets must include reusable application wording, not placeholders. "
                            "Every section must mention concrete facts from this JSON: the applicant name, opportunity title, profile evidence, "
                            "opportunity requirements or call wording, warnings, or retrieved snippets. Avoid generic advice such as 'check eligibility' "
                            "unless you say exactly what should be checked and why for this applicant. If web_research exists, use it only as a cautious "
                            "source lead, not as verified truth.\n\n"
                            f"{json.dumps(facts.__dict__, ensure_ascii=False)}"
                        ),
                    },
                ],
            },
            timeout=settings.advisor_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"].strip()
        return content or deterministic_advisor_memo(facts)
    except Exception as exc:
        logger.warning("advisor provider %s failed; using deterministic fallback: %s", fallback_provider, exc)
        return deterministic_advisor_memo(facts)


def _context_value(context: list[str], label: str) -> str:
    prefix = f"{label}:"
    for item in context:
        if item.startswith(prefix):
            return item.removeprefix(prefix).strip()
    return ""


def _compact_sentence(value: str, limit: int = 180) -> str:
    text = " ".join(value.split()).strip()
    if not text:
        return "the available profile evidence"
    return text if len(text) <= limit else f"{text[:limit].rstrip()}..."
