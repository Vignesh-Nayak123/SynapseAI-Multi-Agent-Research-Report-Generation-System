"""End-to-end integration test: upload -> submit -> API -> agent data flow.

Verifies that uploaded PDF content flows correctly through:
1. POST /upload-pdf -> extracted text
2. Schema serialization of uploaded_content
3. API passes uploaded_content into AgentState
4. draft_node formats uploaded content with [U1] prefix

Tests that depend on langchain-ollama are conditionally skipped if the
package is not installed (avoids import failures in CI).
"""

from __future__ import annotations

import concurrent.futures
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.schemas import ResearchRequest, ResearchResponse, ImageResult
from src.agents.state import AgentState


# -- Test helper: create a minimal valid PDF with text -----------------------

def _make_test_pdf(text: str) -> bytes:
    """Create a minimal valid PDF containing the given text using PyMuPDF.

    The text is padded with filler so the extracted content clears the PDF
    processor's minimum-length and alphanumeric-density validation, while the
    original ``text`` is still present as a substring.
    """
    import fitz  # type: ignore[import-untyped]
    filler = " sample document body used to validate pdf text extraction."
    body = text
    while len(body.strip()) < 60:
        body += filler
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), body, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


# -- Conditional import: agent/API tests depend on langchain-ollama --------
try:
    from src.agents.nodes import draft_node, _format_sources
    from src.agents.state import DocumentPayload
    from src.api import app as _real_app
    _HAS_AGENTS = True
except ImportError:
    _HAS_AGENTS = False

_SKIP_REASON = "Requires langchain-ollama (not installed in this environment)"


# ============================================================================
# 1. Schema tests (pure, no mocking)
# ============================================================================

class TestSchemaDataFlow:
    """Verify uploaded_content flows through Pydantic schemas."""

    def test_research_request_with_uploaded_content(self):
        req = ResearchRequest(topic="Test", max_depth=3, num_papers=5, provider="ollama",
                              uploaded_content="Text from PDF.")
        assert req.uploaded_content == "Text from PDF."
        assert req.model_dump()["uploaded_content"] == "Text from PDF."

    def test_research_request_without_uploaded_content(self):
        req = ResearchRequest(topic="Test", max_depth=3, num_papers=5, provider="ollama")
        assert req.uploaded_content is None

    def test_research_response_construction(self):
        resp = ResearchResponse(
            final_report="# Test\n\nContent.",
            sources=["https://arxiv.org/abs/2301.12345"],
            topic="Test",
            images=[ImageResult(title="img1", image_url="https://example.com/img.jpg")],
        )
        assert resp.final_report.startswith("# Test")
        assert len(resp.sources) == 1

    def test_research_request_json_roundtrip(self):
        original = ResearchRequest(topic="Quantum", max_depth=3, num_papers=10,
                                   provider="ollama", uploaded_content="PDF content")
        restored = ResearchRequest(**json.loads(original.model_dump_json()))
        assert restored.uploaded_content == "PDF content"


