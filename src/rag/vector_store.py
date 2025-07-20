"""
ChromaDB vector store management for LZA diff content.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages ChromaDB vector store for diff content retrieval."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize ChromaDB vector store.
        
        Args:
            config: RAG configuration containing vector store settings
        """
        if chromadb is None:
            raise ImportError(
                "ChromaDB not available. Install with: pip install chromadb"
            )
            
        self.config = config
        self.persist_directory = Path(config.get("persist_directory", "./data/chromadb"))
        self.collection_name = config.get("collection_name", "lza_diff_logs")
        
        # Ensure directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self._client = None
        self._collection = None
        
    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        return self._client
        
    def _get_collection(self):
        """Get or create collection."""
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "LZA diff log content for RAG"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        return self._collection
        
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ) -> None:
        """Add documents to the vector store.
        
        Args:
            documents: List of text documents to add
            metadatas: List of metadata dicts for each document
            ids: List of unique IDs for each document
            embeddings: Pre-computed embeddings (optional)
        """
        collection = self._get_collection()
        
        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
            
    def query(
        self,
        query_texts: List[str],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query the vector store for similar documents.
        
        Args:
            query_texts: List of query strings
            n_results: Number of results to return
            where: Metadata filter conditions
            where_document: Document content filter conditions
            
        Returns:
            Query results with documents, distances, and metadata
        """
        collection = self._get_collection()
        
        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            logger.debug(f"Query returned {len(results.get('documents', []))} results")
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
            
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
        """
        collection = self._get_collection()
        
        try:
            collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
            
    def get_document_count(self) -> int:
        """Get total number of documents in collection."""
        collection = self._get_collection()
        return collection.count()
        
    def reset_collection(self) -> None:
        """Reset/clear the entire collection."""
        client = self._get_client()
        
        try:
            client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except ValueError:
            logger.info(f"Collection {self.collection_name} did not exist")
            
        # Recreate empty collection
        self._collection = None
        self._get_collection()
        
    def list_documents(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """List documents in the collection.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            Documents with their metadata and IDs
        """
        collection = self._get_collection()
        
        try:
            results = collection.get(limit=limit)
            return results
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise