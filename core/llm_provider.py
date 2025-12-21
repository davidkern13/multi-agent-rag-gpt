from llama_index.llms.ollama import Ollama
from llama_index.core import Settings


def get_llm(model_name: str = "gemma3:4b"):
    """
    Get LLM with temperature=0.0 for factual, deterministic responses.
    Critical for accurate retrieval of facts like "highest percentage".
    """
    llm = Ollama(
        model=model_name,
        request_timeout=180,
        temperature=0.0,
        num_ctx=512,
        num_predict=32,
    )
    Settings.llm = llm
    return llm
