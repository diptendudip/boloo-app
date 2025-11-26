"""
RAG (Retrieval Augmented Generation) service.

This service enhances AI responses with context from historical cases.
"""

import logging
from typing import List, Dict, Optional

from app.services.vector_db.vector_search import get_vector_search_service

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval Augmented Generation."""

    def __init__(self, top_k: int = 3, similarity_threshold: float = 0.5):
        """
        Initialize RAG service.

        Args:
            top_k: Number of similar cases to retrieve
            similarity_threshold: Minimum similarity score (0.0-1.0)
        """
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.vector_service = get_vector_search_service()

    def get_relevant_context(
        self,
        problem_description: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve relevant historical cases for a problem.

        Args:
            problem_description: Current user's problem description
            top_k: Override default top_k

        Returns:
            List of similar historical cases with metadata
        """
        k = top_k or self.top_k

        try:
            similar_cases = self.vector_service.search(
                query=problem_description,
                top_k=k,
                similarity_threshold=self.similarity_threshold
            )

            logger.info(f"Retrieved {len(similar_cases)} relevant cases for RAG context")
            return similar_cases

        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}")
            return []

    def build_rag_prompt_context(
        self,
        problem_description: str,
        language: str = "hi"
    ) -> str:
        """
        Build context string to inject into GPT-4o prompt.

        Args:
            problem_description: Current user's problem
            language: 'hi' for Hindi, 'en' for English

        Returns:
            Formatted context string for system prompt
        """
        similar_cases = self.get_relevant_context(problem_description)

        if not similar_cases:
            return ""

        # Build context string
        if language == "hi":
            context_parts = [
                "**संदर्भ**: आपको बस्तर में पहले दर्ज की गई इन समान समस्याओं के बारे में पता होना चाहिए:",
                ""
            ]

            for i, case in enumerate(similar_cases, 1):
                meta = case['metadata']
                score = case['similarity_score']

                desc = meta.get('description', '')[:150]
                tag = meta.get('tag', 'समस्या')
                district = meta.get('district', '')

                context_parts.append(f"{i}. **{tag}** (समानता: {score:.0%})")
                context_parts.append(f"   विवरण: {desc}...")
                if district:
                    context_parts.append(f"   जिला: {district}")
                context_parts.append("")

            context_parts.append(
                "इन समान समस्याओं के आधार पर उपयोगकर्ता से प्रासंगिक प्रश्न पूछें। "
                "यदि कोई पैटर्न दिखाई देता है (जैसे कि बहुत से पानी की समस्याएं हैंडपंप से संबंधित हैं), "
                "तो उस पैटर्न के बारे में पूछें।"
            )
        else:
            context_parts = [
                "**Context**: You should be aware of these similar problems previously reported in Bastar:",
                ""
            ]

            for i, case in enumerate(similar_cases, 1):
                meta = case['metadata']
                score = case['similarity_score']

                desc = meta.get('description', '')[:150]
                tag = meta.get('tag', 'Problem')
                district = meta.get('district', '')

                context_parts.append(f"{i}. **{tag}** (Similarity: {score:.0%})")
                context_parts.append(f"   Description: {desc}...")
                if district:
                    context_parts.append(f"   District: {district}")
                context_parts.append("")

            context_parts.append(
                "Based on these similar problems, ask relevant follow-up questions. "
                "If you see a pattern (e.g., many water problems are related to handpumps), "
                "ask about that pattern."
            )

        return "\n".join(context_parts)

    def get_similar_tags(self, problem_description: str) -> List[str]:
        """
        Get most common tags from similar historical cases.

        Args:
            problem_description: Current problem description

        Returns:
            List of relevant tags
        """
        similar_cases = self.get_relevant_context(problem_description, top_k=5)

        if not similar_cases:
            return []

        # Extract tags and count occurrences
        tag_counts = {}
        for case in similar_cases:
            tag = case['metadata'].get('tag')
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        return [tag for tag, count in sorted_tags]

    def suggest_auto_tag(self, problem_description: str) -> Optional[str]:
        """
        Suggest automatic tag based on most similar case.

        Args:
            problem_description: Current problem description

        Returns:
            Suggested tag or None
        """
        similar_cases = self.get_relevant_context(problem_description, top_k=1)

        if not similar_cases:
            return None

        # Return tag of most similar case
        best_match = similar_cases[0]

        # Only suggest if similarity is high enough
        if best_match['similarity_score'] >= 0.7:
            return best_match['metadata'].get('tag')

        return None


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create singleton RAG service."""
    global _rag_service

    if _rag_service is None:
        _rag_service = RAGService()

    return _rag_service