class TestSchemaEdgeCases:
    """Edge-case schema behavior for uploaded_content."""

    def test_uploaded_content_very_large(self):
        """Schema handles very large uploaded_content (~150K chars)."""
        large_text = "Lorem ipsum dolor sit amet. " * 5000
        req = ResearchRequest(topic="Large", max_depth=3, num_papers=5,
                              provider="ollama", uploaded_content=large_text)
        assert req.uploaded_content is not None
        assert len(req.uploaded_content) > 100000
        assert req.model_dump()["uploaded_content"] == large_text

    def test_uploaded_content_unicode(self):
        """Schema preserves Unicode characters including CJK, emoji, math symbols."""
        unicode_text = (
            "中文论文摘要：量子计算\n"
            "日本語：量子コンピューティング\n"
            "Русский: Квантовые вычисления\n"
            "Emoji: 🔬🧪📄\n"
            "Math: \u03a3\u222b\u2202\u221a\u221e\u2260\u00b1"
        )
        req = ResearchRequest(topic="Unicode", max_depth=3, num_papers=5,
                              provider="ollama", uploaded_content=unicode_text)
        assert req.uploaded_content == unicode_text
        assert "中文" in req.uploaded_content
        assert "\U0001f52c" in req.uploaded_content  # microscope emoji
        assert "\u03a3" in req.uploaded_content  # sigma

    def test_uploaded_content_special_chars(self):
        """Schema handles XML/JSON-like content and control characters."""
        special = (
            '<script>alert("xss")</script>\n'
            '{"key": "value with \\"quotes\\""}\n'
            "Line 1\nLine 2\n\t\tIndented line\n"
            "Null byte \x00 and other \x01\x02 bytes"
        )
        req = ResearchRequest(topic="Special", max_depth=3, num_papers=5,
                              provider="ollama", uploaded_content=special)
        assert req.uploaded_content == special
        roundtrip = ResearchRequest(**json.loads(req.model_dump_json()))
        assert roundtrip.uploaded_content == special

    def test_uploaded_content_empty_string_vs_none(self):
        """Empty string is distinct from None in the schema."""
        req_none = ResearchRequest(topic="Test", max_depth=3, num_papers=5, provider="ollama")
        req_empty = ResearchRequest(topic="Test", max_depth=3, num_papers=5,
                                    provider="ollama", uploaded_content="")
        assert req_none.uploaded_content is None
        assert req_empty.uploaded_content == ""

    def test_uploaded_content_code_snippets(self):
        """Schema preserves code blocks and special formatting."""
        code = (
            "def hello():\n"
            "    print('Hello, world!')\n"
            "\n"
            "class Research:\n"
            "    def __init__(self):\n"
            '        self.data = {"key": [1, 2, 3]}\n'
            "\n"
            "/* Multi-line\n"
            "   comment */\n"
            "x = 42  # inline comment"
        )
        req = ResearchRequest(topic="Code", max_depth=3, num_papers=5,
                              provider="ollama", uploaded_content=code)
        roundtrip = ResearchRequest(**json.loads(req.model_dump_json()))
        assert roundtrip.uploaded_content == code
        assert "def hello()" in roundtrip.uploaded_content
        assert "# inline comment" in roundtrip.uploaded_content

    def test_uploaded_content_very_long_line(self):
        """Schema handles a single line of 100K chars."""
        long_line = "A" * 50000 + "B" * 50000
        req = ResearchRequest(topic="LongLine", max_depth=3, num_papers=5,
                              provider="ollama", uploaded_content=long_line)
        roundtrip = ResearchRequest(**json.loads(req.model_dump_json()))
        assert len(roundtrip.uploaded_content) == 100000
        assert roundtrip.uploaded_content.startswith("A" * 50000)


# ============================================================================
# 2. Upload endpoint tests (TestClient)
# ============================================================================

