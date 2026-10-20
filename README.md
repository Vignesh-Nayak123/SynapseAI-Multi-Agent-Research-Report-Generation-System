# Multi-Agent Research System
### Autonomous Academic Research with Multi-Agent Verification

<p align="left">
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" />
<img src="https://img.shields.io/badge/LangGraph-Multi--Agent-14b8a6?style=flat-square" />
<img src="https://img.shields.io/badge/Local-Ollama-orange?style=flat-square" />
<img src="https://img.shields.io/badge/Cloud-10%2B%20Providers-6366f1?style=flat-square" />
<img src="https://img.shields.io/badge/Benchmarks-8%20suites%20passing-brightgreen?style=flat-square" />
</p>

> An autonomous, multi-agent system that performs deep academic research, analyzes complex papers, and synthesizes comprehensive reviews with verified citations. Three agents - Researcher, Analyst, Critic - collaborate in a feedback loop with up to 3 revision passes, streamed live over Server-Sent Events, with a React 19 frontend for exploring the resulting knowledge graph, images, citations, and follow-up chat.

---

## Table of Contents

- [The Problem](#the-problem)
- [Key Result](#key-result)
- [Architecture](#architecture)
- [Features](#features)
- [Benchmarks](#benchmarks)
- [Repository Structure](#repository-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Related Work](#related-work)
- [Citation](#citation)

---

## The Problem

Deep research is a synthesis problem disguised as a search problem. A single LLM call against a topic produces fluent prose with no guarantee any of it is true - sources get invented, numbers get rounded into confidence they haven't earned, and there is no mechanism that catches a hallucinated claim before it reaches the reader. Manual literature review avoids this failure mode but doesn't scale: reading, ranking, and cross-referencing dozens of papers by hand is exactly the kind of high-volume, well-defined cognitive labor automation should be doing.

The core requirement is not "generate a report." It is "generate a report that has been checked."

**Multi-Agent Research System answers this by never letting a single model both write and grade its own work.**

---

## Key Result

> **Every non-LLM stage of the pipeline - chunking, ranking, citation validation, DOI resolution, PDF extraction, knowledge graph construction, and prompt assembly - runs in single-digit milliseconds or less, with cached image search 10,184x faster than a cold DDGS query.**

The system's latency budget is spent entirely on LLM calls (research, drafting, critique), not on infrastructure. See [Benchmarks](#benchmarks) for the full 8-suite breakdown, including where the pipeline is genuinely fast (chunking: up to 2.36B chars/s) and where it is comparatively the bottleneck (PDF extraction: 11–69ms per document).

---

## Architecture

A Researcher gathers sources, an Analyst drafts the synthesis, and a Critic - running as a genuinely separate pass - scores the draft for hallucinated claims, unsupported numbers, and citation integrity before anything ships. If the score falls short, the draft goes back for revision, up to three times. The whole loop is built on LangGraph and streamed live over Server-Sent Events.

```
Research Topic
      |
      v
+-------------------+
|  Researcher       |  Parallel Tavily + DuckDuckGo search
|                    |  Academic domain filtering (arxiv.org, .edu, .ac.uk)
|                    |  PDF parsing (PyMuPDF), reference-section stripping
+---------+----------+
          |
          v
+-------------------+
|  Analyst           |  High-density synthesis (2400+ words, deep mode)
|                    |  Thematic grouping into structured Markdown sections
+---------+----------+
          |
          v
+-------------------+
|  Critic             |  Hallucination + vague-claim detection
|                    |  Quantitative enforcement (rejects unsupported numbers)
+---------+----------+
          |
   score < threshold?
     |          |
    yes         no
     |          |
     v          v
  revise      ship
 (max 3x)    report
```

| Layer | Technology |
|---|---|
| **Agent Orchestration** | LangGraph, LangChain |
| **Backend** | Python, FastAPI, Server-Sent Events |
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS v4, Framer Motion |
| **LLM Engine (Local)** | Ollama (Llama 3, Mistral, etc.) |
| **LLM Engine (Cloud)** | OpenAI, Anthropic, Google, DeepSeek, Mistral, Groq, Perplexity, Together, OpenRouter |
| **Search** | Tavily API + DuckDuckGo fallback |
| **Images** | DuckDuckGo Image Search (DDGS), 1-hour in-memory cache |
| **PDF** | PyMuPDF (Fitz) |
| **Graphs** | React Force Graph (2D) |
| **Auth** | WebAuthn PRF (biometric unlock) + PBKDF2 encryption |

---

## Features

| Feature | Description |
| :--- | :--- |
| **Multi-agent pipeline** | Three autonomous agents (Researcher, Analyst, Critic) collaborate in a feedback loop with up to 3 revision passes |
| **Academic search** | Searches ArXiv and PDF repositories, parses full-text documents, ranks by relevance (Tavily + DuckDuckGo) |
| **10+ LLM providers** | Ollama, OpenAI, Anthropic, Google, DeepSeek, Mistral, Groq, Perplexity, Together - local or cloud |
| **Knowledge graph** | Interactive force-directed graph of cited papers - click any node to open the source |
| **Structured reports** | Rich Markdown with Executive Summary, Key Findings, Critical Analysis, Methodological Notes, and Implications |
| **Image gallery** | Automatically fetches related images and charts/graphs for any research topic, with lightbox navigation |
| **Follow-up chat** | Ask questions about the report - answers include formatted Markdown with source citation badges linked to the actual papers |
| **Citation styles** | Switch between Inline `[S#]`, APA, MLA, Chicago, and IEEE citation formats |
| **Executive brief** | AI-generated concise summary extracted from the report's key sections - no LLM call needed |
| **Research timeline** | Extracts year-based milestones from the report and arXiv source URLs into a visual timeline |
| **PDF upload & analysis** | Upload multiple PDF files, extract text, and include the content as additional research context |
| **DOI resolution** | Automatically resolves DOIs for arXiv sources and displays clickable DOI badges on reference cards |
| **PDF export** | Generates a styled HTML page optimized for printing as PDF |
| **Text-to-speech** | Reads the report aloud with markdown syntax stripped for clean audio |
| **Zero-knowledge encryption** | Passphrase-protected with WebAuthn biometric unlock. API keys encrypted end-to-end in the browser |
| **Critique & revision** | Automatic scoring, hallucination detection, and citation validation with configurable strictness |
| **Deep controls** | Configure search depth, source count, critic strictness, and custom model overrides |
| **Research queue** | Click multiple topics and they run sequentially - no parallel conflicts |
| **Health check** | `GET /health` reports status, version, provider and pipeline configuration for orchestrators - local state only, no LLM call |

---

## Benchmarks

Full suite: 8 categories covering every non-LLM stage of the pipeline - ranking, validation, summarization, prompt construction, DOI resolution, image search caching, state management, and PDF handling. Run with `python -m benchmarks.run_benchmarks`.

**Environment:** Python 3.14.4 · Windows-11-10.0.26200-SP0 · 8 CPUs (Intel64 Family 6 Model 140) · 15.79 GB RAM · **Duration: 36.16s**

### Document Ranking & Text Chunking

| Chunk Size | Overlap | Chunks | Avg Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| 250 chars | 25 chars | 16 | 11.0us | 325,791,691 chars/s |
| 500 chars | 50 chars | 8 | 8.0us | 458,598,464 chars/s |
| 1000 chars | 100 chars | 4 | 5.0us | 723,618,506 chars/s |
| 2000 chars | 200 chars | 2 | 3.0us | 1,111,112,631 chars/s |
| 4000 chars | 400 chars | 1 | 2.0us | 2,360,655,783 chars/s |

| Documents | Avg Time | Std Dev |
| :--- | :--- | :--- |
| 5 | 3.89ms | ±971.0us |
| 10 | 8.92ms | ±1.91ms |
| 25 | 20.03ms | ±1.37ms |
| 50 | 42.75ms | ±4.70ms |
| 100 | 84.41ms | ±8.40ms |

Ranking accuracy was validated against a hand-labeled query (`"quantum computing artificial intelligence"`): all 7 genuinely quantum-computing documents were returned in the top 7 positions, with two adjacent physics papers correctly pushed to the bottom of the 10-document set.

**What the numbers show.** TF-IDF ranking is linear in document count - 100 documents takes almost exactly 20x longer than 5 (84.41ms vs 3.89ms), the expected behavior for a cosine-similarity sweep with no indexing structure. This is fine at research-pipeline scale (5–50 sources per report) but would need an ANN index if source counts grew into the thousands. Chunking throughput is not the bottleneck at any scale tested - it stays above 300M chars/s even at the smallest chunk size.

### Citation Validation & Factual Consistency

| Documents | Citations in Draft | Invalid Found | Avg Time |
| :--- | :--- | :--- | :--- |
| 10 | 15 | 10 | 50.6us |
| 20 | 25 | 10 | 38.9us |
| 50 | 40 | 10 | 55.9us |
| 100 | 85 | 10 | 52.8us |

| Documents | Claims | Unverified Found | Avg Time |
| :--- | :--- | :--- | :--- |
| 10 | 5 | 3 | 92.2us |
| 20 | 20 | 17 | 256.0us |
| 50 | 50 | 59 | 3.12ms |
| 100 | 100 | 132 | 10.09ms |

**What the numbers show.** Citation validation (does `[S3]` point to a real source?) is a lookup - it stays flat at ~40–56us regardless of document count, because it's checking references against a fixed source list, not comparing text. Factual consistency (does this specific claim match any source content?) scales with claims × documents: 100 documents / 100 claims takes 10.09ms against 10/5's 92.2us, roughly 100x the work for 20x the claims, consistent with pairwise comparison rather than a lookup. The two checks catch different failure modes - a citation can point to a real source and still misrepresent what that source says.

### Summarization & Timeline Extraction

| Report Size | Brief Size | Compression Ratio | Avg Time |
| :--- | :--- | :--- | :--- |
| 500 chars | 509 chars | 101.8% | 9.0us |
| 1,000 chars | 1,008 chars | 100.8% | 14.0us |
| 5,000 chars | 2,411 chars | 48.2% | 43.0us |
| 10,000 chars | 2,411 chars | 24.1% | 50.0us |
| 50,000 chars | 2,929 chars | 5.9% | 448.0us |

**What the numbers show.** Below ~5,000 characters, the executive brief is effectively the full report (100%+ "compression" - brief formatting adds slightly more characters than it removes). This is correct, not a bug: a short report has no fat to trim. Real compression only appears once the report has enough structure to extract *from* - 50,000 chars down to 2,929 (5.9%) is the brief doing its actual job of pulling Executive Summary and Key Findings out of a much longer document, with no LLM call required either way.

| Scenario | Avg Time | Entries |
| :--- | :--- | :--- |
| Report Only | 820.0us | 4 |
| Sources Only | 51.0us | 6 |
| Combined | 539.0us | 7 |
| Many Sources (200) | 1.47ms | 6 |

Timeline extraction parses years (1900–2029) from report text and arXiv submission dates. Combined extraction (539us) is faster than report-only (820us) despite covering more ground, because arXiv-URL date parsing is cheaper than free-text year regex matching - the source-derived entries subsidize the total.

### Chat Prompt Construction

| Sources | Avg Time | Std Dev |
| :--- | :--- | :--- |
| 0 | 7.7us | ±0.7us |
| 5 | 7.2us | ±4.8us |
| 10 | 7.3us | ±1.2us |
| 20 | 19.5us | ±6.4us |
| 50 | 20.7us | ±4.8us |
| 100 | 19.0us | ±0.8us |

All 7 content checks (report inclusion, question, source list, answer marker, formatting/role/citation instructions) passed at every source count. Prompt construction is string concatenation, not analysis - the cost roughly doubles between 10 and 20 sources and then flattens, consistent with a fixed per-source template cost hitting diminishing returns as the prompt becomes dominated by the constant-size report body rather than the source list.

### DOI Resolution (arXiv ID Extraction)

| URLs Processed | IDs Found | Extraction Ratio | Avg Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 8 | 80% | 22.4us | 447,160 urls/s |
| 50 | 40 | 80% | 94.0us | 531,858 urls/s |
| 100 | 80 | 80% | 172.8us | 578,759 urls/s |
| 500 | 400 | 80% | 898.6us | 556,410 urls/s |
| 1,000 | 800 | 80% | 2.77ms | 360,964 urls/s |
| 5,000 | 4,000 | 80% | 11.82ms | 423,028 urls/s |

The extraction ratio holds exactly at 80% across every scale tested - a deliberate property of the benchmark's mixed URL set (arXiv abs/pdf/versioned URLs alongside non-arXiv URLs that should correctly *not* match), not a limitation of the regex. Pattern-level tests confirm this: abs URLs, pdf URLs, versioned URLs, HTTPS variants, case-insensitive matches, and query-param URLs all extract 1-for-1, while non-arXiv-only URLs correctly extract 0.

**What the numbers show.** Throughput is non-monotonic (578K urls/s at 100 URLs, dropping to 361K urls/s at 1,000, recovering to 423K urls/s at 5,000) - this is measurement noise from list allocation and GC pauses at those batch sizes on a single run, not a real performance cliff. At every scale it stays in the same order of magnitude (350K–580K urls/s), which is what matters: DOI resolution's real cost is the arXiv API round-trip this function feeds into, not the regex.

### Image Search Cache & Search Latency

| Metric | Value |
| :--- | :--- |
| Image Search - Cold | 1.273s avg (±0.728s, range 0.487s–1.925s) |
| Image Search - Warm (cached) | 0.125ms avg (±0.017ms) |
| Graph Search - Cold | 1.026s avg (±0.376s) |
| **Cache Acceleration Ratio** | **10,184x** |
| Cache Throughput (50 runs) | 0.1379ms/run, 0.0069s total |

**What the numbers show.** This is the standout number in the suite, and it is exactly what it looks like: the 1-hour in-memory image cache turns a ~1.3s DDGS network round-trip into a 0.125ms dictionary lookup. The wide std dev on cold search (±0.728s, nearly 60% of the mean) reflects real network variance - DDGS latency is not something this system controls - which makes the cache not just a speed optimization but a variance killer: every repeat request for a topic during its cache window has fully deterministic, sub-millisecond latency regardless of what the network is doing that day.

### Pipeline & State Management

| Operation | Avg Time |
| :--- | :--- |
| Basic Agent State Construction | 37.9us |
| Full Agent State Construction | 106.0us |
| Research Response (5 sources) | 98.3us |
| Research Response (100 sources) | 183.4us |
| Model Dump | 61.7us |
| JSON Serialize | 181.8us |
| Full Serialization (end-to-end) | 333.1us |
| Serialized Output Size | 14,091 bytes (13.8 KB) |

| Documents | Nodes | Avg Time |
| :--- | :--- | :--- |
| 5 | 5 | 2.57ms |
| 10 | 10 | 4.51ms |
| 25 | 25 | 14.50ms |
| 50 | 50 | 40.30ms |
| 100 | 100 | 89.45ms |

**What the numbers show.** Knowledge graph construction scales worse than linearly - 100 documents (89.45ms) takes over 2x the per-document cost of 50 documents (40.30ms), consistent with pairwise link-detection between nodes rather than a single pass. At 100 sources this is still under 90ms, well inside any reasonable UI budget, but it's the one component in this suite worth watching if source counts grow substantially past what a single research report typically returns (5–50).

### PDF Upload Handling & Text Extraction

| Pages | PDF Size | Extracted Chars | Avg Time | Throughput |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 8,382 bytes | 2,595 chars | 11.02ms | 90.7 pages/s |
| 3 | 21,887 bytes | 7,302 chars | 19.54ms | 153.5 pages/s |
| 5 | 35,448 bytes | 12,002 chars | 23.96ms | 208.7 pages/s |
| 10 | 69,444 bytes | 23,764 chars | 57.38ms | 174.3 pages/s |
| 20 | 137,435 bytes | 25,878 chars | 68.75ms | 290.9 pages/s |
| 50 | 341,927 bytes | 25,878 chars | 54.79ms | 912.5 pages/s |

**What the numbers show.** Extracted character count plateaus at 25,878 chars from 20 pages onward - this is the configured max-context truncation doing its job, not a parsing failure; the extractor correctly stops once it hits the context budget rather than wastefully parsing pages that will be discarded anyway. That's also why the 50-page row shows *higher* throughput (912.5 pages/s) than the 20-page row (290.9 pages/s): once truncation kicks in, extraction time is bounded by the character budget, not the page count, so nominal "pages/s" becomes an artifact of how many pages exist above the point where extraction stops mattering.

Reference-section stripping removes 2–12% of document text depending on how much of the document is bibliography (`with_references`: 1,989 → 1,899 chars; `large_document`: 27,687 → 24,499 chars), while correctly leaving early in-text citations untouched (`early_references_kept`: only 37 chars removed from 1,675). Column-layout detection and text-density validation both run in under 1 microsecond, confirming they're not meaningfully contributing to the 11–69ms per-document extraction cost - that time is entirely PyMuPDF's PDF parsing.

### Performance Summary

| Benchmark | Best Case | Worst Case |
| :--- | :--- | :--- |
| Text Chunking (250–4000 chars) | 2.0us | 11.0us |
| Citation Validation | 38.9us | 55.9us |
| Executive Brief Generation | 9.0us | 448.0us |
| arXiv ID Extraction | 22.4us | 11.82ms |
| PDF Text Extraction (1–50 pages) | 11.02ms | 68.75ms |
| Image Search Cache Acceleration | - | 10,184x faster |

**Bottom line.** Every stage that isn't an LLM call or a network fetch (DDGS, DOI API) runs in microseconds to low milliseconds. The two genuine cost centers are PDF extraction (bounded by PyMuPDF's parsing speed, ~11–69ms per document) and cold external search (~1.0–1.3s per DDGS call, mitigated 10,184x by the 1-hour cache). Neither is a design flaw - they're the honest floor set by parsing a real file format and hitting a real network, and this benchmark suite exists to keep that floor visible as the system evolves.

*Full report generated by Multi-Agent Research System Benchmark Suite v0.4.0.*

---

## Repository Structure

```
multi-agent-research-system/
├── run.py                    # Backend entry point (uvicorn)
├── requirements.txt
├── src/
│   ├── api.py                # FastAPI routes + SSE streaming
│   ├── config.py             # Environment configuration
│   ├── schemas.py            # Pydantic models
│   ├── agents/
│   │   ├── graph.py          # LangGraph workflow definition
│   │   ├── nodes.py          # Agent node functions
│   │   └── state.py          # Graph state schema
│   ├── tools/
│   │   ├── search.py         # Tavily + DuckDuckGo search
│   │   ├── pdf.py            # PDF download + parsing (PyMuPDF)
│   │   ├── ranking.py        # Source relevance ranking (TF-IDF)
│   │   ├── validation.py     # Citation validation
│   │   ├── graph.py          # Knowledge graph extraction
│   │   ├── chat.py           # Follow-up chat prompt builder
│   │   ├── images.py         # Image + chart search (DDGS)
│   │   ├── summarize.py      # Executive brief + timeline extraction
│   │   ├── doi.py            # ArXiv DOI resolution
│   │   └── __init__.py
│   ├── evaluation/
│   │   └── retrieval.py      # Retrieval evaluation
│   └── utils/
│       ├── crypto.py         # Server-side crypto helpers
│       └── tracing.py        # LangSmith tracing
├── frontend/
│   ├── src/
│   │   ├── main.tsx          # React entry + BrowserRouter
│   │   ├── App.tsx           # Research app (route: /app)
│   │   ├── pages/
│   │   │   └── Welcome.tsx   # Marketing landing page (route: /)
│   │   ├── components/
│   │   │   ├── Sidebar.tsx          # Collapsible nav + passphrase mgmt
│   │   │   ├── ResearchForm.tsx     # Topic input + config + PDF upload
│   │   │   ├── ReportView.tsx       # Report viewer + all features
│   │   │   ├── LoadingState.tsx     # Real-time progress dashboard
│   │   │   ├── KnowledgeGraph.tsx   # Force-directed citation graph
│   │   │   ├── ImageGallery.tsx     # Image/chart gallery with lightbox
│   │   │   ├── ChatPanel.tsx        # Follow-up chat with markdown
│   │   │   ├── ErrorBoundary.tsx    # Error fallback UI
│   │   │   └── BrandIcon.tsx        # SVG brand icon component
│   │   ├── hooks/
│   │   │   └── useResearch.ts       # Research state + queue logic
│   │   └── lib/
│   │       ├── api.ts               # API client + all endpoints
│   │       ├── crypto.ts            # AES-256-GCM + PBKDF2 encryption
│   │       ├── webauthn.ts          # WebAuthn PRF biometric unlock
│   │       └── favicon.ts           # Dynamic theme-aware favicon swap
│   └── package.json
└── benchmarks/
    └── run_benchmarks.py      # 8-category benchmark suite
```

---

## Installation

```bash
git clone https://github.com/royxforge/multi-agent-research-system.git
cd multi-agent-research-system

# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

**Core dependencies:** LangGraph · LangChain · FastAPI · React 19 · Tailwind CSS v4 · PyMuPDF

---

## Usage

```bash
# Terminal 1 - backend
python run.py

# Terminal 2 - frontend
cd frontend && npm run dev
```

Open `http://localhost:5173` and navigate to `/app` to start researching.

**Health & readiness probe:**

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "0.4.0", "graph_loaded": true,
#  "llm": {"configured": {"ollama": true, ...}}, "healthy": true}

# Also verify the local model server is reachable (network I/O, opt-in)
curl "http://localhost:8000/health?probe=true"
```

An unready instance answers **`503`** with `"status": "degraded"`, so a
container orchestrator or load balancer that only checks the status code works
without parsing the body. Without `?probe=true` the endpoint performs no network
I/O, so it is cheap enough to call on a short interval.

1. Enter a research topic (e.g., *"Impact of solid-state batteries on EV range"*)
2. Configure depth (Fast / Balanced / Deep), source count (5–50), critic strictness, and LLM provider
3. Watch the agents work in real time - Researching → Drafting → Critiquing
4. Explore the report: knowledge graph, image gallery, follow-up chat, citation style switching, executive brief, timeline, PDF export, text-to-speech

**Configuration** (`.env`):

```env
TAVILY_API_KEY=your_key_here

# Local Mode
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b

# Cloud Mode (optional - any of these)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
```

---

## Related Work

- [RAG Evaluation Framework](https://github.com/royxforge/rag-evaluation-framework) - The Critic's hallucination detection and citation validation here is a lighter, rule-based counterpart to RAG Evaluation Framework's LLM-judged faithfulness and hallucination-rate metrics. Where that framework scores a single (question, context, answer) triple with an LLM judge, this system's Critic runs the same category of check inline, as a gate, at pipeline speed.
- [Production Drift Detection](https://github.com/royxforge/production-drift-detection) - The image-search cache and its 10,184x acceleration ratio is a caching problem, not a monitoring one, but the underlying instinct matches Production Drift Detection's philosophy: don't re-pay a cost you've already paid recently, and measure the tradeoff explicitly rather than assuming it.
- [Unsupervised Confidence Estimation](https://github.com/royxforge/unsupervised-confidence-estimation) - The Critic's revision loop (up to 3 passes, gated on a quality score) is a coarse-grained analog of that project's label-free confidence signal: both let a system flag its own low-confidence output before a human sees it, without requiring ground truth to do so.

---

## Citation

```bibtex
@software{roy2026multiagentresearchsystem,
  author = {Roy, Sourav},
  title = {Multi-Agent Research System: Autonomous Academic Research with Multi-Agent Verification},
  year = {2026},
  url = {https://github.com/royxforge/multi-agent-research-system}
}
```

---

<p align="center">
<sub>Built by <a href="https://github.com/royxforge">Sourav Roy</a> · Artificial Intelligence Engineer · Accure Inc.</sub>
</p>