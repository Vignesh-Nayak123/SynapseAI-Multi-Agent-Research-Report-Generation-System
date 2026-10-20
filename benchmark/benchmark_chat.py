"""
Benchmark: Chat Prompt Construction
Tests follow-up chat prompt building speed and accuracy.
"""

import time
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.chat import build_chat_prompt


def load_sample_report():
    path = os.path.join(os.path.dirname(__file__), "test_data", "sample_report.txt")
    with open(path, encoding="utf-8") as f:
        return f.read()


def benchmark_prompt_construction():
    """Benchmark prompt construction with varying inputs."""
    report = load_sample_report()
    questions = [
        "What are the key findings about superconducting qubits?",
        "Summarize the limitations and challenges mentioned in the report.",
        "Compare different qubit modalities discussed in the paper.",
        "What is the outlook for quantum computing according to this review?",
        "Explain the error correction techniques mentioned.",
        "What are the implications for practical applications?",
    ]
    
    results = []
    
    # Varying source counts
    for num_sources in [0, 5, 10, 20, 50, 100]:
        sources = [f"https://arxiv.org/abs/{y}.{i:05d}" for y in range(2020, 2025) for i in range(1, 26)][:num_sources]
        
        for question in questions:
            trials = []
            for _ in range(30):
                start = time.perf_counter()
                prompt = build_chat_prompt(question, report, sources)
                elapsed = time.perf_counter() - start
                trials.append(elapsed)
            
            results.append({
                "num_sources": num_sources,
                "question_length": len(question),
                "prompt_length": len(prompt),
                "avg_time_ms": round(statistics.mean(trials) * 1000, 3),
                "std_ms": round(statistics.stdev(trials) * 1000, 3) if len(trials) > 1 else 0,
                "question": question[:30] + "...",
            })
    
    return results


def benchmark_content_verification():
    """Verify that the prompt contains expected content."""
    report = load_sample_report()
    sources = ["https://arxiv.org/abs/2301.12345"]
    question = "What is quantum computing?"
    
    prompt = build_chat_prompt(question, report, sources)
    
    checks = {
        "contains_report": report[:100] in prompt,
        "contains_question": question in prompt,
        "contains_source": sources[0] in prompt,
        "contains_answer_marker": prompt.rstrip().endswith("## Answer"),
        "contains_formatting_instructions": "## and ### headings" in prompt,
        "contains_role_instruction": "research assistant" in prompt.lower(),
        "contains_citation_instruction": "[S#]" in prompt,
    }
    
    return checks


def run():
    print("=" * 60)
    print("BENCHMARK: Chat Prompt Construction")
    print("=" * 60)
    
    print("\n--- Prompt Construction Speed ---")
    results = benchmark_prompt_construction()
    
    # Aggregate by source count
    by_source = {}
    for r in results:
        key = r["num_sources"]
        if key not in by_source:
            by_source[key] = []
        by_source[key].append(r["avg_time_ms"])
    
    for num_src, times in sorted(by_source.items()):
        avg = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0
        print(f"  sources={num_src:>3} | avg={avg:>8.3f}ms ± {std:>5.3f}ms (avg prompt={int(results[0]['prompt_length']):,} chars)")
    
    print("\n--- Content Verification ---")
    checks = benchmark_content_verification()
    all_pass = True
    for check, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        if not passed:
            all_pass = False
        try:
            print(f"  {status} {check}")
        except UnicodeEncodeError:
            safe_status = "PASS" if passed else "FAIL"
            print(f"  [{safe_status}] {check}")

    return {
        "performance": results,
        "content_verification": checks,
        "all_checks_pass": all_pass,
    }


if __name__ == "__main__":
    run()
