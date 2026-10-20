"""
Benchmark: DOI Resolution
Tests arXiv ID extraction speed and DOI resolution performance.
"""

import time
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.doi import extract_arxiv_ids


def generate_arxiv_urls(count: int, valid_ratio: float = 0.8) -> list[str]:
    """Generate a mix of arXiv and non-arXiv URLs."""
    urls = []
    for i in range(count):
        if i / count < valid_ratio:
            # Valid arXiv URL
            year = 2000 + (i % 30)
            id_num = (i * 12345) % 100000
            if i % 3 == 0:
                urls.append(f"https://arxiv.org/abs/{year}.{id_num:05d}")
            elif i % 3 == 1:
                urls.append(f"https://arxiv.org/pdf/{year}.{id_num:05d}.pdf")
            else:
                urls.append(f"https://arxiv.org/abs/{year}.{id_num:05d}v{i % 5}")
        else:
            # Non-arXiv URL
            urls.append(f"https://example.com/papers/{i}.pdf")
    return urls


def benchmark_extraction():
    """Benchmark arXiv ID extraction with varying URL counts."""
    results = []
    
    for count in [10, 50, 100, 500, 1000, 5000]:
        urls = generate_arxiv_urls(count, valid_ratio=0.8)
        
        trials = []
        for _ in range(30):
            start = time.perf_counter()
            ids = extract_arxiv_ids(urls)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results.append({
            "num_urls": count,
            "num_ids_found": len(ids),
            "extraction_ratio": round(len(ids) / count, 3),
            "avg_time_ms": round(statistics.mean(trials) * 1000, 4),
            "std_ms": round(statistics.stdev(trials) * 1000, 4) if len(trials) > 1 else 0,
            "throughput_urls_per_sec": int(count / statistics.mean(trials)),
        })
    
    return results


def benchmark_extraction_patterns():
    """Benchmark various arXiv URL patterns."""
    test_cases = [
        ("abs URL", ["https://arxiv.org/abs/2301.12345"]),
        ("pdf URL", ["https://arxiv.org/pdf/2301.12345.pdf"]),
        ("versioned URL", ["https://arxiv.org/abs/2301.12345v3"]),
        ("HTTPS abs", ["https://arxiv.org/abs/2301.12345"]),
        ("case insensitive", ["https://ARXIV.ORG/ABS/2301.12345"]),
        ("query params", ["https://arxiv.org/abs/2301.12345?utm_source=test"]),
        ("mixed batch", [
            "https://arxiv.org/abs/2301.12345",
            "https://arxiv.org/pdf/2302.67890.pdf",
            "https://example.com/paper",
            "https://arxiv.org/abs/2303.11111v2",
        ]),
        ("non-arxiv only", ["https://example.com/paper", "https://google.com"]),
        ("empty list", []),
    ]
    
    results = []
    for name, urls in test_cases:
        start = time.perf_counter()
        for _ in range(1000):
            ids = extract_arxiv_ids(urls)
        elapsed = time.perf_counter() - start
        
        ids = extract_arxiv_ids(urls)
        results.append({
            "pattern": name,
            "num_input": len(urls),
            "num_output": len(ids),
            "avg_time_ms": round((elapsed / 1000) * 1000, 4),
        })
    
    return results


def benchmark_cache_efficiency():
    """Benchmark the DOI cache (in-memory)."""
    test_ids = ["2301.12345", "2302.67890", "2303.11111", "2304.22222", "2305.33333"]
    urls = [f"https://arxiv.org/abs/{aid}" for aid in test_ids]
    
    results = {}
    
    # First call (cache miss - but extraction is always fast, cache is for resolution)
    start = time.perf_counter()
    for _ in range(100):
        extract_arxiv_ids(urls)
    elapsed = time.perf_counter() - start
    results["extraction_100_runs_ms"] = round((elapsed / 100) * 1000, 4)
    
    # Large batch
    big_urls = generate_arxiv_urls(1000)
    start = time.perf_counter()
    for _ in range(100):
        extract_arxiv_ids(big_urls)
    elapsed = time.perf_counter() - start
    results["large_batch_1000_urls_100_runs_ms"] = round((elapsed / 100) * 1000, 4)
    
    return results


def run():
    print("=" * 60)
    print("BENCHMARK: DOI Resolution (arXiv ID Extraction)")
    print("=" * 60)
    
    print("\n--- Extraction Speed (varying URL counts) ---")
    extract_results = benchmark_extraction()
    for r in extract_results:
        print(f"  urls={r['num_urls']:>5} | found={r['num_ids_found']:>4} ids | "
              f"{r['avg_time_ms']:>8.4f}ms ± {r['std_ms']:>5.4f}ms | "
              f"{r['throughput_urls_per_sec']:,} urls/s")
    
    print("\n--- URL Pattern Support ---")
    pattern_results = benchmark_extraction_patterns()
    for r in pattern_results:
        passed = r["num_output"] > 0 or r["num_input"] == 0
        status = "[OK]" if passed else "[FAIL]"
        try:
            print(f"  {status} {r['pattern']:20s} | {r['num_input']}->{r['num_output']} ids | "
                  f"{r['avg_time_ms']:.4f}ms")
        except UnicodeEncodeError:
            safe_status = "PASS" if passed else "FAIL"
            print(f"  [{safe_status}] {r['pattern']:20s} | {r['num_input']}->{r['num_output']} ids | "
                  f"{r['avg_time_ms']:.4f}ms")
    
    print("\n--- Cache & Batch Efficiency ---")
    cache_results = benchmark_cache_efficiency()
    for k, v in cache_results.items():
        print(f"  {k}: {v:.4f}ms")
    
    return {
        "extraction_speed": extract_results,
        "pattern_support": pattern_results,
        "cache_efficiency": cache_results,
    }


if __name__ == "__main__":
    run()
