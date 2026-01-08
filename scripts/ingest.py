#!/usr/bin/env python3
"""
Document ingestion script for ChromaDB with enhanced metadata.
Loads markdown files from knowledge_base and stores them with comprehensive metadata.
"""

import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import chromadb
from openai import OpenAI

from app.config import settings
from metadata_config import DOCUMENT_METADATA

# Load environment variables from .env file (for local development)
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "app" / "data" / "knowledge_base"
CHROMA_PERSIST_DIR = Path(__file__).parent.parent / "chromadb"
COLLECTION_NAME = "portfolio"

# Category mapping based on directory
CATEGORY_MAP = {
    "profile": "profile",
    "skills": "skills",
    "projects": "projects",
    "experience": "experience",
    "code_snippets": "code_snippets",
    "assessments": "assessments",
}


def extract_section_from_content(content: str) -> str:
    """Extract first H2 heading as section name"""
    match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
    return match.group(1) if match else "Overview"


def load_documents() -> List[Tuple[str, Dict[str, str]]]:
    """
    Load all markdown documents from the knowledge base with enhanced metadata.

    Returns:
        List of (content, metadata) tuples
    """
    documents = []

    for category_dir in KNOWLEDGE_BASE_PATH.iterdir():
        if not category_dir.is_dir():
            continue

        category = CATEGORY_MAP.get(category_dir.name, "general")

        for md_file in category_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                if not content.strip():
                    logger.warning(f"Empty file: {md_file}")
                    continue

                # Get enhanced metadata from config
                doc_config = DOCUMENT_METADATA.get(md_file.name, {})
                
                # Build base metadata
                metadata = {
                    "category": category,
                    "source": f"{category}/{md_file.name}",
                    "doc_id": md_file.stem,
                }
                
                # Add enhanced metadata
                if doc_config:
                    metadata.update({
                        "title": doc_config.get("title", md_file.stem),
                        "subcategory": doc_config.get("subcategory", category),
                        "content_type": doc_config.get("content_type", "technical"),
                        "section": doc_config.get("section", extract_section_from_content(content)),
                        "date_start": doc_config.get("date_start", ""),
                        "date_end": doc_config.get("date_end", ""),
                        "recency_score": doc_config.get("recency_score", 0.5),
                        "company": doc_config.get("company", "personal"),
                        "technologies": ",".join(doc_config.get("technologies", [])),
                        "concepts": ",".join(doc_config.get("concepts", [])),
                        "keywords": ",".join(doc_config.get("keywords", [])),
                        "question_types": ",".join(doc_config.get("question_types", [])),
                        "has_code": str(doc_config.get("has_code", False)),
                        "has_metrics": str(doc_config.get("has_metrics", False)),
                        "has_architecture": str(doc_config.get("has_architecture", False)),
                        "detail_level": doc_config.get("detail_level", "medium"),
                        # Intent relevance scores
                        "intent_quick_answer": doc_config.get("intent_relevance", {}).get("quick_answer", 0.0),
                        "intent_project_deepdive": doc_config.get("intent_relevance", {}).get("project_deepdive", 0.0),
                        "intent_experience_deepdive": doc_config.get("intent_relevance", {}).get("experience_deepdive", 0.0),
                        "intent_code_walkthrough": doc_config.get("intent_relevance", {}).get("code_walkthrough", 0.0),
                        "intent_skill_assessment": doc_config.get("intent_relevance", {}).get("skill_assessment", 0.0),
                        "intent_comparison": doc_config.get("intent_relevance", {}).get("comparison", 0.0),
                        "intent_tour": doc_config.get("intent_relevance", {}).get("tour", 0.0),
                        "intent_general": doc_config.get("intent_relevance", {}).get("general", 0.0),
                    })
                else:
                    logger.warning(f"No metadata config for {md_file.name}, using defaults")

                documents.append((content, metadata))
                logger.info(f"Loaded: {md_file.name} ({category})")

            except Exception as e:
                logger.error(f"Error loading {md_file}: {e}")

    return documents


