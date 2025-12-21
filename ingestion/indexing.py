from ingestion.loader import load_pdf
from core.embeddings import get_embedding_model

from retrieval.hierarchical_retrieval import build_hierarchical_retriever
from retrieval.summary_retrieval import build_summary_index
from core.llm_provider import get_llm


def build_all_indexes(pdf_path: str):
    """
    Main indexing entry point.
    Builds and returns all indexes used by the system.
    """

    documents = load_pdf(pdf_path)

    embed_model = get_embedding_model()

    hierarchical_retriever = build_hierarchical_retriever(
        documents,
        embed_model,
    )

    summary_retriever = build_summary_index(documents, embed_model)

    return {
        "hierarchical_retriever": hierarchical_retriever,
        "summary_retriever": summary_retriever,
    }
