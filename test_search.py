from backend.app.services.rag_engine import (
    search_chunks
)

results = search_chunks(
    "What is machine learning?",
    1
)

for metadata in results["metadatas"][0]:
    print(metadata)
    print()