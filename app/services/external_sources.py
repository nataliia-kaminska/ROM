import logging
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

from app.db.models import OpportunityType
from app.services.external_fetch import ExternalSourceClient, validate_external_source_url
from app.modules.opportunities.mappers import to_opportunity_preview
from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult
from app.schemas.opportunities import OpportunityCreate
from app.integrations.source_connectors import get_source_connector
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_import import import_opportunities
from app.services.opportunity_search import index_opportunity_for_search
from app.services.source_quality import is_generic_provider_reference


logger = logging.getLogger(__name__)


def import_external_source(payload: ExternalSourceImportRequest, db, client: ExternalSourceClient | None = None) -> ExternalSourceImportResult:
    logger.info(
        "external source import requested source=%s kind=%s url=%s import_results=%s limit=%s",
        payload.source_name,
        payload.source_kind,
        payload.source_url,
        payload.import_results,
        payload.limit,
    )
    source_client = client or ExternalSourceClient()
    connector = get_source_connector(payload.source_name)
    ensure_source(db, name=payload.source_name, display_name=connector.display_name, base_url=str(payload.source_url), source_type=payload.source_kind)
    batch = start_batch(db, source_name=payload.source_name, query=str(payload.source_url), dry_run=not payload.import_results)
    try:
        raw = source_client.fetch(str(payload.source_url))
        opportunities = normalize_external_source(raw, payload)
        logger.info("external source normalized source=%s count=%s", payload.source_name, len(opportunities))
        processed, imported_count, updated_count, skipped_count = import_opportunities(
            db=db,
            payloads=opportunities,
            source=payload.source_name,
            dry_run=not payload.import_results,
            commit=False,
        )
        finish_batch(
            db,
            batch,
            imported_count=imported_count if payload.import_results else 0,
            updated_count=updated_count if payload.import_results else 0,
            skipped_count=skipped_count,
        )
        db.commit()
        if payload.import_results:
            for opportunity in processed:
                db.refresh(opportunity)
                index_opportunity_for_search(opportunity)
        db.refresh(batch)
        return ExternalSourceImportResult(
            source=payload.source_name,
            batch_id=batch.id,
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            opportunities=[to_opportunity_preview(opportunity) for opportunity in processed],
        )
    except Exception:
        logger.exception("external source import failed source=%s batch_id=%s", payload.source_name, batch.id)
        finish_batch(db, batch, imported_count=0, updated_count=0, skipped_count=0, error_count=1)
        db.commit()
        raise


def normalize_external_source(raw: str, payload: ExternalSourceImportRequest) -> list[OpportunityCreate]:
    if payload.source_kind == "json":
        items = _json_items(raw)
    elif payload.source_kind == "html":
        items = _html_items(raw, str(payload.source_url))
    else:
        items = _rss_items(raw)
    return [_payload_from_mapping(item, payload) for item in items if not _is_generic_provider_page(item, payload)][: payload.limit]


def _is_generic_provider_page(item: dict[str, Any], payload: ExternalSourceImportRequest) -> bool:
    url = str(item.get("url") or item.get("link") or item.get("href") or "").casefold()
    title = str(item.get("title") or item.get("name") or "").casefold()
    return is_generic_provider_reference(payload.source_name, title, url)


def _json_items(raw: str) -> list[dict[str, Any]]:
    import json

    body = json.loads(raw)
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if isinstance(body, dict):
        for key in ("items", "results", "opportunities", "data"):
            value = body.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _rss_items(raw: str) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(raw)
    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    normalized = []
    for item in items:
        normalized.append(
            {
                "title": _node_text(item, "title"),
                "summary": _node_text(item, "description") or _node_text(item, "summary") or _node_text(item, "content"),
                "url": _rss_link(item),
                "deadline": _node_text(item, "deadline") or _node_text(item, "pubDate") or _node_text(item, "updated"),
                "keywords": [_node_text(child, "") for child in item.findall("category") if _node_text(child, "")],
            }
        )
    return normalized


def _html_items(raw: str, source_url: str) -> list[dict[str, Any]]:
    parser = _OpportunityLinkParser(source_url)
    parser.feed(raw)
    return parser.items()


