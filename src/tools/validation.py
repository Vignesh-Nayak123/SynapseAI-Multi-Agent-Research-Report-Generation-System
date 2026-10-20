import json
import re
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.state import DocumentPayload

def validate_citations(draft: str, documents: List[DocumentPayload]) -> List[str]:
    """
    Verify that all citations in the draft (e.g. [S1], [S2]) exist in the provided documents.
    Returns a list of invalid citation markers.
    """
    # Extract all citation markers like [S1], [S12], etc.
    citations = re.findall(r"\[S(\d+)\]", draft)
    
    # Get valid indices from documents (assuming 1-based indexing in draft)
    # In draft_node, we format sources starting from 1.
    # But documents list is 0-indexed.
    # We need to know how many documents were passed to the draft.
    # The draft prompt uses [S1], [S2]... corresponding to documents[0], documents[1]...
    
    valid_indices = set(range(1, len(documents) + 1))
    
    invalid_citations = []
    for citation in citations:
        idx = int(citation)
        if idx not in valid_indices:
            invalid_citations.append(f"[S{idx}]")
            
    return sorted(list(set(invalid_citations)))

async def detect_hallucinations(draft: str, documents: List[DocumentPayload], llm: Any) -> Dict[str, Any]:
    """
    Use LLM to check for hallucinations.
    """
    # We'll use a simplified version of the critique prompt here, focused solely on hallucination.
    # Or we can rely on the existing critique_node which already does this.
    # But the user asked for a "hallucination detector" module.
    
    context = _format_sources(documents)
    
    prompt = (
        "You are a Hallucination Detector. Check the following draft against the Evidence Bank.\n"
        "Identify any claims in the draft that are NOT supported by the Evidence Bank.\n"
        "Respond in JSON: {\"hallucinations\": [\"claim 1\", \"claim 2\"], \"score\": 0.0 to 1.0}\n"
        "Score 0.0 means no hallucinations, 1.0 means pure hallucination.\n\n"
        f"Evidence Bank:\n{context}\n\nDraft:\n{draft}"
    )
    
    response = await llm.ainvoke([SystemMessage(content="You are a strict fact-checker."), HumanMessage(content=prompt)])
    
    # Parse the JSON response. Returns structured hallucinations/score on
    # success, or an explicit error payload (never a bare raw string that
    # callers mistake for a clean bill of health).
    content = getattr(response, "content", str(response))
    parsed = _parse_hallucination_json(content)
    if parsed is not None:
        return parsed
    return {
        "hallucinations": [],
        "score": 0.0,
        "parse_error": True,
        "raw_response": content[:2000],
    }


def _parse_hallucination_json(content: str) -> Dict[str, Any] | None:
    """Parse the hallucination-detector JSON reply; None if unparseable."""
    text = content.strip()
    candidates = [text]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidates.append(match.group())
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(parsed, dict) and "hallucinations" in parsed:
            try:
                return {
                    "hallucinations": [str(h) for h in parsed.get("hallucinations", [])],
                    "score": float(parsed.get("score", 0.0)),
                }
            except (TypeError, ValueError):
                continue
    return None

def check_factual_consistency(draft: str, documents: List[DocumentPayload]) -> List[str]:
    """
    Extract numerical claims from draft and verify each appears with matching
    nearby context in the documents. Returns a list of unverified claims.

    A bare substring test ("2024" appears *anywhere* in the sources) passes
    claims whose number is real but whose statement is not. Each candidate
    number must therefore appear within a window sharing at least one
    significant (>3 chars) draft token with the claim sentence.
    """
    # Flatten document content
    full_text = " ".join([doc["content"] for doc in documents])
    full_lower = full_text.lower()

    unverified = []
    for sentence in re.split(r"(?<=[.!?])\s+", draft):
        sent_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?', sentence))
        if not sent_numbers:
            continue
        tokens = {t.lower() for t in re.findall(r"[A-Za-z]{4,}", sentence)}
        for num in sent_numbers:
            if num.lower() not in full_lower or not _number_has_context(num, tokens, full_text):
                unverified.append(num + " (in: " + sentence[:80] + ")")

    return sorted(set(unverified))


def _number_has_context(num: str, tokens: set, full_text: str, window: int = 40) -> bool:
    """Check whether any occurrence of num has a shared token nearby."""
    pattern = re.compile(re.escape(num), re.IGNORECASE)
    for match in pattern.finditer(full_text):
        start = max(0, match.start() - window)
        end = min(len(full_text), match.end() + window)
        neighbourhood = full_text[start:end].lower()
        if any(token in neighbourhood for token in tokens):
            return True
    return False


def _format_sources(documents: List[DocumentPayload]) -> str:
    formatted = []
    for idx, doc in enumerate(documents, start=1):
        snippet = doc["content"][:1000]
        formatted.append(f"[S{idx}] Source: {doc['source']}\nSnippet: {snippet}")
    return "\n\n".join(formatted)
