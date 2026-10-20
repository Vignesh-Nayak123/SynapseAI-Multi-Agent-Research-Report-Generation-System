"""
Multi-Agent Research System Benchmark Suite
===========================================
Runs all benchmarks and generates a comprehensive markdown report.
Usage: python benchmark/benchmark_runner.py [--output benchmark_report.md]
"""

import os
import sys
import time
import json
import argparse
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import all benchmark modules
from benchmark import (
    benchmark_ranking,
    benchmark_validation,
    benchmark_summarize,
    benchmark_chat,
    benchmark_doi,
    benchmark_images,
    benchmark_pipeline,
    benchmark_pdf,
)


def get_system_info():
    """Gather system information for the report header."""
    import platform

    info = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor() or "Unknown",
        "cpu_count": os.cpu_count() or "Unknown",
    }

    # Try to get memory info
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["total_ram_gb"] = round(mem.total / (1024**3), 2)
        info["available_ram_gb"] = round(mem.available / (1024**3), 2)
    except ImportError:
        info["total_ram_gb"] = "N/A (install psutil)"
        info["available_ram_gb"] = "N/A"

    return info


def fmt_ms(ms):
    """Format milliseconds for display."""
    if ms < 1:
        return f"{ms * 1000:.1f}us"
    elif ms < 1000:
        return f"{ms:.2f}ms"
    else:
        return f"{ms / 1000:.2f}s"


