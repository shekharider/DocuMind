from backend.app.services.rag_engine import (
    search_chunks,
    extract_chunk_ids
)

from backend.app.db.session import SessionLocal
from backend.app.db.models import DocumentChunk

db = SessionLocal()

results = search_chunks(
    "What is machine learning?",
    1
)

chunk_ids = extract_chunk_ids(results)

for chunk_id in chunk_ids:

    chunk = db.query(
        DocumentChunk
    ).filter(
        DocumentChunk.id == chunk_id
    ).first()

    print()
    print("=" * 100)
    print(chunk.content[:500])