def chunk_document(
    content: str,
    metadata: Dict[str, str],
    chunk_size: int = 1000,
    overlap: int = 100,
) -> List[Tuple[str, Dict[str, str]]]:
    """
    Chunk a document into smaller pieces with enhanced metadata.

    Uses paragraph-based chunking with fallback to size-based.

    Args:
        content: Document content
        metadata: Document metadata
        chunk_size: Maximum chunk size
        overlap: Overlap between chunks

    Returns:
        List of (chunk_content, chunk_metadata) tuples
    """
    chunks = []

    # Try paragraph-based chunking first
    paragraphs = content.split("\n\n")
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph exceeds chunk size, save current and start new
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunk_metadata = {
                **metadata,
                "chunk_id": f"{metadata['doc_id']}_{len(chunks)}",
                "chunk_index": len(chunks),
                "total_chunks": 0,  # Will be updated after all chunks created
            }
            chunks.append((current_chunk.strip(), chunk_metadata))
            # Keep some overlap
            current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""

        current_chunk += para + "\n\n"

    # Add the last chunk
    if current_chunk.strip():
        chunk_metadata = {
            **metadata,
            "chunk_id": f"{metadata['doc_id']}_{len(chunks)}",
            "chunk_index": len(chunks),
            "total_chunks": 0,
        }
        chunks.append((current_chunk.strip(), chunk_metadata))

    # Update total_chunks for all chunks
    total = len(chunks)
    for _, meta in chunks:
        meta["total_chunks"] = total

    return chunks


def generate_doc_id(content: str, metadata: Dict[str, str]) -> str:
    """Generate a unique document ID."""
    unique_string = f"{metadata.get('source', '')}_{metadata.get('chunk_index', 0)}_{content[:100]}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def ingest_to_chromadb(
    chunks: List[Tuple[str, Dict[str, str]]],
    use_openai_embeddings: bool = True,
) -> None:
    """
    Ingest document chunks into ChromaDB with enhanced metadata.

    Args:
        chunks: List of (content, metadata) tuples
        use_openai_embeddings: Whether to use OpenAI embeddings
    """
    # Create ChromaDB client
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
    )

    # Get or create collection - delete existing to refresh
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    logger.info(f"Created collection: {COLLECTION_NAME}")

    # Prepare data for insertion
    documents = []
    metadatas = []
    ids = []

    for content, metadata in chunks:
        # Convert numeric metadata to strings for ChromaDB
        clean_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (int, float)):
                clean_metadata[key] = str(value)
            elif isinstance(value, str):
                clean_metadata[key] = value
            else:
                clean_metadata[key] = str(value)
        
        documents.append(content)
        metadatas.append(clean_metadata)
        ids.append(clean_metadata["chunk_id"])

    # Generate embeddings if using OpenAI
    embeddings = None
    if use_openai_embeddings:
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            openai_client = OpenAI(api_key=api_key)
            logger.info("Generating OpenAI embeddings...")

            # Batch embeddings (max 2048 per request)
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                response = openai_client.embeddings.create(
                    model=settings.openai_embedding_model,
                    input=batch,
                )
                batch_embeddings = [e.embedding for e in response.data]
                all_embeddings.extend(batch_embeddings)
                logger.info(f"Generated embeddings for batch {i // batch_size + 1}")

            embeddings = all_embeddings

        except Exception as e:
            logger.warning(f"Failed to generate OpenAI embeddings: {e}")
            logger.info("Falling back to default ChromaDB embeddings")
            embeddings = None

    # Add to collection
    if embeddings:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )
    else:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    logger.info(f"Ingested {len(documents)} chunks into ChromaDB")
    logger.info(f"Sample metadata keys: {list(metadatas[0].keys())}")


def main():
    """Main ingestion function."""
    logger.info("Starting document ingestion with enhanced metadata...")

    # Check if knowledge base exists
    if not KNOWLEDGE_BASE_PATH.exists():
        logger.error(f"Knowledge base not found: {KNOWLEDGE_BASE_PATH}")
        sys.exit(1)

    # Load documents
    documents = load_documents()
    logger.info(f"Loaded {len(documents)} documents")

    if not documents:
        logger.error("No documents found to ingest")
        sys.exit(1)

    # Chunk documents
    all_chunks = []
    for content, metadata in documents:
        chunks = chunk_document(content, metadata)
        all_chunks.extend(chunks)

    logger.info(f"Created {len(all_chunks)} chunks")

    # Check for OpenAI API key
    use_openai = bool(os.environ.get("OPENAI_API_KEY"))
    if not use_openai:
        logger.warning("OPENAI_API_KEY not set, using default ChromaDB embeddings")

    # Ingest to ChromaDB
    ingest_to_chromadb(all_chunks, use_openai_embeddings=use_openai)

    logger.info("Ingestion complete with enhanced metadata!")
    logger.info("Enhanced metadata includes:")
    logger.info("  - Identity: doc_id, chunk_id, chunk_index, total_chunks")
    logger.info("  - Categorization: category, subcategory, content_type")
    logger.info("  - Source: source, title, section")
    logger.info("  - Temporal: date_start, date_end, recency_score")
    logger.info("  - Entities: company, technologies, concepts")
    logger.info("  - Retrieval: keywords, question_types, intent_relevance")
    logger.info("  - Quality: has_code, has_metrics, has_architecture, detail_level")


if __name__ == "__main__":
    main()
