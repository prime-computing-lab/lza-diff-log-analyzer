"""
LangChain-based RAG implementation for LZA diff content.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib

try:
    from langchain_core.documents import Document
    from langchain_core.vectorstores import VectorStore
    from langchain_core.retrievers import BaseRetriever
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import BaseRetriever
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
except ImportError as e:
    raise ImportError(f"LangChain components not available: {e}. Install with: pip install -e .[rag]")

from .chunker import DiffChunker, ContentChunk

logger = logging.getLogger(__name__)


class LangChainRAGSystem:
    """LangChain-based RAG system for diff content."""
    
    def __init__(self, config_manager):
        """Initialize RAG system with LangChain components.
        
        Args:
            config_manager: LLMConfigManager instance or raw config dict
        """
        # Handle both config manager and raw dict
        if hasattr(config_manager, 'model_dump'):
            # It's a Pydantic model (LLMConfigManager)
            self.config = config_manager.model_dump()
        elif isinstance(config_manager, dict):
            # It's already a dict
            self.config = config_manager
        else:
            # Try to convert to dict
            self.config = dict(config_manager)
            
        self.rag_config = self.config.get("rag", {})
        self.vector_config = self.rag_config.get("vector_store", {})
        self.embedding_config = self.rag_config.get("embedding", {})
        self.retrieval_config = self.rag_config.get("retrieval", {})
        
        # Initialize components
        self.embeddings = None
        self.vectorstore = None
        self.retriever = None
        self.text_splitter = None
        self.chunker = None
        
        # Initialize text splitter
        self._init_text_splitter()
        
        # Initialize custom chunker
        self._init_chunker()
        
        # Initialize embeddings
        self._init_embeddings()
        
        # Initialize vector store
        self._init_vectorstore()
        
    def _init_embeddings(self) -> None:
        """Initialize HuggingFace embeddings."""
        model_name = self.embedding_config.get("model", "all-MiniLM-L6-v2")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            cache_folder=self.embedding_config.get("cache_dir", "./data/embeddings_cache"),
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info(f"Initialized embeddings with model: {model_name}")
        
    def _init_vectorstore(self) -> None:
        """Initialize Chroma vector store."""
        persist_directory = self.vector_config.get("persist_directory", "./data/chromadb")
        collection_name = self.vector_config.get("collection_name", "lza_diff_logs")
        
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        
        # Initialize retriever
        similarity_threshold = self.retrieval_config.get("similarity_threshold", 0.7)
        max_results = self.retrieval_config.get("max_results", 10)
        
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "score_threshold": similarity_threshold,
                "k": max_results
            }
        )
        
        logger.info(f"Initialized Chroma vectorstore: {collection_name}")
        
    def _init_text_splitter(self) -> None:
        """Initialize text splitter for fallback chunking."""
        chunk_size = self.retrieval_config.get("chunk_size", 1000)
        chunk_overlap = self.retrieval_config.get("chunk_overlap", 200)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
    def _init_chunker(self) -> None:
        """Initialize custom diff chunker."""
        self.chunker = DiffChunker(self.retrieval_config)
        
    def index_diff_file(self, file_path: Path, force_reindex: bool = False) -> bool:
        """Index a single diff file using LangChain components.
        
        Args:
            file_path: Path to diff file
            force_reindex: Whether to reindex if already exists
            
        Returns:
            True if indexing was performed
        """
        filename = file_path.name
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract metadata from filename
            stack_name = self._extract_stack_name(filename)
            account_id = self._extract_account_id(filename)
            region = self._extract_region(filename)
            
            # Create custom chunks using our diff chunker
            content_chunks = self.chunker.chunk_diff_file(
                content, filename, stack_name, account_id, region
            )
            
            # Convert to LangChain Documents
            documents = []
            for chunk in content_chunks:
                # Create unique document ID
                doc_id = self._generate_doc_id(filename, chunk)
                
                # Check if already exists (simple approach)
                if not force_reindex:
                    try:
                        # Use proper ChromaDB filter format with $and operator
                        existing_docs = self.vectorstore.similarity_search(
                            chunk.content[:100],  # Use first 100 chars as search
                            k=1,
                            filter={
                                "$and": [
                                    {"filename": {"$eq": filename}},
                                    {"chunk_id": {"$eq": doc_id}}
                                ]
                            }
                        )
                        if existing_docs:
                            logger.debug(f"Skipping existing chunk: {doc_id}")
                            continue
                    except Exception as filter_error:
                        # Fallback: skip duplicate checking if filter fails
                        logger.debug(f"Filter check failed for {doc_id}, proceeding with indexing: {filter_error}")
                        pass
                
                # Enhanced metadata
                metadata = chunk.metadata.copy()
                metadata.update({
                    "chunk_id": doc_id,
                    "file_path": str(file_path),
                    "content_length": len(chunk.content),
                    "chunk_type": chunk.chunk_type.value,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line
                })
                
                doc = Document(
                    page_content=chunk.content,
                    metadata=metadata
                )
                documents.append(doc)
                
            if not documents:
                if force_reindex:
                    logger.warning(f"No new chunks to index for {filename}")
                else:
                    logger.debug(f"All chunks already indexed for {filename}")
                return False
                
            # Add documents to vector store
            ids = [doc.metadata["chunk_id"] for doc in documents]
            self.vectorstore.add_documents(documents, ids=ids)
            
            logger.info(f"Indexed {len(documents)} chunks from {filename}")
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
        
    def retrieve_context(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Retrieve relevant context using hybrid search strategy.
        
        Args:
            query: Query string
            filters: Optional metadata filters in ChromaDB format
            
        Returns:
            List of relevant documents ranked by hybrid scoring
        """
        try:
            # Step 1: Extract metadata filters from query
            extracted_filters = self._extract_metadata_filters(query)
            
            # Step 2: Combine with provided filters
            final_filters = self._combine_filters(filters, extracted_filters)
            
            # Step 3: For IAM-specific queries, prioritize IAM content
            if "iam" in query.lower():
                # First, get IAM-specific content
                iam_docs = self.search_iam_changes(query)
                # Then get general search results
                general_docs = self._hybrid_search(query, final_filters)
                ranked_docs = self._rerank_hybrid_results(general_docs, query)
                
                # Combine and deduplicate, prioritizing IAM content
                seen_ids = set()
                final_docs = []
                
                # Add IAM documents first (higher priority)
                for doc in iam_docs:
                    doc_id = doc.metadata.get("chunk_id")
                    if doc_id and doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        final_docs.append(doc)
                
                # Add general search results (lower priority)
                for doc in ranked_docs:
                    doc_id = doc.metadata.get("chunk_id")
                    if doc_id and doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        final_docs.append(doc)
                        
                max_results = self.retrieval_config.get("max_results", 10)
                return final_docs[:max_results]
            else:
                # Step 3: Hybrid search - keyword + semantic
                hybrid_results = self._hybrid_search(query, final_filters)
                
                # Step 4: Re-rank and deduplicate
                ranked_docs = self._rerank_hybrid_results(hybrid_results, query)
                
                logger.info(f"Hybrid search retrieved {len(ranked_docs)} documents")
                return ranked_docs
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _hybrid_search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute hybrid search combining keyword and semantic approaches."""
        max_results = self.retrieval_config.get("max_results", 10)
        
        # Keyword search: exact term matching
        keyword_docs = self._keyword_search(query, filters, max_results)
        
        # Semantic search: vector similarity
        semantic_docs = self._semantic_search(query, filters, max_results)
        
        return {
            "keyword_results": keyword_docs,
            "semantic_results": semantic_docs,
            "query": query,
            "filters": filters
        }
    
    def _keyword_search(self, query: str, filters: Optional[Dict[str, Any]], max_results: int) -> List[tuple]:
        """Keyword-based search using content matching."""
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        results = []
        for keyword in keywords:
            try:
                # Search for exact keyword matches in content
                docs = self.vectorstore.similarity_search(
                    keyword,  # Use individual keywords
                    k=max_results,
                    filter=filters
                )
                
                # Score based on keyword frequency and position
                for doc in docs:
                    score = self._calculate_keyword_score(doc.page_content, keywords)
                    results.append((doc, score, "keyword"))
                    
            except Exception as e:
                logger.debug(f"Keyword search failed for '{keyword}': {e}")
                
        return results
    
    def _semantic_search(self, query: str, filters: Optional[Dict[str, Any]], max_results: int) -> List[tuple]:
        """Semantic search using vector similarity."""
        try:
            # Use similarity search with scores
            docs_with_scores = self.vectorstore.similarity_search_with_score(
                query,
                k=max_results,
                filter=filters
            )
            
            # Convert scores (lower is better) to relevance scores (higher is better)
            results = []
            for doc, similarity_score in docs_with_scores:
                # Convert distance to relevance: 1 / (1 + distance)
                relevance_score = 1.0 / (1.0 + similarity_score)
                results.append((doc, relevance_score, "semantic"))
                
            return results
            
        except Exception as e:
            logger.debug(f"Semantic search failed: {e}")
            return []
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        import re
        
        # Remove common stop words and question words
        stop_words = {"what", "how", "where", "when", "why", "who", "which", "is", "are", "was", "were", 
                     "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
                     "specific", "changes", "made", "stacks"}
        
        # Extract words, keeping important technical terms
        words = re.findall(r'\b[A-Za-z][A-Za-z0-9]*\b', query.lower())
        
        # Filter and prioritize
        keywords = []
        for word in words:
            if word not in stop_words and len(word) > 2:
                keywords.append(word)
        
        # Add original query for phrase matching
        keywords.append(query.lower())
        
        return keywords
    
    def _calculate_keyword_score(self, content: str, keywords: List[str]) -> float:
        """Calculate keyword relevance score."""
        content_lower = content.lower()
        score = 0.0
        
        for keyword in keywords:
            # Count occurrences
            count = content_lower.count(keyword.lower())
            if count > 0:
                # Weight by keyword importance and frequency
                importance = len(keyword) / 20.0  # Longer terms = more important
                frequency_score = min(count / 5.0, 1.0)  # Diminishing returns
                score += importance * frequency_score
        
        return score
    
    def _rerank_hybrid_results(self, hybrid_results: Dict[str, Any], query: str) -> List[Document]:
        """Combine and re-rank hybrid search results."""
        keyword_results = hybrid_results["keyword_results"]
        semantic_results = hybrid_results["semantic_results"]
        
        # Combine results with weighting
        combined_scores = {}
        
        # Process keyword results (weight: 0.4)
        for doc, score, source in keyword_results:
            doc_id = doc.metadata.get("chunk_id", id(doc))
            if doc_id not in combined_scores:
                combined_scores[doc_id] = {"doc": doc, "keyword_score": 0.0, "semantic_score": 0.0}
            combined_scores[doc_id]["keyword_score"] = max(combined_scores[doc_id]["keyword_score"], score)
        
        # Process semantic results (weight: 0.6)
        for doc, score, source in semantic_results:
            doc_id = doc.metadata.get("chunk_id", id(doc))
            if doc_id not in combined_scores:
                combined_scores[doc_id] = {"doc": doc, "keyword_score": 0.0, "semantic_score": 0.0}
            combined_scores[doc_id]["semantic_score"] = max(combined_scores[doc_id]["semantic_score"], score)
        
        # Calculate final hybrid scores
        final_results = []
        for doc_id, data in combined_scores.items():
            # Weighted combination
            final_score = (0.4 * data["keyword_score"]) + (0.6 * data["semantic_score"])
            
            # Boost for IAM-specific content when IAM is in query
            if "iam" in query.lower():
                metadata = data["doc"].metadata
                if (metadata.get("section") == "iam_statement_table" or 
                    metadata.get("chunk_type") == "iam_section"):
                    final_score *= 1.5  # 50% boost for IAM content
            
            final_results.append((data["doc"], final_score))
        
        # Sort by final score (descending)
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        max_results = self.retrieval_config.get("max_results", 10)
        return [doc for doc, score in final_results[:max_results]]
    
    def _extract_metadata_filters(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract metadata filters from query text."""
        import re
        
        # Look for stack names
        stack_patterns = [
            r'\b(DependenciesStack|OperationsStack|LoggingStack|KeyStack)\b'
        ]
        
        for pattern in stack_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                stack_name = matches[0]
                # Use $in with all possible DependenciesStack filenames
                if 'DependenciesStack' in stack_name:
                    deps_files = [
                        'AWSAccelerator-DependenciesStack-537824365868-ap-southeast-2.diff',
                        'AWSAccelerator-DependenciesStack-238611950256-ap-southeast-2.diff',
                        'AWSAccelerator-DependenciesStack-781953648079-ap-southeast-2.diff',
                        'AWSAccelerator-DependenciesStack-504706990227-ap-southeast-2.diff',
                        'AWSAccelerator-DependenciesStack-145023093216-ap-southeast-2.diff'
                    ]
                    return {"filename": {"$in": deps_files}}
                break
        
        return None
    
    def _combine_filters(self, filters1: Optional[Dict], filters2: Optional[Dict]) -> Optional[Dict]:
        """Combine two filter dictionaries."""
        if not filters1 and not filters2:
            return None
        if not filters1:
            return filters2
        if not filters2:
            return filters1
        
        # Combine using $and operator
        return {"$and": [filters1, filters2]}
            
    def create_rag_chain(self, llm):
        """Create a RAG chain using LangChain LCEL.
        
        Args:
            llm: Language model to use for generation
            
        Returns:
            RAG chain
        """
        # Define prompt template
        prompt = ChatPromptTemplate.from_template("""
You are an AWS CloudFormation diff analyzer assistant. Use the following pieces of retrieved context 
from diff files to answer questions about CloudFormation changes, IAM modifications, and infrastructure updates.

Be specific and cite the source files when possible. If you don't know the answer based on the provided context, 
say so clearly.

Context from diff files:
{context}

Question: {question}

Answer:""")
        
        # Create retrieval chain
        def format_docs(docs):
            return "\n\n".join([
                f"File: {doc.metadata.get('filename', 'unknown')}\n"
                f"Stack: {doc.metadata.get('stack_name', 'unknown')}\n"
                f"Content:\n{doc.page_content}"
                for doc in docs
            ])
            
        rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return rag_chain
        
    def search_by_stack(self, stack_name: str, query: str = "") -> List[Document]:
        """Search within a specific stack.
        
        Args:
            stack_name: Name of the stack to search in
            query: Optional query text
            
        Returns:
            List of relevant documents
        """
        filters = {"stack_name": {"$eq": stack_name}}
        search_query = query or f"stack {stack_name}"
        
        return self.retrieve_context(search_query, filters)
        
    def search_iam_changes(self, query: str = "IAM") -> List[Document]:
        """Search for IAM-related changes.
        
        Args:
            query: Query text (defaults to "IAM")
            
        Returns:
            List of relevant documents
        """
        # Extract any stack filters from query
        stack_filters = self._extract_metadata_filters(query)
        
        # Search for IAM table chunks first
        iam_table_docs = self.vectorstore.similarity_search(
            query,
            k=self.retrieval_config.get("max_results", 10),
            filter=self._combine_filters({"section": {"$eq": "iam_statement_table"}}, stack_filters)
        )
        
        # Search for IAM-specific chunks
        iam_docs = self.vectorstore.similarity_search(
            query,
            k=self.retrieval_config.get("max_results", 10),
            filter=self._combine_filters({"chunk_type": {"$eq": "iam_section"}}, stack_filters)
        )
        
        # Also search general content for IAM mentions with lower threshold
        general_docs = self.vectorstore.similarity_search_with_score(
            f"IAM policy role statement {query}",
            k=self.retrieval_config.get("max_results", 10),
            filter=stack_filters
        )
        # Filter by lower threshold
        general_docs = [doc for doc, score in general_docs if score < 0.8]
        
        # Combine and deduplicate, prioritizing table chunks
        all_docs = iam_table_docs + iam_docs + general_docs
        seen_ids = set()
        unique_docs = []
        
        for doc in all_docs:
            doc_id = doc.metadata.get("chunk_id")
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_docs.append(doc)
                
        return unique_docs[:self.retrieval_config.get("max_results", 10)]
        
    def get_vectorstore_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            # Get collection info
            collection = self.vectorstore._collection
            count = collection.count()
            
            # Sample some documents to get metadata stats
            sample_docs = self.vectorstore.similarity_search("", k=100)
            
            # Analyze metadata
            file_counts = {}
            stack_counts = {}
            chunk_type_counts = {}
            
            for doc in sample_docs:
                metadata = doc.metadata
                
                filename = metadata.get("filename", "unknown")
                file_counts[filename] = file_counts.get(filename, 0) + 1
                
                stack_name = metadata.get("stack_name", "unknown")
                stack_counts[stack_name] = stack_counts.get(stack_name, 0) + 1
                
                chunk_type = metadata.get("chunk_type", "unknown")
                chunk_type_counts[chunk_type] = chunk_type_counts.get(chunk_type, 0) + 1
                
            return {
                "total_documents": count,
                "sample_size": len(sample_docs),
                "unique_files": len(file_counts),
                "unique_stacks": len(stack_counts),
                "chunk_type_distribution": chunk_type_counts,
                "top_files": dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "top_stacks": dict(sorted(stack_counts.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            logger.error(f"Failed to get vectorstore stats: {e}")
            return {"error": str(e)}
            
    def reset_vectorstore(self) -> None:
        """Reset the vector store."""
        try:
            # Get all document IDs and delete them
            collection = self.vectorstore._collection
            result = collection.get()
            
            if result['ids']:
                collection.delete(ids=result['ids'])
                logger.info(f"Deleted {len(result['ids'])} documents from vector store")
            else:
                logger.info("Vector store is already empty")
                
        except Exception as e:
            logger.error(f"Failed to reset vector store: {e}")
            # Try alternative approach - delete the entire collection and recreate
            try:
                import shutil
                from pathlib import Path
                persist_dir = Path(self.vector_config.get("persist_directory", "./data/chromadb"))
                if persist_dir.exists():
                    shutil.rmtree(persist_dir)
                    logger.info("Deleted ChromaDB directory and recreating...")
                    self._init_vectorstore()
            except Exception as e2:
                logger.error(f"Failed to reset by deleting directory: {e2}")
                raise
            
    def _extract_stack_name(self, filename: str) -> Optional[str]:
        """Extract stack name from filename."""
        # Pattern: account-region-stackname-timestamp.diff
        parts = filename.replace('.diff', '').split('-')
        if len(parts) >= 3:
            return '-'.join(parts[2:-1])  # Everything except account, region, timestamp
        return None
        
    def _extract_account_id(self, filename: str) -> Optional[str]:
        """Extract account ID from filename."""
        parts = filename.replace('.diff', '').split('-')
        if len(parts) >= 1 and parts[0].isdigit():
            return parts[0]
        return None
        
    def _extract_region(self, filename: str) -> Optional[str]:
        """Extract region from filename."""
        parts = filename.replace('.diff', '').split('-')
        if len(parts) >= 2:
            region_candidate = parts[1]
            # Basic validation for AWS region format
            import re
            if re.match(r'^[a-z]+-[a-z]+-\d+$', region_candidate):
                return region_candidate
        return None
        
    def _generate_doc_id(self, filename: str, chunk: ContentChunk) -> str:
        """Generate unique document ID."""
        import time
        import uuid
        
        # Create a more unique identifier using multiple factors
        content_hash = hashlib.md5(chunk.content.encode()).hexdigest()[:16]
        
        # Use chunk index and metadata for uniqueness
        metadata_str = f"{chunk.metadata.get('account_id', '')}_{chunk.metadata.get('region', '')}_{chunk.metadata.get('stack_name', '')}"
        
        # Generate truly unique ID with timestamp and UUID components
        unique_id = f"{filename}_{chunk.chunk_type.value}_{chunk.start_line}_{chunk.end_line}_{content_hash}_{metadata_str}"
        
        # Add a small random component to ensure absolute uniqueness
        random_suffix = str(uuid.uuid4())[:8]
        final_id = f"{hashlib.md5(unique_id.encode()).hexdigest()}_{random_suffix}"
        
        return final_id