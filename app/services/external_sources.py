from datetime import date, datetime
from typing import Any
from xml.etree import ElementTree

import httpx
from app.api.opportunities import _to_preview
from app.db.models import OpportunityType
from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult
from app.schemas.opportunities import OpportunityCreate
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_import import import_opportunities


class ExternalSourceClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http_client = http_client or httpx.Client(timeout=20, follow_redirects=True)

    def fetch(self, url: str) -> str:
        response = self.http_client.get(url)
        response.raise_for_status()
        return response.text


def import_external_source(payload: ExternalSourceImportRequest, db, client: ExternalSourceClient | None = None) -> ExternalSourceImportResult:
    source_client = client or ExternalSourceClient()
    ensure_source(db, name=payload.source_name, display_name=payload.source_name, base_url=str(payload.source_url), source_type=payload.source_kind)
    batch = start_batch(db, source_name=payload.source_name, query=str(payload.source_url), dry_run=not payload.import_results)
    try:
        raw = source_client.fetch(str(payload.source_url))
        opportunities = normalize_external_source(raw, payload)
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
        db.refresh(batch)
        return ExternalSourceImportResult(
            source=payload.source_name,
            batch_id=batch.id,
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            opportunities=[_to_preview(opportunity) for opportunity in processed],
        )
    except Exception:
        finish_batch(db, batch, imported_count=0, updated_count=0, skipped_count=0, error_count=1)
        db.commit()
        raise


def normalize_external_source(raw: str, payload: ExternalSourceImportRequest) -> list[OpportunityCreate]:
    if payload.source_kind == "json":
        return [_payload_from_mapping(item, payload) for item in _json_items(raw)[: payload.limit]]
    return [_payload_from_mapping(item, payload) for item in _rss_items(raw)[: payload.limit]]


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


def _payload_from_mapping(item: dict[str, Any], payload: ExternalSourceImportRequest) -> OpportunityCreate:
    title = _first(item, "title", "name", "opportunityTitle") or "Untitled opportunity"
    url = _first(item, "url", "link", "href", "web_url") or str(payload.source_url)
    summary = _first(item, "summary", "description", "abstract", "content") or ""
    keywords = _list_value(item.get("keywords") or item.get("tags") or item.get("category"))
    if payload.keyword:
        keywords.append(payload.keyword)
    country_values = _list_value(item.get("countries") or item.get("country"))
    if payload.default_country:
        country_values.append(payload.default_country)
    stage_values = _list_value(item.get("career_stages") or item.get("careerStage"))
    if payload.default_career_stage:
        stage_values.append(payload.default_career_stage)
    disciplines = _list_value(item.get("disciplines") or item.get("fields"))
    if payload.default_discipline:
        disciplines.append(payload.default_discipline)

    return OpportunityCreate(
        title=title,
        opportunity_type=_opportunity_type(_first(item, "opportunity_type", "type") or payload.default_opportunity_type),
        source=payload.source_name,
        url=url,
        summary=summary,
        eligibility=_first(item, "eligibility", "requirements") or "",
        disciplines=disciplines,
        keywords=keywords,
        countries=country_values,
        career_stages=stage_values,
        deadline=_parse_date(_first(item, "deadline", "closeDate", "closing_date", "pubDate") or ""),
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
