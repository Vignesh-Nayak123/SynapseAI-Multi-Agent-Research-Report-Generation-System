from __future__ import annotations

import re
from typing import Any

import aiohttp
import structlog

logger = structlog.get_logger(__name__)

ARXIV_PATTERN = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/(\d+\.\d+))", re.IGNORECASE)

DOI_CACHE: dict[str, str | None] = {}
# Bound the cache: arXiv IDs are unbounded user input; evict oldest first.
DOI_CACHE_MAX_SIZE = 1000


def extract_arxiv_ids(urls: list[str]) -> list[str]:
    """Extract arXiv IDs from a list of URLs."""
    ids: list[str] = []
    for url in urls:
        match = ARXIV_PATTERN.search(url)
        if match:
            ids.append(match.group(1))
    return ids


async def resolve_doi(arxiv_id: str) -> str | None:
    """Resolve the DOI for an arXiv ID using the arXiv API (HTTPS)."""
    if arxiv_id in DOI_CACHE:
        return DOI_CACHE[arxiv_id]

    if not re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", arxiv_id):
        logger.warning("doi.invalid_arxiv_id", arxiv_id=arxiv_id)
        return None

    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()

        try:
            from defusedxml.ElementTree import fromstring as _safe_fromstring
        except ImportError:
            from xml.etree.ElementTree import fromstring as _safe_fromstring
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        root = _safe_fromstring(text)
        entry = root.find("atom:entry", ns)
        if entry is not None:
            doi_el = entry.find("arxiv:doi", ns)
            if doi_el is not None and doi_el.text:
                _cache_doi(arxiv_id, doi_el.text)
                return doi_el.text
        _cache_doi(arxiv_id, None)
        return None
    except Exception as exc:
        logger.warning("doi.resolve_failed", arxiv_id=arxiv_id, error=str(exc))
        _cache_doi(arxiv_id, None)
        return None


def _cache_doi(arxiv_id: str, doi: str | None) -> None:
    """Insert into the bounded DOI cache, evicting oldest entries first."""
    DOI_CACHE[arxiv_id] = doi
    while len(DOI_CACHE) > DOI_CACHE_MAX_SIZE:
        DOI_CACHE.pop(next(iter(DOI_CACHE)))


async def resolve_dois_batch(urls: list[str], max_concurrency: int = 5) -> dict[str, str | None]:
    """Resolve DOIs for arXiv IDs found in the given URLs (bounded concurrency)."""
    import asyncio

    arxiv_ids = extract_arxiv_ids(urls)
    result: dict[str, str | None] = {}
    semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def _one(aid: str) -> tuple[str, str | None]:
        async with semaphore:
            return aid, await resolve_doi(aid)

    for aid, doi in await asyncio.gather(*(_one(aid) for aid in arxiv_ids)):
        result[aid] = doi
    return result