def generate_report(all_results, system_info, elapsed_total):
    """Generate the comprehensive benchmark report markdown."""
    report = []

    # Title
    report.append("# Multi-Agent Research System Benchmark Report\n")
    report.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    report.append(f"**Duration:** {elapsed_total:.2f}s\n\n")

    # System Information
    report.append("---\n")
    report.append("## System Information\n")
    report.append("| Property | Value |")
    report.append("| :--- | :--- |")
    report.append(f"| Python Version | {system_info['python_version'].split()[0]} |")
    report.append(f"| Platform | {system_info['platform']} |")
    report.append(f"| CPU Count | {system_info['cpu_count']} |")
    report.append(f"| Processor | {system_info['processor']} |")
    report.append(f"| Total RAM | {system_info['total_ram_gb']} GB |")
    report.append(f"| Available RAM | {system_info['available_ram_gb']} GB |")
    report.append("")

    # 1. Document Ranking
    report.append("---\n")
    report.append("## 1. Document Ranking & Text Chunking\n")
    report.append("**Metrics:** TF-IDF cosine similarity ranking speed and text chunking throughput.\n")

    if "ranking" in all_results:
        r = all_results["ranking"]
        if "chunking" in r:
            report.append("### 1.1 Text Chunking Throughput\n")
            report.append("| Chunk Size | Overlap | Chunks | Avg Time | Throughput |")
            report.append("| :--- | :--- | :--- | :--- | :--- |")
            for c in r["chunking"]:
                report.append(f"| {c['chunk_size']} chars | {c['overlap']} chars | {c['num_chunks']} | {fmt_ms(c['avg_time_ms'])} | {c['throughput_chars_per_sec']:,} chars/s |")
            report.append("")

        if "ranking_speed" in r:
            report.append("### 1.2 Ranking Speed (by document count)\n")
            report.append("| Documents | Avg Time | Std Dev | Top Result |")
            report.append("| :--- | :--- | :--- | :--- |")
            latest = {}
            for rec in r["ranking_speed"]:
                latest[rec["num_documents"]] = rec
            for num_docs in sorted(latest.keys()):
                rec = latest[num_docs]
                report.append(f"| {rec['num_documents']} | {fmt_ms(rec['avg_time_ms'])} | +/-{fmt_ms(rec['std_ms'])} | `{rec['top_result'].split('/')[-1][:30]}` |")
            report.append("")

        if "ranking_accuracy" in r:
            report.append("### 1.3 Ranking Accuracy\n")
            report.append("Query: `quantum computing artificial intelligence`\n")
            report.append("| Rank | Source | Content Preview |")
            report.append("| :--- | :--- | :--- |")
            for rec in r["ranking_accuracy"]:
                report.append(f"| {rec['rank']} | `{rec['source'][:25]}` | {rec['content_preview'][:60]} |")
            report.append("")

    # 2. Citation Validation
    report.append("---\n")
    report.append("## 2. Citation Validation & Factual Consistency\n")
    report.append("**Metrics:** Speed of citation validation and numerical claim verification.\n")

    if "validation" in all_results:
        v = all_results["validation"]
        if "citation_validation" in v:
            report.append("### 2.1 Citation Validation Speed\n")
            report.append("| Documents | Citations in Draft | Invalid Found | Avg Time | Std Dev |")
            report.append("| :--- | :--- | :--- | :--- | :--- |")
            for rec in v["citation_validation"]:
                report.append(f"| {rec['num_documents']} | {rec['num_citations_in_draft']} | {rec['num_invalid_found']} | {fmt_ms(rec['avg_time_ms'])} | +/-{fmt_ms(rec['std_ms'])} |")
            report.append("")

        if "factual_consistency" in v:
            report.append("### 2.2 Factual Consistency Speed\n")
            report.append("| Documents | Claims | Unverified Found | Avg Time | Std Dev |")
            report.append("| :--- | :--- | :--- | :--- | :--- |")
            for rec in v["factual_consistency"]:
                report.append(f"| {rec['num_documents']} | {rec['num_claims_in_draft']} | {rec['num_unverified_found']} | {fmt_ms(rec['avg_time_ms'])} | +/-{fmt_ms(rec['std_ms'])} |")
            report.append("")

        if "edge_cases" in v:
            report.append("### 2.3 Edge Case Performance\n")
            report.append("| Test Case | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in v["edge_cases"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
            report.append("")

    # 3. Summarization
    report.append("---\n")
    report.append("## 3. Summarization & Timeline Extraction\n")
    report.append("**Metrics:** Executive brief generation and timeline extraction performance.\n")

    if "summarize" in all_results:
        s = all_results["summarize"]
        if "executive_brief" in s:
            report.append("### 3.1 Executive Brief Generation\n")
            report.append("| Report Size | Brief Size | Compression Ratio | Avg Time | Std Dev |")
            report.append("| :--- | :--- | :--- | :--- | :--- |")
            for rec in s["executive_brief"]:
                report.append(f"| {rec['report_size_chars']:,} chars | {rec['brief_size_chars']:,} chars | {rec['compression_ratio']:.1%} | {fmt_ms(rec['avg_time_ms'])} | +/-{fmt_ms(rec['std_ms'])} |")
            report.append("")

        if "timeline_extraction" in s:
            report.append("### 3.2 Timeline Extraction\n")
            tl = s["timeline_extraction"]
            report.append("| Scenario | Avg Time | Entries |")
            report.append("| :--- | :--- | :--- |")
            for k, val in tl.items():
                if k.endswith("_ms"):
                    key_name = k.replace("_ms", "").replace("_", " ").title()
                    std = tl.get(k.replace("_ms", "_std_ms"), 0)
                    entries = tl.get(k.replace("_ms", "_entries"), "N/A")
                    report.append(f"| {key_name} | {fmt_ms(val)} (+/-{fmt_ms(std)}) | {entries} |")
            report.append("")

        if "edge_cases" in s:
            report.append("### 3.3 Edge Cases\n")
            report.append("| Test Case | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in s["edge_cases"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
            report.append("")

    # 4. Chat Prompt
    report.append("---\n")
    report.append("## 4. Chat Prompt Construction\n")
    report.append("**Metrics:** Follow-up chat prompt building speed.\n")

    if "chat" in all_results:
        c = all_results["chat"]
        if "performance" in c:
            report.append("### 4.1 Prompt Construction Speed (by source count)\n")
            report.append("| Sources | Avg Time | Std Dev |")
            report.append("| :--- | :--- | :--- |")
            by_source = {}
            for rec in c["performance"]:
                ns = rec["num_sources"]
                if ns not in by_source:
                    by_source[ns] = []
                by_source[ns].append(rec["avg_time_ms"])
            for ns in sorted(by_source.keys()):
                times = by_source[ns]
                avg = sum(times) / len(times)
                std = (sum((t - avg)**2 for t in times) / len(times))**0.5
                report.append(f"| {ns} | {fmt_ms(avg)} | +/-{fmt_ms(std)} |")
            report.append("")

        if "content_verification" in c:
            report.append("### 4.2 Content Verification\n")
            report.append("| Check | Status |")
            report.append("| :--- | :--- |")
            for k, val in c["content_verification"].items():
                status = "PASS" if val else "FAIL"
                report.append(f"| {k.replace('_', ' ').title()} | {status} |")
            report.append("")

    # 5. DOI Resolution
    report.append("---\n")
    report.append("## 5. DOI Resolution (arXiv ID Extraction)\n")
    report.append("**Metrics:** arXiv ID extraction speed and pattern support.\n")

    if "doi" in all_results:
        d = all_results["doi"]
        if "extraction_speed" in d:
            report.append("### 5.1 Extraction Speed\n")
            report.append("| URLs Processed | IDs Found | Extraction Ratio | Avg Time | Throughput |")
            report.append("| :--- | :--- | :--- | :--- | :--- |")
            for rec in d["extraction_speed"]:
                report.append(f"| {rec['num_urls']:,} | {rec['num_ids_found']:,} | {rec['extraction_ratio']:.0%} | {fmt_ms(rec['avg_time_ms'])} | {rec['throughput_urls_per_sec']:,} urls/s |")
            report.append("")

        if "pattern_support" in d:
            report.append("### 5.2 URL Pattern Support\n")
            report.append("| Pattern | Input -> Output | Avg Time |")
            report.append("| :--- | :--- | :--- |")
            for rec in d["pattern_support"]:
                report.append(f"| {rec['pattern']} | {rec['num_input']} -> {rec['num_output']} IDs | {fmt_ms(rec['avg_time_ms'])} |")
            report.append("")

    # 6. Image Cache & Search Latency
    report.append("---\n")
    report.append("## 6. Image Search Cache & Search Latency\n")
    report.append("**Metrics:** Cache operations, query normalization, DDGS image/graph search latency, cache throughput.\n")

    if "images" in all_results:
        im = all_results["images"]
        if "cache_operations" in im:
            report.append("### 6.1 Cache Operations\n")
            report.append("| Operation | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in im["cache_operations"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
            report.append("")

        if "query_normalization" in im:
            report.append("### 6.2 Query Normalization\n")
            report.append("| Input Length | Normalized | Avg Time |")
            report.append("| :--- | :--- | :--- |")
            for rec in im["query_normalization"]:
                report.append(f"| {rec['original_length']} chars | `{rec['normalized'][:40]}` | {fmt_ms(rec['avg_time_ms'])} |")
            report.append("")

        if "search_latency" in im:
            report.append("### 6.3 DDGS Search Latency (network-dependent)\n")
            report.append("| Metric | Value |")
            report.append("| :--- | :--- |")
            sl = im["search_latency"]
            for k, val in sl.items():
                report.append(f"| {k.replace('_', ' ').title()} | {val} |")
            report.append("")

        if "cache_throughput" in im:
            report.append("### 6.4 Cache-Accelerated Throughput\n")
            report.append("| Metric | Value |")
            report.append("| :--- | :--- |")
            for k, val in im["cache_throughput"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {val} |")
            report.append("")

    # 7. Pipeline & State
    report.append("---\n")
    report.append("## 7. Pipeline & State Management\n")
    report.append("**Metrics:** State construction, graph generation, response serialization.\n")

    if "pipeline" in all_results:
        p = all_results["pipeline"]
        if "state_construction" in p:
            report.append("### 7.1 Agent State Construction\n")
            report.append("| State Type | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in p["state_construction"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
            report.append("")

        if "graph_construction" in p:
            report.append("### 7.2 Knowledge Graph Construction\n")
            report.append("| Documents | Nodes | Links | Avg Time |")
            report.append("| :--- | :--- | :--- | :--- |")
            for k, v in sorted(p["graph_construction"].items()):
                doc_count = k.split("_")[1]
                report.append(f"| {doc_count} | {v['num_nodes']} | {v['num_links']} | {fmt_ms(v['avg_ms'])} |")
            report.append("")

        if "response_construction" in p:
            report.append("### 7.3 Research Response Construction\n")
            report.append("| Sources | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in p["response_construction"].items():
                src_count = k.split("_")[1]
                report.append(f"| {src_count} | {fmt_ms(val)} |")
            report.append("")

        if "serialization" in p:
            report.append("### 7.4 Serialization Performance\n")
            report.append("| Operation | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in p["serialization"].items():
                if not k.endswith("_bytes"):
                    report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
                else:
                    report.append(f"| JSON Output Size | {val:,} bytes ({val / 1024:.1f} KB) |")
            report.append("")

    # 8. PDF Upload Handling
    report.append("---\n")
    report.append("## 8. PDF Upload Handling & Text Extraction\n")
    report.append("**Metrics:** PDF text extraction, validation density, reference stripping, column detection.\n")

    if "pdf" in all_results:
        pdf = all_results["pdf"]
        if "extraction" in pdf:
            report.append("### 8.1 PDF Text Extraction Speed\n")
            report.append("| Pages | PDF Size | Extracted Chars | Avg Time | Throughput |")
            report.append("| :--- | :--- | :--- | :--- | :--- |")
            for r in pdf["extraction"]:
                report.append(f"| {r['page_count']} | {r['pdf_size_bytes']:,} bytes | {r['extracted_chars']:,} chars | {fmt_ms(r['avg_time_ms'])} | {r['throughput_pages_per_sec']} pages/s |")
            report.append("")

        if "validation" in pdf:
            report.append("### 8.2 Text Segment Validation\n")
            report.append("| Test Case | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in pdf["validation"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
            report.append("")

        if "reference_stripping" in pdf:
            report.append("### 8.3 Reference Section Stripping\n")
            report.append("| Scenario | Input -> Output | Avg Time |")
            report.append("| :--- | :--- | :--- |")
            for r in pdf["reference_stripping"]:
                report.append(f"| {r['scenario']} | {r['input_chars']:,} -> {r['output_chars']:,} chars | {fmt_ms(r['avg_time_ms'])} |")
            report.append("")

        if "column_detection" in pdf:
            report.append("### 8.4 Column Layout Detection\n")
            report.append("| Layout | Avg Time |")
            report.append("| :--- | :--- |")
            for k, val in pdf["column_detection"].items():
                report.append(f"| {k.replace('_', ' ').title()} | {fmt_ms(val)} |")
            report.append("")

        if "page_extraction" in pdf:
            report.append("### 8.5 Individual Page Extraction\n")
            pe = pdf["page_extraction"]
            report.append(f"- **Avg Time:** {fmt_ms(pe['page_extraction_ms'])} +/-{fmt_ms(pe['page_extraction_std_ms'])}")
            report.append(f"- **Extracted Text:** {pe['extracted_text_length']} chars")
            report.append("")

    # Summary
    report.append("---\n")
    report.append("## Performance Summary\n")
    report.append("| Benchmark | Best Case | Worst Case |")
    report.append("| :--- | :--- | :--- |")

    if "ranking" in all_results and "chunking" in all_results["ranking"]:
        chunks = all_results["ranking"]["chunking"]
        best = min(c["avg_time_ms"] for c in chunks)
        worst = max(c["avg_time_ms"] for c in chunks)
        report.append(f"| Text Chunking (250-4000 chars) | {fmt_ms(best)} | {fmt_ms(worst)} |")

    if "validation" in all_results and "citation_validation" in all_results["validation"]:
        cites = all_results["validation"]["citation_validation"]
        best = min(c["avg_time_ms"] for c in cites)
        worst = max(c["avg_time_ms"] for c in cites)
        report.append(f"| Citation Validation | {fmt_ms(best)} | {fmt_ms(worst)} |")

    if "summarize" in all_results and "executive_brief" in all_results["summarize"]:
        briefs = all_results["summarize"]["executive_brief"]
        best = min(b["avg_time_ms"] for b in briefs)
        worst = max(b["avg_time_ms"] for b in briefs)
        report.append(f"| Executive Brief Generation | {fmt_ms(best)} | {fmt_ms(worst)} |")

    if "doi" in all_results and "extraction_speed" in all_results["doi"]:
        exts = all_results["doi"]["extraction_speed"]
        best = min(e["avg_time_ms"] for e in exts)
        worst = max(e["avg_time_ms"] for e in exts)
        report.append(f"| arXiv ID Extraction | {fmt_ms(best)} | {fmt_ms(worst)} |")

    if "pdf" in all_results and "extraction" in all_results["pdf"]:
        pde = all_results["pdf"]["extraction"]
        best = min(e["avg_time_ms"] for e in pde)
        worst = max(e["avg_time_ms"] for e in pde)
        report.append(f"| PDF Text Extraction (1-50 pages) | {fmt_ms(best)} | {fmt_ms(worst)} |")

    if "images" in all_results and "search_latency" in all_results["images"]:
        sl = all_results["images"]["search_latency"]
        if isinstance(sl.get("cache_acceleration_ratio"), (int, float)):
            report.append(f"| Image Search Cache Acceleration | {sl['cache_acceleration_ratio']}x faster | - |")

    report.append("")
    report.append("---\n")
    report.append(f"*Report generated by Multi-Agent Research System Benchmark Suite v0.4.0*\n")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Research System Benchmark Suite")
    parser.add_argument("--output", default="benchmark_report.md",
                       help="Output markdown file path")
    parser.add_argument("--no-save", action="store_true",
                       help="Print report to stdout instead of saving")
    args = parser.parse_args()

    start_total = time.time()
    all_results = {}
    system_info = get_system_info()

    print("=" * 60)
    print("  [BEAM] Multi-Agent Research System Benchmark Suite")
    print("=" * 60)
    print()

    # Run each benchmark
    benchmarks = [
        ("Document Ranking & Chunking", benchmark_ranking, "ranking"),
        ("Citation Validation", benchmark_validation, "validation"),
        ("Summarization & Timeline", benchmark_summarize, "summarize"),
        ("Chat Prompt Construction", benchmark_chat, "chat"),
        ("DOI Resolution", benchmark_doi, "doi"),
        ("Image Search Cache", benchmark_images, "images"),
        ("Pipeline & State Management", benchmark_pipeline, "pipeline"),
        ("PDF Upload Handling & Text Extraction", benchmark_pdf, "pdf"),
    ]

    for name, module, key in benchmarks:
        print(f"\n  [RUN] Running: {name}")
        try:
            start = time.time()
            results = module.run()
            elapsed = time.time() - start
            all_results[key] = results
            print(f"  [DONE] Completed in {elapsed:.2f}s")
        except Exception as e:
            print(f"  [FAIL] Failed: {e}")
            import traceback
            traceback.print_exc()
            all_results[key] = {"error": str(e)}

    elapsed_total = time.time() - start_total

    # Generate report
    print(f"\n  [WRITE] Generating report...")
    report = generate_report(all_results, system_info, elapsed_total)

    if args.no_save:
        print("\n" + report)
    else:
        output_filename = os.path.basename(args.output)
        output_path = os.path.join(os.path.dirname(__file__), output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  [SAVED] Report saved to: {output_path}")

    print(f"\n  [TOTAL] Total benchmark time: {elapsed_total:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
