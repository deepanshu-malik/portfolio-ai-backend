#!/usr/bin/env python3
"""
Document ingestion script for ChromaDB.
Loads markdown files from knowledge_base and stores them in ChromaDB.
"""

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from chromadb.config import Settings
from openai import OpenAI

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


def load_documents() -> List[Tuple[str, Dict[str, str]]]:
    """
    Load all markdown documents from the knowledge base.

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

                metadata = {
                    "category": category,
                    "source": md_file.stem,
                    "filename": md_file.name,
                }

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
    Chunk a document into smaller pieces.

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
                "chunk_index": len(chunks),
            }
            chunks.append((current_chunk.strip(), chunk_metadata))
            # Keep some overlap
            current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""

        current_chunk += para + "\n\n"

    # Add the last chunk
    if current_chunk.strip():
        chunk_metadata = {
            **metadata,
            "chunk_index": len(chunks),
        }
        chunks.append((current_chunk.strip(), chunk_metadata))

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
    Ingest document chunks into ChromaDB.

    Args:
        chunks: List of (content, metadata) tuples
        use_openai_embeddings: Whether to use OpenAI embeddings
    """
    # Create ChromaDB client
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(CHROMA_PERSIST_DIR),
            anonymized_telemetry=False,
        )
    )

    # Get or create collection
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
        doc_id = generate_doc_id(content, metadata)
        documents.append(content)
        metadatas.append(metadata)
        ids.append(doc_id)

    # Generate embeddings if using OpenAI
    embeddings = None
    if use_openai_embeddings:
        try:
            openai_client = OpenAI()
            logger.info("Generating OpenAI embeddings...")

            # Batch embeddings (max 2048 per request)
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
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

    # Persist
    client.persist()

    logger.info(f"Ingested {len(documents)} chunks into ChromaDB")


def main():
    """Main ingestion function."""
    logger.info("Starting document ingestion...")

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

    logger.info("Ingestion complete!")


if __name__ == "__main__":
    main()
