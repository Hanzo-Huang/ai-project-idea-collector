import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx


MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ("text/", "application/xhtml+xml", "application/xml", "application/rss+xml", "application/atom+xml")


def _is_public_address(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


async def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must use http or https and include a hostname")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Local and private network URLs are not allowed")
    try:
        addresses = [hostname] if _is_public_address(hostname) else []
    except ValueError:
        try:
            records = await asyncio.to_thread(socket.getaddrinfo, hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError(f"Could not resolve URL hostname: {hostname}") from exc
        addresses = list({record[4][0] for record in records})
    if not addresses or any(not _is_public_address(address) for address in addresses):
        raise ValueError("Local and private network URLs are not allowed")
    return url


async def safe_get_text(url: str, *, timeout: float = 25, max_redirects: int = 5) -> tuple[str, str]:
    current = url
    headers = {"User-Agent": "Mozilla/5.0 AIProjectCollector/1.0"}
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, headers=headers) as client:
        for redirect_count in range(max_redirects + 1):
            await validate_public_url(current)
            async with client.stream("GET", current) as response:
                if response.is_redirect:
                    if redirect_count == max_redirects:
                        raise ValueError("URL redirected too many times")
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("URL returned an invalid redirect")
                    current = urljoin(str(response.url), location)
                    continue
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if content_type and not content_type.startswith(ALLOWED_CONTENT_TYPES):
                    raise ValueError(f"Unsupported content type: {content_type}")
                declared_size = int(response.headers.get("content-length", "0") or 0)
                if declared_size > MAX_DOCUMENT_BYTES:
                    raise ValueError("Document is larger than 5 MB")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_DOCUMENT_BYTES:
                        raise ValueError("Document is larger than 5 MB")
                    chunks.append(chunk)
                encoding = response.charset_encoding or "utf-8"
                return b"".join(chunks).decode(encoding, errors="replace"), str(response.url)
    raise ValueError("Unable to fetch URL")

