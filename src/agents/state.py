from __future__ import annotations

from typing import List, TypedDict


class DocumentPayload(TypedDict):
    source: str
    content: str


class CritiquePayload(TypedDict, total=False):
    score: float
    hallucination_score: float
    is_vague: bool
    feedback: str
    needs_revision: bool


class ResearchMetadata(TypedDict, total=False):
    job_id: str
    start_time: str
    end_time: str
    model: str
    provider: str
    total_tokens: int
    retrieval_stats: dict
    pdf_stats: dict
    critique_cycles: int
    draft_length: int


class AgentState(TypedDict, total=False):
    query: str
    max_depth: int
    max_search_results: int
    provider: str
    openrouter_api_key: str | None
    model: str | None
    critic_strictness: int
    uploaded_content: str | None
    documents: List[DocumentPayload]
    draft: str
    critique: CritiquePayload
    revision_count: int
    
    # New fields
    job_id: str
    metadata: ResearchMetadata
    seed: int
    temperature: float
    top_p: float

    # Zero-knowledge encryption fields (never persisted to disk, in-memory only)
    encryption_passphrase: str | None
    encryption_salt: str | None

