from __future__ import annotations

import asyncio
import io
import ipaddress
import re
import socket
import urllib.parse
import urllib.request
from typing import List, Tuple, Optional
from urllib.parse import urlparse

import aiohttp
import fitz  # type: ignore
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)

USER_AGENT = "Multi-Agent-Research-System/1.0"
REFERENCE_MARKERS = ("references", "bibliography", "acknowledgements")
MAX_PDF_BYTES = 15 * 1024 * 1024
ALLOWED_SCHEMES = frozenset({"http", "https"})
BLOCKED_METADATA_HOSTS = frozenset({"169.254.169.254", "metadata.google.internal"})

_session: aiohttp.ClientSession | None = None


async def _get_session() -> aiohttp.ClientSession:
    """Return a shared ClientSession (created lazily, reused across calls)."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def close_shared_session() -> None:
    """Close the shared ClientSession (used in tests/teardown)."""
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
    _session = None


def _validate_url(url: str) -> str:
    """Allowlist http/https schemes and block private IP/metadata targets."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")
    host = (parsed.hostname or "").lower()
    if not host or host in BLOCKED_METADATA_HOSTS:
        raise ValueError(f"Blocked PDF host: {host!r}")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValueError(f"Unable to resolve PDF host: {host!r}") from exc
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError(f"Blocked private/link-local PDF target: {host!r}")
    return url


def _check_content_type(content_type: str, url: str) -> None:
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype and ctype not in {"application/pdf", "application/octet-stream", "binary/octet-stream"}:
        raise ValueError(f"Unexpected content-type {ctype!r} for PDF URL: {url!r}")


