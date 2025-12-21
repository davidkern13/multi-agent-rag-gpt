from ingestion.indexing import build_all_indexes
from core.llm_provider import get_llm
from agents.needle_agent import NeedleAgent
from agents.summarization_agent import SummarizationAgent
from agents.manager_agent import ManagerAgent
from mcp.claim_mcp import ClaimMCP
import logging

# 🔥 SILENCE VERBOSE LOGS FOR SPEED
logging.getLogger("llama_index.core.indices.utils").setLevel(logging.ERROR)


def build_system(data_path: str) -> ManagerAgent:
    indexes = build_all_indexes(data_path)
    llm = get_llm()

    needle_agent = NeedleAgent(
        indexes["hierarchical_retriever"],
        llm,
    )

    summary_agent = SummarizationAgent(
        indexes["summary_retriever"],
        llm,
    )

    manager = ManagerAgent(
        needle_agent=needle_agent,
        summary_agent=summary_agent,
        llm=llm,
        mcp=ClaimMCP(),
    )

    return manager
