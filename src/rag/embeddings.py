"""
Text embedding service using sentence-transformers.
"""

import logging
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    SentenceTransformer = None
    np = None

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and caching text embeddings."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize embedding service.
        
        Args:
            config: Embedding configuration
        """
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers not available. Install with: pip install sentence-transformers"
            )
            
        self.config = config
        self.model_name = config.get("model", "all-MiniLM-L6-v2")
        self.batch_size = config.get("batch_size", 32)
        self.cache_dir = Path(config.get("cache_dir", "./data/embeddings_cache"))
        self.enable_caching = config.get("enable_caching", True)
        
        # Ensure cache directory exists
        if self.enable_caching:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
        # Initialize model
        self._model = None
        
    def _get_model(self) -> SentenceTransformer:
        """Get or load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
        return self._model
        
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{self.model_name}_{text_hash}"
        
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for key."""
        return self.cache_dir / f"{cache_key}.pkl"
        
    def _load_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """Load embedding from cache."""
        if not self.enable_caching:
            return None
            
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_path}: {e}")
        return None
        
    def _save_to_cache(self, cache_key: str, embedding: List[float]) -> None:
        """Save embedding to cache."""
        if not self.enable_caching:
            return
            
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_path}: {e}")
            
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Check cache first
        cache_key = self._get_cache_key(text)
        cached_embedding = self._load_from_cache(cache_key)
        if cached_embedding is not None:
            logger.debug(f"Using cached embedding for text (length: {len(text)})")
            return cached_embedding
            
        # Generate embedding
        model = self._get_model()
        embedding = model.encode([text], batch_size=1)[0]
        embedding_list = embedding.tolist()
        
        # Cache the result
        self._save_to_cache(cache_key, embedding_list)
        
        logger.debug(f"Generated embedding for text (length: {len(text)})")
        return embedding_list
        
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        # Check cache for all texts
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            cached_embedding = self._load_from_cache(cache_key)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)
                
        # Generate embeddings for uncached texts
        if uncached_texts:
            logger.info(f"Generating embeddings for {len(uncached_texts)} texts")
            model = self._get_model()
            new_embeddings = model.encode(
                uncached_texts, 
                batch_size=self.batch_size,
                show_progress_bar=len(uncached_texts) > 10
            )
            
            # Fill in the embeddings and cache them
            for i, (idx, text) in enumerate(zip(uncached_indices, uncached_texts)):
                embedding_list = new_embeddings[i].tolist()
                embeddings[idx] = embedding_list
                
                # Cache the result
                cache_key = self._get_cache_key(text)
                self._save_to_cache(cache_key, embedding_list)
                
        logger.info(f"Generated/retrieved {len(embeddings)} embeddings")
        return embeddings
        
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model."""
        model = self._get_model()
        return model.get_sentence_embedding_dimension()
        
    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        if not self.enable_caching:
            return
            
        cache_files = list(self.cache_dir.glob("*.pkl"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")
                
        logger.info(f"Cleared {len(cache_files)} cache files")
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enable_caching:
            return {"enabled": False}
            
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "enabled": True,
            "cache_dir": str(self.cache_dir),
            "cached_embeddings": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }