"""
Benchmark: PDF Upload Handling & Text Extraction
Tests PDFProcessor text extraction, validation, reference stripping,
column detection, upload endpoint simulation, and edge cases.
"""

import time
import io
import statistics
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.pdf import PDFProcessor, _extract_page, _strip_reference_sections, _has_two_columns


def _generate_synthetic_pdf_bytes(page_count: int = 5, words_per_page: int = 200) -> bytes:
    """Generate a synthetic PDF using fitz with realistic academic content."""
    import fitz  # type: ignore

    doc = fitz.open()
    topics = [
        "Quantum Computing",
        "Machine Learning",
        "Neural Networks",
        "Cryptography",
        "Optimization",
    ]
    # Use Courier for headings (always available as a built-in PDF font)
    # Use Helvetica for body text (always available)
    FONT_BODY = "courier"
    FONT_HEAD = "courier"

    for page_num in range(page_count):
        page = doc.new_page()
        rect = page.rect
        y = 72
        # Title
        page.insert_text((72, y), f"Research Paper on {topics[page_num % len(topics)]}", fontsize=11, fontname=FONT_HEAD)
        y += 20
        # Abstract heading
        page.insert_text((72, y), "Abstract", fontsize=10, fontname=FONT_HEAD)
        y += 14
        # Abstract body
        abstract_text = (
            f"This paper presents a comprehensive study of {topics[page_num % len(topics)]}. "
            f"We demonstrate significant advances in the field through novel algorithms and "
            f"experimental validation."
        )
        page.insert_text((72, y), abstract_text, fontsize=8, fontname=FONT_BODY)
        y += 16
        # Body paragraphs
        for i in range(words_per_page // 10):
            if y > rect.height - 72:
                break
            text = (
                f"Experimental results show that our method outperforms existing approaches. "
                f"The proposed framework is evaluated on standard benchmarks."
            )
            page.insert_text((72, y), text, fontsize=8, fontname=FONT_BODY)
            y += 12

        # References section on last page
        if page_num == page_count - 1:
            y += 10
            page.insert_text((72, y), "References", fontsize=10, fontname=FONT_HEAD)
            y += 16
            for ref_num in range(5):
                ref_text = f"[{ref_num + 1}] Smith, J. et al. ({2020 + ref_num}). Nature, 100-110."
                if y > rect.height - 72:
                    break
                page.insert_text((72, y), ref_text, fontsize=7, fontname=FONT_BODY)
                y += 10

    raw_bytes = doc.write()
    doc.close()
    return raw_bytes


def benchmark_extraction():
    """Benchmark PDF text extraction with varying document sizes."""
    results = []

    for page_count in [1, 3, 5, 10, 20, 50]:
        raw_bytes = _generate_synthetic_pdf_bytes(page_count=page_count, words_per_page=200)
        processor = PDFProcessor(max_concurrency=1)

        trials = []
        for _ in range(30):
            start = time.perf_counter()
            text = processor._extract_and_validate(raw_bytes)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)

        results.append({
            "page_count": page_count,
            "pdf_size_bytes": len(raw_bytes),
            "extracted_chars": len(text),
            "avg_time_ms": round(statistics.mean(trials) * 1000, 3),
            "std_ms": round(statistics.stdev(trials) * 1000, 3) if len(trials) > 1 else 0,
            "throughput_pages_per_sec": round(page_count / statistics.mean(trials), 1),
        })

    return results


def benchmark_validation():
    """Benchmark validation segment density checking."""
    processor = PDFProcessor(max_concurrency=1)
    results = {}

    # Valid text (high density)
    valid_text = "This is a normal academic text with alphanumeric content and proper density scoring for validation checks." * 10
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = processor._validate_segment(valid_text)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["valid_text_density_ms"] = round(statistics.mean(trials) * 1000, 4)

    # Garbage text (low density - lots of symbols)
    garbage_text = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~ \t\n" * 20
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = processor._validate_segment(garbage_text)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["garbage_text_density_ms"] = round(statistics.mean(trials) * 1000, 4)

    # Short text (under 50 chars)
    short_text = "Hello world"
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = processor._validate_segment(short_text)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["short_text_under_50_chars_ms"] = round(statistics.mean(trials) * 1000, 4)

    # Empty text
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = processor._validate_segment("")
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["empty_text_ms"] = round(statistics.mean(trials) * 1000, 4)

    return results


def benchmark_reference_stripping():
    """Benchmark reference section identification and stripping."""
    results = []

    configs = [
        ("no_references", "This is a normal document with no references section at all. " * 50),
        ("with_references", "Main content here. " * 100 + "References\n[1] Smith et al. 2023\n[2] Jones et al. 2024\nBibliography\n[3] Brown et al. 2025"),
        ("large_document", "Quantum computing research continues to advance. " * 500 + "\nReferences\n" + "\n".join(f"[{i}] Author {i}, Paper {i}, 202{min(i,9)}." for i in range(1, 101))),
        ("early_references_kept", "Introduction. " * 30 + "References\n[1] Ref1" + "Main content continues. " * 50 + "Acknowledgements\nThanks to everyone."),
    ]

    for name, text in configs:
        trials = []
        for _ in range(100):
            start = time.perf_counter()
            stripped = _strip_reference_sections(text)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)

        results.append({
            "scenario": name,
            "input_chars": len(text),
            "output_chars": len(stripped),
            "avg_time_ms": round(statistics.mean(trials) * 1000, 4),
            "std_ms": round(statistics.stdev(trials) * 1000, 4) if len(trials) > 1 else 0,
        })

    return results


