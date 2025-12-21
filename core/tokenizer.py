"""
Tokenizer utilities using Ollama's built-in token counting.
Uses the actual token counts from Ollama API responses.
"""


def extract_token_info_from_response(response) -> dict:
    """
    Extract token information from Ollama LLM response.

    Args:
        response: Response object from llm.complete() or llm.chat()

    Returns:
        Dictionary with token counts and timing info
    """
    metadata = {}

    if hasattr(response, "additional_kwargs"):
        metadata = response.additional_kwargs
    elif hasattr(response, "raw"):
        metadata = response.raw

    return {
        "prompt_tokens": metadata.get("prompt_eval_count", 0),
        "completion_tokens": metadata.get("eval_count", 0),
        "total_tokens": metadata.get("prompt_eval_count", 0)
        + metadata.get("eval_count", 0),
        "prompt_eval_duration_ms": metadata.get("prompt_eval_duration", 0)
        / 1_000_000,  # ns to ms
        "eval_duration_ms": metadata.get("eval_duration", 0) / 1_000_000,  # ns to ms
        "total_duration_ms": metadata.get("total_duration", 0) / 1_000_000,  # ns to ms
        "tokens_per_second": (
            metadata.get("eval_count", 0)
            / (metadata.get("eval_duration", 1) / 1_000_000_000)
            if metadata.get("eval_duration", 0) > 0
            else 0
        ),
    }


def analyze_token_usage(
    query: str, answer: str, contexts: list = None, response_obj=None
) -> dict:
    """
    Analyze token usage for a query-answer pair.

    Args:
        query: User query
        answer: Generated answer
        contexts: Retrieved contexts (optional)
        response_obj: Ollama response object with metadata (optional)

    Returns:
        Dictionary with token counts
    """
    result = {}

    if response_obj:
        # Use actual Ollama token counts
        token_info = extract_token_info_from_response(response_obj)
        result.update(token_info)
    else:
        # Fallback to approximation (1 token ≈ 0.75 words)
        query_tokens = int(len(query.split()) * 1.3)
        answer_tokens = int(len(answer.split()) * 1.3)

        result = {
            "prompt_tokens": query_tokens,
            "completion_tokens": answer_tokens,
            "total_tokens": query_tokens + answer_tokens,
        }

    # Add context token count (approximation)
    if contexts:
        context_text = "\n".join([str(c) for c in contexts])
        result["context_tokens"] = int(len(context_text.split()) * 1.3)
        result["total_with_context"] = result["total_tokens"] + result["context_tokens"]

    return result


def format_token_report(token_data: dict) -> str:
    """
    Format token usage data as a readable string.

    Args:
        token_data: Output from analyze_token_usage()

    Returns:
        Formatted string
    """
    lines = ["📊 Token Usage:"]

    if "prompt_tokens" in token_data:
        lines.append(f"  • Prompt:      {token_data['prompt_tokens']:>6} tokens")

    if "completion_tokens" in token_data:
        lines.append(f"  • Completion:  {token_data['completion_tokens']:>6} tokens")

    if "context_tokens" in token_data:
        lines.append(
            f"  • Context:     {token_data['context_tokens']:>6} tokens (approx)"
        )

    if "total_tokens" in token_data:
        lines.append(f"  • Total:       {token_data['total_tokens']:>6} tokens")

    if "total_with_context" in token_data:
        lines.append(f"  • With Context:{token_data['total_with_context']:>6} tokens")

    if "tokens_per_second" in token_data and token_data["tokens_per_second"] > 0:
        lines.append("")
        lines.append("⚡ Performance:")
        lines.append(
            f"  • Speed:       {token_data['tokens_per_second']:>6.1f} tokens/sec"
        )

        if "total_duration_ms" in token_data:
            lines.append(f"  • Total Time:  {token_data['total_duration_ms']:>6.0f} ms")

    return "\n".join(lines)
