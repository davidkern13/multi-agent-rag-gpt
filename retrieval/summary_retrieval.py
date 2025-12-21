"""
Summary Index with MapReduce Strategy
Using VectorStoreIndex for top_k retrieval support
"""

from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Document,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
import chromadb
import os
import json
from retrieval.metadata_extractor import (
    extract_doc_type,
    extract_timestamp,
    extract_entities_from_text,
)


def build_summary_index(docs, embed_model, top_k: int = 5):
    """
    Build a summary index with MapReduce strategy:
    1. MAP: Summarize each chunk
    2. REDUCE: Store hierarchical summaries

    Returns retriever with top_k support
    """
    chroma_path = "./chroma_storage"
    docstore_path = "./docstore_summary"
    collection_name = "insurance_summaries"

    chroma_exists = os.path.exists(chroma_path)
    docstore_exists = os.path.exists(docstore_path)

    if chroma_exists and docstore_exists:
        print("[INFO] Found existing summary storage, loading from disk...")

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

            print("[INFO] ✅ Loaded existing summary index successfully!")
            return index.as_retriever(similarity_top_k=top_k)

        except Exception as e:
            print(f"[WARN] Failed to load summary index: {e}")
            print("[INFO] Creating new summary index...")

    else:
        print("[INFO] Creating new summary index with MapReduce strategy...")

    # ==========================================
    # MAP-REDUCE IMPLEMENTATION
    # ==========================================

    print("[INFO] Splitting documents into chunks...")
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=4)

    all_nodes = []

    for doc_idx, doc in enumerate(docs):
        chunks = splitter.split_text(doc.text)
        print(f"[INFO] Document split into {len(chunks)} chunks")

        for chunk_idx, chunk in enumerate(chunks):
            # Extract entities and convert to JSON string for ChromaDB
            entities_list = extract_entities_from_text(chunk, top_n=10)
            entities_str = json.dumps(entities_list)

            metadata = {
                "doc_idx": doc_idx,
                "chunk_idx": chunk_idx,
                "doc_type": extract_doc_type(chunk),
                "timestamp": extract_timestamp(chunk),
                "entities": entities_str,
                "is_leaf": True,
            }

            node = Document(
                text=chunk,
                metadata=metadata,
            )
            all_nodes.append(node)

        section_size = 5
        for i in range(0, len(chunks), section_size):
            section_chunks = chunks[i : min(i + section_size, len(chunks))]
            combined_text = "\n\n---\n\n".join(section_chunks)

            section_metadata = {
                "doc_idx": doc_idx,
                "section_idx": i // section_size,
                "doc_type": "section_summary",
                "is_section": True,
                "chunk_count": len(section_chunks),
            }

            section_node = Document(
                text=f"[SECTION SUMMARY]\n{combined_text}",
                metadata=section_metadata,
            )
            all_nodes.append(section_node)

        doc_summary_text = "\n\n".join(chunks[:3])

        doc_metadata = {
            "doc_idx": doc_idx,
            "doc_type": "document_summary",
            "is_document": True,
            "total_chunks": len(chunks),
        }

        doc_node = Document(
            text=f"[DOCUMENT SUMMARY]\n{doc_summary_text}",
            metadata=doc_metadata,
        )
        all_nodes.append(doc_node)

    print(f"[INFO] MapReduce complete:")
    print(f"[INFO]   - Total nodes: {len(all_nodes)}")
    print(
        f"[INFO]   - Leaf chunks: {sum(1 for n in all_nodes if n.metadata.get('is_leaf'))}"
    )
    print(
        f"[INFO]   - Section summaries: {sum(1 for n in all_nodes if n.metadata.get('is_section'))}"
    )
    print(
        f"[INFO]   - Document summaries: {sum(1 for n in all_nodes if n.metadata.get('is_document'))}"
    )

    chroma_client = chromadb.PersistentClient(path=chroma_path)

    try:
        chroma_client.delete_collection(name=collection_name)
    except:
        pass

    chroma_collection = chroma_client.create_collection(name=collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("[INFO] Building summary index from MapReduce documents...")
    index = VectorStoreIndex.from_documents(
        all_nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )

    print(f"[INFO] Persisting summary index to {docstore_path}...")
    storage_context.persist(persist_dir=docstore_path)

    print(f"[INFO] ✅ Created and persisted MapReduce summary index!")
    print(f"[INFO]    - ChromaDB: {chroma_path}")
    print(f"[INFO]    - Docstore: {docstore_path}")
    print(f"[INFO]    - Strategy: MAP (chunks) → REDUCE (sections) → REDUCE (document)")

    return index.as_retriever(similarity_top_k=top_k)
