"""
LLM Provider

- LangChain ChatOpenAI for Agents
- LlamaIndex OpenAI for Retrieval/Indexing
"""

import os
from langchain_openai import ChatOpenAI
from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI
from llama_index.core import Settings


def get_llm(model: str = "gpt-4o-mini", temperature: float = 0.0) -> ChatOpenAI:
    """
    Get LangChain ChatOpenAI for agents.
    
    Args:
        model: OpenAI model name
        temperature: 0.0 for factual responses
    
    Returns:
        ChatOpenAI instance
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=os.getenv("OPENAI_API_KEY"),
        streaming=True,
    )


def get_llama_llm(model: str = "gpt-4o-mini") -> LlamaIndexOpenAI:
    """
    Get LlamaIndex OpenAI for retrieval/indexing.
    
    Args:
        model: OpenAI model name
    
    Returns:
        LlamaIndex OpenAI instance
    """
    llm = LlamaIndexOpenAI(
        model=model,
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    Settings.llm = llm
    return llm