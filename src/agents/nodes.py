from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, List

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama  # type: ignore
from langchain_openai import ChatOpenAI

from src.agents.state import AgentState, CritiquePayload, DocumentPayload
from src.config import get_settings
from src.tools.pdf import parse_pdf, PDFProcessor
from src.tools.search import search_papers
from src.tools.ranking import rank_documents, chunk_text
from src.tools.validation import validate_citations, check_factual_consistency
from src.utils.crypto import decrypt_api_key
from src.utils.tracing import TraceLogger

logger = structlog.get_logger(__name__)


# Provider configuration: mapping of provider names to their OpenAI-compatible base URLs
# and config field prefixes for defaults
PROVIDER_CONFIG: dict[str, dict[str, str]] = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "config_prefix": "openrouter",
        "default_model": "openai/gpt-3.5-turbo",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "config_prefix": "openai",
        "default_model": "gpt-4o",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "config_prefix": "anthropic",
        "default_model": "claude-sonnet-4-20250514",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "config_prefix": "google",
        "default_model": "gemini-2.0-flash",
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "config_prefix": "perplexity",
        "default_model": "sonar-pro",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "config_prefix": "groq",
        "default_model": "mixtral-8x7b-32768",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "config_prefix": "together",
        "default_model": "mistralai/Mixtral-8x22B-Instruct-v0.1",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "config_prefix": "deepseek",
        "default_model": "deepseek-chat",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "config_prefix": "mistral",
        "default_model": "mistral-large-latest",
    },
}


@lru_cache(maxsize=2)
def _get_cached_llm_config(
    provider: str = "ollama",
    model: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.2,
    seed: int | None = None,
    top_p: float | None = None
) -> Any:
    """Resolve non-secret LLM config (cached); api_key is never cached."""
    settings = get_settings()

    # Ollama uses LangChain's ChatOllama directly
    if provider == "ollama":
        resolved_model = model or settings.ollama_model
        resolved_base = base_url or settings.ollama_base_url
        return {
            "client": "ollama",
            "model": resolved_model,
            "base_url": resolved_base,
            "temperature": temperature,
            "top_p": top_p,
            "seed": seed,
        }

    # For all other providers, use OpenAI-compatible ChatOpenAI
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unknown provider: {provider}")

    prefix = config["config_prefix"]
    resolved_model = model or getattr(
        settings, f"{prefix}_model", None) or config["default_model"]
    resolved_base = base_url or config["base_url"]

    model_kwargs = {}
    if seed is not None:
        model_kwargs["seed"] = seed
    if top_p is not None:
        model_kwargs["top_p"] = top_p

    extra_headers = {}
    if provider == "openrouter":
        extra_headers["HTTP-Referer"] = "http://localhost:5173"
        extra_headers["X-Title"] = "Multi-Agent Research System"

    return {
        "client": "openai",
        "model": resolved_model,
        "base_url": resolved_base,
        "temperature": temperature,
        "model_kwargs": model_kwargs or None,
        "extra_headers": extra_headers or None,
    }


def _get_llm(
    provider: str = "ollama",
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.2,
    seed: int | None = None,
    top_p: float | None = None,
) -> Any:
    """Build an LLM client that is never cached with its ``api_key``.

    ``api_key`` is bound directly to the returned client and the local
    reference is dropped before returning (best-effort; the client keeps
    its own copy).
    """
    try:
        resolved = _get_cached_llm_config(
            provider=provider,
            model=model,
            base_url=base_url,
            temperature=temperature,
            seed=seed,
            top_p=top_p,
        )
        if resolved["client"] == "ollama":
            return ChatOllama(
                model=resolved["model"],
                base_url=resolved["base_url"],
                temperature=resolved["temperature"],
                top_p=resolved["top_p"],
                seed=resolved["seed"],
            )
        settings = get_settings()
        prefix = PROVIDER_CONFIG[provider]["config_prefix"]
        resolved_key = api_key or getattr(settings, f"{prefix}_api_key", None)
        if not resolved_key:
            raise ValueError(
                f"API key is required for {provider}. "
                f"Set {prefix.upper()}_API_KEY or pass it in the request."
            )
        client_kwargs: dict[str, Any] = {
            "model": resolved["model"],
            "api_key": resolved_key,
            "base_url": resolved["base_url"],
            "temperature": resolved["temperature"],
        }
        # Only pass optional kwargs when set: langchain-core >=1 rejects
        # ``model_kwargs=None`` / ``default_headers=None``.
        if resolved["model_kwargs"]:
            client_kwargs["model_kwargs"] = resolved["model_kwargs"]
        if resolved["extra_headers"]:
            client_kwargs["default_headers"] = resolved["extra_headers"]
        return ChatOpenAI(**client_kwargs)
    finally:
        del api_key


