from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import structlog
import json
import asyncio
import re
import time
import uuid
from datetime import datetime, timezone

import aiohttp
import xml.etree.ElementTree as ET
from collections import Counter

from pydantic import BaseModel
from src.agents.graph import build_research_graph
from src.agents.state import AgentState
from src.config import configure_logging, get_settings
from src.schemas import ResearchRequest, ResearchResponse, ImageResult
from src.utils.tracing import TraceLogger
from src.tools.graph import build_citation_graph
from src.tools.images import search_related_images, search_related_graphs
from src.tools.pdf import PDFProcessor
from src.tools.doi import resolve_dois_batch
from src.tools.summarize import generate_simple_explanation, generate_timeline_data
from src.tools.chat import build_chat_prompt

settings = get_settings()
configure_logging(settings)
logger = structlog.get_logger(__name__)

# Never log these sensitive fields
_SENSITIVE_LOG_FIELDS = frozenset({
    "api_key",
    "openrouter_api_key",
    "encrypted_api_key",
    "encryption_iv",
    "encryption_salt",
    "encryption_passphrase",
})


def _deduplicate_documents(documents: list) -> list:
    """Merge chunks sharing the same base URL into a single document for graph generation."""
    unique = {}
    for doc in documents:
        base_url = re.sub(r'\s*\(part \d+\)$', '', doc["source"])
        if base_url in unique:
            unique[base_url]["content"] += "\n\n" + doc["content"]
        else:
            unique[base_url] = {"source": base_url, "content": doc["content"]}
    return list(unique.values())


def _safe_log_request(request: ResearchRequest) -> dict:
    """Return a sanitised dict of request fields safe for logging."""
    return {
        k: v
        for k, v in request.model_dump().items()
        if k not in _SENSITIVE_LOG_FIELDS and v is not None
    }


_ALLOWED_HTML_TAGS = frozenset(
    {
        "h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "strong", "em",
        "code", "pre", "blockquote", "table", "thead", "tbody", "tr",
        "th", "td", "a", "hr", "br",
    }
)
_ALLOWED_HTML_ATTRS = {"a": ["href", "title"]}


def _sanitize_html_body(html_body: str) -> str:
    """Strip unsafe markup from markdown-rendered HTML (bleach/nh3, else escape)."""
    try:
        import bleach

        return bleach.clean(
            html_body,
            tags=_ALLOWED_HTML_TAGS,
            attributes=_ALLOWED_HTML_ATTRS,
            strip=True,
        )
    except ImportError:
        pass
    try:
        import nh3  # type: ignore

        return nh3.clean(html_body, tags=_ALLOWED_HTML_TAGS, attributes=_ALLOWED_HTML_ATTRS)
    except ImportError:
        pass
    import html as html_lib

    return html_lib.escape(html_body)


