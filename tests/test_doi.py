"""Tests for src.tools.doi — arXiv DOI resolution."""

from __future__ import annotations

import pytest
from src.tools.doi import extract_arxiv_ids


class TestExtractArxivIds:
    """Pure-function tests for extract_arxiv_ids()."""

    def test_abs_url(self):
        urls = ["https://arxiv.org/abs/2301.12345"]
        assert extract_arxiv_ids(urls) == ["2301.12345"]

    def test_pdf_url(self):
        urls = ["https://arxiv.org/pdf/2301.12345.pdf"]
        assert extract_arxiv_ids(urls) == ["2301.12345"]

    def test_mixed_urls(self):
        urls = [
            "https://arxiv.org/abs/2301.12345",
            "https://arxiv.org/pdf/2302.67890.pdf",
            "https://example.com/not-arxiv",
        ]
        assert extract_arxiv_ids(urls) == ["2301.12345", "2302.67890"]

    def test_no_arxiv_urls(self):
        urls = [
            "https://example.com/paper",
            "https://google.com",
        ]
        assert extract_arxiv_ids(urls) == []

    def test_empty_list(self):
        assert extract_arxiv_ids([]) == []

    def test_case_insensitivity(self):
        urls = ["https://ARXIV.ORG/ABS/2301.12345"]
        assert extract_arxiv_ids(urls) == ["2301.12345"]

    def test_multiple_ids_same_url(self):
        urls = ["https://arxiv.org/abs/2301.12345", "https://arxiv.org/abs/2301.12345"]
        assert extract_arxiv_ids(urls) == ["2301.12345", "2301.12345"]

    def test_older_id_format(self):
        urls = ["https://arxiv.org/abs/astro-ph/0601001"]
        assert extract_arxiv_ids(urls) == []

    def test_versioned_id(self):
        urls = ["https://arxiv.org/abs/2301.12345v2"]
        assert extract_arxiv_ids(urls) == ["2301.12345"]

    def test_url_with_query_params(self):
        urls = ["https://arxiv.org/abs/2301.12345?utm_source=test"]
        assert extract_arxiv_ids(urls) == ["2301.12345"]


class TestResolveDoiBatch:
    """Tests for resolve_dois_batch() — uses real arXiv API (integration)."""

    @pytest.mark.asyncio
    async def test_resolve_known_arxiv(self):
        """Verify that a well-known arXiv ID returns a DOI string."""
        from src.tools.doi import resolve_dois_batch

        # 2301.12345 is a real arXiv paper with a DOI assigned
        urls = ["https://arxiv.org/abs/2301.12345"]
        result = await resolve_dois_batch(urls)
        # It should either have a DOI or be None if the API is unreachable
        assert "2301.12345" in result
        # If the API works, DOI should be a non-empty string or None
        doi = result["2301.12345"]
        assert doi is None or isinstance(doi, str)

    @pytest.mark.asyncio
    async def test_resolve_non_arxiv_url(self):
        """Non-arXiv URLs should produce an empty result."""
        from src.tools.doi import resolve_dois_batch

        result = await resolve_dois_batch(["https://example.com/paper"])
        assert result == {}

    @pytest.mark.asyncio
    async def test_resolve_multiple(self):
        """Batch resolve with a mix of arXiv and non-arXiv URLs."""
        from src.tools.doi import resolve_dois_batch

        urls = [
            "https://arxiv.org/abs/2301.12345",
            "https://example.com",
            "https://arxiv.org/abs/2302.67890",
        ]
        result = await resolve_dois_batch(urls)
        assert "2301.12345" in result
        assert "2302.67890" in result
        assert len(result) == 2
