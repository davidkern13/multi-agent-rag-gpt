"""
Indexing Module with ChromaDB

- Vector database for embeddings
- Persistent storage
"""

import os
from pathlib import Path
from typing import Dict, Any

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
    VectorStoreIndex,
    Document,
)
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.indices.document_summary import DocumentSummaryIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

# ChromaDB imports
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# Storage paths
HIERARCHICAL_STORAGE = "./docstore_hierarchical"
SUMMARY_STORAGE = "./docstore_summary"
CHROMA_DB_PATH = "./chroma_db"


def _check_indexes_exist() -> bool:
    """Check if both indexes already exist."""
    hierarchical_exists = os.path.exists(HIERARCHICAL_STORAGE) and \
                          os.path.exists(os.path.join(HIERARCHICAL_STORAGE, "docstore.json"))
    summary_exists = os.path.exists(SUMMARY_STORAGE) and \
                     os.path.exists(os.path.join(SUMMARY_STORAGE, "docstore.json"))
    chroma_exists = os.path.exists(CHROMA_DB_PATH)
    
    return hierarchical_exists and summary_exists and chroma_exists


def _init_settings():
    """Initialize LlamaIndex settings."""
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)


def _get_chroma_vector_store(collection_name: str = "financial_docs"):
    """Get or create ChromaDB vector store."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
        print(f"[ChromaDB] Using existing collection: {collection_name}")
    except:
        chroma_collection = chroma_client.create_collection(collection_name)
        print(f"[ChromaDB] Created new collection: {collection_name}")
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return vector_store


def _load_existing_indexes() -> Dict[str, Any]:
    """Load existing indexes from storage."""
    print("[Indexing] Loading existing indexes from storage...")
    _init_settings()
    
    # Get ChromaDB vector store
    vector_store = _get_chroma_vector_store()
    
    # Load hierarchical index with ChromaDB
    print("[Indexing] Loading hierarchical index with ChromaDB...")
    hierarchical_storage = StorageContext.from_defaults(
        persist_dir=HIERARCHICAL_STORAGE,
        vector_store=vector_store
    )
    hierarchical_index = load_index_from_storage(hierarchical_storage)
    
    base_retriever = hierarchical_index.as_retriever(similarity_top_k=12)
    hierarchical_retriever = AutoMergingRetriever(
        base_retriever,
        storage_context=hierarchical_storage,
        verbose=False,
    )
    
    # Load summary index
    print("[Indexing] Loading summary index...")
    summary_storage = StorageContext.from_defaults(persist_dir=SUMMARY_STORAGE)
    summary_index = load_index_from_storage(summary_storage)
    summary_retriever = summary_index.as_retriever(similarity_top_k=5)
    
    print("[Indexing] ✅ Loaded existing indexes from ChromaDB!")
    
    return {
        "hierarchical_index": hierarchical_index,
        "hierarchical_retriever": hierarchical_retriever,
        "summary_index": summary_index,
        "summary_retriever": summary_retriever,
    }


def _build_new_indexes(data_path: str) -> Dict[str, Any]:
    """Build new indexes from PDF with ChromaDB."""
    from ingestion.loader import load_pdf
    
    print(f"[Indexing] Loading PDF: {data_path}")
    documents = load_pdf(data_path)
    print(f"[Indexing] Loaded {len(documents)} document(s)")
    
    print("[Indexing] Initializing embedding model...")
    _init_settings()
    
    # Get ChromaDB vector store
    vector_store = _get_chroma_vector_store()
    
    # Build hierarchical index with ChromaDB
    print("[Indexing] Building hierarchical index with ChromaDB...")
    node_parser = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])
    nodes = node_parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(nodes)
    
    hierarchical_storage = StorageContext.from_defaults(vector_store=vector_store)
    hierarchical_storage.docstore.add_documents(nodes)
    
    hierarchical_index = VectorStoreIndex(
        leaf_nodes,
        storage_context=hierarchical_storage,
        show_progress=True,
    )
    hierarchical_storage.persist(persist_dir=HIERARCHICAL_STORAGE)
    print(f"[Indexing] Saved hierarchical index to {HIERARCHICAL_STORAGE}")
    print(f"[Indexing] Saved vectors to ChromaDB at {CHROMA_DB_PATH}")
    
    base_retriever = hierarchical_index.as_retriever(similarity_top_k=12)
    hierarchical_retriever = AutoMergingRetriever(
        base_retriever,
        storage_context=hierarchical_storage,
        verbose=False,
    )
    
    # Build summary index
    print("[Indexing] Building summary index...")
    summary_index = DocumentSummaryIndex.from_documents(
        documents,
        show_progress=True,
    )
    summary_index.storage_context.persist(persist_dir=SUMMARY_STORAGE)
    print(f"[Indexing] Saved summary index to {SUMMARY_STORAGE}")
    
    summary_retriever = summary_index.as_retriever(similarity_top_k=5)
    
    print("[Indexing] ✅ Built and saved new indexes with ChromaDB!")
    
    return {
        "hierarchical_index": hierarchical_index,
        "hierarchical_retriever": hierarchical_retriever,
        "summary_index": summary_index,
        "summary_retriever": summary_retriever,
    }


def build_all_indexes(data_path: str = None, force_rebuild: bool = False) -> Dict[str, Any]:
    """
    Build or load indexes with ChromaDB vector storage.
    
    Args:
        data_path: Path to PDF file (only needed if building new)
        force_rebuild: Force rebuild even if indexes exist
        
    Returns:
        Dictionary with retrievers and indexes
    """
    # Check if indexes already exist FIRST
    if not force_rebuild and _check_indexes_exist():
        print("[Indexing] Found existing indexes in ChromaDB, skipping PDF loading...")
        return _load_existing_indexes()
    
    # Build new indexes (only now do we need the PDF)
    if data_path is None:
        raise ValueError("data_path required when building new indexes")
    
    return _build_new_indexes(data_path)