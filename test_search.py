from backend.app.services.rag_engine import (
    search_chunks_mmr
)

try:
    results = search_chunks_mmr(
        "What is machine learning?",
        1
    )

    print(f"Found {len(results)} chunks:")
    for metadata in results:
        print(metadata)
        print()
except Exception as e:
    print("Error during MMR search:", e)