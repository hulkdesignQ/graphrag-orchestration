"""
Ingestion Service

Normalizes various document inputs and extracts text when needed.

Supports:
- Raw text strings
- Dicts with {"text": str, "metadata": {...}}
- URLs (http/https) pointing to text or PDF content

For PDFs, uses a lightweight local parser (pypdf).
"""

from typing import Any, Dict, List, Union
import ipaddress
import logging
import io
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

# IP ranges that must be blocked to prevent SSRF attacks
_BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_url(url: str) -> None:
    """Block requests to internal/private networks."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL has no hostname")
    import socket
    try:
        resolved = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in resolved:
            addr = ipaddress.ip_address(sockaddr[0])
            for blocked in _BLOCKED_IP_RANGES:
                if addr in blocked:
                    raise ValueError(f"URL resolves to blocked IP range")
    except socket.gaierror:
        raise ValueError(f"Cannot resolve hostname: {hostname}")


class IngestionService:
    def __init__(self) -> None:
        try:
            import pypdf  # noqa: F401
            self._pdf_available = True
        except Exception:
            self._pdf_available = False

    def _extract_pdf_text(self, content: bytes) -> str:
        if not self._pdf_available:
            raise RuntimeError("PDF parser not available (pypdf not installed)")
        from pypdf import PdfReader
        text_parts: List[str] = []
        with io.BytesIO(content) as bio:
            reader = PdfReader(bio)
            for page in reader.pages:
                try:
                    text_parts.append(page.extract_text() or "")
                except Exception:
                    # best effort per page
                    continue
        return "\n".join([t for t in text_parts if t])

    def _fetch_url_text(self, url: str) -> str:
        _validate_url(url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        ctype = (resp.headers.get("content-type") or "").lower()

        # If PDF
        if ("application/pdf" in ctype) or url.lower().endswith(".pdf"):
            logger.info("ingestion_pdf_detected url=%s", url)
            return self._extract_pdf_text(resp.content)

        # Textual content types
        if ctype.startswith("text/") or "application/json" in ctype or "application/xml" in ctype:
            return resp.text

        # Fallback: try decode as UTF-8
        try:
            return resp.content.decode("utf-8", errors="ignore")
        except Exception:
            return resp.text  # let requests guess

    def preprocess(self, input_items: List[Union[str, Dict[str, Any]]]):
        """Return LlamaIndex Document objects from mixed inputs."""
        from llama_index.core import Document

        docs: List[Document] = []
        for item in input_items:
            if isinstance(item, dict):
                if "text" in item:
                    docs.append(Document(text=item["text"], metadata=item.get("metadata") or {}))
                    continue
                if "url" in item and isinstance(item["url"], str):
                    url = item["url"]
                    text = self._fetch_url_text(url)
                    meta = item.get("metadata") or {}
                    if "source_url" not in meta:
                        meta = {**meta, "source_url": url}
                    docs.append(Document(text=text, metadata=meta))
                    continue
                raise ValueError("Document dict must include 'text' or 'url'.")

            if isinstance(item, str):
                s = item.strip()
                if s.startswith("http://") or s.startswith("https://"):
                    text = self._fetch_url_text(s)
                    docs.append(Document(text=text, metadata={"source_url": s}))
                else:
                    docs.append(Document(text=s))
                continue

            raise ValueError("Unsupported document item type. Use string or {text|url}.")

        return docs
