"""
Script to ingest Excel data into vector database.

Usage:
    python scripts/data_ingestion/ingest_excel_to_vector_db.py

This script:
1. Reads both Excel files
2. Extracts problem descriptions
3. Generates embeddings
4. Builds FAISS index
5. Saves to disk
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import pandas as pd
import logging
from typing import List, Dict

from app.services.vector_db.vector_search import VectorSearchService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_cgnet_problems(file_path: str) -> List[Dict]:
    """
    Load CGNet problems from Excel.

    Args:
        file_path: Path to Excel file

    Returns:
        List of problem dicts with metadata
    """
    logger.info(f"Loading CGNet problems from {file_path}")

    df = pd.read_excel(file_path)
    logger.info(f"Loaded {len(df)} rows")

    problems = []
    for idx, row in df.iterrows():
        # Skip rows without description
        if pd.isna(row.get('Description')):
            continue

        problem = {
            "description": str(row['Description']),
            "district": str(row.get('District', '')).strip(),
            "state": str(row.get('State', '')).strip(),
            "location": str(row.get('Location', '')) if not pd.isna(row.get('Location')) else '',
            "status": str(row.get('Status', '')) if not pd.isna(row.get('Status')) else '',
            "tag": str(row.get('Tags', '')) if not pd.isna(row.get('Tags')) else '',
            "date": str(row.get('On Air Date ', '')) if not pd.isna(row.get('On Air Date ')) else '',
            "problem_id": int(row.get('Problem ID')) if not pd.isna(row.get('Problem ID')) else None,
            "source": "cgnet_problems"
        }

        problems.append(problem)

    logger.info(f"Extracted {len(problems)} problems with descriptions")
    return problems


def load_cultural_stories(file_path: str) -> List[Dict]:
    """
    Load cultural stories/tagged problems from Excel.

    Args:
        file_path: Path to Excel file

    Returns:
        List of problem dicts with metadata
    """
    logger.info(f"Loading cultural stories from {file_path}")

    df = pd.read_excel(file_path)
    logger.info(f"Loaded {len(df)} rows")

    problems = []
    for idx, row in df.iterrows():
        # Skip rows without description
        if pd.isna(row.get('description')):
            continue

        problem = {
            "description": str(row['description']),
            "district": "Bastar",  # All from Bastar
            "state": "Chhattisgarh",
            "location": "",
            "status": "",
            "tag": str(row.get('tags', '')) if not pd.isna(row.get('tags')) else '',
            "date": str(row.get('date', '')) if not pd.isna(row.get('date')) else '',
            "problem_id": int(row.get('problem_id')) if not pd.isna(row.get('problem_id')) else None,
            "link": str(row.get('link', '')) if not pd.isna(row.get('link')) else '',
            "source": "cultural_stories"
        }

        problems.append(problem)

    logger.info(f"Extracted {len(problems)} problems with descriptions")
    return problems


def ingest_to_vector_db(problems: List[Dict]) -> None:
    """
    Ingest problems into vector database.

    Args:
        problems: List of problem dicts
    """
    logger.info(f"Ingesting {len(problems)} problems into vector database")

    # Initialize vector search service
    vector_service = VectorSearchService(
        index_path="backend/data/vector_db/knowledge_base.index",
        metadata_path="backend/data/vector_db/metadata.json"
    )

    # Extract texts and metadata
    texts = [p['description'] for p in problems]
    metadatas = problems

    # Add to vector database
    vector_service.add_documents(texts, metadatas)

    # Save to disk
    vector_service.save_index()

    # Print stats
    stats = vector_service.get_stats()
    logger.info(f"Vector database stats: {stats}")

    # Test search
    logger.info("\n=== Testing semantic search ===")
    test_queries = [
        "पानी की समस्या है",
        "राशन कार्ड नहीं बना",
        "सड़क ख़राब है",
    ]

    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        results = vector_service.search(query, top_k=3)
        for i, result in enumerate(results, 1):
            score = result['similarity_score']
            desc = result['metadata']['description'][:100]
            tag = result['metadata'].get('tag', 'N/A')
            logger.info(f"  {i}. Score: {score:.3f}, Tag: {tag}")
            logger.info(f"     {desc}...")


def main():
    """Main ingestion script."""
    logger.info("=== Starting Vector DB Ingestion ===\n")

    # File paths
    cgnet_file = "/Users/diptendu/Downloads/bastar problems (1).xlsx"
    stories_file = "/Users/diptendu/Downloads/bastar problems latest_rag.xlsx"

    # Load both files
    all_problems = []

    if os.path.exists(cgnet_file):
        cgnet_problems = load_cgnet_problems(cgnet_file)
        all_problems.extend(cgnet_problems)
        logger.info(f"✓ Loaded {len(cgnet_problems)} CGNet problems")
    else:
        logger.warning(f"✗ CGNet file not found: {cgnet_file}")

    if os.path.exists(stories_file):
        cultural_problems = load_cultural_stories(stories_file)
        all_problems.extend(cultural_problems)
        logger.info(f"✓ Loaded {len(cultural_problems)} cultural stories")
    else:
        logger.warning(f"✗ Stories file not found: {stories_file}")

    logger.info(f"\n✓ Total problems to ingest: {len(all_problems)}")

    if not all_problems:
        logger.error("No problems to ingest. Exiting.")
        return

    # Ingest into vector database
    ingest_to_vector_db(all_problems)

    logger.info("\n=== Ingestion Complete! ===")
    logger.info("Vector database is ready for RAG queries.")


if __name__ == "__main__":
    main()