async def research_node(state: AgentState) -> AgentState:
    query = state.get("query", "")
    limit = state.get("max_search_results") or 10
    job_id = state.get("job_id", "unknown")

    metadata = state.get("metadata") or {
        "job_id": job_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "model": state.get("model", "unknown"),
        "provider": state.get("provider", "unknown"),
        "retrieval_stats": {},
        "pdf_stats": {},
    }

    print(
        f"\n--- [1/3] Researching Topic: {query} "
        f"(Target: {limit} papers) ---"
    )
    logger.info("node.research.start", query=query, limit=limit)

    # Step 1: Search for source URLs.
    search_start = time.time()

    try:
        urls = search_papers(query, limit=limit)
    except Exception as exc:
        logger.exception(
            "node.research.search_failed",
            query=query,
            error=str(exc),
        )
        raise ValueError(
            "Research search failed. Check your search API configuration "
            "and backend logs, then try again."
        ) from exc

    metadata["retrieval_stats"] = {
        "found_urls": len(urls),
        "search_duration": time.time() - search_start,
    }

    if not urls:
        raise ValueError(
            f"No sources were found for '{query}'. "
            "Try a more specific research topic."
        )

    print(f"Found {len(urls)} potential sources. Parsing documents...")

    # Step 2: Download and parse the sources.
    pdf_start_time = time.time()
    processor = PDFProcessor(max_concurrency=5)

    try:
        contents = await processor.process_batch(urls)
    except Exception as exc:
        logger.exception(
            "node.research.processing_failed",
            query=query,
            error=str(exc),
        )
        raise ValueError(
            "Source processing failed. Please try again."
        ) from exc

    raw_documents: List[DocumentPayload] = []
    failed_count = 0
    settings = get_settings()

    for url, content in zip(urls, contents):
        if isinstance(content, Exception) or content is None:
            failed_count += 1
            logger.warning(
                "node.research.source_failed",
                url=url,
                error=str(content) if isinstance(
                    content, Exception) else "No content",
            )
            continue

        trimmed = content[:settings.max_context_chars].strip()

        if not trimmed:
            failed_count += 1
            logger.warning("node.research.source_empty", url=url)
            continue

        chunks = chunk_text(
            trimmed,
            chunk_size=2000,
            overlap=200,
        )

        for index, chunk in enumerate(chunks, start=1):
            if chunk and chunk.strip():
                raw_documents.append({
                    "source": f"{url} (part {index})",
                    "content": chunk,
                })

    print(f"Ranking {len(raw_documents)} chunks...")

    # Record retrieval statistics, even when no sources are usable.
    metadata["pdf_stats"] = {
        "attempted": len(urls),
        "successful": max(0, len(urls) - failed_count),
        "failed": failed_count,
        "total_chunks": len(raw_documents),
        "selected_chunks": 0,
        "parse_duration": time.time() - pdf_start_time,
    }

    # Never generate an evidence-based review without source material.
    if not raw_documents:
        if job_id != "unknown":
            TraceLogger(job_id).save_metadata(metadata)

        logger.error(
            "node.research.no_usable_documents",
            query=query,
            attempted=len(urls),
            failed=failed_count,
        )

        raise ValueError(
            "No accessible source documents could be read for this topic. "
            "Some publishers block automated downloads. Try another topic "
            "or provide an accessible PDF."
        )

    # Step 3: Rank the retrieved text chunks.
    try:
        ranked_documents = rank_documents(
            query,
            raw_documents,
            top_k=limit,
        )
    except Exception as exc:
        logger.exception(
            "node.research.ranking_failed",
            query=query,
            error=str(exc),
        )
        raise ValueError(
            "Source ranking failed. Check the backend logs and try again."
        ) from exc

    if not ranked_documents:
        if job_id != "unknown":
            TraceLogger(job_id).save_metadata(metadata)

        logger.error(
            "node.research.no_ranked_documents",
            query=query,
            raw_chunks=len(raw_documents),
        )

        raise ValueError(
            "Sources were retrieved, but no relevant text chunks were "
            "selected. Try a broader or more specific topic."
        )

    metadata["pdf_stats"].update({
        "selected_chunks": len(ranked_documents),
        "parse_duration": time.time() - pdf_start_time,
    })

    print(f"Selected top {len(ranked_documents)} chunks.")

    logger.info(
        "node.research.complete",
        documents=len(ranked_documents),
    )

    # Save metadata and return the selected documents to the graph.
    if job_id != "unknown":
        TraceLogger(job_id).save_metadata(metadata)

    return {
        **state,
        "documents": ranked_documents,
        "revision_count": 0,
        "metadata": metadata,
    }


