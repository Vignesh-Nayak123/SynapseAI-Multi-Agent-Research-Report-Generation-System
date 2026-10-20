from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


def build_chat_prompt(question: str, report: str, sources: list[str]) -> str:
    """Build a prompt for the follow-up chat based on report context."""
    source_list = "\n".join(f"- {s}" for s in sources[:20])

    return (
        f"You are a research assistant helping a user understand a report they generated.\n"
        f"Answer their question based **only** on the information in the report below.\n"
        f"If the answer is not in the report, say so rather than making up information.\n"
        f"Always cite sources using [S#] notation when referencing specific claims.\n\n"
        f"## Formatting Requirements\n"
        f"Format your answer in clean, readable Markdown using these rules:\n"
        f"1. Use ## and ### headings to organize your answer into clear sections.\n"
        f"2. Break text into short paragraphs (2-4 sentences each) separated by blank lines.\n"
        f"3. Use bullet points (-) for lists and key findings instead of run-on sentences.\n"
        f"4. Use **bold** for key terms, concepts, and important numbers.\n"
        f"5. Include source citations [S#] inline where each claim is made.\n"
        f"6. Use > blockquotes for direct quotes from the report.\n"
        f"7. Use --- to separate distinct sections if needed.\n"
        f"8. Never output a single wall of text — always use structure.\n\n"
        f"## Research Report\n\n{report}\n\n"
        f"## Sources Referenced\n{source_list}\n\n"
        f"## Question\n{question}\n\n"
        f"## Answer\n"
    )
