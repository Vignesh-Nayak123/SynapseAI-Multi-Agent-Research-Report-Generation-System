"""Tests for src.tools.chat — follow-up chat prompt construction."""

from __future__ import annotations

import pytest
from src.tools.chat import build_chat_prompt


SAMPLE_REPORT = "Quantum computing research has advanced significantly."
SAMPLE_SOURCES = [
    "https://arxiv.org/abs/2301.12345",
    "https://arxiv.org/abs/2302.67890",
    "https://arxiv.org/abs/2303.11111",
]


class TestBuildChatPrompt:
    """Tests for build_chat_prompt()."""

    def test_includes_report_in_output(self):
        prompt = build_chat_prompt("What is progress?", SAMPLE_REPORT, [])
        assert SAMPLE_REPORT in prompt

    def test_includes_question(self):
        question = "What are the key findings?"
        prompt = build_chat_prompt(question, SAMPLE_REPORT, [])
        assert question in prompt

    def test_includes_sources(self):
        prompt = build_chat_prompt("Question?", "Report", SAMPLE_SOURCES)
        for src in SAMPLE_SOURCES:
            assert src in prompt

    def test_limits_sources_to_20(self):
        many_sources = [f"https://example.com/{i}" for i in range(50)]
        prompt = build_chat_prompt("Q?", "Report", many_sources)
        # Count occurrences of "example.com" in the output
        count = prompt.count("example.com")
        assert count <= 20

    def test_contains_role_instruction(self):
        prompt = build_chat_prompt("Q?", "Report", [])
        assert "research assistant" in prompt.lower()

    def test_contains_honesty_instruction(self):
        prompt = build_chat_prompt("Q?", "Report", [])
        assert "not in the report" in prompt.lower() or "say so" in prompt.lower()

    def test_empty_sources(self):
        prompt = build_chat_prompt("Question?", "Report", [])
        assert "Question?" in prompt
        assert "Report" in prompt
        # Sources section should be empty
        assert "## Sources" in prompt

    def test_empty_report(self):
        prompt = build_chat_prompt("Question?", "", ["https://example.com"])
        assert "Question?" in prompt
        assert "https://example.com" in prompt

    def test_question_with_special_characters(self):
        prompt = build_chat_prompt("What's the <rate> of 5+5?", "Report", [])
        assert "<rate>" in prompt

    def test_output_starts_with_instructions(self):
        prompt = build_chat_prompt("Q?", "R", [])
        # Should start with the instruction block
        assert prompt.startswith("You are a research assistant")

    def test_ends_with_answer_marker(self):
        prompt = build_chat_prompt("Q?", "R", [])
        assert prompt.rstrip().endswith("## Answer")