def _safe_parse_pdf(url: str) -> DocumentPayload | None:
    # Deprecated in favor of PDFProcessor
    try:
        content = parse_pdf(url)
    except Exception as exc:  # pragma: no cover - network failure path
        logger.warning("pdf.parse.failed", url=url, error=str(exc))
        return None

    settings = get_settings()
    trimmed = content[: settings.max_context_chars]
    if not trimmed:
        return None
    return {"source": url, "content": trimmed}


async def draft_node(state: AgentState) -> AgentState:
    revisions = state.get("revision_count", 0)
    print(f"\n--- [2/3] Drafting Review (Revision {revisions}) ---")
    logger.info("node.draft.start", revisions=revisions)

    documents = state.get("documents") or []
    uploaded_content = state.get("uploaded_content")

    logger.info(
        "node.draft.input_check",
        documents_type=type(documents).__name__,
        documents_count=len(documents) if isinstance(
            documents, (list, tuple, str)) else -1,
        uploaded_content_present=bool(uploaded_content),
        state_keys=list(state.keys()),
    )

    if not documents and not uploaded_content:
        raise ValueError(
            "Draft node received no documents. "
            f"Available state keys: {list(state.keys())}"
        )

    settings = get_settings()
    provider = state.get("provider", "ollama")
    api_key = state.get("openrouter_api_key")
    model = state.get("model")
    job_id = state.get("job_id", "unknown")

    # Deterministic settings
    seed = state.get("seed", settings.default_seed)
    temperature = state.get("temperature", settings.default_temperature)
    top_p = state.get("top_p", settings.default_top_p)

    # Zero-knowledge: decrypt API key from encrypted fields if provided
    encryption_passphrase = state.get("encryption_passphrase")
    encrypted_api_key = state.get("encrypted_api_key")
    encryption_iv = state.get("encryption_iv")
    encryption_salt = state.get("encryption_salt")

    resolved_api_key: str | None = api_key
    if encryption_passphrase and encrypted_api_key and encryption_iv and encryption_salt:
        try:
            resolved_api_key = decrypt_api_key(
                encrypted_api_key, encryption_iv, encryption_salt, encryption_passphrase
            )
            logger.debug("api_key.decrypted", provider=provider)
        except ValueError as exc:
            raise ValueError(
                f"Failed to decrypt API key for {provider}: {exc}") from exc

    # Minimize passphrase memory exposure — drop references now that decryption is done
    encryption_passphrase = None
    state.pop("encryption_passphrase", None)
    state.pop("encryption_salt", None)

    llm = _get_llm(
        provider=provider,
        model=model,
        api_key=resolved_api_key,
        seed=seed,
        temperature=temperature,
        top_p=top_p,
    )
    # Drop local references to the decrypted key (best-effort, matching the
    # passphrase handling above; the client built above holds its own copy).
    resolved_api_key = None
    api_key = None

    # Include user-uploaded content as additional context with distinct [U1] prefix
    uploaded_content = state.get("uploaded_content")
    upload_section = ""
    if uploaded_content:
        snippet = uploaded_content[:1500]
        upload_section = f"[U1] Source: User-uploaded document\nContent: {snippet}\n\n"
    context_sections = upload_section + _format_sources(documents)
    critique_feedback = (state.get("critique") or {}).get("feedback")
    current_draft = state.get("draft")

    if revisions > 0 and current_draft:
        print("Refining draft based on feedback...")
        prompt = _build_revision_prompt(
            state.get("query", ""), current_draft, critique_feedback, context_sections)
    else:
        prompt = _build_draft_prompt(state.get("query", ""), state.get(
            "max_depth", 3), context_sections, critique_feedback)

    print("Generating draft with LLM...")
    start_time = time.time()
    response = await llm.ainvoke([SystemMessage(content="You are the Analyst agent who writes structured literature reviews."), HumanMessage(content=prompt)])
    duration = time.time() - start_time

    draft_text = _coerce_content(response)

    # Log trace (with encryption at rest if passphrase is available)
    if job_id != "unknown":
        tracer = TraceLogger(
            job_id,
            encryption_passphrase=encryption_passphrase,
            encryption_salt=encryption_salt,
        )
        tracer.log_llm_call(
            step=f"draft_revision_{revisions}",
            prompt=prompt,
            response=draft_text,
            model=model or "default",
            duration=duration
        )

        # Update metadata
        metadata = state.get("metadata", {})
        metadata["draft_length"] = len(draft_text)
        tracer.save_metadata(metadata)

    print("Draft generation complete.")
    logger.info("node.draft.complete", char_count=len(draft_text))
    return {**state, "draft": draft_text}