app = FastAPI(title="Multi-Agent Research System", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.graph = build_research_graph()

# ── Trending topics cache ──────────────────────────────────────────
_TRENDING_CACHE: dict[str, object] = {"topics": [], "timestamp": 0.0}
_TRENDING_CACHE_TTL = 3600  # 1 hour

_ARXIV_CATEGORY_TOPICS: dict[str, str] = {
    "cs.AI": "Advances in Artificial Intelligence",
    "cs.LG": "Machine Learning Research",
    "cs.CL": "Natural Language Processing",
    "cs.CV": "Computer Vision",
    "cs.RO": "Robotics & Autonomous Systems",
    "cs.CR": "Cybersecurity Research",
    "cs.NE": "Neural Networks & Deep Learning",
    "cs.SE": "Software Engineering",
    "cs.DB": "Data Management & Mining",
    "cs.SI": "Social & Information Networks",
    "cs.IR": "Information Retrieval",
    "cs.HC": "Human-Computer Interaction",
    "cs.MA": "Multiagent Systems",
    "cs.CY": "Computers & Society",
    "stat.ML": "Statistical Machine Learning",
    "q-bio.GN": "Genomics & Bioinformatics",
    "q-bio.NC": "Neurons & Cognition",
    "q-fin": "Quantitative Finance",
    "eess.AS": "Audio & Speech Processing",
    "eess.IV": "Image & Video Processing",
    "physics.soc-ph": "Physics & Society",
    "math.OC": "Optimization & Control",
}


async def _fetch_trending_topics() -> list[str]:
    """Fetch recent papers from arXiv and return trending topic names."""
    url = (
        "http://export.arxiv.org/api/query?"
        "search_query=all:"
        "&sortBy=submittedDate"
        "&sortOrder=descending"
        "&max_results=150"
    )
    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning("arxiv.api.error", status=resp.status)
                    return []
                text = await resp.text()

        root = ET.fromstring(text)
        categories: list[str] = []
        for entry in root.findall("atom:entry", namespaces):
            primary = entry.find("arxiv:primary_category", namespaces)
            if primary is not None:
                cat = primary.get("term", "")
                if cat:
                    categories.append(cat)

        if not categories:
            return []

        # Count, sort, map to readable names, take top 5
        counts = Counter(categories)
        top = [cat for cat, _ in counts.most_common(12)]

        # Map to readable topic names
        topics: list[str] = []
        seen: set[str] = set()
        for cat in top:
            # Try exact match, then prefix match
            topic = _ARXIV_CATEGORY_TOPICS.get(cat)
            if not topic:
                prefix = cat.rsplit(".", 1)[0]
                topic = _ARXIV_CATEGORY_TOPICS.get(prefix)
            if topic and topic not in seen:
                topics.append(topic)
                seen.add(topic)
            if len(topics) >= 5:
                break

        return topics if topics else []

    except Exception as exc:
        logger.warning("trending.fetch_failed", error=str(exc))
        return []


# Providers whose presence is decided purely by an environment credential.
_PROVIDER_KEY_FIELDS = {
    "ollama": None,
    "openrouter": "openrouter_api_key",
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "google": "google_api_key",
    "perplexity": "perplexity_api_key",
    "groq": "groq_api_key",
    "together": "together_api_key",
    "deepseek": "deepseek_api_key",
    "mistral": "mistral_api_key",
}


async def _ollama_reachable(timeout: float = 2.0) -> bool:
    """Best-effort reachability probe for the configured Ollama server."""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(f"{settings.ollama_base_url}/api/tags") as resp:
                return resp.status == 200
    except Exception:
        return False


@app.get("/health")
async def health(probe: bool = False) -> dict:
    """Liveness + readiness probe for orchestrators, load balancers and the UI.

    Fast by default (no network I/O). Pass ``?probe=true`` to additionally
    verify that the default LLM backend is reachable - a missing model server
    is the most common cause of failing research jobs, and without this probe
    an otherwise healthy process reports OK while every job times out.
    """
    configured = {"ollama": True}  # local server, no credentials required
    for name, key_field in _PROVIDER_KEY_FIELDS.items():
        if name != "ollama":
            configured[name] = bool(key_field and getattr(settings, key_field, None))

    llm: dict[str, object] = {"configured": configured}
    if probe:
        llm["ollama_reachable"] = await _ollama_reachable()

    graph_loaded = app.state.graph is not None
    # Without a probe we only know which backends are configured; ollama is the
    # default and always counts as usable until proven otherwise.
    healthy = graph_loaded and (configured["ollama"] or any(configured.values()))

    # The status code carries the verdict: orchestrators and load balancers
    # (k8s readiness probes, ALB health checks) only look at the code, so an
    # unhealthy instance must not answer 200. The body keeps the detail for
    # clients that want to know *why*.
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "degraded",
            "version": app.version,
            "graph_loaded": graph_loaded,
            "llm": llm,
            "healthy": healthy,
        },
    )


@app.get("/trending")
async def get_trending_topics():
    """Return trending research topics based on recent arXiv submissions."""
    now = time.time()
    if now - _TRENDING_CACHE["timestamp"] > _TRENDING_CACHE_TTL or not _TRENDING_CACHE["topics"]:
        topics = await _fetch_trending_topics()
        if topics:
            _TRENDING_CACHE["topics"] = topics
            _TRENDING_CACHE["timestamp"] = now
    return {"topics": _TRENDING_CACHE["topics"]}


