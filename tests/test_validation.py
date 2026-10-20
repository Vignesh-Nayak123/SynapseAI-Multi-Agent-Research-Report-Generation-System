import pytest
from src.tools.validation import validate_citations, check_factual_consistency, detect_hallucinations
from src.agents.state import DocumentPayload

def test_validate_citations():
    documents = [
        {"source": "url1", "content": "content1"},
        {"source": "url2", "content": "content2"}
    ]
    
    # Valid citations
    draft_valid = "This is a claim [S1]. This is another [S2]."
    assert validate_citations(draft_valid, documents) == []
    
    # Invalid citation
    draft_invalid = "This is a claim [S3]."
    assert validate_citations(draft_invalid, documents) == ["[S3]"]
    
    # Mixed
    draft_mixed = "Valid [S1], invalid [S5]."
    assert validate_citations(draft_mixed, documents) == ["[S5]"]

def test_check_factual_consistency():
    documents = [
        {"source": "url1", "content": "The revenue was 50% higher."}
    ]
    
    # Verified claim
    draft_verified = "Revenue increased by 50%."
    assert check_factual_consistency(draft_verified, documents) == []
    
    # Unverified claim
    draft_unverified = "Revenue increased by 60%."
    result = check_factual_consistency(draft_unverified, documents)
    assert len(result) == 1 and result[0].startswith("60%")

    # Number present but claim context unsupported ("2024" anywhere must not verify)
    docs = [
        {"source": "s1", "content": "Founded in 2024, the lab studies marine biology."},
    ]
    draft_mismatch = "Revenue reached 2024 dollars in Q3."
    mismatch = check_factual_consistency(draft_mismatch, docs)
    assert len(mismatch) == 1 and mismatch[0].startswith("2024")


@pytest.mark.asyncio
async def test_detect_hallucinations_parses_json():
    class _Msg:
        def __init__(self, content):
            self.content = content

    class _LLM:
        def __init__(self, content):
            self._content = content

        async def ainvoke(self, messages):
            return _Msg(self._content)

    docs = [{"source": "s1", "content": "Paris is the capital of France."}]
    good = await detect_hallucinations(
        "Paris is the capital of France.", docs, _LLM('{"hallucinations": [], "score": 0.0}')
    )
    assert good == {"hallucinations": [], "score": 0.0}

    bad = await detect_hallucinations("Anything.", docs, _LLM("not json at all"))
    assert bad["parse_error"] is True
    assert "raw_response" in bad
