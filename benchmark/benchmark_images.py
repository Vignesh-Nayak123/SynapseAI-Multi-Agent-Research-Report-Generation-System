"""
Benchmark: Image Search Cache & Search Latency
Tests cache hit/miss, query normalization, DDGS image search latency,
graph search, and cache-accelerated throughput.
"""

import time
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.images import _normalize_query, clear_image_cache, _IMAGE_CACHE, search_related_images, search_related_graphs


def benchmark_cache_hit_miss():
    """Benchmark cache hit vs miss performance (cache operations only, not network)."""
    results = {}
    
    # Test cache set performance
    clear_image_cache()
    test_data = [{"title": f"Image {i}", "image": f"https://example.com/img{i}.jpg", 
                  "url": f"https://example.com/page{i}"} for i in range(20)]
    
    trials_set = []
    for _ in range(100):
        start = time.perf_counter()
        _IMAGE_CACHE["test_query"] = (time.time(), test_data)
        elapsed = time.perf_counter() - start
        trials_set.append(elapsed)
    results["cache_set_20_items_ms"] = round(statistics.mean(trials_set) * 1000, 4)
    
    # Test cache get (hit)
    trials_get = []
    for _ in range(100):
        start = time.perf_counter()
        entry = _IMAGE_CACHE.get("test_query")
        elapsed = time.perf_counter() - start
        trials_get.append(elapsed)
    results["cache_get_hit_ms"] = round(statistics.mean(trials_get) * 1000, 4)
    
    # Test cache get (miss)
    trials_miss = []
    for _ in range(100):
        start = time.perf_counter()
        entry = _IMAGE_CACHE.get("nonexistent_query")
        elapsed = time.perf_counter() - start
        trials_miss.append(elapsed)
    results["cache_get_miss_ms"] = round(statistics.mean(trials_miss) * 1000, 4)
    
    # Test clear cache
    trials_clear = []
    for _ in range(100):
        _IMAGE_CACHE["temp"] = (time.time(), [])
        start = time.perf_counter()
        clear_image_cache()
        elapsed = time.perf_counter() - start
        trials_clear.append(elapsed)
    results["cache_clear_ms"] = round(statistics.mean(trials_clear) * 1000, 4)
    
    return results


def benchmark_query_normalization():
    """Benchmark query normalization performance."""
    queries = [
        "Quantum Computing Research",
        "  quantum  computing  research  ",
        "QUANTUM COMPUTING RESEARCH!@#$",
        "What is the impact of quantum computing on machine learning?",
        "A very long query about quantum computing with multiple spaces  and  special   chars!!!",
    ]
    
    results = []
    for query in queries:
        trials = []
        for _ in range(1000):
            start = time.perf_counter()
            normalized = _normalize_query(query)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results.append({
            "original_length": len(query),
            "normalized": normalized,
            "avg_time_ms": round(statistics.mean(trials) * 1000, 4),
            "std_ms": round(statistics.stdev(trials) * 1000, 4) if len(trials) > 1 else 0,
        })
    
    return results