@app.post("/research/stream")
async def run_research_stream(request: ResearchRequest):
    graph = getattr(app.state, "graph", None)
    if graph is None:
        graph = build_research_graph()
        app.state.graph = graph

    job_id = str(uuid.uuid4())
    
    # Zero-knowledge encryption params
    encryption_passphrase = request.encryption_passphrase
    encryption_salt = request.encryption_salt

    initial_state: AgentState = {
        "query": request.topic,
        "max_depth": request.max_depth,
        "max_search_results": request.num_papers,
        "provider": request.provider,
        "openrouter_api_key": request.openrouter_api_key,
        "model": request.model,
        "critic_strictness": request.critic_strictness,
        "encrypted_api_key": request.encrypted_api_key,
        "encryption_iv": request.encryption_iv,
        "encryption_salt": encryption_salt,
        "encryption_passphrase": encryption_passphrase,
        "uploaded_content": request.uploaded_content,
        "job_id": job_id,
        "seed": settings.default_seed,
        "temperature": settings.default_temperature,
        "top_p": settings.default_top_p,
        "metadata": {
            "job_id": job_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "model": request.model or "default",
            "provider": request.provider,
            "retrieval_stats": {},
            "pdf_stats": {},
            "has_uploaded_content": request.uploaded_content is not None,
        }
    }

    async def event_generator():
        try:
            current_step = None
            # Stream events from the graph
            async for event in graph.astream_events(initial_state, version="v1"):
                kind = event["event"]
                
                # Filter for node start/end events to track progress
                if kind == "on_chain_start" and event["name"] in ["research", "draft", "critique"]:
                    current_step = event["name"]
                    yield f"data: {json.dumps({'type': 'progress', 'step': event['name'], 'status': 'running'})}\n\n"
                
                elif kind == "on_chain_end" and event["name"] in ["research", "draft", "critique"]:
                    yield f"data: {json.dumps({'type': 'progress', 'step': event['name'], 'status': 'completed'})}\n\n"
                    current_step = None
                
                elif kind == "on_chat_model_stream" and current_step == "draft":
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

            # Get final state to return the result
            final_state = await graph.ainvoke(initial_state)
            draft = final_state.get("draft")
            # Deduplicate sources by base URL (strip " (part N)" suffix)
            raw_sources = [doc["source"] for doc in final_state.get("documents", [])]
            sources = list(dict.fromkeys(
                re.sub(r'\s*\(part \d+\)$', '', s) for s in raw_sources
            ))
            
            # Save graph execution trace (encrypted at rest if passphrase provided)
            tracer = TraceLogger(
                job_id,
                encryption_passphrase=encryption_passphrase,
                encryption_salt=encryption_salt,
            )
            tracer.save_graph_execution(final_state)

            # Update end time in metadata
            metadata = final_state.get("metadata", {})
            metadata["end_time"] = datetime.now(timezone.utc).isoformat()
            tracer.save_metadata(metadata)
            
            if not draft:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Workflow produced no draft'})}\n\n"
            else:
                graph_data = build_citation_graph(_deduplicate_documents(final_state.get("documents", [])))

                # Search for related images and graphs in parallel
                images, graphs = await asyncio.gather(
                    asyncio.to_thread(search_related_images, request.topic, 8),
                    asyncio.to_thread(search_related_graphs, request.topic, 6),
                )

                image_results = [
                    ImageResult(
                        title=img.get("title", ""),
                        image_url=img.get("image", ""),
                        thumbnail_url=img.get("thumbnail"),
                        source_url=img.get("url", ""),
                        source_domain=img.get("source", ""),
                        width=int(img["width"]) if img.get("width") and img["width"].isdigit() else None,
                        height=int(img["height"]) if img.get("height") and img["height"].isdigit() else None,
                    )
                    for img in images
                ]
                graph_results = [
                    ImageResult(
                        title=img.get("title", ""),
                        image_url=img.get("image", ""),
                        thumbnail_url=img.get("thumbnail"),
                        source_url=img.get("url", ""),
                        source_domain=img.get("source", ""),
                        width=int(img["width"]) if img.get("width") and img["width"].isdigit() else None,
                        height=int(img["height"]) if img.get("height") and img["height"].isdigit() else None,
                    )
                    for img in graphs
                ]

                result = ResearchResponse(
                    final_report=draft,
                    sources=sources,
                    topic=request.topic,
                    graph_data=graph_data,
                    images=image_results,
                    graphs=graph_results,
                )
                yield f"data: {json.dumps({'type': 'result', 'data': result.model_dump()})}\n\n"

        except Exception as e:
            logger.error("stream.error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/research", response_model=ResearchResponse)
