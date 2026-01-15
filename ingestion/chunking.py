"""
Chunking - Hierarchical Node Parser

- Optimized for SEC filings
- Large → Medium → Small chunks
"""

from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes


def build_hierarchical_nodes(documents):
    """
    Creates hierarchical chunk structure for SEC filings.
    
    Hierarchy:
    - Large (1024): Full sections, complete context
    - Medium (512): Paragraphs, balanced reasoning
    - Small (256): Sentences, precise retrieval
    
    Args:
        documents: List of documents
        
    Returns:
        Tuple of (all_nodes, leaf_nodes)
    """
    parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[1024, 512, 256],  # Larger chunks for financial docs
        chunk_overlap=50,  # More overlap for context preservation
    )

    nodes = parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(nodes)

    return nodes, leaf_nodes