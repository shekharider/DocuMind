from pypdf import PdfReader

import numpy as np

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from langchain_chroma.vectorstores import maximal_marginal_relevance
from langchain_core.embeddings import Embeddings

import chromadb

# ============================================================================
# EMBEDDING MODEL INITIALIZATION
# ============================================================================
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ============================================================================
# RAW CHROMA CLIENT (for direct chunk storage)
# ============================================================================
chroma_client = chromadb.PersistentClient(path="backend/chroma_dbs")
collection = chroma_client.get_or_create_collection(name="documind_chunks")

# ============================================================================
# LANGCHAIN EMBEDDINGS ADAPTER
# ============================================================================


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain Embeddings adapter for SentenceTransformer."""

    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        embeddings = self.model.encode(texts)
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text):
        embedding = self.model.encode(text)
        return embedding.tolist()


langchain_embeddings = SentenceTransformerEmbeddings(model=embedding_model)

# ============================================================================
# LANGCHAIN CHROMA VECTOR STORE
# ============================================================================

vector_store = Chroma(
    client=chroma_client,
    collection_name="documind_chunks",
    embedding_function=langchain_embeddings,
)

# ============================================================================
# PDF TEXT EXTRACTION
# ============================================================================


def extract_text_from_pdf(pdf_path: str):
    """Extract all text content from a PDF file."""
    reader = PdfReader(pdf_path)

    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


# ============================================================================
# TEXT CHUNKING
# ============================================================================


def chunk_text(text: str):
    """Split text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


# ============================================================================
# CHUNK STORAGE IN CHROMA
# ============================================================================


def store_chunks_in_chroma(chunks, document_id, session_id, filename):
    """Store document chunks and their embeddings in Chroma DB."""
    for chunk_data in chunks:
        embedding = embedding_model.encode(chunk_data["content"]).tolist()

        collection.add(
            ids=[str(chunk_data["id"])],
            embeddings=[embedding],
            metadatas=[
                {
                    "chunk_id": chunk_data["id"],
                    "document_id": document_id,
                    "session_id": session_id,
                    "filename": filename,
                    "chunk_index": chunk_data["chunk_index"],
                }
            ],
        )


# ============================================================================
# MMR (MAXIMUM MARGINAL RELEVANCE) SEARCH
# ============================================================================


def search_chunks_mmr(
    query: str,
    session_id: int,
    k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.7,
):
    """Search for document chunks using Maximum Marginal Relevance (MMR)."""
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        where={"session_id": session_id},
        include=["embeddings", "metadatas"],
    )

    embeddings = results.get("embeddings", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    if len(embeddings) == 0:
        return []

    selected_indexes = maximal_marginal_relevance(
        np.array(query_embedding, dtype=np.float32),
        embeddings,
        k=k,
        lambda_mult=lambda_mult,
    )

    return [
        metadatas[index]
        for index in selected_indexes
        if index < len(metadatas) and metadatas[index]
    ]


def extract_chunk_ids_from_mmr(results):
    """Extract chunk IDs from MMR results."""
    return [
        result["chunk_id"]
        for result in results
        if result and "chunk_id" in result
    ]


def search_chunk_ids_by_similarity(query: str, session_id: int, top_k: int = 5):
    """Fallback search for older Chroma rows."""
    query_embedding = embedding_model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"session_id": session_id},
        include=["metadatas"],
    )

    metadatas = results.get("metadatas", [[]])[0]

    return [
        metadata["chunk_id"]
        for metadata in metadatas
        if metadata and "chunk_id" in metadata
    ]


# ============================================================================
# CHROMA DELETE HELPERS (kept; used elsewhere if needed)
# ============================================================================


def delete_document_embeddings(document_id: int):
    """Delete all Chroma rows that belong to a given document."""
    results = collection.get(where={"document_id": document_id}, include=["metadatas"])
    ids = []
    for _ in range(len(results.get("ids", []))):
        ids.append(results["ids"][_])
    if ids:
        collection.delete(ids=ids)


def delete_session_embeddings(session_id: int):
    """Delete all Chroma rows that belong to a given chat session."""
    results = collection.get(where={"session_id": session_id}, include=["metadatas"])
    ids = []
    for _ in range(len(results.get("ids", []))):
        ids.append(results["ids"][_])
    if ids:
        collection.delete(ids=ids)


# ============================================================================
# CONTEXT FETCH HELPERS
# ============================================================================