async def run_research(request: ResearchRequest) -> ResearchResponse:
    graph = getattr(app.state, "graph", None)
    if graph is None:
        logger.warning("graph.not_initialized")
        graph = build_research_graph()
        app.state.graph = graph

    job_id = str(uuid.uuid4())

    encryption_passphrase = request.encryption_passphrase
    encryption_salt = request.encryption_salt

    initial_state: AgentState = {
        "query": request.topic,
        "max_depth": request.max_depth,
        "max_search_results": request.num_papers,
        "provider": request.provider,
        "openrouter_api_key": request.openrouter_api_key,
        "model": request.model,
        "critic_strictness": request.critic_strictness,
        "encrypted_api_key": request.encrypted_api_key,
        "encryption_iv": request.encryption_iv,
        "encryption_salt": encryption_salt,
        "encryption_passphrase": encryption_passphrase,
        "uploaded_content": request.uploaded_content,
        "job_id": job_id,
        "seed": settings.default_seed,
        "temperature": settings.default_temperature,
        "top_p": settings.default_top_p,
        "metadata": {
            "job_id": job_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "model": request.model or "default",
            "provider": request.provider,
            "retrieval_stats": {},
            "pdf_stats": {},
            "has_uploaded_content": request.uploaded_content is not None,
        }
    }

    log_fields = _safe_log_request(request)
    logger.info("api.research.start", **log_fields, job_id=job_id)
    try:
        result: AgentState = await graph.ainvoke(initial_state)
        
        # Save graph execution trace (encrypted at rest if passphrase provided)
        tracer = TraceLogger(
            job_id,
            encryption_passphrase=encryption_passphrase,
            encryption_salt=encryption_salt,
        )
        tracer.save_graph_execution(result)

        # Update end time in metadata
        metadata = result.get("metadata", {})
        metadata["end_time"] = datetime.now(timezone.utc).isoformat()
        tracer.save_metadata(metadata)

    except Exception as exc:
        logger.error("api.research.failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to complete research workflow") from exc

    draft = result.get("draft")
    if not draft:
        logger.error("api.research.empty_draft")
        raise HTTPException(status_code=424, detail="Workflow did not produce a draft")

    # Deduplicate sources by base URL (strip " (part N)" suffix)
    raw_sources = [doc["source"] for doc in result.get("documents", [])]
    sources = list(dict.fromkeys(
        re.sub(r'\s*\(part \d+\)$', '', s) for s in raw_sources
    ))
    logger.info("api.research.complete", sources=len(sources))
    
    graph_data = build_citation_graph(_deduplicate_documents(result.get("documents", [])))

    # Search for related images and graphs
    images = await asyncio.to_thread(search_related_images, request.topic, 8)
    graphs = await asyncio.to_thread(search_related_graphs, request.topic, 6)

    image_results = [
        ImageResult(
            title=img.get("title", ""),
            image_url=img.get("image", ""),
            thumbnail_url=img.get("thumbnail"),
            source_url=img.get("url", ""),
            source_domain=img.get("source", ""),
            width=int(img["width"]) if img.get("width") and img["width"].isdigit() else None,
            height=int(img["height"]) if img.get("height") and img["height"].isdigit() else None,
        )
        for img in images
    ]
    graph_results = [
        ImageResult(
            title=img.get("title", ""),
            image_url=img.get("image", ""),
            thumbnail_url=img.get("thumbnail"),
            source_url=img.get("url", ""),
            source_domain=img.get("source", ""),
            width=int(img["width"]) if img.get("width") and img["width"].isdigit() else None,
            height=int(img["height"]) if img.get("height") and img["height"].isdigit() else None,
        )
        for img in graphs
    ]
    
    return ResearchResponse(
        final_report=draft,
        sources=sources,
        topic=request.topic,
        graph_data=graph_data,
        images=image_results,
        graphs=graph_results,
    )


# ── Feature: ArXiv DOI Badges ──────────────────────────────────────