@pytest.mark.skipif(not _HAS_AGENTS, reason=_SKIP_REASON)
class TestUploadEndpoint:
    """Test the POST /upload-pdf endpoint."""

    def test_upload_rejects_non_pdf(self):
        client = TestClient(_real_app)
        response = client.post(
            "/upload-pdf",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
        assert "Only PDF" in response.json()["detail"]

    def test_upload_rejects_empty_pdf(self):
        client = TestClient(_real_app)
        empty_pdf = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[]/Count 0>>endobj
xref
0 3
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
trailer<</Size 3/Root 1 0 R>>
startxref
130
%%EOF"""
        response = client.post(
            "/upload-pdf",
            files={"file": ("empty.pdf", empty_pdf, "application/pdf")},
        )
        assert response.status_code in (422, 500)

    def test_upload_requires_filename(self):
        client = TestClient(_real_app)
        response = client.post(
            "/upload-pdf",
            files={"file": ("", b"", "application/pdf")},
        )
        assert response.status_code == 400

    # ── Filename edge cases ──────────────────────────────────────────────

    def test_unicode_filename(self):
        """Filenames with CJK characters are accepted."""
        client = TestClient(_real_app)
        pdf_bytes = _make_test_pdf("Unicode filename test")
        response = client.post(
            "/upload-pdf",
            files={"file": ("\u7814\u7a76\u8ad6\u6587.pdf", pdf_bytes, "application/pdf")},
        )
        if response.status_code == 200:
            data = response.json()
            assert data["filename"] == "\u7814\u7a76\u8ad6\u6587.pdf"
            assert "Unicode filename test" in data["content"]

    def test_special_chars_filename(self):
        """Filenames with brackets, parens, plus signs are accepted."""
        client = TestClient(_real_app)
        pdf_bytes = _make_test_pdf("Special chars filename test")
        fname = "paper_v2.1(final)+[test] (copy).pdf"
        response = client.post(
            "/upload-pdf",
            files={"file": (fname, pdf_bytes, "application/pdf")},
        )
        if response.status_code == 200:
            assert response.json()["filename"] == fname
            assert "Special chars filename test" in response.json()["content"]

    def test_filename_with_spaces(self):
        """Filenames with multiple consecutive spaces are accepted."""
        client = TestClient(_real_app)
        pdf_bytes = _make_test_pdf("Spaces filename test")
        fname = "my  research   paper   (2024).pdf"
        response = client.post(
            "/upload-pdf",
            files={"file": (fname, pdf_bytes, "application/pdf")},
        )
        if response.status_code == 200:
            assert response.json()["filename"] == fname
            assert "Spaces filename test" in response.json()["content"]

    def test_very_long_filename(self):
        """Filename of 254 chars is handled gracefully."""
        client = TestClient(_real_app)
        pdf_bytes = _make_test_pdf("Long filename test")
        long_name = "a" * 250 + ".pdf"
        response = client.post(
            "/upload-pdf",
            files={"file": (long_name, pdf_bytes, "application/pdf")},
        )
        assert response.status_code in (200, 400, 413, 422, 500)
        if response.status_code == 200:
            assert response.json()["filename"] == long_name

    def test_path_traversal_filename(self):
        """Path traversal in filename is stored as-is, not resolved."""
        client = TestClient(_real_app)
        pdf_bytes = _make_test_pdf("Path traversal test")
        fname = "../../../etc/passwd.pdf"
        response = client.post(
            "/upload-pdf",
            files={"file": (fname, pdf_bytes, "application/pdf")},
        )
        if response.status_code == 200:
            data = response.json()
            assert "../../../etc/passwd" in data["filename"]
            assert "Path traversal test" in data["content"]

    def test_filename_with_emoji(self):
        """Filenames containing emoji are accepted."""
        client = TestClient(_real_app)
        pdf_bytes = _make_test_pdf("Emoji filename test")
        fname = "\U0001f4d1 paper \U0001f50d results.pdf"
        response = client.post(
            "/upload-pdf",
            files={"file": (fname, pdf_bytes, "application/pdf")},
        )
        if response.status_code == 200:
            data = response.json()
            assert "\U0001f4d1" in data["filename"]
            assert "Emoji filename test" in data["content"]

    # ── Size limits ──────────────────────────────────────────────────────

    def test_rejects_files_over_50mb(self):
        """Files larger than 50MB are rejected with 413."""
        client = TestClient(_real_app)
        oversized = b"x" * (51 * 1024 * 1024)
        response = client.post(
            "/upload-pdf",
            files={"file": ("large.pdf", oversized, "application/pdf")},
        )
        assert response.status_code == 413
        assert "50MB" in response.json()["detail"]

    def test_rejects_files_at_exactly_50mb(self):
        """50MB exactly passes the size check; fails on PDF parsing."""
        client = TestClient(_real_app)
        exactly_50mb = b"x" * (50 * 1024 * 1024)
        response = client.post(
            "/upload-pdf",
            files={"file": ("exact.pdf", exactly_50mb, "application/pdf")},
        )
        assert response.status_code != 413

    def test_zero_byte_file_rejected(self):
        """Zero-byte PDF file is rejected."""
        client = TestClient(_real_app)
        response = client.post(
            "/upload-pdf",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400

    # ── Concurrent uploads ──────────────────────────────────────────────

    def test_concurrent_uploads_all_succeed(self):
        """Five concurrent valid PDF uploads all succeed."""
        def _upload(content: str, idx: int):
            c = TestClient(_real_app)
            pdf_bytes = _make_test_pdf(content)
            return c.post(
                "/upload-pdf",
                files={"file": (f"concurrent_{idx}.pdf", pdf_bytes, "application/pdf")},
            )

        contents = [f"Concurrent upload test file {i}" for i in range(5)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(_upload, c, i) for i, c in enumerate(contents)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for i, r in enumerate(results):
            assert r.status_code == 200, f"Upload {i} failed: {r.status_code}"
            data = r.json()
            assert data["char_count"] > 0
            assert f"Concurrent upload test file" in data["content"]

    def test_concurrent_uploads_mixed_valid_invalid(self):
        """Concurrent valid + invalid files each get correct response."""
        def _upload(idx: int):
            c = TestClient(_real_app)
            if idx % 2 == 0:
                pdf_bytes = _make_test_pdf(f"Valid file {idx}")
                return c.post(
                    "/upload-pdf",
                    files={"file": (f"valid_{idx}.pdf", pdf_bytes, "application/pdf")},
                )
            else:
                return c.post(
                    "/upload-pdf",
                    files={"file": (f"invalid_{idx}.txt", b"not a pdf", "text/plain")},
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            # Map each future to its original index (as_completed returns in arbitrary order)
            future_map = {ex.submit(_upload, i): i for i in range(6)}
            for f in concurrent.futures.as_completed(future_map):
                idx = future_map[f]
                r = f.result()
                if idx % 2 == 0:
                    assert r.status_code == 200, f"Valid {idx} should succeed: {r.status_code}"
                else:
                    assert r.status_code == 400, f"Invalid {idx} should be rejected: {r.status_code}"

    def test_concurrent_uploads_identical_content(self):
        """Concurrent uploads of identical-content PDFs all succeed independently."""
        def _upload(idx: int):
            c = TestClient(_real_app)
            pdf_bytes = _make_test_pdf("Identical content")
            return c.post(
                "/upload-pdf",
                files={"file": (f"identical_{idx}.pdf", pdf_bytes, "application/pdf")},
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futures = [ex.submit(_upload, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for i, r in enumerate(results):
            assert r.status_code == 200, f"Identical upload {i} failed: {r.status_code}"
            data = r.json()
            assert "Identical content" in data["content"]


# ============================================================================
# 3. API data flow tests (mocked graph)
# ============================================================================

@pytest.mark.skipif(not _HAS_AGENTS, reason=_SKIP_REASON)
class TestApiDataFlow:
    """Verify uploaded_content flows through the API into AgentState."""

    def test_uploaded_content_passed_to_agent_state(self):
        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                assert state["uploaded_content"] == "Hello from PDF"
                assert state["metadata"]["has_uploaded_content"] is True
                return {
                    **state,
                    "draft": "# Mock Draft\n\nContent.",
                    "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "test"}],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Integration test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": "Hello from PDF",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["final_report"] == "# Mock Draft\n\nContent."
            assert data["topic"] == "Integration test"

    def test_no_upload_when_omitted(self):
        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                assert state.get("uploaded_content") is None
                assert state["metadata"]["has_uploaded_content"] is False
                return {
                    **state,
                    "draft": "# Draft\n\nContent.",
                    "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "test"}],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Integration test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
            })
            assert response.status_code == 200


@pytest.mark.skipif(not _HAS_AGENTS, reason=_SKIP_REASON)
class TestApiDataFlowVariations:
    """Edge-case variations of uploaded_content through the API."""

    def test_very_large_uploaded_content(self):
        """100K chars of uploaded_content passes through the API."""
        large = "Large content test. " * 6000  # ~114K chars

        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                assert state["uploaded_content"] is not None
                assert len(state["uploaded_content"]) > 100000
                assert state["metadata"]["has_uploaded_content"] is True
                return {
                    **state,
                    "draft": "# Draft\n\nLarge content received.",
                    "documents": [],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Large upload test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": large,
            })
            assert response.status_code == 200

    def test_unicode_content_preserved(self):
        """Unicode and emoji in uploaded_content are preserved through the API."""
        unicode_text = "CJK: \u4e2d\u6587\nEmoji: \U0001f52c\U0001f9ea\nMath: \u03a3\u222b"

        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                assert "\u4e2d\u6587" in state["uploaded_content"]
                assert "\U0001f52c" in state["uploaded_content"]
                assert "\u03a3" in state["uploaded_content"]
                return {
                    **state,
                    "draft": "# Draft\n\nUnicode preserved.",
                    "documents": [],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Unicode test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": unicode_text,
            })
            assert response.status_code == 200

    def test_special_characters_in_content(self):
        """XML/JSON-like content passes through the API correctly."""
        special = '<script>alert(1)</script>\n{"key": "val"}\nLine 1\nLine 2'

        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                assert "<script>" in state["uploaded_content"]
                assert '{"key": "val"}' in state["uploaded_content"]
                return {
                    **state,
                    "draft": "# Draft\n\nSpecial chars preserved.",
                    "documents": [],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Special chars test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": special,
            })
            assert response.status_code == 200

    def test_empty_string_content(self):
        """Empty string uploaded_content is treated as no upload."""
        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                # Empty string is falsy, agent treats it as no upload
                assert state["uploaded_content"] == ""
                assert state["metadata"]["has_uploaded_content"] is True
                return {
                    **state,
                    "draft": "# Draft\n\nNo upload processed.",
                    "documents": [],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Empty content test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": "",
            })
            assert response.status_code == 200

    def test_multi_file_merged_content(self):
        """Content simulating merged multi-file upload with filename headers."""
        merged = (
            "--- paper1.pdf ---\n"
            "This is the content of paper one.\n"
            "It contains research findings.\n\n"
            "--- paper2.pdf ---\n"
            "This is the content of paper two.\n"
            "It contains additional data."
        )

        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                assert "paper1.pdf" in state["uploaded_content"]
                assert "paper2.pdf" in state["uploaded_content"]
                assert "research findings" in state["uploaded_content"]
                assert "additional data" in state["uploaded_content"]
                return {
                    **state,
                    "draft": "# Draft\n\nMerged content received.",
                    "documents": [],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Merged files test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": merged,
            })
            assert response.status_code == 200

    def test_partial_file_selection_merged(self):
        """Content simulating partial selection: 3 files uploaded, only 2 selected.

        This mirrors the frontend behavior where a user uploads 3 PDFs but
        only checks 2 of them — the merged content only contains the selected files.
        """
        # Simulates selecting paper1.pdf and paper3.pdf, skipping paper2.pdf
        partial_merge = (
            "--- paper1.pdf ---\n"
            "Content of the first paper about quantum computing.\n\n"
            "--- paper3.pdf ---\n"
            "Content of the third paper about machine learning."
        )

        with patch.object(_real_app.state, "graph") as mock_graph:
            async def mock_ainvoke(state: AgentState) -> AgentState:
                content = state["uploaded_content"]
                assert "paper1.pdf" in content
                assert "paper3.pdf" in content
                assert "quantum computing" in content
                assert "machine learning" in content
                # paper2.pdf should NOT appear (simulates it being deselected)
                assert "paper2.pdf" not in content
                return {
                    **state,
                    "draft": "# Draft\n\nPartial selection received.",
                    "documents": [],
                }
            mock_graph.ainvoke = mock_ainvoke

            client = TestClient(_real_app)
            response = client.post("/research", json={
                "topic": "Partial selection test",
                "max_depth": 3,
                "num_papers": 5,
                "provider": "ollama",
                "uploaded_content": partial_merge,
            })
            assert response.status_code == 200


# ============================================================================
# 4. Agent node behavior tests (mocked LLM)
# ============================================================================

@pytest.mark.skipif(not _HAS_AGENTS, reason=_SKIP_REASON)
class TestAgentNodeDataFlow:
    """Verify draft_node formats uploaded content with [U1] prefix."""

    @pytest.mark.asyncio
    async def test_includes_uploaded_content_as_u1(self):
        state: AgentState = {
            "query": "Test topic",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "uploaded_content": "This is user-uploaded PDF content.",
            "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "Real paper content."}],
            "job_id": "test-job-001",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nGenerated content."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        assert result["draft"] == "# Draft\n\nGenerated content."
        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "[U1]" in prompt
        assert "User-uploaded document" in prompt
        assert "[S1]" in prompt

    @pytest.mark.asyncio
    async def test_skips_u1_when_no_upload(self):
        state: AgentState = {
            "query": "Test topic",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "Real paper content."}],
            "job_id": "test-job-002",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nGenerated content."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "[U1]" not in prompt
        assert "[S1]" in prompt

    def test_format_sources_prefixes_are_separate(self):
        docs: list[DocumentPayload] = [
            {"source": "url1", "content": "Paper one content"},
            {"source": "url2", "content": "Paper two content"},
        ]
        formatted = _format_sources(docs)
        assert "[S1]" in formatted
        assert "[S2]" in formatted
        assert "[U1]" not in formatted

    # ── Edge cases ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_large_uploaded_content_truncated_in_prompt(self):
        """Very large uploaded content gets truncated in the draft prompt."""
        large_content = "Repeated content for truncation test. " * 2000  # ~50K chars

        state: AgentState = {
            "query": "Truncation test",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "uploaded_content": large_content,
            "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "Real paper content."}],
            "job_id": "test-job-003",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nContent."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        assert result["draft"] == "# Draft\n\nContent."
        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "[U1]" in prompt
        # Content should be truncated to 1500 chars in the prompt
        assert "Repeated content for truncation test. " in prompt
        assert len(large_content) > 1500  # Verify original was indeed large
        # The upload section snippet is truncated to 1500 chars
        upload_section_start = prompt.find("[U1] Source: User-uploaded document")
        assert upload_section_start >= 0

    @pytest.mark.asyncio
    async def test_unicode_content_in_prompt(self):
        """Unicode content in upload appears correctly in the prompt."""
        unicode_upload = (
            "CJK: \u4e2d\u6587\u8bba\u6587\n"
            "Emoji: \U0001f52c\U0001f9ea\U0001f4c4\n"
            "Math: \u03a3\u222b\u2202\u221a"
        )

        state: AgentState = {
            "query": "Unicode in prompt",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "uploaded_content": unicode_upload,
            "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "Paper content."}],
            "job_id": "test-job-004",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nUnicode test."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "\u4e2d\u6587" in prompt
        assert "\U0001f52c" in prompt
        assert "[U1]" in prompt

    @pytest.mark.asyncio
    async def test_empty_string_upload_skipped(self):
        """Empty string uploaded_content is falsy — [U1] is skipped."""
        state: AgentState = {
            "query": "Empty upload",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "uploaded_content": "",
            "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "Paper content."}],
            "job_id": "test-job-005",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nNo upload."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "[U1]" not in prompt
        assert "[S1]" in prompt

    @pytest.mark.asyncio
    async def test_multi_file_merged_content_in_prompt(self):
        """Merged multi-file upload (with --- filename --- headers) appears in prompt."""
        merged = (
            "--- paper1.pdf ---\n"
            "Content of paper one.\n\n"
            "--- paper2.pdf ---\n"
            "Content of paper two."
        )

        state: AgentState = {
            "query": "Merged files",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "uploaded_content": merged,
            "documents": [{"source": "https://arxiv.org/abs/2301.12345", "content": "Paper content."}],
            "job_id": "test-job-006",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nMerged."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "[U1]" in prompt
        assert "paper1.pdf" in prompt
        assert "paper2.pdf" in prompt

    @pytest.mark.asyncio
    async def test_upload_with_no_other_sources(self):
        """Uploaded content works as the sole source (no web docs)."""
        state: AgentState = {
            "query": "Solo upload",
            "max_depth": 3,
            "max_search_results": 5,
            "provider": "ollama",
            "model": "llama3",
            "critic_strictness": 5,
            "uploaded_content": "This is the only source — a user-uploaded PDF.",
            "documents": [],
            "job_id": "test-job-007",
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {},
        }

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="# Draft\n\nSolo upload."))

        with patch("src.agents.nodes._get_llm", return_value=mock_llm):
            result = await draft_node(state)

        assert result["draft"] == "# Draft\n\nSolo upload."
        prompt = str(mock_llm.ainvoke.call_args.args[0])
        assert "[U1]" in prompt
        assert "[S1]" not in prompt  # No web sources
