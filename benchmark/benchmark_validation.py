"""
Benchmark: Citation Validation & Factual Consistency
Tests citation validation speed and numerical claim verification.
"""

import time
import json
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.validation import validate_citations, check_factual_consistency


def load_documents():
    path = os.path.join(os.path.dirname(__file__), "test_data", "sample_documents.json")
    with open(path) as f:
        return json.load(f)


def benchmark_validate_citations():
    """Benchmark citation validation with varying draft sizes and citation counts."""
    docs = load_documents()
    results = []
    
    # Generate drafts with varying numbers of citations
    configs = [
        (10, 5),    # 10 docs, 5 citations
        (20, 15),   # 20 docs, 15 citations
        (50, 30),   # 50 docs, 30 citations
        (100, 75),  # 100 docs, 75 citations
    ]
    
    for num_docs, num_citations in configs:
        subset = (docs * (num_docs // len(docs) + 1))[:num_docs]
        
        # Create a draft with citations
        valid_cites = " ".join([f"[S{i}]" for i in range(1, num_citations + 1)])
        invalid_cites = " ".join([f"[S{i}]" for i in range(num_docs + 1, num_docs + 11)])
        draft = f"This is a research draft with citations. {valid_cites}. Some invalid: {invalid_cites}. End of draft."
        
        trials = []
        for _ in range(20):
            start = time.perf_counter()
            invalid = validate_citations(draft, subset)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results.append({
            "num_documents": num_docs,
            "num_citations_in_draft": num_citations + 10,
            "num_invalid_found": len(invalid),
            "avg_time_ms": round(statistics.mean(trials) * 1000, 4),
            "std_ms": round(statistics.stdev(trials) * 1000, 4) if len(trials) > 1 else 0,
        })
    
    return results


def benchmark_factual_consistency():
    """Benchmark factual consistency checking with numerical claims."""
    docs = load_documents()
    results = []
    
    configs = [
        (10, 5),    # 10 docs, 5 numerical claims
        (20, 20),   # 20 docs, 20 claims
        (50, 50),   # 50 docs, 50 claims
        (100, 100), # 100 docs, 100 claims
    ]
    
    for num_docs, num_claims in configs:
        subset = (docs * (num_docs // len(docs) + 1))[:num_docs]
        
        # Generate claims: some valid, some not
        draft_parts = []
        for i in range(num_claims):
            if i % 3 == 0:
                # Valid claim (exists in doc content)
                draft_parts.append(f"The fidelity reached 99.9% in experiment {i}.")
            elif i % 3 == 1:
                # Unverifiable claim
                draft_parts.append(f"The temperature reached {i * 100 + 42} Kelvin in experiment {i}.")
            else:
                # Mixed claim
                draft_parts.append(f"Coherence time of {i * 10 + 15} microseconds was measured at {i * 5 + 10} mK.")
        
        draft = " ".join(draft_parts)
        
        trials = []
        for _ in range(20):
            start = time.perf_counter()
            unverified = check_factual_consistency(draft, subset)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)
        
        results.append({
            "num_documents": num_docs,
            "num_claims_in_draft": num_claims,
            "num_unverified_found": len(unverified),
            "avg_time_ms": round(statistics.mean(trials) * 1000, 4),
            "std_ms": round(statistics.stdev(trials) * 1000, 4) if len(trials) > 1 else 0,
        })
    
    return results


def benchmark_empty_inputs():
    """Test edge case performance."""
    docs = load_documents()
    results = {}
    
    # Empty draft
    start = time.perf_counter()
    for _ in range(100):
        validate_citations("", docs)
    elapsed = time.perf_counter() - start
    results["empty_draft_citations_ms"] = round((elapsed / 100) * 1000, 4)
    
    # Empty documents
    start = time.perf_counter()
    for _ in range(100):
        validate_citations("[S1] claim [S2]", [])
    elapsed = time.perf_counter() - start
    results["empty_docs_citations_ms"] = round((elapsed / 100) * 1000, 4)
    
    # No citations in draft
    start = time.perf_counter()
    for _ in range(100):
        validate_citations("No citations here.", docs)
    elapsed = time.perf_counter() - start
    results["no_citations_draft_ms"] = round((elapsed / 100) * 1000, 4)
    
    return results


def run():
    print("=" * 60)
    print("BENCHMARK: Citation Validation & Factual Consistency")
    print("=" * 60)
    
    print("\n--- Citation Validation Speed ---")
    cite_results = benchmark_validate_citations()
    for r in cite_results:
        print(f"  docs={r['num_documents']:>4} | cites={r['num_citations_in_draft']:>3} | "
              f"invalid={r['num_invalid_found']:>2} | {r['avg_time_ms']:>8.4f}ms ± {r['std_ms']:>5.4f}ms")
    
    print("\n--- Factual Consistency Speed ---")
    fact_results = benchmark_factual_consistency()
    for r in fact_results:
        print(f"  docs={r['num_documents']:>4} | claims={r['num_claims_in_draft']:>3} | "
              f"unverified={r['num_unverified_found']:>3} | {r['avg_time_ms']:>8.4f}ms ± {r['std_ms']:>5.4f}ms")
    
    print("\n--- Edge Cases ---")
    edge_results = benchmark_empty_inputs()
    for k, v in edge_results.items():
        print(f"  {k}: {v:.4f}ms")
    
    return {
        "citation_validation": cite_results,
        "factual_consistency": fact_results,
        "edge_cases": edge_results,
    }


if __name__ == "__main__":
    run()
