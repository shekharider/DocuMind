from pypdf import PdfReader

import numpy as np

from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.app.core.config import settings

from langchain_chroma import Chroma
from langchain_chroma.vectorstores import maximal_marginal_relevance
from langchain_core.embeddings import Embeddings
import chromadb

# ============================================================================
# HUGGING FACE INFERENCE EMBEDDINGS ADAPTER (Render Memory-safe)
# ============================================================================

class HuggingFaceInferenceEmbeddings(Embeddings):
    """LangChain Embeddings adapter for Hugging Face Inference API."""

    def __init__(self, hf_token: str, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if not hf_token:
            raise ValueError("Hugging Face access token (HF_TOKEN) is not set in environment or config.")
        self.hf_token = hf_token.strip().strip('"').strip("'")
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json",
            "x-wait-for-model": "true"
        }

    def _query(self, texts: list[str]) -> list[list[float]]:
        import urllib.request
        import json
        import time

        payload = {"inputs": texts}
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self.headers,
            method="POST"
        )

        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    if response.status == 200:
                        res = json.loads(response.read().decode("utf-8"))
                        if isinstance(res, list):
                            return res
                        raise ValueError(f"Unexpected response format from HF API: {type(res)}")
            except urllib.error.HTTPError as e:
                # Handle model loading status (503 Service Unavailable)
                try:
                    err_content = e.read().decode("utf-8")
                    err_data = json.loads(err_content)
                    if "estimated_time" in err_data:
                        wait_time = min(float(err_data["estimated_time"]), 15.0)
                        time.sleep(wait_time)
                        continue
                except Exception:
                    pass
                if attempt == 4:
                    raise e
            except Exception as e:
                if attempt == 4:
                    raise e
                time.sleep(2)
        raise RuntimeError("Failed to retrieve embeddings from Hugging Face Inference API.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Hugging Face API has size/payload limits, so batch texts in sizes of 16.
        batch_size = 16
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self._query(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        # query is a single text, but we wrap it in a list to call _query and get back a list of one vector
        embeddings = self._query([text])
        return embeddings[0]


langchain_embeddings = HuggingFaceInferenceEmbeddings(settings.HF_TOKEN)


# ============================================================================
# CHROMA (LAZY INITIALIZATION)
# ============================================================================

_chroma_client = None
_collection = None


def get_collection():
    """Lazy-load Chroma collection.

    IMPORTANT: do not create PersistentClient/get_or_create_collection at
    module import time; Render startup can hang due to large resource
    initialization.
    """
    global _chroma_client, _collection

    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path="backend/chroma_dbs")
        _collection = _chroma_client.get_or_create_collection(
            name="documind_chunks"
        )

    return _collection



# ============================================================================
# LANGCHAIN CHROMA VECTOR STORE
# ============================================================================

# NOTE: Chroma initialization should not load the model; embeddings are only
# required when embeddings are computed (upload/query time).
def get_vector_store():
    """Lazy-create a LangChain Chroma vector store.

    This must not run at import time.
    """
    return Chroma(
        client=get_chroma_client(),
        collection_name="documind_chunks",
        embedding_function=langchain_embeddings,
    )


def get_chroma_client():
    """Get underlying Chroma persistent client lazily."""
    global _chroma_client
    if _chroma_client is None:
        # ensures get_collection() triggers client creation
        get_collection()
    return _chroma_client



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
    if not chunks:
        return

    contents = [chunk_data["content"] for chunk_data in chunks]
    embeddings = langchain_embeddings.embed_documents(contents)

    for chunk_data, embedding in zip(chunks, embeddings):
        get_collection().add(
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
    query_embedding = langchain_embeddings.embed_query(query)


    results = get_collection().query(
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
    query_embedding = langchain_embeddings.embed_query(query)


    results = get_collection().query(

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
    results = get_collection().get(where={"document_id": document_id}, include=["metadatas"])

    ids = []
    for _ in range(len(results.get("ids", []))):
        ids.append(results["ids"][_])
    if ids:
        get_collection().delete(ids=ids)


def delete_session_embeddings(session_id: int):
    """Delete all Chroma rows that belong to a given chat session."""
    results = get_collection().get(where={"session_id": session_id}, include=["metadatas"])
    ids = []
    for _ in range(len(results.get("ids", []))):
        ids.append(results["ids"][_])
    if ids:
        get_collection().delete(ids=ids)


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


# TEMPORARY RENDER MEMORY DIAGNOSTIC
# When enabled, we skip all embedding + retrieval work.




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

