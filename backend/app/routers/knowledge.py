"""
Knowledge base API endpoints for semantic search and RAG.

Provides:
- Semantic search for similar historical cases
- Vector database statistics
- Auto-tagging suggestions
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging

from app.services.rag.rag_service import get_rag_service
from app.services.vector_db.vector_search import get_vector_search_service
from app.utils.auth import get_current_user_or_dev
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])


class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Search query in Hindi or English")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    similarity_threshold: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity score")


class SemanticSearchResult(BaseModel):
    """Single search result."""
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    description: str = Field(..., description="Problem description")
    tag: Optional[str] = Field(None, description="Problem tag/category")
    district: Optional[str] = Field(None, description="District")
    problem_id: Optional[int] = Field(None, description="Problem ID")
    source: str = Field(..., description="Data source")


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""
    query: str
    results: List[SemanticSearchResult]
    total_results: int


class AutoTagRequest(BaseModel):
    """Request for auto-tag suggestion."""
    description: str = Field(..., description="Problem description")


class AutoTagResponse(BaseModel):
    """Response for auto-tag suggestion."""
    suggested_tag: Optional[str] = Field(None, description="Suggested tag")
    confidence: float = Field(..., description="Confidence score (0-1)")
    similar_cases_count: int = Field(..., description="Number of similar cases found")


class VectorDBStats(BaseModel):
    """Vector database statistics."""
    total_vectors: int
    dimension: int
    model: str
    index_exists: bool
    metadata_count: int


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Semantic search for similar historical cases.

    This endpoint uses FAISS vector search to find historically similar
    problems based on semantic similarity (not just keyword matching).

    Example:
        Query: "पानी की समस्या है गाँव में"
        Returns: All historical water-related problems
    """
    try:
        vector_service = get_vector_search_service()

        # Perform search
        results = vector_service.search(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )

        # Format results
        formatted_results = []
        for result in results:
            meta = result['metadata']
            formatted_results.append(SemanticSearchResult(
                similarity_score=result['similarity_score'],
                description=meta.get('description', ''),
                tag=meta.get('tag'),
                district=meta.get('district'),
                problem_id=meta.get('problem_id'),
                source=meta.get('source', 'unknown')
            ))

        return SemanticSearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results)
        )

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-tag", response_model=AutoTagResponse)
async def suggest_auto_tag(
    request: AutoTagRequest,
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Suggest automatic tag based on similar historical cases.

    Analyzes the problem description and suggests the most likely tag
    based on semantic similarity to previously tagged cases.

    Example:
        Description: "हमारे गाँव में हैंडपंप ख़राब हो गया है"
        Returns: { suggested_tag: "WATER_PROBLEM", confidence: 0.85 }
    """
    try:
        rag_service = get_rag_service()

        # Get suggested tag
        suggested_tag = rag_service.suggest_auto_tag(request.description)

        # Get similar cases for confidence calculation
        similar_cases = rag_service.get_relevant_context(request.description, top_k=5)

        # Calculate confidence based on best similarity score
        confidence = similar_cases[0]['similarity_score'] if similar_cases else 0.0

        return AutoTagResponse(
            suggested_tag=suggested_tag,
            confidence=confidence,
            similar_cases_count=len(similar_cases)
        )

    except Exception as e:
        logger.error(f"Error in auto-tag suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=VectorDBStats)
async def get_vector_db_stats(
    current_user: User = Depends(get_current_user_or_dev)
):
    """
    Get vector database statistics.

    Returns information about the knowledge base:
    - Number of vectors/cases indexed
    - Model information
    - Index status
    """
    try:
        vector_service = get_vector_search_service()
        stats = vector_service.get_stats()

        return VectorDBStats(**stats)

    except Exception as e:
        logger.error(f"Error getting vector DB stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def knowledge_health():
    """Health check for knowledge base service."""
    try:
        vector_service = get_vector_search_service()
        stats = vector_service.get_stats()

        is_healthy = stats['index_exists'] and stats['total_vectors'] > 0

        return {
            "status": "healthy" if is_healthy else "degraded",
            "vector_count": stats['total_vectors'],
            "message": "Knowledge base is operational" if is_healthy else "Index not loaded or empty"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": str(e)
        }
