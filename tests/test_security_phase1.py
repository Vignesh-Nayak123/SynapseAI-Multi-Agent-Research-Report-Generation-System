"""Tests for Phase 1 security fixes: cache key hygiene, SSRF guards, HTML escaping."""

import base64
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.nodes import _get_cached_llm_config, _get_llm
from src.tools.pdf import (
    MAX_PDF_BYTES,
    _check_content_type,
    _validate_url,
    close_shared_session,
)
from src.utils.crypto import decrypt_trace_data, encrypt_trace_data


def test_llm_cache_key_excludes_api_key():
    info_before = _get_cached_llm_config.cache_info()
    _get_cached_llm_config(provider="ollama", model="m1")
    # api_key must not be an accepted cache-key parameter.
    with pytest.raises(TypeError):
        _get_cached_llm_config(provider="ollama", model="m1", api_key="sk-secret")  # type: ignore[call-arg]


def test_get_llm_does_not_cache_secrets(monkeypatch):
    from src.agents import nodes as nodes_mod
    from src.config import get_settings

    monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
    # get_settings() is an lru_cache singleton: clear it so the patched env is visible.
    get_settings.cache_clear()
    llm = _get_llm(provider="openai", model="gpt-4o")
    try:
        cached_keys = str(nodes_mod._get_cached_llm_config.cache_info())
        assert "sk-env-key" not in cached_keys
        params = nodes_mod._get_cached_llm_config.cache_parameters() if hasattr(
            nodes_mod._get_cached_llm_config, "cache_parameters"
        ) else None
        assert params is None or "api_key" not in str(params)
    finally:
        _get_cached_llm_config.cache_clear()
    assert llm is not None
    assert llm.openai_api_key.get_secret_value() == "sk-env-key"


def test_get_llm_binds_call_specific_key_not_cached_one(monkeypatch):
    """Two calls with the same config but different keys must not share a client."""
    from src.config import get_settings

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        first = _get_llm(provider="openai", model="gpt-4o", api_key="sk-first")
        second = _get_llm(provider="openai", model="gpt-4o", api_key="sk-second")
        assert first.openai_api_key.get_secret_value() == "sk-first"
        assert second.openai_api_key.get_secret_value() == "sk-second"
        assert first is not second
    finally:
        _get_cached_llm_config.cache_clear()
        get_settings.cache_clear()


def test_validate_url_rejects_non_http():
    with pytest.raises(ValueError):
        _validate_url("file:///etc/passwd")
    with pytest.raises(ValueError):
        _validate_url("ftp://example.com/x.pdf")


def test_validate_url_blocks_private_and_metadata():
    with pytest.raises(ValueError):
        _validate_url("http://169.254.169.254/latest/meta-data/")
    with pytest.raises(ValueError):
        _validate_url("http://127.0.0.1/x.pdf")


def test_check_content_type_rejects_html():
    with pytest.raises(ValueError):
        _check_content_type("text/html", "http://example.com/x.pdf")
    _check_content_type("application/pdf", "http://example.com/x.pdf")


def test_max_pdf_bytes_cap():
    assert MAX_PDF_BYTES == 15 * 1024 * 1024


def test_process_batch_filters_exceptions():
    import asyncio

    from src.tools.pdf import PDFProcessor

    async def _boom(_url: str):
        raise RuntimeError("boom")

    async def _run():
        processor = PDFProcessor(max_concurrency=1)
        with patch.object(processor, "process_url", side_effect=_boom):
            results = await processor.process_batch(["http://example.com/a.pdf"])
        assert results == [None]
        for item in results:
            assert not isinstance(item, Exception)

    asyncio.run(_run())
    asyncio.run(close_shared_session())


def test_encrypt_trace_data_reuses_session_salt():
    salt = base64.b64decode("AAAAAAAAAAAAAAAAAAAAAA==")
    enc1, salt1 = encrypt_trace_data("hello", "passphrase", salt=salt)
    enc2, salt2 = encrypt_trace_data("hello", "passphrase", salt=salt)
    assert salt1 == salt2 == "AAAAAAAAAAAAAAAAAAAAAA=="
    assert decrypt_trace_data(enc1, salt1, "passphrase") == "hello"
    assert decrypt_trace_data(enc2, salt2, "passphrase") == "hello"


def test_sanitize_html_body_strips_script():
    from src.api import _sanitize_html_body

    cleaned = _sanitize_html_body('<p>hi</p><script>alert(1)</script>')
    assert "<script" not in cleaned
    assert "hi" in cleaned
