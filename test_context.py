from backend.app.services.rag_engine import (
    search_chunks_mmr,
    extract_chunk_ids_from_mmr
)

from backend.app.db.session import SessionLocal
from backend.app.db.models import DocumentChunk

db = SessionLocal()

results = search_chunks_mmr(
    "What is machine learning?",
    1
)

chunk_ids = extract_chunk_ids_from_mmr(
    results
)

for chunk_id in chunk_ids:

    chunk = db.query(
        DocumentChunk
    ).filter(
        DocumentChunk.id == chunk_id
    ).first()

    if chunk:

        print()
        print("=" * 100)

        print(
            f"Chunk ID: {chunk.id}"
        )

        print(
            f"Document ID: {chunk.document_id}"
        )

        print()

        print(
            chunk.content[:500]
        )