from pypdf import PdfReader

import numpy as np

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)
from sentence_transformers import (
    SentenceTransformer
)
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

import chromadb

# ============================================================================
# EMBEDDING MODEL INITIALIZATION
# ============================================================================
# Initialize the embedding model used for both storage and retrieval
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# ============================================================================
# RAW CHROMA CLIENT (for direct chunk storage)
# ============================================================================
# Used by store_chunks_in_chroma() to persist chunks with metadata.
# This maintains compatibility with existing upload flow.

chroma_client = chromadb.PersistentClient(
    path="backend/chroma_dbs"
)

collection = chroma_client.get_or_create_collection(
    name="documind_chunks"
)


# ============================================================================
# LANGCHAIN EMBEDDINGS ADAPTER
# ============================================================================
# This adapter wraps SentenceTransformer to be compatible with LangChain's
# Embeddings interface, allowing LangChain methods to use our embedding model.

class SentenceTransformerEmbeddings(Embeddings):
    """
    LangChain Embeddings adapter for SentenceTransformer models.
    
    Converts numpy embeddings to lists for compatibility with Chroma.
    Implements the two required methods from LangChain's Embeddings ABC:
    - embed_documents(): batch embedding of document texts
    - embed_query(): single embedding of query text
    """
    
    def __init__(self, model):
        """
        Initialize with a SentenceTransformer model.
        
        Args:
            model: A SentenceTransformer instance
        """
        self.model = model
    
    def embed_documents(self, texts):
        """
        Embed a list of document texts.
        
        Args:
            texts (list): List of document strings to embed
            
        Returns:
            list: List of embeddings, each as a list of floats
        """
        embeddings = self.model.encode(texts)
        return [embedding.tolist() for embedding in embeddings]
    
    def embed_query(self, text):
        """
        Embed a single query text.
        
        Args:
            text (str): Query string to embed
            
        Returns:
            list: Single embedding as a list of floats
        """
        embedding = self.model.encode(text)
        return embedding.tolist()


# Initialize the LangChain embeddings adapter
langchain_embeddings = SentenceTransformerEmbeddings(
    model=embedding_model
)

# ============================================================================
# LANGCHAIN CHROMA VECTOR STORE
# ============================================================================
# This wraps the existing persistent Chroma collection for use with
# LangChain's retrieval methods (like max_marginal_relevance_search for MMR).
# 
# Key benefits:
# - Uses the same persistent Chroma database as the raw client
# - Enables LangChain's advanced retrieval strategies (MMR, similarity, etc.)
# - Maintains all metadata stored by store_chunks_in_chroma()

vector_store = Chroma(
    client=chroma_client,
    collection_name="documind_chunks",
    embedding_function=langchain_embeddings
)


# ============================================================================
# PDF TEXT EXTRACTION
# ============================================================================

def extract_text_from_pdf(
    pdf_path: str
):
    """
    Extract all text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Concatenated text from all pages
    """
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

def chunk_text(
    text: str
):
    """
    Split text into overlapping chunks using RecursiveCharacterTextSplitter.
    
    This splitter respects document structure:
    - Prefers splitting on paragraph breaks
    - Falls back to sentence boundaries
    - Finally splits on words
    - Last resort: split on characters
    
    Args:
        text (str): Text to chunk
        
    Returns:
        list: List of text chunks
    """
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


# ============================================================================
# CHUNK STORAGE IN CHROMA (Unchanged)
# ============================================================================
# This function stores chunks directly in the raw Chroma collection.
# It remains unchanged from the original implementation.

def store_chunks_in_chroma(
    chunks,
    document_id,
    session_id,
    filename
):
    """
    Store document chunks and their embeddings in Chroma DB.
    
    Each chunk is embedded and stored with metadata for filtering and
    source retrieval. Uses the raw Chroma collection directly.
    
    Args:
        chunks (list): List of dicts with keys: id, content, chunk_index
        document_id (int): ID of the source document
        session_id (int): ID of the chat session (for filtering)
        filename (str): Original filename (for source attribution)
    """
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
                    "filename": filename,
                    "chunk_index": chunk_data["chunk_index"]
                }
            ]
        )


