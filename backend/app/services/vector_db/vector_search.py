"""
Vector search service using FAISS for semantic similarity search.

This service handles:
- Loading/saving FAISS index
- Generating embeddings for text
- Semantic search for similar problems

NOTE: Heavy ML dependencies (FAISS, sentence-transformers, PyTorch) are gated behind
ENABLE_VECTOR_SEARCH environment variable. On Azure B1 tier (1.75GB RAM), these
libraries cause OOM. Set ENABLE_VECTOR_SEARCH=1 only on larger tiers (B2+).
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Gate heavy ML dependencies behind environment variable
ENABLE_VECTOR_SEARCH = os.getenv("ENABLE_VECTOR_SEARCH", "0") == "1"

if ENABLE_VECTOR_SEARCH:
    import faiss
    import numpy as np
    from sentence_transformers import SentenceTransformer
    logger.info("Vector search ENABLED - ML libraries loaded")
else:
    # Stub implementations when disabled
    faiss = None
    np = None
    SentenceTransformer = None
    logger.warning("Vector search DISABLED - Set ENABLE_VECTOR_SEARCH=1 to enable (requires B2+ tier)")


class VectorSearchService:
    """Service for semantic vector search using FAISS."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        index_path: str = "data/vector_db/knowledge_base.index",
        metadata_path: str = "data/vector_db/metadata.json"
    ):
        """
        Initialize vector search service.

        Args:
            model_name: Sentence transformer model name (supports Hindi/English)
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
        """
        self.model_name = model_name
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)

        # Create directories if they don't exist
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Load sentence transformer model
        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = 768  # paraphrase-multilingual-mpnet-base-v2 dimension

        # Load or create FAISS index
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict] = []

        if self.index_path.exists() and self.metadata_path.exists():
            self.load_index()
        else:
            logger.warning("Index not found. Creating empty index.")
            self.index = faiss.IndexFlatL2(self.dimension)

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for input text.

        Args:
            text: Input text (Hindi or English)

        Returns:
            768-dimensional embedding vector
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype('float32')
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict]
    ) -> None:
        """
        Add documents to the vector database.

        Args:
            texts: List of text descriptions
            metadatas: List of metadata dicts (one per text)
        """
        if len(texts) != len(metadatas):
            raise ValueError("texts and metadatas must have same length")

        logger.info(f"Adding {len(texts)} documents to vector database")

        # Generate embeddings
        embeddings = []
        for text in texts:
            emb = self.generate_embedding(text)
            embeddings.append(emb)

        embeddings_matrix = np.array(embeddings).astype('float32')

        # Add to FAISS index
        self.index.add(embeddings_matrix)

        # Add metadata
        self.metadata.extend(metadatas)

        logger.info(f"Total vectors in index: {self.index.ntotal}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Semantic search for similar documents.

        Args:
            query: Query text (Hindi or English)
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of matching documents with metadata and scores
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty. No results to return.")
            return []

        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)

        # Search FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))

        # Convert L2 distances to similarity scores (0-1 range)
        # L2 distance: lower is better, so we convert to similarity
        # similarity = 1 / (1 + distance)
        similarities = 1.0 / (1.0 + distances[0])

        # Build results
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx < len(self.metadata) and similarity >= similarity_threshold:
                result = {
                    "similarity_score": float(similarity),
                    "metadata": self.metadata[int(idx)]
                }
                results.append(result)

        logger.info(f"Found {len(results)} results for query: {query[:50]}...")
        return results

    def save_index(self) -> None:
        """Save FAISS index and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return

        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        logger.info(f"Saved FAISS index to {self.index_path}")

        # Save metadata
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved metadata to {self.metadata_path}")

    def load_index(self) -> None:
        """Load FAISS index and metadata from disk."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")

        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")

        # Load FAISS index
        self.index = faiss.read_index(str(self.index_path))
        logger.info(f"Loaded FAISS index from {self.index_path} ({self.index.ntotal} vectors)")

        # Load metadata
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        logger.info(f"Loaded {len(self.metadata)} metadata entries")

    def get_stats(self) -> Dict:
        """Get vector database statistics."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "model": self.model_name,
            "index_exists": self.index_path.exists(),
            "metadata_count": len(self.metadata)
        }


# Singleton instance
_vector_search_service: Optional[VectorSearchService] = None


def get_vector_search_service() -> VectorSearchService:
    """Get or create singleton vector search service."""
    global _vector_search_service

    if _vector_search_service is None:
        _vector_search_service = VectorSearchService()

    return _vector_search_service
