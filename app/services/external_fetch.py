import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.core.exceptions import BadRequestError


ALLOWED_CONTENT_TYPES = (
    "application/atom+xml",
    "application/json",
    "application/rss+xml",
    "application/xml",
    "text/html",
    "text/plain",
    "text/xml",
)


class ExternalSourceClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self.http_client = http_client or httpx.Client(timeout=20, follow_redirects=True)

    def fetch(self, url: str) -> str:
        validate_external_source_url(url)
        with self.http_client.stream("GET", url) as response:
            response.raise_for_status()
            validate_response_content_type(response.headers.get("content-type", ""))
            chunks: list[bytes] = []
            total_size = 0
            for chunk in response.iter_bytes():
                total_size += len(chunk)
                if total_size > settings.external_source_max_bytes:
                    raise BadRequestError("External source response is too large")
                chunks.append(chunk)
            return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")


def validate_external_source_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise BadRequestError("External source URL must use HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise BadRequestError("External source URL must not include credentials")
    hostname = (parsed.hostname or "").strip().casefold()
    if not hostname:
        raise BadRequestError("External source URL must include a host")
    _validate_allowed_host(hostname)
    _validate_host_is_public(hostname)


def validate_response_content_type(content_type: str) -> None:
    normalized = content_type.split(";", 1)[0].strip().casefold()
    if normalized and not any(normalized == allowed for allowed in ALLOWED_CONTENT_TYPES):
        raise BadRequestError("External source content type is not supported")


def _validate_allowed_host(hostname: str) -> None:
    allowed_hosts = [host.strip().casefold() for host in settings.external_source_allowed_hosts if host.strip()]
    if not allowed_hosts:
        return
    if not any(hostname == allowed or hostname.endswith(f".{allowed}") for allowed in allowed_hosts):
        raise BadRequestError("External source host is not allowed")


def _validate_host_is_public(hostname: str) -> None:
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise BadRequestError("External source host must not be localhost")
    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None
    if literal_ip is not None:
        _reject_private_address(literal_ip)
        return
    if not settings.external_source_resolve_hosts:
        return
    try:
        address_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise BadRequestError("External source host could not be resolved") from exc
    for item in address_info:
        address = item[4][0]
        _reject_private_address(ipaddress.ip_address(address))


def _reject_private_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if any(
        (
            address.is_loopback,
            address.is_private,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    ):
        raise BadRequestError("External source host resolves to a blocked network address")