@app.post("/resolve-dois")
async def resolve_dois(urls: list[str]):
    """Resolve DOIs for arXiv URLs."""
    dois = await resolve_dois_batch(urls)
    return {"dois": dois}


# ── Feature: File Upload & Analysis ────────────────────────────────

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile | None = File(None)):
    """Upload a PDF file and extract its text content."""
    if file is None or not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(raw_bytes) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")

        processor = PDFProcessor(max_concurrency=1)
        text = await asyncio.to_thread(processor._extract_and_validate, raw_bytes)
        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=422, detail="Could not extract meaningful text from PDF")

        # Truncate to max context chars
        text = text[: get_settings().max_context_chars]
        return {"filename": file.filename, "content": text, "char_count": len(text)}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("upload.failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {exc}")


# ── Feature: Explain / Simplify ────────────────────────────────────

class ExplainRequest(BaseModel):
    report: str
    mode: str = "brief"  # "brief" or "eli5"

@app.post("/explain")
async def explain_report(request: ExplainRequest):
    """Generate a simplified version of a research report."""
    brief = generate_simple_explanation(request.report)
    return {"explanation": brief}


# ── Feature: Research Timeline ─────────────────────────────────────

class TimelineRequest(BaseModel):
    report: str
    sources: list[str]

@app.post("/timeline")
async def get_timeline(request: TimelineRequest):
    """Extract timeline data from a report and its sources."""
    data = generate_timeline_data(request.report, request.sources)
    return {"timeline": data}


# ── Feature: Follow-up Chat ────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    report: str
    sources: list[str]
    provider: str = "ollama"
    model: str | None = None

_SYSTEM_PROMPT = (
    "You are a helpful research assistant. Answer concisely using only the provided report. "
    "Always format your answer in clean Markdown with headings, paragraphs, bullet points, "
    "and bold terms for readability."
)


@app.post("/chat")
async def chat_followup(request: ChatRequest):
    """Answer a follow-up question about a research report (non-streaming)."""
    settings = get_settings()
    prompt = build_chat_prompt(request.question, request.report, request.sources)

    from src.agents.nodes import _get_llm
    try:
        llm = _get_llm(
            provider=request.provider,
            model=request.model,
            seed=settings.default_seed,
            temperature=0.3,
            top_p=0.9,
        )
        from langchain_core.messages import HumanMessage, SystemMessage
        response = await llm.ainvoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        answer = response.content if hasattr(response, "content") else str(response)
        return {"answer": answer}
    except Exception as exc:
        logger.error("chat.failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Chat failed: {exc}")





# ── Feature: Generate PDF (returns HTML for client-side printing) ──

class PdfRequest(BaseModel):
    report: str
    topic: str
    sources: list[str]

@app.post("/generate-html")
async def generate_html(request: PdfRequest):
    """Generate styled HTML from a report for PDF printing."""
    import html as html_lib

    import markdown
    html_body = markdown.markdown(request.report, extensions=["extra", "codehilite"])
    html_body = _sanitize_html_body(html_body)
    safe_topic = html_lib.escape(request.topic)
    safe_sources = "".join(f"<li>{html_lib.escape(s)}</li>" for s in request.sources[:20])
    sources_html = f"<ul>{safe_sources}</ul>"
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{safe_topic}</title>
<style>
body {{ font-family: 'Times New Roman', Georgia, serif; font-size: 12pt; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 40px; color: #222; }}
h1 {{ font-size: 22pt; margin-bottom: 5px; }}
h2 {{ font-size: 16pt; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
h3 {{ font-size: 13pt; }}
p {{ margin-bottom: 10px; }}
table {{ width: 100%; border-collapse: collapse; }}
td, th {{ border: 1px solid #ccc; padding: 6px; }}
pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
code {{ background: #f0f0f0; padding: 1px 4px; border-radius: 2px; }}
ul, ol {{ margin-bottom: 10px; }}
blockquote {{ border-left: 3px solid #999; padding-left: 15px; color: #555; }}
.sources {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #333; }}
.sources ul {{ font-size: 10pt; color: #555; }}
@media print {{ body {{ padding: 0; }} }}
</style></head>
<body>
<h1>{safe_topic}</h1>
{html_body}
<div class="sources"><h2>Sources</h2>{sources_html}</div>
</body>
</html>"""
    return {"html": html}

