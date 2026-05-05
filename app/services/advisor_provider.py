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
    urgency = f" Deadline: {facts.deadline}." if facts.deadline else ""
    top_strengths = facts.strengths[:3] or ["No strong fit signals are confirmed yet."]
    top_gaps = facts.gaps[:3] or ["No major gaps are flagged by the deterministic analysis."]
    warnings = facts.warnings[:3] or ["No eligibility warnings are currently flagged."]
    next_steps = facts.checklist[:4]
    return "\n".join(
        [
            f"{facts.profile_name} should treat {facts.opportunity_title} as a {facts.readiness_score}% readiness opportunity.{urgency}",
            "",
            "Strongest signals:",
            *[f"- {item}" for item in top_strengths],
            "",
            "Main risks or gaps:",
            *[f"- {item}" for item in top_gaps],
            "",
            "Eligibility cautions:",
            *[f"- {item}" for item in warnings],
            "",
            "Recommended next actions:",
            *[f"- {item}" for item in next_steps],
        ]
    )


def _chat_completion(base_url: str, api_key: str, model: str, facts: AdvisorFacts, fallback_provider: str) -> str:
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.25,
                "max_tokens": 700,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an academic application advisor. Use only the provided JSON facts. "
                            "Do not invent eligibility requirements, deadlines, publications, countries, or scores. "
                            "Write concise, practical advice with clear next actions."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Create an advisor memo from these facts. Include: fit summary, risks, missing evidence, "
                            "and next actions.\n\n"
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
