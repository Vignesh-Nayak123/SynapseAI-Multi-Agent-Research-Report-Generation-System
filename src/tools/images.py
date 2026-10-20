from __future__ import annotations

import time
from typing import Any

import structlog
from ddgs import DDGS

logger = structlog.get_logger(__name__)

# ── In-memory TTL cache ────────────────────────────────────────────
# Maps normalized query -> (timestamp, results)
_IMAGE_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_IMAGE_CACHE_TTL = 3600  # 1 hour
_IMAGE_CACHE_MAXSIZE = 200  # evict oldest when above this


def _normalize_query(query: str) -> str:
    """Normalize a query string for use as a cache key."""
    return query.strip().lower()


def _cache_get(key: str) -> list[dict[str, Any]] | None:
    """Return cached results for *key* if they exist and are fresh, else None."""
    entry = _IMAGE_CACHE.get(key)
    if entry is None:
        return None
    timestamp, results = entry
    if time.time() - timestamp > _IMAGE_CACHE_TTL:
        del _IMAGE_CACHE[key]
        return None
    return results


def _cache_set(key: str, results: list[dict[str, Any]]) -> None:
    """Store *results* in the cache under *key* with the current timestamp.

    If the cache exceeds *_IMAGE_CACHE_MAXSIZE*, the oldest entries are evicted.
    """
    _IMAGE_CACHE[key] = (time.time(), results)
    if len(_IMAGE_CACHE) > _IMAGE_CACHE_MAXSIZE:
        # Evict the oldest 25% of entries to avoid thrashing the boundary
        sorted_keys = sorted(_IMAGE_CACHE, key=lambda k: _IMAGE_CACHE[k][0])
        for old_key in sorted_keys[: _IMAGE_CACHE_MAXSIZE // 4]:
            del _IMAGE_CACHE[old_key]
        logger.info("images.cache_evicted", count=_IMAGE_CACHE_MAXSIZE // 4)


def clear_image_cache() -> None:
    """Clear all cached image and graph results."""
    _IMAGE_CACHE.clear()
    logger.info("images.cache_cleared")


def search_related_images(query: str, max_results: int = 8) -> list[dict[str, Any]]:
    """Search for images related to a research topic.

    Results are cached in-memory for *IMAGE_CACHE_TTL* seconds so that repeated
    queries on the same topic skip the network request.

    Returns a list of image results, each containing:
        - title: Alt text / title
        - image: Direct URL to the full-size image
        - thumbnail: Thumbnail URL
        - url: Source page URL
        - source: Source domain
        - width, height: Image dimensions
    """
    cache_key = _normalize_query(query)
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("images.cache_hit", query=query)
        return cached

    try:
        with DDGS() as ddgs:
            results = list(
                ddgs.images(
                    query=query,
                    max_results=max_results,
                    safesearch="moderate",
                )
            )
        _cache_set(cache_key, results)
        logger.info("images.search_success", query=query, count=len(results))
        return results
    except Exception as exc:
        logger.warning("images.search_failed", query=query, error=str(exc))
        return []


def search_related_graphs(query: str, max_results: int = 6) -> list[dict[str, Any]]:
    """Search for charts, graphs, and data visualizations related to a research topic.

    Enhances the query with chart/graph terms to find data visualizations.
    Results are cached in-memory for *IMAGE_CACHE_TTL* seconds.
    """
    cache_key = _normalize_query(query) + "::graphs"
    cached = _cache_get(cache_key)
    if cached is not None:
        logger.info("graphs.cache_hit", query=query)
        return cached

    # Try multiple enriched queries to find relevant charts/graphs
    enriched_queries = [
        f"{query} chart graph data visualization",
        f"{query} statistics diagram",
    ]

    seen_urls: set[str] = set()
    results: list[dict[str, Any]] = []

    try:
        with DDGS() as ddgs:
            for eq in enriched_queries:
                if len(results) >= max_results:
                    break
                batch = list(
                    ddgs.images(
                        query=eq,
                        max_results=max_results,
                        safesearch="moderate",
                    )
                )
                for item in batch:
                    img_url = item.get("image", "")
                    if img_url and img_url not in seen_urls:
                        seen_urls.add(img_url)
                        results.append(item)
                    if len(results) >= max_results:
                        break

        _cache_set(cache_key, results)
        logger.info("graphs.search_success", query=query, count=len(results))
        return results
    except Exception as exc:
        logger.warning("graphs.search_failed", query=query, error=str(exc))
        return []
