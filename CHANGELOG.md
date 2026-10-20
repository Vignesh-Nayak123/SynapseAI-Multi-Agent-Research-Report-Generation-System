# Changelog

> *Autonomous Academic Research with Multi-Agent Verification*
>
> All notable changes to this project are documented herein. The format adheres to the principles of semantic versioning and maintains a chronological record of the repository's evolution, from its prototype inception through successive refinements toward a production-grade research automation platform.

---

## Table of Contents

- [2026-10-12 - Upload Pipeline & Test Fixes](#2026-10-12--upload-pipeline--test-fixes)
- [2026-07-20 - Repository Migration & Remote URL Update](#2026-07-20--repository-migration--remote-url-update)
- [2026-07-20 - Community Health Files](#2026-07-20--community-health-files)
- [2026-07-14 - Documentation Restructuring](#2026-07-14--documentation-restructuring)
- [2026-06-22 - Benchmark Suite & Uploaded Content Integration](#2026-06-22--benchmark-suite--uploaded-content-integration)
- [2026-05-26 - Documentation & Examples (Revision)](#2026-05-26--documentation--examples-revision)
- [2026-05-26 - Contribution Guidelines & Documentation Enhancement](#2026-05-26--contribution-guidelines--documentation-enhancement)
- [2026-05-26 - README Asset Restructuring](#2026-05-26--readme-asset-restructuring)
- [2026-05-26 - Brand Identity & Theme Integration](#2026-05-26--brand-identity--theme-integration)
- [2026-05-26 - Welcome Page & Example Report](#2026-05-26--welcome-page--example-report)
- [2026-05-26 - General Improvements](#2026-05-26--general-improvements)
- [2025-11-30 - Test Suite Expansion](#2025-11-30--test-suite-expansion)
- [2025-11-26 - Strictness Parameter & Streaming Research](#2025-11-26--strictness-parameter--streaming-research)
- [2025-11-25 - Initial Commit](#2025-11-25--initial-commit)

---

## [0.4.0] - 2026-10-13

### Added

- **Health endpoint**: `GET /health` reports service status, the version, which LLM backends are configured and whether the research graph is loaded, so a supervisor, container orchestrator or load balancer can decide whether an instance is ready without spending a research request. No network I/O happens by default; `?probe=true` additionally checks whether the Ollama server is reachable (a missing model server is the most common cause of jobs that time out). An unready instance now answers **HTTP 503** with `"status": "degraded"` instead of always returning `200`, so a probe that only inspects the status code cannot mistake a degraded instance for a healthy one:

  ```json
  {
    "status": "ok",
    "version": "0.4.0",
    "graph_loaded": true,
    "llm": {"configured": {"ollama": true, "openai": false}, "ollama_reachable": true},
    "healthy": true
  }
  ```

---

## [0.2.0] - 2026-09-26

### Security

- **LLM cache**: the `@lru_cache`d `_get_llm` no longer includes `api_key` in its cache key (secrets were embedded in cache keys and allowed cross-key poisoning).
- **PDF fetching**: SSRF and resource guards before processing remote documents -- scheme/host allowlist, `max_bytes` cap, shared `ClientSession`, and non-exception results filtered out of `asyncio.gather`.
- **Report export**: markdown-rendered HTML is sanitised (`bleach`/`nh3` with an allow-listed tag set) and topic/source strings are HTML-escaped; `markdown>=3.6`, `bleach`, and `defusedxml` added to `requirements.txt`.
- **Trace crypto**: `encrypt_trace_data` honours the supplied `encryption_salt` (previously ignored and replaced with a random salt, so traces could not be decrypted with the configured salt).

### Fixed

- **DOI resolver**: HTTPS arXiv endpoint, `defusedxml` parsing (XXE), bounded `DOI_CACHE` (1000 entries), validated arXiv ID format, and batch resolution capped at 5 concurrent requests.
- **Factual-consistency checker**: numeric claims must appear within a +/-40-char window sharing a significant token with their claim sentence; the previous bare substring check passed any number appearing *anywhere* in the sources (e.g. "2024" in an unrelated sentence).
- **Hallucination detector**: parses the LLM's JSON reply into `{hallucinations, score}`; unparseable replies return an explicit `parse_error` payload instead of `{"raw_response": ...}`.

---

## Unreleased / In Development

The following capabilities are under active investigation or development and have not yet been incorporated into a formal release:

- Alternative indexing structures (e.g., approximate nearest neighbor) for document ranking at scales exceeding 1,000 sources
- Additional LLM provider integrations beyond the current 11 supported engines
- Enhanced knowledge graph interactivity and filtering controls
- Expanded benchmark coverage for LLM-dependent pipeline stages
- Performance optimization for knowledge graph construction at scale

---

## 2026-10-12 - Upload Pipeline & Test Fixes

**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Fixed

- **Upload-only drafting**: `draft_node` aborted with "requires at least one document" when a run had an uploaded PDF but no web sources; uploaded content now counts as a valid source.
- **Upload endpoint errors**: `POST /upload-pdf` returns `400` (not `422`) for an empty filename or a zero-byte file, and the handler owns its filename/empty-file validation; a duplicate `fastapi` import was removed.
- **Retrieval evaluator type import**: `src/evaluation/retrieval.py` annotated with `Any` without importing it (a `NameError` before Python 3.14).
- **Timestamps**: `datetime.utcnow()` (deprecated, scheduled for removal) replaced with `datetime.now(timezone.utc)`.
- **Upload integration tests**: the PDF fixture now generates documents that clear the extractor's minimum-text validation, so the concurrency and round-trip tests exercise real uploads.

---

## 2026-07-20 - Repository Migration & Remote URL Update

**Commit:** Not yet committed  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Updated the Git remote URL from `royxlead` to `royxforge` to reflect the permanent repository home under the royxforge GitHub organization.

### Changed

- **Git remote origin**: Updated from `https://github.com/royxlead/auto-researcher-python.git` to `https://github.com/royxforge/multi-agent-research-system.git` to align with the canonical repository location.

---

## 2026-07-20 - Community Health Files

**Commit:** Not yet committed  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Added community health and governance files to standardize contribution workflows and project documentation.

### Added

- **`CODE_OF_CONDUCT.md`** *(New)* - Contributor Covenant v2.1 establishing community standards, enforcement guidelines, and reporting procedures.
- **`CONTRIBUTING.md`** *(New)* - Comprehensive contribution guide covering development setup, coding standards, testing requirements, pull request process, and commit message conventions.
- **`SECURITY.md`** *(New)* - Security policy with vulnerability reporting procedures and coordinated disclosure timeline.
- **`CITATION.cff`** *(New)* - Citation metadata for academic attribution, including author, title, version, repository URL, and keywords.

---

## 2026-07-14 - Documentation Restructuring

**Commit:** [`4c0fc0e`](https://github.com/royxforge/multi-agent-research-system/commit/4c0fc0e)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

A comprehensive documentation consolidation and restructuring pass. The README was rewritten to function as the singular, definitive system reference, supplanting auxiliary documentation files that had accrued during the previous development cycle. This restructuring reflects the project's maturation from an experimental prototype to a documented, externally understandable system.

### Changes

#### Documentation

- **README.md** - Complete rewrite. Expanded to encompass the full system architecture description, benchmark results across all eight evaluation suites, repository structure map, installation and usage instructions, and citations for related work. The document was reorganized into a hierarchical structure with dedicated sections for the problem domain, key results, architecture, features, benchmarks, repository structure, installation, usage, and related work.
- **Removed:** `CHANGELOG.md`, `CONTRIBUTING.md` - Deleted to centralize all documentation within the README, eliminating fragmentation and ensuring a single source of truth.
- **Removed:** `assets/Features.png`, `assets/HomeScreen.png`, `assets/SearchScreen.png` - Redundant asset images removed.

#### Frontend

- **`frontend/README.md`** - Minor corrections and formatting improvements.
- **`frontend/index.html`** - Updated metadata and branding references.
- **`frontend/src/App.tsx`, `frontend/src/components/Sidebar.tsx`** - Component refinements.
- **`frontend/src/lib/api.ts`, `frontend/src/lib/crypto.ts`, `frontend/src/lib/webauthn.ts`** - Minor corrections and edge-case handling improvements.

#### Backend

- **`src/agents/nodes.py`, `src/api.py`, `src/tools/pdf.py`** - Minor corrections, robustness improvements, and edge-case handling.

#### Benchmarking

- **`benchmark/benchmark_report.md`** - Updated report formatting.
- **`benchmark/benchmark_runner.py`** - Minor improvements to benchmark execution.

#### Licensing

- **`LICENSE`** - Minor formatting correction.

---

## 2026-06-22 - Benchmark Suite & Uploaded Content Integration

**Commit:** [`052057c`](https://github.com/royxforge/multi-agent-research-system/commit/052057c)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

A major expansion introducing the Auto-Researcher Benchmark Suite-a comprehensive, eight-category evaluation framework spanning all non-LLM components of the pipeline-alongside support for uploaded PDF content, DOI resolution, image search with in-memory caching, and follow-up chat capabilities. This release transforms the system from a research demonstration into a quantitatively characterized platform.

### Changes

#### Benchmark Suite (New)

Introduced an entirely new `benchmark/` directory containing a modular, parameterized benchmark framework:

| Module | Purpose |
|---|---|
| `benchmark_runner.py` | Central orchestration harness with configurable iteration counts, warm-up runs, and CSV/JSON output |
| `benchmark_ranking.py` | TF-IDF ranking and chunking throughput evaluation across document sets of 5–100 sources |
| `benchmark_validation.py` | Citation validation and factual consistency checking across document/claim scales |
| `benchmark_summarize.py` | Executive brief generation and timeline extraction at report sizes from 500 to 50,000 characters |
| `benchmark_chat.py` | Prompt construction latency for follow-up chat with 0–100 source references |
| `benchmark_doi.py` | arXiv DOI extraction throughput at scales from 10 to 5,000 URLs |
| `benchmark_images.py` | Image search latency with cache acceleration measurement (warm vs. cold) |
| `benchmark_pdf.py` | PDF text extraction throughput across documents of 1–50 pages |
| `benchmark_pipeline.py` | End-to-end state management and knowledge graph construction performance |
| `benchmark_report.md` | Auto-generated report templates for results documentation |
| `test_data/sample_documents.json` | Curated document corpus for deterministic ranking validation |
| `test_data/sample_report.txt` | Multi-section mock report for summarization benchmarks |

#### Backend & Tools

- **`src/tools/chat.py`** *(New)* - Follow-up chat prompt construction with templated source citation formatting, role instructions, and structured answer marker generation.
- **`src/tools/doi.py`** *(New)* - arXiv ID extraction from heterogeneous URL patterns (abstract, PDF, versioned, query-parameter variants) via regex, with non-arXiv URL rejection.
- **`src/tools/images.py`** *(New)* - DuckDuckGo image search with 1-hour time-to-live (TTL) in-memory cache. Automatically fetches diagrams, charts, and figures relevant to research topics.
- **`src/tools/summarize.py`** *(New)* - Executive brief generation via section extraction (Executive Summary, Key Findings) without LLM invocation. Timeline extraction from report text and arXiv source metadata.
- **`src/api.py`** - Extended with endpoints for uploaded PDF content ingestion, image search, and chat completion streaming.

#### Frontend

- **`frontend/src/components/ChatPanel.tsx`** *(New)* - Follow-up chat interface with Markdown rendering, source citation badges, and streaming response display.
- **`frontend/src/components/ImageGallery.tsx`** *(New)* - Image gallery with lightbox navigation, grid layout, and automatic topic-based image/chart retrieval.
- **`frontend/src/components/ReportView.tsx`** - Major expansion: citation style switching (Inline, APA, MLA, Chicago, IEEE), executive brief panel, research timeline, PDF export via styled HTML generation, and text-to-speech with markdown stripping.
- **`frontend/src/components/ResearchForm.tsx`** - PDF upload zone with multi-file drag-and-drop support and content extraction confirmation.
- **`frontend/src/lib/api.ts`** - Extended with endpoints for upload, chat, image search, and report export.

#### Testing

- **`tests/test_chat.py`** *(New)* - Prompt construction correctness across 8 configuration combinations (report inclusion, question formatting, source list, answer markers, instruction adherence).
- **`tests/test_doi.py`** *(New)* - arXiv URL pattern matching across 19 test cases covering abs, PDF, versioned, HTTPS, case-insensitive, query-parameter, and non-arXiv URLs.
- **`tests/test_summarize.py`** *(New)* - Executive brief generation and timeline extraction with reports of 500–50,000 characters and 0–200 sources.
- **`tests/test_integration_upload.py`** *(New)* - End-to-end PDF upload and analysis pipeline integration tests.

#### Documentation

- **`README.md`** - Expanded with benchmark results tables, architecture diagram, complete feature matrix, repository structure map, related work citations, and BibTeX citation entry.

---

## 2026-05-26 - Documentation & Examples (Revision)

**Commit:** [`9c1de52`](https://github.com/royxforge/multi-agent-research-system/commit/9c1de52)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

A comprehensive documentation update pass: `.env.example` added with all supported provider configuration entries, CHANGELOG revised for chronological consistency, CONTRIBUTING.md and README.md refined for accuracy, formatting improvements, and expanded examples.

### Changes

- **`.env.example`** *(New)* - 78-line environment configuration template documenting all LLM providers (Ollama, OpenAI, Anthropic, Google, DeepSeek, Mistral, Groq, Perplexity, Together, OpenRouter), Tavily API key, and WebAuthn configuration.
- **`CHANGELOG.md`** - Revised for chronological accuracy with corrected dates and expanded descriptions.
- **`CONTRIBUTING.md`** - Refined guidelines with updated examples and formatting improvements.
- **`README.md`** - Expanded examples section, corrected provider references, improved formatting.

---

## 2026-05-26 - Contribution Guidelines & Documentation Enhancement

**Commit:** [`033ac4c`](https://github.com/royxforge/multi-agent-research-system/commit/033ac4c)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Introduced formal contribution guidelines and enhanced the README with a changelog reference and contribution instructions.

### Changes

- **`CONTRIBUTING.md`** *(New)* - Comprehensive 511-line contribution guide covering: code of conduct, development setup (backend and frontend), coding standards (Python and TypeScript), testing requirements, pull request process, commit message conventions, issue reporting templates, and feature request guidelines.
- **`CHANGELOG.md`** *(New)* - Initial changelog created with 146 lines documenting the project's history.
- **`README.md`** - Added changelog reference and contribution section links.

---

## 2026-05-26 - README Asset Restructuring

**Commit:** [`1316101`](https://github.com/royxforge/multi-agent-research-system/commit/1316101)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

README content expansion with new feature documentation, asset image restructuring (adding Features.png and SearchScreen.png, removing outdated screenshots), and improved project structure visualization.

### Changes

- **`README.md`** - Substantially rewritten: 205 additions, 100 deletions. Expanded feature descriptions, new structure visualization, and updated usage instructions.
- **`assets/Features.png`** *(New)* - Feature showcase screenshot.
- **`assets/SearchScreen.png`** *(New)* - Search interface screenshot.
- **`assets/HomeScreen.png`** - Updated to reflect UI changes.
- **`assets/OutputScreen.png`** - Removed (replaced by more representative screenshots).
- **`assets/ProcessingScreen.png`** - Removed (redundant).

---

## 2026-05-26 - Brand Identity & Theme Integration

**Commit:** [`e33bc05`](https://github.com/royxforge/multi-agent-research-system/commit/e33bc05)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Introduced a scalable brand icon component, integrated theme-aware color mapping into the knowledge graph visualization, implemented trending topics caching via the arXiv API, improved research queue management, and added document deduplication.

### Changes

#### Frontend - Components

- **`BrandIcon.tsx`** *(New)* - Scalable SVG brand icon component with theme-aware color variants, responsive sizing, and accessibility attributes.
- **`KnowledgeGraph.tsx`** - Theme-aware color integration for node and edge rendering. Color palette now responds to the application's theme state.
- **`Sidebar.tsx`** - Queue management improvements with visual indicators for pending, active, and completed research topics.
- **`Welcome.tsx`** - Trending topics section with arXiv API-backed data, cached to reduce redundant network requests.

#### Frontend - Core

- **`App.tsx`** - Integrated BrandIcon in navigation header. Research queue state management enhancements.
- **`favicon.ts`** *(New)* - Dynamic theme-aware favicon generation that swaps between light and dark variants based on system preference.
- **`lib/api.ts`** - Trending topics API integration with arXiv source and caching layer.
- **`hooks/useResearch.ts`** - Queue management refinements with document deduplication logic to prevent duplicate source entries across sequential research runs.

#### Backend

- **`src/api.py`** - Trending topics endpoint exposing arXiv daily submissions with configurable result counts and cache invalidation.

#### Infrastructure

- **`frontend/index.html`** - Updated metadata for brand consistency.

---

## 2026-05-26 - Welcome Page & Example Report

**Commit:** [`4d209c0`](https://github.com/royxforge/multi-agent-research-system/commit/4d209c0)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Introduced a marketing-oriented landing page with interactive metrics, an example report for zero-configuration exploration, and significant frontend component optimization. Backend improvements focused on report generation efficiency and source deduplication.

### Changes

#### Frontend - New Pages & Data

- **`frontend/src/pages/Welcome.tsx`** *(New)* - Full-screen marketing landing page (620 lines) featuring: animated hero section with system architecture visualization, interactive metric counters (papers analyzed, citations verified, models supported), feature showcase cards with icons, live demo prompt, and responsive layout with mobile optimization.
- **`frontend/src/lib/exampleReport.ts`** *(New)* - Pre-generated example research report demonstrating the system's output capabilities, enabling immediate frontend exploration without an active backend.

#### Frontend - Components

- **`ReportView.tsx`** - Major optimization pass (453 modifications): improved section rendering performance, enhanced citation style switching, streamlined report navigation.
- **`LoadingState.tsx`** - Enhanced progress visualization with agent-stage indicators and timing estimates.
- **`ResearchForm.tsx`** - Depth configuration UI refinements.
- **`KnowledgeGraph.tsx`** - Graph layout and interaction improvements.
- **`ErrorBoundary.tsx`** - Improved error messaging and recovery flows.
- **`Sidebar.tsx`** - Navigation and state display improvements.

#### Frontend - Core

- **`App.tsx`** - Route configuration for Welcome page (`/`) and research app (`/app`). Page transition management.
- **`main.tsx`** - React Router setup with BrowserRouter and route definitions.
- **`index.html`** - Updated entry point with Welcome page styling.
- **`index.css`** - Expanded design system with Welcome page component styles, animations, and responsive breakpoints.
- **`package.json`** - Added `react-router-dom` dependency.

#### Backend

- **`src/agents/nodes.py`** - Source deduplication logic to prevent redundant entries when multiple search queries return overlapping results.
- **`src/api.py`** - Report generation optimization with streamlined source processing.

---

## 2026-05-26 - General Improvements

**Commit:** [`5540d6c`](https://github.com/royxforge/multi-agent-research-system/commit/5540d6c)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

A substantial refactoring and feature addition release: 43 files changed, 2,669 insertions and 2,039 deletions. Introduced end-to-end encryption for API keys, WebAuthn biometric authentication, a redesigned sidebar, restructured frontend architecture (removal of legacy CSS and components), expanded backend tracing, and comprehensive state management improvements.

### Changes

#### Security & Authentication (Zero-Knowledge Architecture)

- **`frontend/src/lib/crypto.ts`** *(New)* - Client-side cryptography module (175 lines): AES-256-GCM symmetric encryption, PBKDF2 key derivation with configurable iterations, salt generation, and base64url encoding for secure API key storage.
- **`frontend/src/lib/webauthn.ts`** *(New)* - WebAuthn PRF (Pseudo-Random Function) biometric unlock (224 lines): browser-native authentication via fingerprint, Face ID, or Windows Hello for passphrase-protected decryption keys.
- **`src/utils/crypto.py`** *(New)* - Server-side cryptographic utilities (108 lines): secure key generation, hashing, and validation primitives.

#### Frontend - Component Refactoring

- **`Sidebar.tsx`** *(Rewritten)* - 576 modifications: collapsible navigation panel with passphrase management UI, research history display, and session controls. Integrated WebAuthn unlock flow and encrypted credential management.
- **`ResearchForm.tsx`** *(Rewritten)* - 555 modifications: redesigned topic input with depth selector (Fast/Balanced/Deep), source count slider (5–50), critic strictness toggle, LLM provider dropdown, and PDF upload zone with drag-and-drop.
- **`LoadingState.tsx`** *(Rewritten)* - 501 modifications: real-time progress dashboard showing agent stages (Researcher, Analyst, Critic), per-agent status indicators, timing estimates, and animated transitions.
- **`KnowledgeGraph.tsx`** *(Rewritten)* - 353 modifications: interactive force-directed graph with node selection, edge highlighting, zoom controls, and source link integration.
- **`ErrorBoundary.tsx`** - Enhanced error recovery with contextual fallback UI.
- **`ReportView.tsx`** - Report rendering and navigation improvements.

#### Frontend - Architecture

- **`App.tsx`** - Major restructuring (460 additions): context providers for research state and authentication, layout composition, and route management.
- **`index.css`** - 353 lines of new styles: design system tokens, component styles, responsive utilities.
- **`types.ts`** - Extended type definitions for encryption, authentication, and state management.
- **`hooks/useResearch.ts`** - Streamlined research state management.
- **Removed:** `App.css` (367 lines), `Header.tsx`, `HistorySidebar.tsx` - Legacy components eliminated in favor of consolidated `Sidebar.tsx`.

#### Backend

- **`src/agents/nodes.py`** - 202 modifications: enhanced agent state transitions, error handling, and tracing instrumentation.
- **`src/agents/state.py`** - Extended state schema with new fields for encryption metadata and authentication status.
- **`src/api.py`** - 60 modifications: new endpoints for credential management and authentication verification.
- **`src/config.py`** - Added WebAuthn configuration parameters and encryption settings.
- **`src/schemas.py`** - Extended Pydantic models for encrypted data exchange.
- **`src/tools/search.py`** - Search configuration and error handling improvements.
- **`src/utils/tracing.py`** - 99 modifications: expanded LangSmith tracing coverage with detailed agent execution traces and performance metrics.

#### Infrastructure

- **`.gitignore`** - Added entries for environment files, build artifacts, and IDE configurations.
- **`requirements.txt`** - Added `cryptography` and `pydantic-settings` dependencies.

---

## 2025-11-30 - Test Suite Expansion

**Commit:** [`aba1e77`](https://github.com/royxforge/multi-agent-research-system/commit/aba1e77)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Added comprehensive unit and integration tests for the core pipeline components: PDF extraction, document ranking, and citation validation. Established the testing infrastructure and patterns for all subsequent test development.

### Changes

#### Testing - New Test Suites

- **`tests/test_pdf.py`** *(New)* - PDF processing tests: text extraction accuracy across single/multi-page documents, reference section stripping, column layout detection, text-density validation, and binary content rejection.
- **`tests/test_ranking.py`** *(New)* - Document ranking tests: TF-IDF scoring correctness, query relevance ordering, edge-case handling for empty/identical/deduplicate documents, and performance benchmarks for 5–100 document sets.
- **`tests/test_validation.py`** *(New)* - Citation validation tests: source reference integrity checking, hallucinated citation detection, factual consistency verification, and strictness parameter behavior.

#### Backend - Evaluation

- **`src/evaluation/retrieval.py`** - Retrieval evaluation metrics: precision, recall, F1-score computation, mean reciprocal rank (MRR), and normalized discounted cumulative gain (NDCG).

#### Backend - Tools

- **`src/tools/pdf.py`** - Enhanced PDF extraction with reference section boundary detection and configurable truncation.
- **`src/tools/ranking.py`** - TF-IDF vectorization with cosine similarity ranking and deduplication.
- **`src/tools/validation.py`** - Citation validation with configurable strictness levels.
- **`src/tools/graph.py`** - Knowledge graph node/link extraction from research documents.

#### Backend - Core

- **`src/config.py`** - Added configuration for extraction limits, ranking parameters, and validation thresholds.
- **`src/agents/nodes.py`** - Agent node enhancements for research pipeline state management.
- **`src/agents/state.py`** - Extended state schema for research artifacts.
- **`src/api.py`** - Additional endpoints for research execution and state retrieval.
- **`src/utils/tracing.py`** - LangSmith tracing integration for agent execution monitoring.

#### Frontend

- **`App.tsx`, `KnowledgeGraph.tsx`, `LoadingState.tsx`, `ReportView.tsx`, `ResearchForm.tsx`** - Refinements to support new backend capabilities.
- **`types.ts`** - Type definitions for new data structures.
- **`index.css`, `tailwind.config.js`** - Styling adjustments for new UI components.

#### Documentation

- **`README.md`** - Updated with architecture description and usage instructions.
- **`assets/*.png`** - Updated screenshots reflecting current UI state.

---

## 2025-11-26 - Strictness Parameter & Streaming Research

**Commit:** [`5f4752c`](https://github.com/royxforge/multi-agent-research-system/commit/5f4752c)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Introduced the configurable critic strictness parameter, the interactive knowledge graph visualization with `react-force-graph-2d`, a dedicated error boundary component for resilience, streaming research via Server-Sent Events, and significantly enhanced loading state visualization.

### Changes

#### Backend - Streaming & Configuration

- **`src/agents/nodes.py`** - Agent node implementation with research, analysis, and critique stages. Integrated strictness parameter propagation through the agent pipeline.
- **`src/agents/state.py`** - Graph state schema defining research request, agent outputs, source documents, critique scores, and revision state.
- **`src/api.py`** - Server-Sent Events (SSE) streaming endpoint for real-time research progress updates. Research initiation and state retrieval endpoints.
- **`src/schemas.py`** - Pydantic models for request/response validation: research parameters, agent outputs, critique scores, and configuration schemas.

#### Frontend - New Components

- **`KnowledgeGraph.tsx`** *(New)* - Interactive force-directed graph visualization using `react-force-graph-2d`. Renders cited papers as nodes with click-to-open source links.
- **`ErrorBoundary.tsx`** *(New)* - React error boundary with fallback UI, error reporting, and recovery prompt.

#### Frontend - Enhanced Components

- **`LoadingState.tsx`** - Real-time progress dashboard with agent-stage indicators, progress bars, and timing estimates. SSE-driven live updates during research execution.
- **`ReportView.tsx`** - Structured report rendering with sections for Executive Summary, Key Findings, Critical Analysis, Methodological Notes, and Implications.
- **`ResearchForm.tsx`** - Depth selector (Fast/Balanced/Deep), source count configuration, critic strictness toggle, and LLM provider selection.
- **`App.tsx`** - Research state management integration with SSE stream handling.
- **`hooks/useResearch.ts`** - Custom hook for research state management: initiation, progress tracking, completion, and error handling.
- **`types.ts`** - TypeScript definitions for research parameters, agent states, source documents, and critique scores.

#### Frontend - Dependencies

- **`package.json`** - Added `react-force-graph-2d`, `framer-motion`, `lucide-react`, `react-markdown` dependencies for graph visualization, animations, icons, and Markdown rendering.

#### Documentation

- **`README.md`** - Installation instructions, configuration guide, and usage documentation.

---

## 2025-11-25 - Initial Commit

**Commit:** [`f7361a5`](https://github.com/royxforge/multi-agent-research-system/commit/f7361a5)  
**Author:** Sourav Roy ([royxforge@gmail.com](mailto:royxforge@gmail.com))

### Summary

Repository inception. The complete foundational codebase was committed, establishing the full-stack architecture comprising a Python/FastAPI backend with LangGraph-based multi-agent orchestration and a React 19/TypeScript frontend with Vite build tooling.

### Changes

#### Project Structure (47 files, 7,835 insertions)

##### Backend - Application Core

- **`run.py`** - Backend entry point: uvicorn server launcher with hot-reload, CORS configuration, and port binding.
- **`requirements.txt`** - Python dependency specification: FastAPI, LangGraph, LangChain, PyMuPDF, uvicorn, Tavily, DuckDuckGo Search, structlog, Pydantic, aiohttp, NetworkX, and pytest.
- **`src/__init__.py`** - Package initialization.
- **`src/api.py`** - FastAPI application with route definitions, CORS middleware, SSE streaming support, and request validation.
- **`src/config.py`** - Environment-based configuration via Pydantic Settings: LLM provider selection (Ollama local / OpenAI cloud), Tavily API key, server settings, and model parameters.
- **`src/schemas.py`** - Pydantic data models: research requests, source documents, agent outputs, critique scores, and configuration options.

##### Backend - Agent System

- **`src/agents/__init__.py`** - Agent module initialization.
- **`src/agents/graph.py`** - LangGraph workflow definition: directed acyclic graph specifying agent execution order, state transitions, and revision loop configuration.
- **`src/agents/nodes.py`** - Agent node functions: Researcher (source gathering), Analyst (synthesis drafting), Critic (hallucination detection and citation validation), with revision pass support.
- **`src/agents/state.py`** - Graph state schema: TypedDict defining the complete execution state, including research topic, sources, report drafts, critique scores, and iteration counters.

##### Backend - Tools

- **`src/tools/__init__.py`** - Tools module initialization.
- **`src/tools/search.py`** - Parallel search orchestration: Tavily API primary search with DuckDuckGo fallback, academic domain filtering (arxiv.org, .edu, .ac.uk), and result deduplication.
- **`src/tools/pdf.py`** - PDF download and text extraction via PyMuPDF: URL-to-local download, text extraction with layout preservation, and configurable character limits.
- **`src/tools/ranking.py`** - Source relevance ranking: TF-IDF vectorization, cosine similarity scoring, and ranked result ordering.
- **`src/tools/validation.py`** - Citation validation: source reference integrity checking, hallucinated citation detection, and citation-to-source mapping.
- **`src/tools/graph.py`** - Knowledge graph construction: node extraction (paper titles, authors, URLs) and edge detection (citation relationships, thematic connections).

##### Backend - Utilities

- **`src/utils/__init__.py`** - Utilities module initialization.
- **`src/utils/tracing.py`** - LangSmith tracing configuration for agent execution monitoring and debugging.

##### Backend - Evaluation

- **`src/evaluation/__init__.py`** - Evaluation module initialization.
- **`src/evaluation/retrieval.py`** - Retrieval quality metrics: precision, recall, F1-score, and ranking evaluation utilities.

##### Frontend - Build Configuration

- **`frontend/package.json`** - NPM configuration with React 19, Vite 7, TypeScript 5.9, Tailwind CSS v4, Framer Motion, and development tooling.
- **`frontend/vite.config.ts`** - Vite build configuration with React plugin, path aliases, and dev server settings.
- **`frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/tsconfig.node.json`** - TypeScript compiler configuration with strict mode, path resolution, and type definitions.
- **`frontend/eslint.config.js`** - ESLint configuration with TypeScript and React-Hooks plugins.
- **`frontend/postcss.config.js`** - PostCSS configuration with Tailwind CSS and autoprefixer.
- **`frontend/tailwind.config.js`** - Tailwind CSS configuration with content paths, theme extensions, and plugin settings.
- **`frontend/index.html`** - HTML entry point with Vite script injection and metadata.

##### Frontend - Application Code

- **`frontend/src/main.tsx`** - React application entry point with StrictMode and BrowserRouter.
- **`frontend/src/App.tsx`** - Root application component with research form, loading state, report view, and knowledge graph layout composition.
- **`frontend/src/index.css`** - Global styles with Tailwind directives, custom design tokens, and responsive utilities.
- **`frontend/src/types.ts`** - TypeScript type definitions for research parameters, agent state, source documents, and application configuration.

##### Frontend - Components

- **`frontend/src/components/Header.tsx`** - Application header with logo, navigation, and provider selection.
- **`frontend/src/components/HistorySidebar.tsx`** - Research history sidebar with previous topic listing and reload capability.
- **`frontend/src/components/ResearchForm.tsx`** - Topic input form with depth configuration, source count selection, and submission.
- **`frontend/src/components/LoadingState.tsx`** - Research progress visualization with agent-stage indicators.
- **`frontend/src/components/ReportView.tsx`** - Structured report viewer with section rendering and citation display.
- **`frontend/src/components/KnowledgeGraph.tsx`** - Citation graph visualization container.
- **`frontend/src/components/Sidebar.tsx`** - Application sidebar with navigation and configuration.

##### Frontend - Styles & Assets

- **`frontend/src/App.css`** - Application-level styles.

##### Documentation & Configuration

- **`README.md`** - Project overview, architecture description, installation instructions, and usage guide.
- **`LICENSE`** - MIT License.
- **`.gitignore`** - Git exclusion rules for Python virtual environments, Node modules, build artifacts, IDE configurations, and environment files.

##### Assets

- **`assets/HomeScreen.png`** - Home screen screenshot.
- **`assets/OutputScreen.png`** - Output report screenshot.
- **`assets/ProcessingScreen.png`** - Processing visualization screenshot.

---
