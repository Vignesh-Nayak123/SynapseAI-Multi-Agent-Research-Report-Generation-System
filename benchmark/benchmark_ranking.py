"""
Benchmark: Document Ranking & Text Chunking
Tests TF-IDF ranking speed, accuracy, and text chunking throughput.
"""

import time
import json
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.ranking import rank_documents, chunk_text


def load_documents():
    path = os.path.join(os.path.dirname(__file__), "test_data", "sample_documents.json")
    with open(path) as f:
        return json.load(f)


def benchmark_chunking(sizes: list[int], overlap_ratio: float = 0.1):
    """Benchmark text chunking with various chunk sizes."""
    results = []
    # Generate large text
    base_text = " ".join(["quantum computing research advances " * 100])
    
    for chunk_size in sizes:
        overlap = int(chunk_size * overlap_ratio)
        trials = []
        for _ in range(20):
            start = time.perf_counter()
            chunks = chunk_text(base_text, chunk_size=chunk_size, overlap=overlap)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results.append({
            "chunk_size": chunk_size,
            "overlap": overlap,
            "num_chunks": len(chunks),
            "total_chars": sum(len(c) for c in chunks),
            "avg_time_ms": round(statistics.mean(trials) * 1000, 3),
            "std_ms": round(statistics.stdev(trials) * 1000, 3) if len(trials) > 1 else 0,
            "throughput_chars_per_sec": int(len(base_text) / statistics.mean(trials)),
        })
    return results


def benchmark_ranking(sizes: list[int]):
    """Benchmark ranking with varying document counts."""
    docs = load_documents()
    queries = [
        "superconducting qubit gate fidelity quantum computing",
        "trapped ion coherence time quantum memory",
        "quantum error correction surface code logical qubit",
        "quantum key distribution QKD fiber optic",
        "quantum machine learning neural networks speedup",
    ]
    
    results = []
    for size in sizes:
        subset = (docs * (size // len(docs) + 1))[:size]
        for query in queries:
            trials = []
            for _ in range(10):
                start = time.perf_counter()
                ranked = rank_documents(query, subset, top_k=min(5, size))
                elapsed = time.perf_counter() - start
                trials.append(elapsed)
            
            results.append({
                "num_documents": size,
                "query": query[:40] + "...",
                "avg_time_ms": round(statistics.mean(trials) * 1000, 3),
                "std_ms": round(statistics.stdev(trials) * 1000, 3) if len(trials) > 1 else 0,
                "top_result": ranked[0]["source"] if ranked else "none",
                "top_score": round(ranked[0].get("_score", 0), 4) if ranked else 0,
            })
    
    return results


def benchmark_ranking_accuracy():
    """Test that ranking ranks relevant documents higher."""
    docs = load_documents()
    query = "quantum computing artificial intelligence"
    ranked = rank_documents(query, docs, top_k=len(docs))
    
    results = []
    for i, doc in enumerate(ranked):
        results.append({
            "rank": i + 1,
            "source": doc["source"].split("/")[-1],
            "content_preview": doc["content"][:60] + "...",
        })
    return results


def run():
    print("=" * 60)
    print("BENCHMARK: Document Ranking & Text Chunking")
    print("=" * 60)
    
    # Chunking benchmarks
    print("\n--- Chunking Throughput ---")
    chunk_results = benchmark_chunking([250, 500, 1000, 2000, 4000])
    for r in chunk_results:
        print(f"  chunk_size={r['chunk_size']:>5} | overlap={r['overlap']:>3} | "
              f"{r['num_chunks']:>3} chunks | {r['avg_time_ms']:>7.3f}ms | "
              f"{r['throughput_chars_per_sec']:,} chars/s")
    
    # Ranking speed benchmarks
    print("\n--- Ranking Speed (varying document counts) ---")
    rank_results = benchmark_ranking([5, 10, 25, 50, 100])
    for r in rank_results:
        print(f"  docs={r['num_documents']:>3} | {r['avg_time_ms']:>8.3f}ms ± {r['std_ms']:>5.3f}ms | "
              f"top={r['top_result'].split('/')[-1][:25]}")
    
    # Ranking accuracy
    print("\n--- Ranking Accuracy (query: 'quantum computing artificial intelligence') ---")
    accuracy_results = benchmark_ranking_accuracy()
    for r in accuracy_results:
        print(f"  Rank {r['rank']:>2}: {r['source'][:20]:20s} | {r['content_preview']}")
    
    return {
        "chunking": chunk_results,
        "ranking_speed": rank_results,
        "ranking_accuracy": accuracy_results,
        "metrics": {
            "avg_chunking_time_ms": statistics.mean([r["avg_time_ms"] for r in chunk_results]),
            "avg_ranking_time_ms": statistics.mean([r["avg_time_ms"] for r in rank_results]),
        }
    }


if __name__ == "__main__":
    run()
