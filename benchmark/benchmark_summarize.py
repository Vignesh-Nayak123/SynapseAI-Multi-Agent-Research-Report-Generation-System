"""
Benchmark: Summarization & Timeline Extraction
Tests executive brief generation and research timeline extraction speed and accuracy.
"""

import time
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.summarize import generate_simple_explanation, generate_timeline_data


def load_sample_report():
    path = os.path.join(os.path.dirname(__file__), "test_data", "sample_report.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()


def benchmark_generate_explanation(report_sizes: list[int]):
    """Benchmark executive brief generation with varying report sizes."""
    results = []
    full_report = load_sample_report()
    
    for size in report_sizes:
        # Adjust report to target size by repeating content
        repeats = max(1, size // len(full_report))
        report = (full_report * repeats)[:size]
        
        trials = []
        for _ in range(30):
            start = time.perf_counter()
            brief = generate_simple_explanation(report)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results.append({
            "report_size_chars": size,
            "brief_size_chars": len(brief),
            "compression_ratio": round(len(brief) / size, 3) if size > 0 else 0,
            "avg_time_ms": round(statistics.mean(trials) * 1000, 3),
            "std_ms": round(statistics.stdev(trials) * 1000, 3) if len(trials) > 1 else 0,
        })
    
    return results


def benchmark_generate_timeline():
    """Benchmark timeline extraction from reports and sources."""
    report = load_sample_report()
    sources = [
        "https://arxiv.org/abs/2020.12345",
        "https://arxiv.org/abs/2021.67890",
        "https://arxiv.org/abs/2022.11111",
        "https://arxiv.org/abs/2023.22222",
        "https://arxiv.org/abs/2024.33333",
        "https://arxiv.org/abs/2025.44444",
    ]
    
    results = {}
    
    # Timeline from report only
    trials = []
    for _ in range(30):
        start = time.perf_counter()
        timeline = generate_timeline_data(report, [])
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["report_only_ms"] = round(statistics.mean(trials) * 1000, 3)
    results["report_only_std_ms"] = round(statistics.stdev(trials) * 1000, 3)
    results["report_only_entries"] = len(timeline)
    
    # Timeline from sources only
    trials = []
    for _ in range(30):
        start = time.perf_counter()
        timeline = generate_timeline_data("", sources)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["sources_only_ms"] = round(statistics.mean(trials) * 1000, 3)
    results["sources_only_std_ms"] = round(statistics.stdev(trials) * 1000, 3)
    results["sources_only_entries"] = len(timeline)
    
    # Timeline from both
    trials = []
    for _ in range(30):
        start = time.perf_counter()
        timeline = generate_timeline_data(report, sources)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["combined_ms"] = round(statistics.mean(trials) * 1000, 3)
    results["combined_std_ms"] = round(statistics.stdev(trials) * 1000, 3)
    results["combined_entries"] = len(timeline)
    
    # Large source lists
    many_sources = [f"https://arxiv.org/abs/{y}.{i:05d}" for y in range(2020, 2025) for i in range(1, 51)]
    trials = []
    for _ in range(10):
        start = time.perf_counter()
        timeline = generate_timeline_data(report, many_sources)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["many_sources_200_ms"] = round(statistics.mean(trials) * 1000, 3)
    results["many_sources_200_std_ms"] = round(statistics.stdev(trials) * 1000, 3)
    results["many_sources_200_entries"] = len(timeline)
    
    return results


def benchmark_edge_cases():
    """Benchmark edge cases for summarization."""
    results = {}
    
    # Empty report
    start = time.perf_counter()
    for _ in range(100):
        generate_simple_explanation("")
    elapsed = time.perf_counter() - start
    results["empty_report_ms"] = round((elapsed / 100) * 1000, 4)
    
    # Tiny report
    start = time.perf_counter()
    for _ in range(100):
        generate_simple_explanation("# Just a Title")
    elapsed = time.perf_counter() - start
    results["tiny_report_ms"] = round((elapsed / 100) * 1000, 4)
    
    # Huge report
    big_report = load_sample_report() * 100
    start = time.perf_counter()
    for _ in range(10):
        generate_simple_explanation(big_report)
    elapsed = time.perf_counter() - start
    results["large_report_100x_ms"] = round((elapsed / 10) * 1000, 3)
    
    return results


def run():
    print("=" * 60)
    print("BENCHMARK: Summarization & Timeline Extraction")
    print("=" * 60)
    
    print("\n--- Executive Brief Generation ---")
    brief_results = benchmark_generate_explanation([500, 1000, 5000, 10000, 50000])
    for r in brief_results:
        print(f"  report={r['report_size_chars']:>6} chars | brief={r['brief_size_chars']:>4} chars | "
              f"ratio={r['compression_ratio']:.3f} | {r['avg_time_ms']:>8.3f}ms ± {r['std_ms']:>5.3f}ms")
    
    print("\n--- Timeline Extraction ---")
    tl_results = benchmark_generate_timeline()
    for k, v in tl_results.items():
        if not k.endswith("_std_ms") and not k.endswith("_entries"):
            print(f"  {k}: avg={v:.4f}ms (±{tl_results.get(k.replace('_ms', '_std_ms'), 0):.4f}ms, "
                  f"{tl_results.get(k.replace('_ms', '_entries'), 0)} entries)")
    
    print("\n--- Edge Cases ---")
    edge_results = benchmark_edge_cases()
    for k, v in edge_results.items():
        print(f"  {k}: {v:.4f}ms")
    
    return {
        "executive_brief": brief_results,
        "timeline_extraction": tl_results,
        "edge_cases": edge_results,
    }


if __name__ == "__main__":
    run()