def _format_sources(documents: List[DocumentPayload]) -> str:
    formatted = []
    for idx, doc in enumerate(documents, start=1):
        snippet = doc["content"][:1500]
        formatted.append(
            f"[S{idx}] Source: {doc['source']}\nSnippet: {snippet}")
    return "\n\n".join(formatted)


def _build_draft_prompt(topic: str, depth: int, context_sections: str, feedback: str | None) -> str:
    feedback_section = feedback or "None"
    target_length = 1500 + depth * 300
    return (
        f"Topic: {topic}\n"
        f"Depth Target: {depth}\n"
        f"Prior Critique: {feedback_section}\n"
        "You are an elite academic researcher. Write a COMPREHENSIVE, IN-DEPTH academic literature review in Markdown.\n"
        "Rules:\n"
        "1. NO FLUFF. Do not use phrases like 'The paper discusses' or 'It is important to note'. State facts directly.\n"
        "2. Prioritize quantitative data (numbers, percentages, dates) over general statements.\n"
        "3. Use bullet points for 'Key Findings' to maximize readability.\n"
        "4. WRITE AT LENGTH. Each section must be detailed and exhaustive. Do not summarize briefly.\n"
        "5. CITATIONS ARE MANDATORY. Every claim must be backed by a source [S#].\n"
        "6. SYNTHESIZE. Do not just list papers. Connect findings across sources.\n"
        "7. NO REFERENCES SECTION. Do not include a References or Bibliography section at the end of the report.\n\n"
        "Structure:\n"
        "# Title\n\n"
        "## Executive Summary\n"
        "(300+ words synthesizing the core narrative and high-level conclusions)\n\n"
        "## Key Findings\n"
        "(Detailed bullet points with inline citations [S#]. Group by themes (e.g., 'Theme 1: ...'). Aim for 800+ words.)\n\n"
        "## Critical Analysis\n"
        "(Evaluate the strength of the evidence, conflicting results, and limitations of the current body of work. 300+ words.)\n\n"
        "## Methodological Notes\n"
        "(Analyze the methods used in the sources: qualitative/quantitative/review. 300+ words.)\n\n"
        "## Implications & Open Questions\n"
        "(Discuss future research directions and practical applications. 300+ words.)\n\n"
        f"Target Length: ~{target_length} words.\n\n"
        f"Evidence Bank:\n{context_sections}"
    )


def _build_revision_prompt(topic: str, current_draft: str, feedback: str, context_sections: str) -> str:
    return (
        f"Topic: {topic}\n"
        "You are an elite academic researcher. You have written a draft that has been critiqued.\n"
        "Your task is to REVISE the draft based on the feedback provided.\n"
        "Do not rewrite the entire draft from scratch if not necessary. Focus on fixing the issues mentioned in the feedback.\n"
        "Ensure all citations [S#] are correct and exist in the Evidence Bank.\n"
        "7. NO REFERENCES SECTION. Do not include a References or Bibliography section at the end of the report.\n\n"
        f"Critique Feedback:\n{feedback}\n\n"
        f"Current Draft:\n{current_draft}\n\n"
        f"Evidence Bank:\n{context_sections}\n\n"
        "Output the FULL revised draft in Markdown."
    )


async def critique_node(state: AgentState) -> AgentState:
    print("\n--- [3/3] Critiquing Draft ---")
    logger.info("node.critique.start")
    draft = state.get("draft", "")
    documents = state.get("documents", [])
    if not draft:
        raise ValueError("Critique node requires an existing draft")

    settings = get_settings()
    provider = state.get("provider", "ollama")
    api_key = state.get("openrouter_api_key")
    model = state.get("model")
    job_id = state.get("job_id", "unknown")

    # Deterministic settings
    seed = state.get("seed", settings.default_seed)
    temperature = state.get("temperature", settings.default_temperature)
    top_p = state.get("top_p", settings.default_top_p)

    # Zero-knowledge: decrypt API key from encrypted fields if provided
    encryption_passphrase = state.get("encryption_passphrase")
    encrypted_api_key = state.get("encrypted_api_key")
    encryption_iv = state.get("encryption_iv")
    encryption_salt = state.get("encryption_salt")

    resolved_api_key: str | None = api_key
    if encryption_passphrase and encrypted_api_key and encryption_iv and encryption_salt:
        try:
            resolved_api_key = decrypt_api_key(
                encrypted_api_key, encryption_iv, encryption_salt, encryption_passphrase
            )
            logger.debug("api_key.decrypted", provider=provider)
        except ValueError as exc:
            raise ValueError(
                f"Failed to decrypt API key for {provider}: {exc}") from exc

    llm = _get_llm(
        provider=provider,
        model=model,
        api_key=resolved_api_key,
        seed=seed,
        temperature=temperature,
        top_p=top_p,
    )
    resolved_api_key = None
    api_key = None
    context = _format_sources(documents)

    # Run validation tools
    invalid_citations = validate_citations(draft, documents)
    unverified_numbers = check_factual_consistency(draft, documents)

    validation_feedback = ""
    if invalid_citations:
        validation_feedback += f"\nCRITICAL: The following citations are invalid (do not exist in sources): {', '.join(invalid_citations)}."
    if unverified_numbers:
        validation_feedback += f"\nWARNING: The following numerical claims could not be verified in the source text: {', '.join(unverified_numbers[:10])}..."

    strictness = state.get("critic_strictness", 5)
    # Calculate passing threshold: 1->5.0, 5->7.0, 10->9.5
    threshold = 4.5 + (strictness * 0.5)

    strictness_instruction = "Be balanced. Ensure accuracy and good citation usage."
    if strictness <= 3:
        strictness_instruction = "Be lenient. Focus only on major factual errors. Accept general statements if they seem reasonable."
    elif strictness >= 8:
        strictness_instruction = "Be extremely strict. Nitpick every detail, require high citation density, and penalize any vague language severely."

    critique_prompt = (
        f"You are the Critic agent. Strictness Level: {strictness}/10. {strictness_instruction} "
        "Score the draft from 1-10 for accuracy and rigor. "
        "Estimate hallucination probability between 0 and 1 based on mismatches with the evidence bank. "
        "Check if the draft contains specific quantitative data or just vague generalizations. "
        "Verify that citations [S#] are used correctly and exist in the evidence bank. "
        f"{validation_feedback}\n"
        "Respond ONLY in JSON like "
        '{"score": 8.5, "hallucination": 0.2, "vague": false, "feedback": "..."}. '
        f"\nEvidence Bank:\n{context}\n\nDraft:\n{draft}"
    )

    print(
        f"Analyzing draft quality (Strictness: {strictness}, Threshold: {threshold})...")
    start_time = time.time()
    response = await llm.ainvoke([SystemMessage(content="You are the Critic who ensures fidelity to evidence."), HumanMessage(content=critique_prompt)])
    duration = time.time() - start_time

    critique_data = _parse_critique(response)

    # Log trace (with encryption at rest if passphrase is available)
    if job_id != "unknown":
        tracer = TraceLogger(
            job_id,
            encryption_passphrase=encryption_passphrase,
            encryption_salt=encryption_salt,
        )
        tracer.log_llm_call(
            step=f"critique_revision_{state.get('revision_count', 0)}",
            prompt=critique_prompt,
            response=_coerce_content(response),
            model=model or "default",
            duration=duration
        )

    score = critique_data.get("score", 0)
    needs_revision = bool(
        score < threshold
        or critique_data.get("hallucination_score", 0) > 0.4
        or critique_data.get("is_vague", False)
        or bool(invalid_citations)  # Force revision if citations are invalid
    )
    revisions = state.get("revision_count", 0)
    if needs_revision:
        print(
            f"Critique: Needs revision (Score: {score}/{threshold}, Feedback: {critique_data.get('feedback')[:50]}...)")
        revisions += 1
    else:
        print(f"Critique: Passed (Score: {score}/{threshold})")

    payload: CritiquePayload = {
        "score": float(critique_data.get("score", 0)),
        "hallucination_score": float(critique_data.get("hallucination_score", 0)),
        "is_vague": bool(critique_data.get("is_vague", False)),
        "feedback": critique_data.get("feedback", "Provide clearer evidence alignment."),
        "needs_revision": needs_revision,
    }

    # Update metadata
    if job_id != "unknown":
        metadata = state.get("metadata", {})
        metadata["critique_cycles"] = revisions
        tracer = TraceLogger(job_id)
        tracer.save_metadata(metadata)

    logger.info("node.critique.complete",
                needs_revision=needs_revision, revisions=revisions)
    return {**state, "critique": payload, "revision_count": revisions}


def _parse_critique(message: Any) -> dict[str, Any]:
    raw = _coerce_content(message)
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("node.critique.json_error", raw=raw)
        data = {}
    return {
        "score": float(data.get("score", 0)),
        "hallucination_score": float(data.get("hallucination", data.get("hallucination_score", 0))),
        "is_vague": bool(data.get("vague", data.get("is_vague", False))),
        "feedback": data.get("feedback", raw),
    }


def _coerce_content(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for chunk in content:
            if isinstance(chunk, dict) and chunk.get("type") == "text":
                text_parts.append(chunk.get("text", ""))
        return "\n".join(text_parts)
    return str(content)
