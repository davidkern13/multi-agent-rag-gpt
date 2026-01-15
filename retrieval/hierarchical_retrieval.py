"""
Hierarchical Retrieval - Financial Reports

- SEC filing indexing
- Auto-Merging Retriever
"""

from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
import os

from retrieval.metadata_extractor import (
    extract_doc_type,
    extract_section_title,
    extract_entities_from_text,
)
from ingestion.chunking import build_hierarchical_nodes


def build_hierarchical_retriever(docs, embed_model, top_k: int = 5):
    """
    Build hierarchical retriever for SEC filings.
    Uses Auto-Merging strategy for context expansion.
    
    Args:
        docs: List of documents
        embed_model: Embedding model
        top_k: Number of results to retrieve
        
    Returns:
        AutoMergingRetriever
    """
    chroma_path = "./chroma_storage"
    docstore_path = "./docstore_hierarchical"
    collection_name = "financial_hierarchical"  # Changed from insurance

    chroma_exists = os.path.exists(chroma_path)
    docstore_exists = os.path.exists(docstore_path)

    if chroma_exists and docstore_exists:
        print("[INFO] Found existing storage, loading from disk...")

        try:
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            chroma_collection = chroma_client.get_collection(name=collection_name)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

            storage_context = StorageContext.from_defaults(
                vector_store=vector_store, persist_dir=docstore_path
            )

            index = load_index_from_storage(
                storage_context,
                embed_model=embed_model,
            )

            print("[INFO] ✅ Loaded existing index successfully!")

            return AutoMergingRetriever(
                index.as_retriever(similarity_top_k=top_k),
                storage_context=storage_context,
                verbose=False,
            )

        except Exception as e:
            print(f"[WARN] Failed to load existing storage: {e}")
            print("[INFO] Rebuilding index from scratch...")

    else:
        print("[INFO] No existing storage found, creating new index...")

    # ==========================================
    # CREATE NEW INDEX
    # ==========================================

    print("[INFO] Extracting entities from documents...")
    all_entities = set()
    for doc in docs:
        entities = extract_entities_from_text(doc.text, top_n=20)
        all_entities.update([e[0] for e in entities])
    print(f"[INFO] Found {len(all_entities)} unique entities")

    print("[INFO] Creating hierarchical chunks...")
    nodes, leaf_nodes = build_hierarchical_nodes(docs)
    print(f"[INFO] Created {len(nodes)} total nodes, {len(leaf_nodes)} leaf nodes")

    print("[INFO] Adding metadata to nodes...")
    for node in leaf_nodes:
        text = node.get_content()
        node.metadata.update({
            "doc_type": extract_doc_type(text),
            "section_title": extract_section_title(text),
            "parent_id": node.parent_node.node_id if node.parent_node else None,
        })

    print("[INFO] Creating ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=chroma_path)

    try:
        chroma_client.delete_collection(name=collection_name)
    except:
        pass

    chroma_collection = chroma_client.create_collection(name=collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    storage_context.docstore.add_documents(nodes)

    print("[INFO] Building vector index...")
    index = VectorStoreIndex(
        leaf_nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )

    print(f"[INFO] Persisting to {docstore_path}...")
    storage_context.persist(persist_dir=docstore_path)

    print("[INFO] ✅ Created financial hierarchical index!")

    return AutoMergingRetriever(
        index.as_retriever(similarity_top_k=top_k),
        storage_context=storage_context,
        verbose=False,
    )