"""
System Builder

- MCP enabled
- Memory and HITL
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from ingestion.indexing import build_all_indexes
from ingestion.pdf_downloader import get_corpus_path
from core.llm_provider import get_llm
from agents.needle_agent import NeedleAgent
from agents.summarization_agent import SummarizationAgent
from agents.manager_agent import ManagerAgent
from mcp.financial_mcp import FinancialMCP

logging.getLogger("llama_index.core.indices.utils").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)


def build_system(data_path: str = None, debug: bool = False) -> ManagerAgent:
    """
    Build the financial analysis system.
    
    Components:
    - NeedleAgent: Specific financial data extraction
    - SummarizationAgent: Executive summaries
    - ManagerAgent: Query routing with Memory & HITL
    - FinancialMCP: Financial analysis tools (enabled)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    
    # Only get PDF path if we need it (indexes don't exist)
    # The indexing module will check if indexes exist first
    if data_path is None:
        # Try to get path, but it might not be needed
        try:
            data_path = get_corpus_path(auto_download=False)
        except:
            data_path = "data/corpus.pdf"
    
    print(f"[System] Initializing...")
    
    # Build or load indexes (LlamaIndex)
    # Will skip PDF loading if indexes already exist
    indexes = build_all_indexes(data_path=data_path)
    
    # LangChain LLM
    llm = get_llm()
    
    print("[System] Creating agents...")
    
    # Create agents
    needle_agent = NeedleAgent(
        retriever=indexes["hierarchical_retriever"],
        llm=llm,
        debug=debug,
    )
    
    summary_agent = SummarizationAgent(
        summary_retriever=indexes["summary_retriever"],
        llm=llm,
        debug=debug,
    )
    
    # MCP with financial tools - ENABLED
    mcp = FinancialMCP(enabled=True)
    print(f"[System] MCP Tools: {len(mcp.get_tools())} tools loaded")
    
    # Manager with memory, HITL, and MCP
    manager = ManagerAgent(
        needle_agent=needle_agent,
        summary_agent=summary_agent,
        llm=llm,
        mcp=mcp,  # MCP enabled!
        debug=debug,
    )
    
    print("[System] ✅ System ready!")
    print("[System] Features: Memory ✓, HITL ✓, MCP ✓")
    
    return manager