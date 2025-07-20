"""
Diff content indexing engine for RAG system.
"""

import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime

from .vector_store import VectorStore
from .embeddings import EmbeddingService
from .chunker import DiffChunker, ContentChunk

logger = logging.getLogger(__name__)


class DiffIndexer:
    """Indexes diff file content for semantic search."""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        chunker: DiffChunker
    ):
        """Initialize diff indexer.
        
        Args:
            vector_store: Vector store for storing embeddings
            embedding_service: Service for generating embeddings
            chunker: Content chunker for diff files
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.chunker = chunker
        
        # Track indexed files
        self._indexed_files: Set[str] = set()
        self._load_indexed_files()
        
    def _load_indexed_files(self) -> None:
        """Load list of already indexed files from vector store."""
        try:
            results = self.vector_store.list_documents(limit=10000)
            if results and "metadatas" in results:
                for metadata in results["metadatas"]:
                    if metadata and "filename" in metadata:
                        self._indexed_files.add(metadata["filename"])
            logger.info(f"Loaded {len(self._indexed_files)} indexed files")
        except Exception as e:
            logger.warning(f"Could not load indexed files: {e}")
            
    def index_diff_file(
        self, 
        file_path: Path,
        force_reindex: bool = False
    ) -> bool:
        """Index a single diff file.
        
        Args:
            file_path: Path to diff file
            force_reindex: Whether to reindex if already indexed
            
        Returns:
            True if indexing was performed, False if skipped
        """
        filename = file_path.name
        
        # Check if already indexed
        if not force_reindex and filename in self._indexed_files:
            logger.debug(f"Skipping already indexed file: {filename}")
            return False
            
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Chunk the content
            chunks = self.chunker.chunk_diff_file(content, filename)
            
            if not chunks:
                logger.warning(f"No chunks created for {filename}")
                return False
                
            # Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.embed_texts(chunk_texts)
            
            # Prepare data for vector store
            documents = []
            metadatas = []
            ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create unique ID
                chunk_id = self._generate_chunk_id(filename, i, chunk.content)
                
                # Enhance metadata
                metadata = chunk.metadata.copy()
                metadata.update({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "indexed_at": datetime.now().isoformat(),
                    "file_path": str(file_path),
                    "content_length": len(chunk.content),
                    "chunk_type": chunk.chunk_type.value
                })
                
                documents.append(chunk.content)
                metadatas.append(metadata)
                ids.append(chunk_id)
                
            # Store in vector database
            self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            # Track as indexed
            self._indexed_files.add(filename)
            
            logger.info(f"Indexed {len(chunks)} chunks from {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            return False
            
    def index_diff_directory(
        self, 
        directory: Path,
        file_pattern: str = "*.diff",
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """Index all diff files in a directory.
        
        Args:
            directory: Directory containing diff files
            file_pattern: Pattern for matching diff files
            force_reindex: Whether to reindex existing files
            
        Returns:
            Indexing statistics
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")
            
        diff_files = list(directory.glob(file_pattern))
        if not diff_files:
            logger.warning(f"No diff files found in {directory}")
            return {
                "total_files": 0,
                "indexed_files": 0,
                "skipped_files": 0,
                "failed_files": 0
            }
            
        stats = {
            "total_files": len(diff_files),
            "indexed_files": 0,
            "skipped_files": 0,
            "failed_files": 0
        }
        
        logger.info(f"Starting indexing of {len(diff_files)} files from {directory}")
        
        for file_path in diff_files:
            try:
                if self.index_diff_file(file_path, force_reindex):
                    stats["indexed_files"] += 1
                else:
                    stats["skipped_files"] += 1
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                stats["failed_files"] += 1
                
        logger.info(
            f"Indexing complete: {stats['indexed_files']} indexed, "
            f"{stats['skipped_files']} skipped, {stats['failed_files']} failed"
        )
        
        return stats
        
    def update_index(
        self, 
        directory: Path,
        file_pattern: str = "*.diff"
    ) -> Dict[str, Any]:
        """Update index with new or changed files.
        
        Args:
            directory: Directory containing diff files
            file_pattern: Pattern for matching diff files
            
        Returns:
            Update statistics
        """
        # Get all diff files
        diff_files = list(directory.glob(file_pattern))
        new_files = []
        
        for file_path in diff_files:
            filename = file_path.name
            if filename not in self._indexed_files:
                new_files.append(file_path)
                
        logger.info(f"Found {len(new_files)} new files to index")
        
        stats = {
            "total_files_checked": len(diff_files),
            "new_files": len(new_files),
            "indexed_files": 0,
            "failed_files": 0
        }
        
        # Index new files
        for file_path in new_files:
            try:
                if self.index_diff_file(file_path):
                    stats["indexed_files"] += 1
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                stats["failed_files"] += 1
                
        return stats
        
    def remove_file_from_index(self, filename: str) -> bool:
        """Remove all chunks for a specific file from the index.
        
        Args:
            filename: Name of file to remove
            
        Returns:
            True if removal was successful
        """
        try:
            # Query for all chunks from this file
            results = self.vector_store.query(
                query_texts=[""],  # Empty query
                n_results=10000,  # Large number to get all
                where={"filename": filename}
            )
            
            if results and "ids" in results and results["ids"]:
                chunk_ids = [chunk_id for chunk_list in results["ids"] for chunk_id in chunk_list]
                self.vector_store.delete_documents(chunk_ids)
                self._indexed_files.discard(filename)
                logger.info(f"Removed {len(chunk_ids)} chunks for {filename}")
                return True
            else:
                logger.info(f"No chunks found for {filename}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove {filename} from index: {e}")
            return False
            
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the current index."""
        try:
            total_chunks = self.vector_store.get_document_count()
            
            # Get file statistics
            results = self.vector_store.list_documents(limit=10000)
            files_count = len(self._indexed_files)
            
            # Get chunk type distribution
            chunk_types = {}
            if results and "metadatas" in results:
                for metadata in results["metadatas"]:
                    if metadata and "chunk_type" in metadata:
                        chunk_type = metadata["chunk_type"]
                        chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
                        
            return {
                "total_chunks": total_chunks,
                "total_files": files_count,
                "chunk_types": chunk_types,
                "indexed_files": sorted(list(self._indexed_files))
            }
            
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {"error": str(e)}
            
    def reset_index(self) -> None:
        """Reset the entire index."""
        try:
            self.vector_store.reset_collection()
            self._indexed_files.clear()
            logger.info("Index reset complete")
        except Exception as e:
            logger.error(f"Failed to reset index: {e}")
            raise
            
    def _generate_chunk_id(self, filename: str, chunk_index: int, content: str) -> str:
        """Generate unique ID for a chunk."""
        # Create hash from filename, index, and content snippet
        content_snippet = content[:100]  # First 100 chars
        id_string = f"{filename}_{chunk_index}_{content_snippet}"
        return hashlib.md5(id_string.encode()).hexdigest()
        
    def validate_index(self) -> Dict[str, Any]:
        """Validate the current index for consistency."""
        try:
            results = self.vector_store.list_documents(limit=10000)
            
            validation_results = {
                "total_chunks": 0,
                "valid_chunks": 0,
                "invalid_chunks": 0,
                "missing_metadata_fields": [],
                "files_with_issues": []
            }
            
            required_fields = ["filename", "chunk_type", "indexed_at"]
            
            if results and "metadatas" in results:
                validation_results["total_chunks"] = len(results["metadatas"])
                
                for i, metadata in enumerate(results["metadatas"]):
                    if not metadata:
                        validation_results["invalid_chunks"] += 1
                        continue
                        
                    missing_fields = [field for field in required_fields if field not in metadata]
                    if missing_fields:
                        validation_results["invalid_chunks"] += 1
                        validation_results["missing_metadata_fields"].extend(missing_fields)
                        if "filename" in metadata:
                            validation_results["files_with_issues"].append(metadata["filename"])
                    else:
                        validation_results["valid_chunks"] += 1
                        
            # Remove duplicates
            validation_results["missing_metadata_fields"] = list(set(validation_results["missing_metadata_fields"]))
            validation_results["files_with_issues"] = list(set(validation_results["files_with_issues"]))
            
            logger.info(f"Index validation: {validation_results['valid_chunks']}/{validation_results['total_chunks']} chunks valid")
            return validation_results
            
        except Exception as e:
            logger.error(f"Index validation failed: {e}")
            return {"error": str(e)}