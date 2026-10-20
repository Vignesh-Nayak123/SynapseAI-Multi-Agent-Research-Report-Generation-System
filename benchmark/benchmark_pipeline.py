"""
Benchmark: Pipeline & State Management
Tests agent state construction, graph creation, and coordination overhead.
"""

import time
import json
import statistics
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.state import AgentState
from src.agents.graph import build_research_graph
from src.schemas import ResearchRequest, ResearchResponse, ImageResult
from src.tools.graph import build_citation_graph
from src.config import get_settings


def benchmark_state_construction():
    """Benchmark AgentState construction performance."""
    results = {}
    
    # Basic state construction
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        state: AgentState = {
            "query": "Quantum computing research",
            "max_depth": 3,
            "max_search_results": 10,
            "provider": "ollama",
            "job_id": str(uuid.uuid4()),
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
            "metadata": {
                "job_id": str(uuid.uuid4()),
                "start_time": datetime.utcnow().isoformat(),
                "model": "llama3",
                "provider": "ollama",
                "retrieval_stats": {},
                "pdf_stats": {},
            }
        }
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["basic_state_ms"] = round(statistics.mean(trials) * 1000, 4)
    
    # State with documents
    trials = []
    for _ in range(500):
        start = time.perf_counter()
        state: AgentState = {
            "query": "Quantum computing",
            "documents": [
                {"source": f"https://arxiv.org/abs/2301.{i:05d}", "content": "A" * 500}
                for i in range(50)
            ],
            "draft": "# Draft\n\nThis is a sample draft." * 100,
            "critique": {"score": 7.5, "hallucination_score": 0.2, "is_vague": False,
                        "feedback": "Good draft, but needs more citations.", "needs_revision": False},
            "revision_count": 1,
            "job_id": str(uuid.uuid4()),
        }
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["full_state_ms"] = round(statistics.mean(trials) * 1000, 4)
    
    return results


def benchmark_graph_construction():
    """Benchmark knowledge graph construction from documents."""
    results = {}
    
    # Varying document counts
    for num_docs in [0, 5, 10, 25, 50, 100]:
        documents = []
        for i in range(num_docs):
            documents.append({
                "source": f"https://arxiv.org/abs/2301.{i:05d}",
                "content": f"Quantum computing research paper {i}. " * 50,
            })
        
        trials = []
        for _ in range(20):
            start = time.perf_counter()
            graph = build_citation_graph(documents)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results[f"graph_{num_docs}_docs_ms"] = {
            "avg_ms": round(statistics.mean(trials) * 1000, 3),
            "std_ms": round(statistics.stdev(trials) * 1000, 3) if len(trials) > 1 else 0,
            "num_nodes": len(graph.get("nodes", [])),
            "num_links": len(graph.get("links", [])),
        }
    
    return results


def benchmark_response_construction():
    """Benchmark ResearchResponse construction."""
    results = {}
    
    for num_sources in [5, 20, 50, 100]:
        trials = []
        for _ in range(100):
            start = time.perf_counter()
            response = ResearchResponse(
                final_report="# Report\n\n" + "Content. " * 500,
                sources=[f"https://arxiv.org/abs/2301.{i:05d}" for i in range(num_sources)],
                topic="Quantum Computing",
                graph_data={"nodes": [], "links": []},
                images=[ImageResult(title=f"Image {i}", image_url=f"https://example.com/{i}.jpg",
                                   source_url=f"https://example.com/{i}", source_domain="example.com")
                       for i in range(8)],
                graphs=[],
            )
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results[f"response_{num_sources}_sources_ms"] = round(statistics.mean(trials) * 1000, 4)
    
    return results


def benchmark_serialization():
    """Benchmark serialization of research response."""
    response = ResearchResponse(
        final_report="# Report\n\n" + "Content. " * 1000,
        sources=[f"https://arxiv.org/abs/2301.{i:05d}" for i in range(50)],
        topic="Quantum Computing",
        graph_data={"nodes": [{"id": f"node_{i}", "label": f"Paper {i}"} for i in range(20)],
                   "links": [{"source": f"node_{i}", "target": f"node_{(i+1) % 20}"} for i in range(20)]},
        images=[ImageResult(title=f"Image {i}", image_url=f"https://example.com/{i}.jpg",
                           source_url=f"https://example.com/{i}", source_domain="example.com")
               for i in range(8)],
        graphs=[],
    )
    
    results = {}
    
    # Model dump
    trials = []
    for _ in range(100):
        start = time.perf_counter()
        data = response.model_dump()
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["model_dump_ms"] = round(statistics.mean(trials) * 1000, 4)
    
    # JSON serialization
    trials = []
    for _ in range(100):
        data = response.model_dump()
        start = time.perf_counter()
        json_str = json.dumps(data)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["json_serialize_ms"] = round(statistics.mean(trials) * 1000, 4)
    
    # Full pipeline (model_dump + json)
    trials = []
    for _ in range(100):
        start = time.perf_counter()
        data = response.model_dump()
        json_str = json.dumps(data)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["full_serialization_ms"] = round(statistics.mean(trials) * 1000, 4)
    results["json_size_bytes"] = len(json_str)
    
    return results


def run():
    print("=" * 60)
    print("BENCHMARK: Pipeline & State Management")
    print("=" * 60)
    
    print("\n--- State Construction ---")
    state_results = benchmark_state_construction()
    for k, v in state_results.items():
        print(f"  {k}: {v:.4f}ms")
    
    print("\n--- Knowledge Graph Construction ---")
    graph_results = benchmark_graph_construction()
    for k, v in sorted(graph_results.items()):
        print(f"  {k}: {v['avg_ms']:.3f}ms ± {v['std_ms']:.3f}ms ({v['num_nodes']} nodes, {v['num_links']} links)")
    
    print("\n--- Response Construction ---")
    resp_results = benchmark_response_construction()
    for k, v in resp_results.items():
        print(f"  {k}: {v:.4f}ms")
    
    print("\n--- Serialization ---")
    ser_results = benchmark_serialization()
    for k, v in ser_results.items():
        if not k.endswith("_bytes"):
            print(f"  {k}: {v:.4f}ms")
    print(f"  json_output_size: {ser_results.get('json_size_bytes', 0):,} bytes")
    
    return {
        "state_construction": state_results,
        "graph_construction": graph_results,
        "response_construction": resp_results,
        "serialization": ser_results,
    }


if __name__ == "__main__":
    run()
