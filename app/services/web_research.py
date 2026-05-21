import logging
import warnings
from functools import lru_cache
from urllib.parse import urlparse

from app.core.config import settings
from app.db.models import Opportunity
from app.services.serialization import unpack_list


logger = logging.getLogger(__name__)


def research_opportunity_web(opportunity: Opportunity) -> list[str]:
    if not settings.assistant_web_research_enabled:
        return []
    if settings.assistant_web_research_provider.strip().lower() != "duckduckgo":
        logger.info("assistant web research skipped unsupported_provider=%s", settings.assistant_web_research_provider)
        return []
    return _cached_research(
        opportunity.title,
        opportunity.source,
        opportunity.url,
        opportunity.keywords,
        opportunity.disciplines,
        opportunity.opportunity_type.value,
        settings.assistant_web_research_max_results,
    )


@lru_cache(maxsize=128)
def _cached_research(
    title: str,
    source: str,
    url: str | None,
    keywords: str,
    disciplines: str,
    opportunity_type: str,
    max_results: int,
) -> list[str]:
    opportunity = Opportunity(
        title=title,
        source=source,
        url=url or "",
        keywords=keywords,
        disciplines=disciplines,
        opportunity_type=opportunity_type,
    )
    snippets: list[str] = []
    seen: set[str] = set()
    for query in _research_queries(opportunity):
        remaining = max_results - len(snippets)
        if remaining <= 0:
            break
        for snippet in _duckduckgo_search(query, remaining):
            key = snippet.casefold()
            if key in seen:
                continue
            seen.add(key)
            snippets.append(snippet)
            if len(snippets) >= max_results:
                break
    logger.info(
        "assistant web research complete provider=duckduckgo title=%s queries=%s results=%s",
        title,
        len(_research_queries(opportunity)),
        len(snippets),
    )
    return snippets


@lru_cache(maxsize=128)
def _duckduckgo_search(query: str, max_results: int) -> list[str]:
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed to.*")
                from duckduckgo_search import DDGS
    except ImportError:
        logger.warning("assistant web research unavailable reason=ddgs_or_duckduckgo_search_not_installed")
        return []

    try:
        with DDGS(timeout=settings.assistant_web_research_timeout_seconds) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        logger.warning("assistant web research failed provider=duckduckgo query=%s error=%s", query, exc)
        return []

    snippets = []
    for result in results[:max_results]:
        title = _clean(result.get("title", ""))
        href = _clean(result.get("href", ""))
        body = _clean(result.get("body", ""))
        if not title and not body:
            continue
        snippets.append(f"Web research: {title}. {body} Source: {href}".strip())
    logger.info("assistant web research query complete provider=duckduckgo query=%s results=%s", query, len(snippets))
    return snippets


def _research_queries(opportunity: Opportunity) -> list[str]:
    source = opportunity.source.replace("_", " ")
    domain = _source_domain(opportunity.url)
    compact_title = _compact_title(opportunity.title)
    topics = _topic_terms(opportunity)
    queries = [
        f"{opportunity.title} {source} official call eligibility deadline",
        f"{compact_title} {source} grant opportunity",
        f"{source} {topics} official funding call",
    ]
    if domain:
        queries.append(f"site:{domain} {compact_title or topics} funding opportunity")
        queries.append(f"site:{domain} {topics} eligibility deadline")
    queries.append(f"{compact_title or opportunity.title} eligibility deadline official")
    return _dedupe([query for query in queries if query.strip()])


def _compact_title(title: str) -> str:
    stopwords = {
        "fy",
        "fy24",
        "fy25",
        "fy26",
        "research",
        "evaluation",
        "program",
        "purpose",
        "purposes",
        "funding",
        "opportunity",
        "announcement",
        "grant",
        "grants",
        "and",
        "of",
        "for",
        "to",
        "the",
        "a",
        "an",
        "with",
        "on",
        "in",
    }
    words = []
    for raw_word in title.replace("/", " ").replace("-", " ").split():
        word = raw_word.strip(".,:;()[]{}").lower()
        if not word or word in stopwords or word.isdigit():
            continue
        if word.startswith("fy") and word[2:].isdigit():
            continue
        words.append(raw_word.strip(".,:;()[]{}"))
    return " ".join(words[:8])


def _topic_terms(opportunity: Opportunity) -> str:
    opportunity_type = getattr(opportunity.opportunity_type, "value", opportunity.opportunity_type)
    terms = [
        *unpack_list(opportunity.keywords),
        *unpack_list(opportunity.disciplines),
        str(opportunity_type).replace("_", " "),
    ]
    cleaned = _dedupe([_clean(term) for term in terms if _clean(term)])
    return " ".join(cleaned[:6]) or _compact_title(opportunity.title) or opportunity.title


def _source_domain(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _research_query(opportunity: Opportunity) -> str:
    return _research_queries(opportunity)[0]


def _clean(value: str) -> str:
    return " ".join((value or "").split())