def benchmark_column_detection():
    """Benchmark two-column layout detection."""
    results = {}

    # Two column layout
    left_col = [(100.0, "Left col text left col text") for _ in range(20)]
    right_col = [(400.0, "Right col text right col text") for _ in range(15)]
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = _has_two_columns(left_col, right_col)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["two_column_detection_ms"] = round(statistics.mean(trials) * 1000, 4)

    # Single column (empty right)
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = _has_two_columns(left_col, [])
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["single_column_empty_right_ms"] = round(statistics.mean(trials) * 1000, 4)

    # Imbalanced columns
    right_few = [(400.0, "Right text") for _ in range(3)]
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = _has_two_columns(left_col, right_few)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["imbalanced_columns_ms"] = round(statistics.mean(trials) * 1000, 4)

    # Both empty
    trials = []
    for _ in range(1000):
        start = time.perf_counter()
        result = _has_two_columns([], [])
        elapsed = time.perf_counter() - start
        trials.append(elapsed)
    results["both_empty_ms"] = round(statistics.mean(trials) * 1000, 4)

    return results


def benchmark_page_extraction():
    """Benchmark individual page text extraction (text block sorting, column alignment)."""
    import fitz  # type: ignore

    doc = fitz.open()
    page = doc.new_page()

    # Insert various text blocks across the page
    positions = [(72, 72), (72, 100), (72, 130), (72, 160), (350, 72), (350, 110)]
    for x, y in positions:
        page.insert_text((x, y), f"Block at ({x}, {y})", fontsize=10, fontname="helv")

    trials = []
    for _ in range(100):
        start = time.perf_counter()
        extracted = _extract_page(page)
        elapsed = time.perf_counter() - start
        trials.append(elapsed)

    results = {"page_extraction_ms": round(statistics.mean(trials) * 1000, 3),
               "page_extraction_std_ms": round(statistics.stdev(trials) * 1000, 3),
               "extracted_text_length": len(extracted)}

    doc.close()
    return results


def benchmark_batch_processing():
    """Benchmark PDFProcessor batch processing with synthetic PDFs."""
    processor = PDFProcessor(max_concurrency=3)
    batch_results = []

    for batch_size in [1, 3, 5, 10]:
        pdfs = [_generate_synthetic_pdf_bytes(page_count=3, words_per_page=100) for _ in range(batch_size)]

        trials = []
        for _ in range(10):
            start = time.perf_counter()
            for raw_bytes in pdfs:
                processor._extract_and_validate(raw_bytes)
            elapsed = time.perf_counter() - start
            trials.append(elapsed)

        avg_ms = statistics.mean(trials) * 1000
        std_ms = statistics.stdev(trials) * 1000 if len(trials) > 1 else 0
        per_pdf_ms = avg_ms / batch_size

        batch_results.append({
            "batch_size": batch_size,
            "avg_ms": round(avg_ms, 3),
            "std_ms": round(std_ms, 3),
            "per_pdf_ms": round(per_pdf_ms, 3),
        })

        print(f"  batch_size={batch_size:>2} | avg={avg_ms:>8.3f}ms | per_pdf={per_pdf_ms:.3f}ms")

    return batch_results


def run():
    print("=" * 60)
    print("BENCHMARK: PDF Upload Handling & Text Extraction")
    print("=" * 60)

    print("\n--- Extraction Speed (varying page counts) ---")
    extract_results = benchmark_extraction()
    for r in extract_results:
        print(f"  pages={r['page_count']:>2} | {r['pdf_size_bytes']:>8} bytes | "
              f"{r['extracted_chars']:>5} chars | {r['avg_time_ms']:>8.3f}ms +/-{r['std_ms']:>5.3f}ms | "
              f"{r['throughput_pages_per_sec']:>8.1f} pages/s")

    print("\n--- Validation Segment Density ---")
    valid_results = benchmark_validation()
    for k, v in valid_results.items():
        print(f"  {k}: {v:.4f}ms")

    print("\n--- Reference Section Stripping ---")
    ref_results = benchmark_reference_stripping()
    for r in ref_results:
        print(f"  {r['scenario']:30s} | {r['input_chars']:>6} -> {r['output_chars']:>6} chars | "
              f"{r['avg_time_ms']:.4f}ms +/-{r['std_ms']:.4f}ms")

    print("\n--- Column Detection ---")
    col_results = benchmark_column_detection()
    for k, v in col_results.items():
        print(f"  {k}: {v:.4f}ms")

    print("\n--- Page Extraction ---")
    page_results = benchmark_page_extraction()
    print(f"  page_extraction: {page_results['page_extraction_ms']:.3f}ms +/-{page_results['page_extraction_std_ms']:.3f}ms "
          f"({page_results['extracted_text_length']} chars)")

    print("\n--- Batch Processing ---")
    batch_results = benchmark_batch_processing()

    print()

    return {
        "extraction": extract_results,
        "validation": valid_results,
        "reference_stripping": ref_results,
        "column_detection": col_results,
        "page_extraction": page_results,
        "batch_processing": batch_results,
    }


if __name__ == "__main__":
    run()
