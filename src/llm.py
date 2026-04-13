"""LLM client wrapper with dynamic model selection.

Provides call_llm() which dispatches to the correct Anthropic model
based on the `target_model` tier in AgentState.
See spec_LLM.md for tier definitions.
"""

import os

import anthropic

# Tier name → Anthropic model ID
MODEL_MAP: dict[str, str] = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

# Default token limits per tier
MAX_TOKENS: dict[str, int] = {
    "opus": 16384,
    "sonnet": 16384,
    "haiku": 8192,
}


def _get_client() -> anthropic.Anthropic:
    """Create an Anthropic client using CLAUDE_API_KEY (or ANTHROPIC_API_KEY fallback)."""
    api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set CLAUDE_API_KEY or ANTHROPIC_API_KEY in environment."
        )
    return anthropic.Anthropic(api_key=api_key)


def call_llm(
    *,
    tier: str,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int | None = None,
) -> anthropic.types.Message:
    """Call the Anthropic API with dynamic model selection.

    Args:
        tier: Model tier key ("opus", "sonnet", or "haiku").
        system: System prompt string.
        messages: Conversation messages in Anthropic API format
                  (list of {"role": ..., "content": ...}).
        tools: Optional tool definitions for tool-use.
        max_tokens: Override default max tokens for this tier.

    Returns:
        The raw Anthropic Message response.
    """
    if tier not in MODEL_MAP:
        raise ValueError(f"Unknown model tier '{tier}'. Expected one of: {list(MODEL_MAP.keys())}")

    model_id = MODEL_MAP[tier]
    tokens = max_tokens or MAX_TOKENS[tier]
    client = _get_client()

    kwargs: dict = {
        "model": model_id,
        "max_tokens": tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    return client.messages.create(**kwargs)