def _fetch_chunk_texts_by_ids(chunk_ids, session_id, db):
    """Fetch chunk texts from SQLite for ids, preserving chunk_ids order."""
    from backend.app.db.models import Document, DocumentChunk

    chunk_id_set = set(chunk_ids)

    rows = (
        db.query(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(
            DocumentChunk.id.in_(chunk_id_set),
            Document.session_id == session_id,
        )
        .all()
    )

    id_to_content = {row[0].id: row[0].content for row in rows}

    context_parts = []
    for cid in chunk_ids:
        if cid in id_to_content:
            context_parts.append(id_to_content[cid])

    return "\n\n".join(context_parts)


# ============================================================================
# SINGLE-QUERY RETRIEVAL
# ============================================================================


def retrieve_context_singlequery(query, session_id, db, top_k=5):
    """Original behavior: MMR once, then similarity fallback, then SQLite fetch."""
    results = search_chunks_mmr(
        query=query,
        session_id=session_id,
        k=top_k,
        fetch_k=top_k * 3,
        lambda_mult=0.7,
    )

    chunk_ids = extract_chunk_ids_from_mmr(results)

    if not chunk_ids:
        chunk_ids = search_chunk_ids_by_similarity(
            query=query,
            session_id=session_id,
            top_k=top_k,
        )

    context = _fetch_chunk_texts_by_ids(chunk_ids, session_id, db)

    return {"context": context, "chunk_ids": chunk_ids}


# ============================================================================
# MULTI-QUERY RETRIEVAL (MQR)
# ============================================================================


def generate_search_queries(question: str, num_queries: int = 3, max_retries: int = 2):
    """Generate alternative search queries using Groq.

    Returns a list of strings length <= num_queries.
    If generation fails, returns [].
    """

    try:
        from backend.app.services.llm_service import client

        prompt = f"""
You are a search query rewriting assistant.
Generate {num_queries} concise alternative search queries for the user's question.
Rules:
- Keep the original meaning.
- Use different wording/syntax.
- Output ONLY a JSON array of strings.

User question:
{question}
"""

        for _ in range(max_retries + 1):
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )

                text = resp.choices[0].message.content or ""

                import json

                queries = json.loads(text.strip())
                if not isinstance(queries, list):
                    return []

                cleaned = [str(q).strip() for q in queries if str(q).strip()]
                return cleaned[:num_queries]
            except Exception:
                continue

        return []
    except Exception:
        return []


def _dedupe_preserve_order(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def retrieve_context_multiquery(
    query,
    session_id,
    db,
    top_k_per_query: int = 5,
    final_chunk_count_min: int = 5,
    final_chunk_count_max: int = 10,
):
    """MultiQuery retrieval: original query + N generated variants.

    Uses existing MMR retrieval per query, merges chunk_ids, dedupes, caps,
    then fetches chunk texts from SQLite.

    API response format unchanged.
    """

    variants = generate_search_queries(query, num_queries=3)
    if not variants:
        # safeguard per requirements: if generation fails, fall back.
        return retrieve_context_singlequery(
            query=query,
            session_id=session_id,
            db=db,
            top_k=top_k_per_query,
        )

    queries = [query] + variants

    all_chunk_ids = []
    for q in queries:
        results = search_chunks_mmr(
            query=q,
            session_id=session_id,
            k=top_k_per_query,
            fetch_k=top_k_per_query * 3,
            lambda_mult=0.7,
        )

        chunk_ids = extract_chunk_ids_from_mmr(results)
        if not chunk_ids:
            chunk_ids = search_chunk_ids_by_similarity(
                query=q,
                session_id=session_id,
                top_k=top_k_per_query,
            )

        all_chunk_ids.extend(chunk_ids)

    all_chunk_ids = _dedupe_preserve_order(all_chunk_ids)
    if not all_chunk_ids:
        return {"context": "", "chunk_ids": []}

    final_cap = min(
        max(final_chunk_count_min, len(all_chunk_ids)),
        final_chunk_count_max,
    )
    final_chunk_ids = all_chunk_ids[:final_cap]

    context = _fetch_chunk_texts_by_ids(final_chunk_ids, session_id, db)

    return {"context": context, "chunk_ids": final_chunk_ids}


# ============================================================================
# PUBLIC ENTRYPOINT (used by /chat/ask)
# ============================================================================


def retrieve_context(query, session_id, db, top_k=5):
    """Enhanced retrieve_context: uses MultiQuery retrieval with safeguards."""
    try:
        return retrieve_context_multiquery(
            query=query,
            session_id=session_id,
            db=db,
            top_k_per_query=top_k,
            final_chunk_count_min=top_k,
            final_chunk_count_max=max(top_k * 2, 10),
        )
    except Exception:
        # safeguard: never break ask endpoint; fall back to single-query.
        return retrieve_context_singlequery(
            query=query,
            session_id=session_id,
            db=db,
            top_k=top_k,
        )

