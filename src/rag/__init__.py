"""
RAG (Retrieval Augmented Generation) module for LZA Diff Analyzer.

This module provides semantic search capabilities over diff file contents
using LangChain components with ChromaDB vector store and HuggingFace embeddings.
"""

from .chunker import DiffChunker
from .langchain_rag import LangChainRAGSystem

# Legacy components (kept for compatibility)
try:
    from .vector_store import VectorStore
    from .embeddings import EmbeddingService
    from .indexer import DiffIndexer
    from .retriever import SemanticRetriever
    
    __all__ = [
        "LangChainRAGSystem",  # Primary implementation
        "DiffChunker",
        "VectorStore",        # Legacy
        "EmbeddingService",   # Legacy
        "DiffIndexer",        # Legacy
        "SemanticRetriever",  # Legacy
    ]
except ImportError:
    # Only include LangChain components if dependencies are available
    __all__ = [
        "LangChainRAGSystem",
        "DiffChunker",
    ]