class _OpportunityLinkParser(HTMLParser):
    opportunity_terms = (
        "apply",
        "award",
        "call",
        "competition",
        "contest",
        "fellowship",
        "funding",
        "grant",
        "internship",
        "mobility",
        "opportunit",
        "programme",
        "program",
        "research",
        "scholarship",
        "стипенд",
        "грант",
        "конкурс",
        "можлив",
        "програм",
    )
    generic_titles = {
        "all opportunities",
        "calls",
        "competitions",
        "contests",
        "current calls",
        "funding",
        "funding opportunities",
        "grants",
        "open calls",
        "opportunities",
        "programmes",
        "programs",
        "scholarship database",
        "scholarships",
        "всі можливості",
        "гранти",
        "конкурси",
        "можливості",
        "програми",
        "стипендії",
    }
    blocked_path_terms = (
        "/about",
        "/archive",
        "/blog",
        "/calendar",
        "/category",
        "/contact",
        "/events",
        "/faq",
        "/login",
        "/opportunities",
        "/programs",
        "/programmes",
        "/search",
        "/tag",
    )
    concrete_path_terms = (
        "/call",
        "/calls/",
        "/competition",
        "/contest",
        "/grant",
        "/grants/",
        "/opportunity/",
        "/post/",
        "/posts/",
        "/scholarship",
        "/stipend",
        "/vacancy",
    )

    def __init__(self, source_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source_url = source_url
        self._active_href: str | None = None
        self._active_text: list[str] = []
        self._links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href")
        if href:
            self._active_href = href
            self._active_text = []

    def handle_data(self, data: str) -> None:
        if self._active_href:
            self._active_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._active_href:
            return
        title = " ".join(" ".join(self._active_text).split())
        href = self._active_href
        self._active_href = None
        self._active_text = []
        if not self._looks_like_opportunity(title, href):
            return
        self._links.append(
            {
                "title": title,
                "url": urljoin(self.source_url, href),
                "summary": title,
            }
        )

    def items(self) -> list[dict[str, str]]:
        seen: set[str] = set()
        items: list[dict[str, str]] = []
        for link in self._links:
            key = link["url"].casefold()
            if key in seen:
                continue
            seen.add(key)
            items.append(link)
        return items

    def _looks_like_opportunity(self, title: str, href: str) -> bool:
        if len(title) < 8 or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            return False
        absolute_url = urljoin(self.source_url, href)
        if _same_page(self.source_url, absolute_url):
            return False
        title_normalized = " ".join(title.casefold().split()).strip(" .:-|")
        if title_normalized in self.generic_titles:
            return False
        path = urlparse(absolute_url).path.casefold().rstrip("/")
        if self._is_generic_listing_path(path):
            return False
        searchable = f"{title_normalized} {path}".casefold()
        return any(term in searchable for term in self.opportunity_terms) and self._has_specificity(title_normalized, path)

    def _is_generic_listing_path(self, path: str) -> bool:
        if not path:
            return True
        return any(path == term.rstrip("/") or path.endswith(term.rstrip("/")) for term in self.blocked_path_terms) and not any(
            term in path for term in self.concrete_path_terms
        )

    def _has_specificity(self, title: str, path: str) -> bool:
        if any(char.isdigit() for char in f"{title} {path}"):
            return True
        if any(term in path for term in self.concrete_path_terms):
            return True
        words = [word for word in title.replace("/", " ").replace("-", " ").split() if len(word) > 2]
        return len(words) >= 4


def _payload_from_mapping(item: dict[str, Any], payload: ExternalSourceImportRequest) -> OpportunityCreate:
    connector = get_source_connector(payload.source_name)
    normalized = connector.normalize(item)
    title = normalized.title
    url = normalized.url or str(payload.source_url)
    summary = normalized.summary
    keywords = _dedupe(normalized.keywords)
    if payload.keyword:
        keywords.append(payload.keyword)
    country_values = _dedupe(normalized.countries)
    if payload.default_country:
        country_values.append(payload.default_country)
    stage_values = _dedupe(normalized.career_stages)
    if payload.default_career_stage:
        stage_values.append(payload.default_career_stage)
    disciplines = _dedupe(normalized.disciplines)
    if payload.default_discipline:
        disciplines.append(payload.default_discipline)

    return OpportunityCreate(
        title=title,
        opportunity_type=normalized.opportunity_type or _opportunity_type(payload.default_opportunity_type),
        source=payload.source_name,
        url=url,
        summary=summary,
        eligibility=normalized.eligibility,
        disciplines=_dedupe(disciplines),
        keywords=_dedupe(keywords),
        countries=_dedupe(country_values),
        career_stages=_dedupe(stage_values),
        deadline=_parse_date(normalized.deadline),
    )


def _first(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        text = str(value).strip()
        if text:
            return text
    return ""


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).replace(";", ",").split(",") if item.strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _opportunity_type(value: str) -> OpportunityType:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return OpportunityType(normalized) if normalized in {item.value for item in OpportunityType} else OpportunityType.fellowship


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    for candidate in (value[:10], value):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                return date.fromisoformat(candidate) if fmt == "%Y-%m-%d" else datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    return None


def _node_text(item: ElementTree.Element, tag: str) -> str:
    if not tag:
        node = item
    else:
        node = item.find(tag)
        if node is None:
            node = item.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
    return "".join(node.itertext()).strip() if node is not None else ""


def _rss_link(item: ElementTree.Element) -> str:
    text_link = _node_text(item, "link")
    if text_link:
        return text_link
    atom_link = item.find("{http://www.w3.org/2005/Atom}link")
    return atom_link.attrib.get("href", "") if atom_link is not None else ""


def _same_page(left: str, right: str) -> bool:
    left_parts = urlparse(left)
    right_parts = urlparse(right)
    left_path = left_parts.path.rstrip("/") or "/"
    right_path = right_parts.path.rstrip("/") or "/"
    return left_parts.netloc.casefold() == right_parts.netloc.casefold() and left_path.casefold() == right_path.casefold()
