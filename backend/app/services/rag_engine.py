from pypdf import PdfReader

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)
from sentence_transformers import (
    SentenceTransformer
)

import chromadb

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(
    path="backend/chroma_dbs"
)

collection = chroma_client.get_or_create_collection(
    name="documind_chunks"
)

def extract_text_from_pdf(
    pdf_path: str
):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def chunk_text(
    text: str
):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_text(text)

    return chunks 

def store_chunks_in_chroma(
    chunks,
    document_id,
    session_id
):

    for chunk_data in chunks:

        embedding = embedding_model.encode(
            chunk_data["content"]
        ).tolist()

        collection.add(
            ids=[
                str(chunk_data["id"])
            ],

            embeddings=[
                embedding
            ],

            metadatas=[
                {
                    "chunk_id": chunk_data["id"],
                    "document_id": document_id,
                    "session_id": session_id,
                    "chunk_index": chunk_data["chunk_index"]
                }
            ]
        )

def search_chunks(
    query: str,
    session_id: int,
    top_k: int = 5
):

    query_embedding = embedding_model.encode(
        query
    ).tolist()

    results = collection.query(

        query_embeddings=[
            query_embedding
        ],

        n_results=top_k,

        where={
            "session_id": session_id
        }
    )

    return results

def extract_chunk_ids(results):

    return [
        metadata["chunk_id"]
        for metadata in results["metadatas"][0]
    ]


def retrieve_context(
    query,
    session_id,
    db,
    top_k=5
):

    results = search_chunks(
        query,
        session_id,
        top_k
    )

    chunk_ids = extract_chunk_ids(
        results
    )

    from backend.app.db.models import (
        DocumentChunk
    )

    context_parts = []

    for chunk_id in chunk_ids:

        chunk = db.query(
            DocumentChunk
        ).filter(
            DocumentChunk.id == chunk_id
        ).first()

        if chunk:
            context_parts.append(
                chunk.content
            )

    return "\n\n".join(
        context_parts
    )