class PDFProcessor:
    def __init__(self, max_concurrency: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def process_batch(self, urls: List[str]) -> List[Optional[str]]:
        tasks = [self.process_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        texts: List[Optional[str]] = []
        for url, result in zip(urls, results):
            if isinstance(result, BaseException):
                # Never leak exception objects into the document list; log instead.
                logger.warning("pdf.batch.task_failed", url=url, error=str(result))
                texts.append(None)
            else:
                texts.append(result)
        return texts

    async def process_url(self, url: str) -> Optional[str]:
        async with self.semaphore:
            try:
                logger.info("pdf.process.start", url=url)
                raw_bytes = await self._download_pdf_async(url)
                if not raw_bytes:
                    return None
                
                # Run CPU-bound extraction in a thread
                text = await asyncio.to_thread(self._extract_and_validate, raw_bytes)
                if not text:
                    return None
                    
                cleaned = _strip_reference_sections(text)
                logger.info("pdf.process.complete", url=url, char_count=len(cleaned))
                return cleaned
            except Exception as exc:
                logger.warning("pdf.process.failed", url=url, error=str(exc))
                return None

    async def _download_pdf_async(self, url: str) -> Optional[bytes]:
        try:
            _validate_url(url)
            session = await _get_session()
            async with session.get(url, headers={"User-Agent": USER_AGENT}, timeout=15) as response:
                if response.status != 200:
                    logger.warning("pdf.download.status_error", url=url, status=response.status)
                    return None
                _check_content_type(response.headers.get("Content-Type", ""), url)
                chunks: list[bytes] = []
                total = 0
                async for chunk in response.content.iter_chunked(64 * 1024):
                    total += len(chunk)
                    if total > MAX_PDF_BYTES:
                        logger.warning("pdf.download.too_large", url=url, total=total)
                        return None
                    chunks.append(chunk)
                return b"".join(chunks)
        except ValueError:
            raise
        except Exception as exc:
            logger.warning("pdf.download.network_error", url=url, error=str(exc))
            return None

    def _extract_and_validate(self, raw_bytes: bytes) -> str:
        settings = get_settings()
        char_limit = settings.max_context_chars * 2
        
        text_parts = []
        current_length = 0
        
        try:
            with fitz.open(stream=io.BytesIO(raw_bytes), filetype="pdf") as document:
                for page in document:
                    page_text = _extract_page(page)
                    if page_text and self._validate_segment(page_text):
                        text_parts.append(page_text)
                        current_length += len(page_text)
                        if current_length >= char_limit:
                            break
        except Exception as exc:
            logger.warning("pdf.extract.error", error=str(exc))
            return ""
            
        return "\n".join(text_parts)

    def _validate_segment(self, text: str) -> bool:
        """
        Validate text segment based on density scoring.
        Reject segments with low alphanumeric density (e.g. OCR garbage, sparse tables).
        """
        if not text or len(text) < 50:
            return False
            
        # Calculate density: (alphanumeric chars) / (total chars)
        alphanum = sum(c.isalnum() for c in text)
        density = alphanum / len(text)
        
        # Threshold: 0.5 means at least 50% of characters must be alphanumeric
        if density < 0.5:
            return False
            
        return True


# Legacy wrapper for backward compatibility if needed, but we'll update nodes.py
def parse_pdf(url: str) -> str:
    """Download and parse a PDF into clean text optimized for LLM consumption."""
    # ... implementation ...
    # For now, we can keep the old implementation or redirect to the new one synchronously
    # But since we are moving to async, we should use the class.
    # This function is kept for the synchronous parts of the code if any.
    
    logger.info("pdf.parse.start", url=url)
    print(f"Downloading PDF: {url}...")
    raw_bytes = _download_pdf(url)
    text = _extract_text(raw_bytes)
    cleaned = _strip_reference_sections(text)
    print(f"Parsed PDF: {url} ({len(cleaned)} chars)")
    logger.info("pdf.parse.complete", url=url, char_count=len(cleaned))
    return cleaned


def _download_pdf(url: str) -> bytes:
    _validate_url(url)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:  # nosec: B310
        _check_content_type(response.headers.get_content_type(), url)
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(64 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_PDF_BYTES:
                raise ValueError(f"PDF exceeds {MAX_PDF_BYTES} byte cap: {url!r}")
            chunks.append(chunk)
        return b"".join(chunks)


def _extract_text(raw_bytes: bytes) -> str:
    settings = get_settings()
    # Fetch a bit more than the limit to allow for cleanup/stripping
    char_limit = settings.max_context_chars * 2
    
    text_parts = []
    current_length = 0
    
    with fitz.open(stream=io.BytesIO(raw_bytes), filetype="pdf") as document:
        for page in document:
            page_text = _extract_page(page)
            if page_text:
                text_parts.append(page_text)
                current_length += len(page_text)
                if current_length >= char_limit:
                    break
                    
    return "\n".join(text_parts)


def _extract_page(page: fitz.Page) -> str:
    blocks: List[Tuple[float, float, float, float, str, int]] = page.get_text("blocks")  # type: ignore[assignment]
    filtered = [(x0, y0, x1, y1, text.strip()) for x0, y0, x1, y1, text, *_ in blocks if text.strip()]
    if not filtered:
        return ""

    mid_x = page.rect.width / 2
    left: List[Tuple[float, str]] = []
    right: List[Tuple[float, str]] = []
    for x0, y0, x1, _, text in filtered:
        column = left if ((x0 + x1) / 2) <= mid_x else right
        column.append((y0, text))

    is_two_column = _has_two_columns(left, right)
    if is_two_column:
        left_text = "\n".join(text for _, text in sorted(left, key=lambda b: b[0]))
        right_text = "\n".join(text for _, text in sorted(right, key=lambda b: b[0]))
        ordered = f"{left_text}\n{right_text}".strip()
    else:
        ordered = "\n".join(text for _, text in sorted(left + right, key=lambda b: b[0]))
    ordered = re.sub(r"\s+", " ", ordered)
    return ordered.strip()


def _has_two_columns(left: List[Tuple[float, str]], right: List[Tuple[float, str]]) -> bool:
    if not left or not right:
        return False
    imbalance = abs(len(left) - len(right)) / max(len(left), len(right))
    return imbalance < 0.6


def _strip_reference_sections(text: str) -> str:
    lower = text.lower()
    cutoff = len(text)
    for marker in REFERENCE_MARKERS:
        idx = lower.rfind(marker)
        if idx != -1 and idx > len(text) * 0.5:
            cutoff = min(cutoff, idx)
    cleaned = text[:cutoff]
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()

