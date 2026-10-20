from __future__ import annotations

from collections import OrderedDict

import structlog
from ddgs import DDGS  # type: ignore
from tavily import TavilyClient  # type: ignore

from src.config import get_settings

logger = structlog.get_logger(__name__)


def search_papers(query: str, limit: int | None = None) -> list[str]:
    """Return a list of PDF URLs relevant to the query."""

    settings = get_settings()
    target = limit or settings.max_search_results
    # Enriched query to target academic sources, theses, and research papers
    enriched_query = f"{query} (site:arxiv.org OR site:edu OR site:ac.uk OR site:researchgate.net OR filetype:pdf) research paper thesis"
    urls: list[str] = []

    # Execute searches in parallel if API key is present
    if settings.tavily_api_key:
        print("Searching Tavily and DuckDuckGo in parallel...")
        tavily_results = _search_tavily(enriched_query, target, settings.tavily_api_key)
        urls.extend(tavily_results)

    # Always try DDG to supplement, especially if Tavily returns few results
    if len(urls) < target:
        remaining = target - len(urls)
        print(f"Supplementing with DuckDuckGo ({remaining} needed)...")
        ddg_results = _search_duckduckgo(enriched_query, remaining)
        urls.extend(ddg_results)

    # Preserve first occurrence order while removing duplicates
    ordered = list(OrderedDict((url, True) for url in urls if url).keys())
    print(f"Search complete. Found {len(ordered)} unique PDFs.")
    logger.info("search.complete", query=query, count=len(ordered))
    return ordered


def _search_tavily(query: str, limit: int, api_key: str) -> list[str]:
    if limit <= 0:
        return []
    client = TavilyClient(api_key=api_key)
    settings = get_settings()
    allowed_topics = {"general", "news", "finance"}
    topic = settings.tavily_topic.lower()
    if topic not in allowed_topics:
        logger.warning("search.tavily_invalid_topic", configured=topic)
        topic = "general"
    try:
        response = client.search(query=query, search_depth="advanced", max_results=limit, topic=topic)
    except Exception as exc:  # pragma: no cover - network failure paths harder to simulate
        logger.warning("search.tavily_error", error=str(exc))
        return []

    urls = [item.get("url") for item in response.get("results", []) if item.get("url")]
    logger.info("search.tavily_success", count=len(urls))
    return urls


def _search_duckduckgo(query: str, limit: int) -> list[str]:
    if limit <= 0:
        return []
    urls: list[str] = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=limit)
            for item in results:
                candidate = item.get("href") or item.get("url")
                if candidate:
                    urls.append(candidate)
    except Exception as exc:  # pragma: no cover - network failure paths harder to simulate
        logger.warning("search.ddg_error", error=str(exc))
    logger.info("search.ddg_success", count=len(urls))
    return urls
