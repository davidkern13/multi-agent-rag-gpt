"""
Tokenizer utilities

- tiktoken for OpenAI token counting
"""

import tiktoken


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        return int(len(text.split()) * 1.3)


def analyze_token_usage(query: str, answer: str, contexts: list = None, response_obj=None) -> dict:
    """Analyze token usage."""
    prompt_tokens = count_tokens(query)
    completion_tokens = count_tokens(answer)
    
    result = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    
    if contexts:
        context_text = "\n".join([str(c) for c in contexts])
        result["context_tokens"] = count_tokens(context_text)
        result["total_with_context"] = result["total_tokens"] + result["context_tokens"]
    
    return result


def format_token_report(token_data: dict) -> str:
    """Format token report."""
    lines = ["📊 Token Usage:"]

    if "prompt_tokens" in token_data:
        lines.append(f"  • Prompt:      {token_data['prompt_tokens']:>6} tokens")
    if "completion_tokens" in token_data:
        lines.append(f"  • Completion:  {token_data['completion_tokens']:>6} tokens")
    if "context_tokens" in token_data:
        lines.append(f"  • Context:     {token_data['context_tokens']:>6} tokens")
    if "total_tokens" in token_data:
        lines.append(f"  • Total:       {token_data['total_tokens']:>6} tokens")

    return "\n".join(lines)