# ============================================================================
# MMR (MAXIMUM MARGINAL RELEVANCE) SEARCH - NEW IMPLEMENTATION
# ============================================================================
# Replaces plain similarity search with MMR retrieval.
#
# MMR balances diversity and relevance:
# - Finds the k most relevant chunks by embedding similarity
# - Among those top candidates (fetch_k), selects diverse results
# - Uses lambda_mult to weight relevance vs diversity
#   - 0.0: pure diversity (select most different chunks)
#   - 1.0: pure relevance (same as similarity search)
#   - 0.7: balance between relevance and diversity (default)

def search_chunks_mmr(
    query: str,
    session_id: int,
    k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.7
):
    """
    Search for document chunks using Maximum Marginal Relevance (MMR).
    
    MMR retrieval finds diverse, relevant chunks by:
    1. Embedding the query
    2. Finding the top fetch_k most similar chunks to the query
    3. Selecting k diverse results from those fetch_k candidates
    4. Ranking results by relevance*lambda_mult + diversity*(1-lambda_mult)
    
    This reduces redundancy in retrieved chunks and improves answer diversity.
    
    Args:
        query (str): The search query/question
        session_id (int): ID of the session (filters results)
        k (int): Number of results to return (default: 5)
        fetch_k (int): Number of candidates to search among (default: 20)
                       Higher values = more candidates to choose from = slower
                       Typically 3-5x of k
        lambda_mult (float): Diversity weight (default: 0.7)
                            - 1.0 = pure relevance (normal similarity)
                            - 0.7 = balance relevance and diversity
                            - 0.0 = pure diversity
    
    Returns:
        list: List of LangChain Document objects with metadata
              Each doc has:
              - page_content: the chunk text
              - metadata: {chunk_id, document_id, session_id, filename, chunk_index}
    """
    # Perform MMR search using LangChain's vector store
    # The where filter ensures we only search within the specified session
    results = vector_store.max_marginal_relevance_search(
        query=query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
        where={
            "session_id": session_id
        }
    )
    
    return results


def extract_chunk_ids_from_mmr(results):
    """
    Extract chunk IDs from MMR search results.
    
    MMR returns LangChain Document objects with metadata.
    This extracts the chunk_id from each result's metadata.
    
    Args:
        results (list): List of Document objects from max_marginal_relevance_search
        
    Returns:
        list: List of chunk IDs (integers)
    """
    return [
        result.metadata["chunk_id"]
        for result in results
    ]


# ============================================================================
# CONTEXT RETRIEVAL - UPDATED FOR MMR
# ============================================================================
# Updated to use MMR search instead of plain similarity search.

def retrieve_context(
    query,
    session_id,
    db,
    top_k=5
):
    """
    Retrieve relevant document chunks and their full text for a query.
    
    Flow:
    1. Search for relevant chunks using MMR
    2. Extract chunk IDs from search results
    3. Fetch full chunk text from SQLite (for complete content)
    4. Combine texts into a single context string
    
    Args:
        query (str): The user's question
        session_id (int): ID of the chat session
        db: SQLAlchemy database session
        top_k (int): Number of chunks to retrieve (default: 5)
        
    Returns:
        dict: {
            "context": concatenated text of retrieved chunks,
            "chunk_ids": list of chunk IDs used for attribution
        }
    """
    # Use MMR to find relevant chunks
    # fetch_k is set to 3x top_k to give MMR more diversity options
    results = search_chunks_mmr(
        query=query,
        session_id=session_id,
        k=top_k,
        fetch_k=top_k * 3,
        lambda_mult=0.7
    )

    # Extract chunk IDs from MMR results
    chunk_ids = extract_chunk_ids_from_mmr(results)

    from backend.app.db.models import (
        DocumentChunk
    )

    context_parts = []

    # Fetch full chunk text from SQLite for complete context
    # (Chroma stores chunks for search, SQLite stores for full retrieval)
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

    return {
        "context": "\n\n".join(
            context_parts
        ),
        "chunk_ids": chunk_ids
    }