def benchmark_search_latency():
    """Benchmark actual DDGS image search call latency (network-dependent).
    
    Measures cold-call (first request to DDGS) vs warm-call (cached) latency.
    These numbers are highly dependent on network conditions and DDGS availability.
    """
    clear_image_cache()
    results = {}
    
    queries = [
        "quantum computing",
        "machine learning",
        "neural network architecture diagram",
    ]
    
    # --- Image search cold latency (first call, no cache) ---
    cold_times = []
    for q in queries:
        clear_image_cache()
        start = time.perf_counter()
        try:
            _ = search_related_images(q, max_results=4)
            elapsed = time.perf_counter() - start
            cold_times.append(elapsed)
        except Exception as e:
            print(f"  [SKIP] Cold search '{q}' failed (network issue): {e}")
    
    if cold_times:
        results["image_search_cold_avg_s"] = round(statistics.mean(cold_times), 3)
        results["image_search_cold_std_s"] = round(statistics.stdev(cold_times), 3) if len(cold_times) > 1 else 0
        results["image_search_cold_min_s"] = round(min(cold_times), 3)
        results["image_search_cold_max_s"] = round(max(cold_times), 3)
    else:
        results["image_search_cold_avg_s"] = "N/A (network down)"
        results["image_search_cold_std_s"] = "N/A"
        results["image_search_cold_min_s"] = "N/A"
        results["image_search_cold_max_s"] = "N/A"
    
    # --- Image search warm latency (cached hit) ---
    warm_times = []
    for q in queries:
        # Populate cache by making the call first
        try:
            _ = search_related_images(q, max_results=4)
            # Now it's cached -- measure the cache hit
            start = time.perf_counter()
            for _ in range(20):
                _ = search_related_images(q, max_results=4)
            elapsed = (time.perf_counter() - start) / 20
            warm_times.append(elapsed)
        except Exception:
            pass
    
    if warm_times:
        results["image_search_warm_avg_ms"] = round(statistics.mean(warm_times) * 1000, 3)
        results["image_search_warm_std_ms"] = round(statistics.stdev(warm_times) * 1000, 3) if len(warm_times) > 1 else 0
    else:
        results["image_search_warm_avg_ms"] = "N/A"
        results["image_search_warm_std_ms"] = "N/A"
    
    # --- Graph search cold latency ---
    clear_image_cache()
    cold_graph_times = []
    for q in queries:
        clear_image_cache()
        start = time.perf_counter()
        try:
            _ = search_related_graphs(q, max_results=4)
            elapsed = time.perf_counter() - start
            cold_graph_times.append(elapsed)
        except Exception as e:
            print(f"  [SKIP] Graph search '{q}' failed (network issue): {e}")
    
    if cold_graph_times:
        results["graph_search_cold_avg_s"] = round(statistics.mean(cold_graph_times), 3)
        results["graph_search_cold_std_s"] = round(statistics.stdev(cold_graph_times), 3) if len(cold_graph_times) > 1 else 0
    else:
        results["graph_search_cold_avg_s"] = "N/A (network down)"
        results["graph_search_cold_std_s"] = "N/A"
    
    # --- Cache acceleration ratio ---
    if isinstance(results.get("image_search_cold_avg_s"), (int, float)) and \
       isinstance(results.get("image_search_warm_avg_ms"), (int, float)):
        cold_ms = results["image_search_cold_avg_s"] * 1000
        warm_ms = results["image_search_warm_avg_ms"]
        if warm_ms > 0:
            results["cache_acceleration_ratio"] = round(cold_ms / warm_ms, 1)
    
    return results


def benchmark_batch_throughput():
    """Benchmark cache throughput with repeated queries (simulates real usage)."""
    clear_image_cache()
    results = {}
    
    try:
        # Single cold query to populate cache
        search_related_images("quantum computing research", max_results=8)
        
        # Now measure cache-only throughput
        trials = []
        for _ in range(50):
            start = time.perf_counter()
            _ = search_related_images("quantum computing research", max_results=8)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results["cache_throughput_50_runs_ms"] = round(statistics.mean(trials) * 1000, 4)
        results["cache_throughput_50_runs_total_s"] = round(sum(trials), 4)
    except Exception as e:
        print(f"  [SKIP] Throughput benchmark failed: {e}")
        results["cache_throughput_50_runs_ms"] = "N/A (network needed)"
    
    return results


def run():
    print("=" * 60)
    print("BENCHMARK: Image Search Cache & Search Latency")
    print("=" * 60)
    
    print("\n--- Cache Operation Speed ---")
    cache_results = benchmark_cache_hit_miss()
    for k, v in cache_results.items():
        print(f"  {k}: {v:.4f}ms")
    
    print("\n--- Query Normalization ---")
    norm_results = benchmark_query_normalization()
    for r in norm_results:
        print(f"  len={r['original_length']:>3} -> '{r['normalized'][:40]:40s}' | "
              f"{r['avg_time_ms']:.4f}ms +/-{r['std_ms']:.4f}ms")
    
    print("\n--- Search Latency (cold DDGS calls, network-dependent) ---")
    latency_results = benchmark_search_latency()
    for k, v in latency_results.items():
        print(f"  {k}: {v}")
    
    print("\n--- Cache Throughput ---")
    throughput_results = benchmark_batch_throughput()
    for k, v in throughput_results.items():
        print(f"  {k}: {v}")
    
    # Clear cache after benchmarks
    clear_image_cache()
    
    return {
        "cache_operations": cache_results,
        "query_normalization": norm_results,
        "search_latency": latency_results,
        "cache_throughput": throughput_results,
    }


if __name__ == "__main__":
    run()
