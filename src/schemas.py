from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResearchRequest(BaseModel):
    """Input payload accepted by the /research endpoint."""

    topic: str = Field(min_length=3, description="Primary research topic or question")
    max_depth: int = Field(default=3, ge=1, le=10, description="Controls how exhaustive the review should be")
    num_papers: int = Field(default=10, ge=1, le=50, description="Number of papers to search for")
    provider: str = Field(default="ollama", pattern="^(ollama|openrouter|openai|anthropic|google|perplexity|groq|together|deepseek|mistral)$", description="LLM provider to use")
    openrouter_api_key: str | None = Field(default=None, description="API key for OpenRouter (required if provider is openrouter)")
    api_key: str | None = Field(default=None, description="API key for providers that require one (openai, perplexity, groq, etc.) — used directly (non-encrypted path)")
    model: str | None = Field(default=None, description="Specific model to use (e.g. 'llama3', 'x-ai/grok-4.1-fast')")
    critic_strictness: int = Field(default=5, ge=1, le=10, description="Strictness level of the critic agent (1=Lenient, 10=Strict)")

    # Optional uploaded PDF content for context
    uploaded_content: str | None = Field(
        default=None,
        description="Text content extracted from a user-uploaded PDF, used as additional context for the research.",
    )

    # Zero-knowledge encrypted fields
    encrypted_api_key: str | None = Field(
        default=None,
        description="AES-256-GCM encrypted API key (base64). Requires encryption_passphrase.",
    )
    encryption_iv: str | None = Field(
        default=None,
        description="Initialization vector for decryption (base64).",
    )
    encryption_salt: str | None = Field(
        default=None,
        description="PBKDF2 salt for decryption (base64).",
    )
    encryption_passphrase: str | None = Field(
        default=None,
        description="Session passphrase used to derive the decryption key. Never stored or logged, only used in-memory.",
    )

    model_config = ConfigDict(extra="forbid")


class ImageResult(BaseModel):
    """A single image result from a search."""

    title: str = Field(default="", description="Image title or alt text")
    image_url: str = Field(description="Direct URL to the image")
    thumbnail_url: str | None = Field(default=None, description="Thumbnail URL")
    source_url: str = Field(default="", description="URL of the page containing the image")
    source_domain: str = Field(default="", description="Source domain name")
    width: int | None = Field(default=None, description="Image width in pixels")
    height: int | None = Field(default=None, description="Image height in pixels")


class ResearchResponse(BaseModel):
    """Successful research result envelope."""

    final_report: str = Field(description="Structured literature review synthesized by the system")
    sources: list[str] = Field(default_factory=list, description="List of source URLs cited in the review")
    topic: str = Field(description="The original research topic")
    graph_data: dict | None = Field(default=None, description="Citation graph data for visualization")
    images: list[ImageResult] = Field(default_factory=list, description="Related images for the research topic")
    graphs: list[ImageResult] = Field(default_factory=list, description="Related charts and data visualizations for the topic")
