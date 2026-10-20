from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


def generate_simple_explanation(report: str) -> str:
    """Generate a simplified executive brief from a report by extracting key sections."""
    lines = report.split("\n")
    brief_parts: list[str] = []
    in_exec = False
    exec_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Grab the title
        if stripped.startswith("# ") and not stripped.startswith("## "):
            brief_parts.append(f"# {stripped[2:].strip()} (Executive Brief)")

        # Grab executive summary
        if stripped.startswith("## Executive Summary") or stripped.startswith("## Summary"):
            in_exec = True
            exec_lines = []
            continue
        if in_exec:
            if stripped.startswith("## "):
                in_exec = False
            else:
                exec_lines.append(line)

    if exec_lines:
        brief_parts.append("## Overview")
        brief_parts.append(" ".join(l.strip() for l in exec_lines if l.strip()))

    # Grab key findings
    in_findings = False
    finding_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Key Findings") or stripped.startswith("## Findings"):
            in_findings = True
            finding_lines = []
            continue
        if in_findings:
            if stripped.startswith("## "):
                in_findings = False
            else:
                finding_lines.append(line)

    if finding_lines:
        brief_parts.append("\n## Key Points")
        brief_parts.append("\n".join(finding_lines[:20]))

    if not brief_parts:
        # Fallback: just take first 500 chars
        brief_parts.append(report[:500] + "...")

    return "\n\n".join(brief_parts)


def generate_timeline_data(report: str, sources: list[str]) -> list[dict]:
    """Extract year-based milestones from a report and sources."""
    import re
    import urllib.parse

    years: set[int] = set()
    topics: dict[int, str] = {}

    # Extract years from report (4-digit numbers between 1900-2029)
    year_matches = re.findall(r'\b(19\d\d|20[0-2]\d)\b', report)
    for y in year_matches:
        years.add(int(y))

    # Extract context around each year
    for y in sorted(years):
        # Find the sentence containing this year
        for line in report.split('\n'):
            if str(y) in line:
                # Clean up the line for use as a label
                label = line.strip()[:60].strip()
                if label:
                    topics[y] = label
                    break

    # Try to extract years from arXiv source URLs
    arxiv_years: set[int] = set()
    for src in sources:
        match = re.search(r'/(\d{4})\.\d+', src)
        if match:
            yr = int(match.group(1))
            if 1900 <= yr <= 2029:
                arxiv_years.add(yr)

    years_combined = sorted(years | arxiv_years)

    timeline = []
    for y in years_combined:
        entry = {"year": y, "label": topics.get(y, f"Research activity in {y}")}
        timeline.append(entry)

    return timeline
