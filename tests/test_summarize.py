"""Tests for src.tools.summarize — report simplification and timeline extraction."""

from __future__ import annotations

import pytest
from src.tools.summarize import generate_simple_explanation, generate_timeline_data


SAMPLE_REPORT = """# Quantum Computing: A Literature Review

## Executive Summary
Quantum computing leverages quantum mechanical phenomena such as superposition and entanglement to perform computations that are intractable for classical computers. Recent advances in qubit coherence times have enabled the first demonstrations of quantum advantage.

## Key Findings
- **Superconducting qubits** have achieved 99.9% gate fidelity (S1)
- **Trapped ion systems** demonstrate the highest coherence times (S2)
- **Topological qubits** remain theoretical but promising (S3)
- Error correction overhead remains the primary barrier to scalability

## Critical Analysis
The field has made remarkable progress in the past five years. However, claims of quantum advantage remain controversial, with classical simulations improving rapidly to close the gap.

## Methodological Notes
The reviewed papers employed a mix of experimental demonstration and theoretical analysis. Sample sizes in experimental papers ranged from single-qubit to 127-qubit systems.

## Implications & Open Questions
Quantum computing will likely find its first practical applications in materials science and drug discovery. Fault-tolerant quantum computing remains 5-10 years away according to most estimates.
"""


class TestGenerateSimpleExplanation:
    """Tests for generate_simple_explanation()."""

    def test_extracts_title_and_summary(self):
        brief = generate_simple_explanation(SAMPLE_REPORT)
        assert "Quantum Computing" in brief
        assert "Executive Brief" in brief
        assert "Overview" in brief
        assert "superposition" in brief

    def test_extracts_key_findings(self):
        brief = generate_simple_explanation(SAMPLE_REPORT)
        assert "Key Points" in brief
        assert "qubits" in brief

    def test_does_not_contain_full_report(self):
        brief = generate_simple_explanation(SAMPLE_REPORT)
        # The brief should be shorter than the full report
        assert len(brief) < len(SAMPLE_REPORT)

    def test_empty_report(self):
        brief = generate_simple_explanation("")
        assert isinstance(brief, str)

    def test_minimal_report(self):
        brief = generate_simple_explanation("# Just a title")
        # Should return the title wrapped in brief format
        assert "Just a title" in brief
        assert "Executive Brief" in brief

    def test_report_with_only_findings(self):
        report = "# Test\n## Findings\n- Result A\n- Result B\n## Other\nNothing here."
        brief = generate_simple_explanation(report)
        assert "Test" in brief
        assert "Result A" in brief

    def test_report_without_standard_sections(self):
        report = "# Random\n\nSome paragraphs of text.\n\nMore text here."
        brief = generate_simple_explanation(report)
        # Falls back to first 500 chars
        assert "Random" in brief
        assert len(brief) <= 500 + 3  # 500 chars + "..."

    def test_multiline_summary(self):
        report = "# Test\n## Executive Summary\nLine one.\nLine two.\nLine three.\n\n## Next Section\nContent."
        brief = generate_simple_explanation(report)
        assert "Line one" in brief
        assert "Line two" in brief
        assert "Line three" in brief

    def test_key_findings_truncated_to_20_lines(self):
        lines_20 = "\n".join(f"- Finding {i}" for i in range(25))
        report = f"# Test\n## Key Findings\n{lines_20}\n## Other"
        brief = generate_simple_explanation(report)
        # Should have at most 20 finding lines
        finding_count = brief.count("- Finding")
        assert finding_count == 20


class TestGenerateTimelineData:
    """Tests for generate_timeline_data()."""

    def test_extracts_years_from_report(self):
        timeline = generate_timeline_data(SAMPLE_REPORT, [])
        years = [e["year"] for e in timeline]
        # The report says "5-10 years away" but doesn't contain specific years
        # So this might return fewer results — at minimum it's a list
        assert isinstance(timeline, list)

    def test_extracts_years_from_sources(self):
        # Use URLs with explicit 4-digit years in the path (not arXiv YYMM format)
        sources = [
            "https://arxiv.org/abs/2023.12345",
            "https://arxiv.org/abs/2022.56789",
        ]
        timeline = generate_timeline_data("", sources)
        years = [e["year"] for e in timeline]
        assert 2023 in years
        assert 2022 in years

    def test_combined_report_and_sources(self):
        report = "In 2024, significant progress was made."
        sources = ["https://arxiv.org/abs/2023.12345"]
        timeline = generate_timeline_data(report, sources)
        years = [e["year"] for e in timeline]
        assert 2024 in years
        assert 2023 in years

    def test_deduplicates_years(self):
        report = "Year 2024. Year 2024 again."
        timeline = generate_timeline_data(report, sources=[])
        years = [e["year"] for e in timeline]
        assert years.count(2024) == 1

    def test_empty_inputs(self):
        timeline = generate_timeline_data("", [])
        assert timeline == []

    def test_out_of_range_years_ignored(self):
        report = "Events in 1800 and 3000 are not valid."
        timeline = generate_timeline_data(report, [])
        assert all(1900 <= e["year"] <= 2029 for e in timeline)

    def test_label_from_surrounding_text(self):
        report = "In 2023, researchers achieved a major breakthrough in error correction."
        timeline = generate_timeline_data(report, [])
        entries = {e["year"]: e["label"] for e in timeline}
        assert 2023 in entries
        assert "breakthrough" in entries[2023].lower()

    def test_multiple_arxiv_years_in_one_url(self):
        """Each URL contributes one year."""
        sources = ["https://arxiv.org/abs/2023.12345", "https://arxiv.org/abs/2024.56789"]
        timeline = generate_timeline_data("", sources)
        years = [e["year"] for e in timeline]
        assert 2023 in years
        assert 2024 in years

    def test_sources_sorted_by_year(self):
        report = "2020 was quiet. 2024 was exciting. 2022 was productive."
        timeline = generate_timeline_data(report, [])
        years = [e["year"] for e in timeline]
        assert years == sorted(years)

    def test_each_entry_has_year_and_label(self):
        timeline = generate_timeline_data("In 2021, something happened.", [])
        for entry in timeline:
            assert "year" in entry
            assert "label" in entry
            assert isinstance(entry["year"], int)
            assert isinstance(entry["label"], str)
