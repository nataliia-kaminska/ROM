import logging
from html.parser import HTMLParser

import httpx

from app.core.config import settings
from app.services.external_fetch import ExternalSourceClient

logger = logging.getLogger(__name__)


class _ReadableTextParser(HTMLParser):
    ignored_tags = {"button", "footer", "form", "header", "nav", "noscript", "script", "style", "svg"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._inside_title = False
        self._meta_parts: list[str] = []
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.casefold()
        attr_map = {name.casefold(): value for name, value in attrs if value}
        if normalized_tag == "title":
            self._inside_title = True
        if normalized_tag == "meta":
            key = (attr_map.get("name") or attr_map.get("property") or "").casefold()
            if key in {"description", "og:title", "og:description", "twitter:title", "twitter:description"}:
                self._append_meta(attr_map.get("content", ""))
        if normalized_tag in self.ignored_tags:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag == "title":
            self._inside_title = False
        if normalized_tag in self.ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._append_meta(data)
            return
        if self._ignored_depth:
            return
        cleaned = " ".join(data.split())
        if cleaned:
            self._parts.append(cleaned)

    def text(self) -> str:
        seen: set[str] = set()
        parts: list[str] = []
        for part in [*self._meta_parts, *self._parts]:
            key = part.casefold()
            if key not in seen:
                seen.add(key)
                parts.append(part)
        return " ".join(parts)

    def _append_meta(self, value: str) -> None:
        cleaned = " ".join(value.split())
        if cleaned:
            self._meta_parts.append(cleaned)


def fetch_opportunity_page_preview(url: str) -> str:
    if not settings.opportunity_page_enrichment_enabled:
        return ""
    timeout = max(1, settings.opportunity_page_enrichment_timeout_seconds)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as http_client:
            client = ExternalSourceClient(http_client)
            raw = client.fetch(url)
        text = _html_to_readable_text(raw)
        preview = text[: settings.opportunity_page_enrichment_max_chars].strip()
        logger.info("opportunity page preview fetched url=%s chars=%s", url, len(preview))
        return preview
    except Exception as exc:
        logger.info("opportunity page preview skipped url=%s reason=%s", url, exc)
        return ""


def _html_to_readable_text(raw: str) -> str:
    if "<" not in raw or ">" not in raw:
        return " ".join(raw.split())
    parser = _ReadableTextParser()
    parser.feed(raw)
    return parser.text()
